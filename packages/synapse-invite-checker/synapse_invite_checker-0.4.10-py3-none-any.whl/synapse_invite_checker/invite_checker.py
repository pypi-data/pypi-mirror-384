# Copyright (C) 2020,2025 Famedly
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import base64
import functools
import logging
from collections.abc import Collection
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Literal, cast
from urllib.parse import quote, urlparse

import emoji
from cachetools import TTLCache, keys
from jwcrypto import jwk, jws
from OpenSSL.crypto import (
    FILETYPE_ASN1,
    FILETYPE_PEM,
    X509,
    X509Store,
    X509StoreContext,
    dump_certificate,
    load_certificate,
)
from synapse.api.constants import (
    AccountDataTypes,
    Direction,
    EventContentFields,
    EventTypes,
    HistoryVisibility,
    JoinRules,
    Membership,
    RoomCreationPreset,
)
from synapse.api.errors import SynapseError
from synapse.api.filtering import Filter
from synapse.api.room_versions import RoomVersion
from synapse.config import ConfigError
from synapse.config._base import Config
from synapse.events import EventBase
from synapse.handlers.pagination import SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME
from synapse.http.client import BaseHttpClient
from synapse.http.proxyagent import ProxyAgent
from synapse.http.server import JsonResource
from synapse.module_api import NOT_SPAM, ModuleApi, errors
from synapse.server import HomeServer
from synapse.storage.database import LoggingTransaction
from synapse.types import (
    Requester,
    ScheduledTask,
    StateMap,
    TaskStatus,
    UserID,
    create_requester,
)
from synapse.types.handlers import ShutdownRoomParams
from synapse.types.state import StateFilter
from synapse.util.metrics import measure_func
from twisted.internet.defer import Deferred
from twisted.internet.ssl import PrivateCertificate, optionsForClientTLS, platformTrust
from twisted.web.client import HTTPConnectionPool
from twisted.web.iweb import IAgent, IPolicyForHTTPS
from zope.interface import implementer

from synapse_invite_checker.config import DefaultPermissionConfig, InviteCheckerConfig
from synapse_invite_checker.permissions import InviteCheckerPermissionsHandler
from synapse_invite_checker.rest.messenger_info import (
    INFO_API_PREFIX,
    MessengerFindByIkResource,
    MessengerInfoResource,
    MessengerIsInsuranceResource,
)
from synapse_invite_checker.types import (
    EpaRoomTimestampResults,
    FederationList,
    TimType,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from synapse.storage.roommember import RoomsForUser

# We need to access the private API in some places, in particular the store and the homeserver
# ruff: noqa: SLF001


def cached(cache):
    """Simplified cached decorator from cachetools, that allows calling an async function."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            k = keys.hashkey(*args, **kwargs)
            with suppress(KeyError):
                return cache[k]

            v = await func(*args, **kwargs)

            with suppress(ValueError):
                cache[k] = v

            return v

        def cache_clear():
            cache.clear()

        wrapper.cache = cache
        wrapper.cache_clear = cache_clear

        return functools.update_wrapper(wrapper, func)

    return decorator


@implementer(IPolicyForHTTPS)
class MtlsPolicy:
    def __init__(self, config: InviteCheckerConfig):
        super().__init__()

        self.url = urlparse(config.federation_list_url)

        # Handle different cases based on URL scheme and mTLS requirements
        client_cert = None
        if config.federation_list_client_cert:
            # If a certificate is provided, always use it
            with open(config.federation_list_client_cert) as file:
                content = file.read()

            client_cert = PrivateCertificate.loadPEM(content)
        elif self.url.scheme == "https" and config.federation_list_require_mtls:
            # HTTPS with required mTLS but no certificate
            msg = "No mtls cert and scheme is https with mTLS required"
            raise Exception(msg)
        elif self.url.scheme not in ("http", "https"):
            # Neither HTTP nor HTTPS
            msg = "URL scheme must be either http or https"
            raise Exception(msg)

        self.options = optionsForClientTLS(
            self.url.hostname, platformTrust(), clientCertificate=client_cert
        )

    def creatorForNetloc(self, hostname: bytes, port: int):
        if (
            self.url.hostname
            and self.url.hostname.encode("utf-8") != hostname
            or self.url.port != port
        ):
            logger.error(
                "Destination mismatch: %r:%r != %r:%r",
                self.url.hostname,
                self.url.port,
                hostname,
                port,
            )
            msg = "Invalid connection attempt by MTLS Policy"
            raise Exception(msg)
        return self.options


class FederationAllowListClient(BaseHttpClient):
    """Custom http client since we need to pass a custom agent to enable mtls"""

    def __init__(
        self,
        hs: HomeServer,
        config: InviteCheckerConfig,
        # We currently assume the configured endpoint is always trustworthy and bypass the proxy
        # ip_allowlist: Optional[IPSet] = None,
        # ip_blocklist: Optional[IPSet] = None,
        # use_proxy: bool = False,
    ):
        super().__init__(hs)

        pool = HTTPConnectionPool(self.reactor)

        mstls_policy = MtlsPolicy(config)
        proxy_agent = ProxyAgent(
            reactor=self.reactor,
            proxy_reactor=hs.get_reactor(),
            connectTimeout=15,
            contextFactory=cast(IPolicyForHTTPS, mstls_policy),
            pool=pool,
        )
        self.agent = cast(IAgent, proxy_agent)


BASE_API_PREFIX = "/_synapse/client/com.famedly/tim"


class InviteChecker:
    __version__ = "0.4.10"

    def __init__(self, config: InviteCheckerConfig, api: ModuleApi):
        self.api = api
        # This needs to be on the Class itself so that metrics functions that measure
        # requests and database calls will function. Specifically for @measure_func
        self.server_name = api.server_name
        self.clock = api._hs.get_clock()

        self.config = config
        # Can not do this as part of parse_config() as there is no access to the server
        # name yet
        self.config.default_permissions.maybe_update_server_exceptions(
            self.api._hs.config.server.server_name
        )

        self.federation_list_client = FederationAllowListClient(api._hs, self.config)

        self.api.register_spam_checker_callbacks(user_may_invite=self.user_may_invite)
        self.api.register_spam_checker_callbacks(
            user_may_join_room=self.user_may_join_room
        )
        self.api.register_third_party_rules_callbacks(
            on_create_room=self.on_create_room
        )
        self.api.register_third_party_rules_callbacks(
            on_upgrade_room=self.on_upgrade_room
        )
        self.api.register_third_party_rules_callbacks(
            check_event_allowed=self.check_event_allowed
        )
        self.api.register_spam_checker_callbacks(
            check_login_for_spam=self.check_login_for_spam
        )

        # Make sure this doesn't get initialized until after the default permissions
        # were potentially modified to account for the local server template
        self.permissions_handler = InviteCheckerPermissionsHandler(
            self.api,
            self.config,
            self.is_domain_insurance,
            self.config.default_permissions,
        )

        self.task_scheduler = api._hs.get_task_scheduler()

        if (
            self.config.room_scan_run_interval_ms > 0
            and self.api.should_run_background_tasks()
        ):
            # The docstring for 'looping_background_call()' is slightly incorrect
            # > Waits msec initially before calling f for the first time.
            # Should be
            # > Calls f after waiting msec, then repeats. This is an inexact, "best effort"
            # > figure when the reactor/event loop is under heavy load
            self.api.looping_background_call(
                self.room_scan, self.config.room_scan_run_interval_ms
            )

        if self.config.tim_type == TimType.PRO:
            # The TiMessengerInformation API resource
            self.resource = JsonResource(api._hs)
            MessengerInfoResource(self.api, self.config).register(self.resource)
            MessengerIsInsuranceResource(
                self.api, self.config, self.is_domain_insurance
            ).register(self.resource)
            MessengerFindByIkResource(
                self.api, self.config, self._fetch_federation_list
            ).register(self.resource)
            self.api.register_web_resource(INFO_API_PREFIX, self.resource)

        self.api._clock.call_when_running(self.after_startup)

        logger.info("Module initialized at %s", BASE_API_PREFIX)

    @staticmethod
    def parse_config(config: dict[str, Any]) -> InviteCheckerConfig:
        logger.error("PARSE CONFIG")

        _default_permissions = config.get("default_permissions", {})
        # The default for permissions when not declared in the configuration as a
        # template is now part of the PermissionConfig class. If you need to change a
        # default, do so there.
        _config = InviteCheckerConfig(DefaultPermissionConfig(**_default_permissions))

        _config.title = config.get("title", _config.title)
        _config.description = config.get("description", _config.description)
        _config.contact = config.get("contact", _config.contact)
        _config.federation_list_client_cert = config.get(
            "federation_list_client_cert", ""
        )
        _config.federation_list_url = config.get("federation_list_url", "")
        _config.federation_list_require_mtls = config.get(
            "federation_list_require_mtls", _config.federation_list_require_mtls
        )
        _config.gematik_ca_baseurl = config.get("gematik_ca_baseurl", "")

        if not _config.federation_list_url or not _config.gematik_ca_baseurl:
            msg = "Incomplete federation list config"
            raise Exception(msg)

        if (
            _config.federation_list_url.startswith("https")
            and _config.federation_list_require_mtls
            and not _config.federation_list_client_cert
        ):
            msg = "Federation list config requires an mtls (PEM) cert for https connections when mTLS is required"
            raise Exception(msg)

        # Validate federation_list_require_mtls is a boolean
        if not isinstance(_config.federation_list_require_mtls, bool):
            msg = "`federation_list_require_mtls` must be a boolean"
            raise ConfigError(msg)

        # Check that the configuration is defined. This allows a grace period for
        # migration. For now, just issue a warning in the logs. The default of 'pro'
        # is set inside InviteCheckerConfig
        _tim_type = config.get("tim-type", "").lower()
        if not _tim_type:
            logger.warning(
                "Please remember to set `tim-type` in your configuration. Defaulting to 'Pro' mode"
            )

        elif _tim_type == "epa":
            _config.tim_type = TimType.EPA
        elif _tim_type == "pro":
            _config.tim_type = TimType.PRO
        else:
            msg = "`tim-type` setting is not a recognized value. Please fix."
            raise ConfigError(msg)

        _allowed_room_versions = config.get("allowed_room_versions", ["9", "10"])
        if not _allowed_room_versions or not isinstance(_allowed_room_versions, list):
            msg = "Allowed room versions must be formatted as a list."
            raise ConfigError(msg)

        _config.allowed_room_versions = [
            # Coercing into a string, in case the yaml loader thought it was an int
            str(_room_ver)
            for _room_ver in _allowed_room_versions
        ]

        run_interval = Config.parse_duration(config.get("room_scan_run_interval", "1h"))
        clamp_minimum_to = Config.parse_duration("1m")

        # If 'room_scan_run_interval' is not set to 0 for disabling the room scan
        # completely, make sure anything less than the minimum of 1 minute is ignored
        _config.room_scan_run_interval_ms = (
            max(run_interval, clamp_minimum_to) if run_interval > 0 else run_interval
        )

        insured_room_scan_section = config.get("insured_only_room_scan", {})
        if not isinstance(insured_room_scan_section, dict):
            msg = "`insured_only_room_scan` should be configured as a dictionary"
            raise ConfigError(msg)

        # Only default enable this room scan if in EPA mode
        enable_insured_room_scan = insured_room_scan_section.get(
            "enabled", _config.tim_type == TimType.EPA
        )
        # But also prevent it running in PRO mode completely
        enable_insured_room_scan = (
            False if _config.tim_type == TimType.PRO else enable_insured_room_scan
        )
        _config.insured_room_scan_options.enabled = enable_insured_room_scan

        epa_room_grace_period = Config.parse_duration(
            insured_room_scan_section.get("grace_period", "1w")
        )
        # For now, Gematik spec requires invites to count as room participation, but this
        # can lead to a room never being considered for epa user kicking. Allow an
        # enforceable maximum on this that is optional
        epa_room_invites_grace_period = Config.parse_duration(
            insured_room_scan_section.get("invites_grace_period", 0)
        )

        _config.insured_room_scan_options.grace_period_ms = epa_room_grace_period
        _config.insured_room_scan_options.invites_grace_period_ms = (
            epa_room_invites_grace_period
        )

        # This option is considered for all server modes unlike 'insured_only_room_scan'
        inactive_room_scan_section = config.get("inactive_room_scan", {})
        if not isinstance(inactive_room_scan_section, dict):
            msg = "`inactive_room_scan` should be formatted as a dictionary"
            raise ConfigError(msg)

        enable_inactive_room_scan = inactive_room_scan_section.get("enabled", True)
        _config.inactive_room_scan_options.enabled = enable_inactive_room_scan

        # "26w" calculates as 6 months
        inactive_room_scan_grace_period = Config.parse_duration(
            inactive_room_scan_section.get("grace_period", "26w")
        )
        _config.inactive_room_scan_options.grace_period_ms = (
            inactive_room_scan_grace_period
        )

        _override_public_room_federation = config.get(
            "override_public_room_federation", _config.override_public_room_federation
        )
        if not isinstance(_override_public_room_federation, bool):
            msg = "`override_public_room_federation` must be a boolean"
            raise ConfigError(msg)
        _config.override_public_room_federation = _override_public_room_federation

        _prohibit_world_readable_rooms = config.get(
            "prohibit_world_readable_rooms", _config.prohibit_world_readable_rooms
        )
        if not isinstance(_prohibit_world_readable_rooms, bool):
            msg = "`prohibit_world_readable_rooms` must be a boolean"
            raise ConfigError(msg)
        _config.prohibit_world_readable_rooms = _prohibit_world_readable_rooms

        _block_invites_into_dms = config.get(
            "block_invites_into_dms", _config.block_invites_into_dms
        )
        _config.block_invites_into_dms = _block_invites_into_dms

        _limit_reactions = config.get("limit_reactions", _config.limit_reactions)
        if not isinstance(_limit_reactions, bool):
            msg = "`limit_reactions` must be a boolean"
            raise ConfigError(msg)
        _config.limit_reactions = _limit_reactions

        return _config

    def after_startup(self) -> None:
        _ = Deferred.fromCoroutine(self._after_startup())

    async def _after_startup(self) -> None:
        """
        To be called when the reactor is running. Validates that the epa setting matches
        the insurance setting in the federation list.
        """
        try:
            fed_list = await self._fetch_federation_list()
            if self.config.tim_type == TimType.EPA and not fed_list.is_insurance(
                self.api._hs.config.server.server_name
            ):
                logger.warning(
                    "This server has enabled ePA Mode in its config, but is not found on "
                    "the Federation List as an Insurance Domain!"
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "The server had an issue retrieving the Federation List: %r", e
            )

    async def _raw_federation_list_fetch(self) -> str:
        resp = await self.federation_list_client.get_raw(
            self.config.federation_list_url
        )
        return resp.decode()

    async def _raw_gematik_root_ca_fetch(self) -> dict:
        return await self.api._hs.get_proxied_http_client().get_json(
            f"{self.config.gematik_ca_baseurl}/ECC/ROOT-CA/roots.json"
        )

    async def _raw_gematik_intermediate_cert_fetch(self, cn: str) -> bytes:
        return await self.api._hs.get_proxied_http_client().get_raw(
            f"{self.config.gematik_ca_baseurl}/ECC/SUB-CA/{quote(cn.replace(' ', '_'), safe='')}.der"
        )

    def _load_cert_b64(self, cert: str) -> X509:
        return load_certificate(FILETYPE_ASN1, base64.b64decode(cert))

    @cached(cache=TTLCache(maxsize=1, ttl=60 * 60))
    async def _fetch_federation_list(
        self,
    ) -> FederationList:
        """
        Fetch the raw data for the federation list, verify it is authentic and parse
        the data into a usable format

        Returns:
            a FederationList object

        """
        raw_list = await self._raw_federation_list_fetch()
        jws_verify = jws.JWS()
        jws_verify.deserialize(raw_list, alg="BP256R1")
        jws_verify.allowed_algs = ["BP256R1"]

        jwskey = self._load_cert_b64(jws_verify.jose_header["x5c"][0])

        # TODO(Nico): Fetch the ca only once a week
        store = X509Store()
        roots = await self._raw_gematik_root_ca_fetch()
        for r in roots:
            rawcert = r["cert"]
            if rawcert:
                store.add_cert(self._load_cert_b64(rawcert))

        chain = load_certificate(
            FILETYPE_ASN1,
            await self._raw_gematik_intermediate_cert_fetch(
                jwskey.get_issuer().CN or ""
            ),
        )
        store_ctx = X509StoreContext(store, jwskey, chain=[chain])
        store_ctx.verify_certificate()

        key = jwk.JWK.from_pem(dump_certificate(FILETYPE_PEM, jwskey))

        jws_verify.verify(key, alg="BP256R1")

        if jws_verify.payload is None:
            msg = "Empty federation list"
            raise Exception(msg)

        # Validate incoming, potentially incomplete or corrupt data
        return FederationList.model_validate_json(jws_verify.payload)

    async def is_domain_allowed(self, domain: str) -> bool:
        """
        See if a domain is found on the Federation List. If it was not, refetch the list
        to try again.
        """
        fed_list = await self._fetch_federation_list()
        if fed_list.allowed(domain):
            return True

        # Per A_25537:
        # The domain wasn't found but the list may have changed since the last look.
        # Re-fetch the list and try again. See:
        # https://gemspec.gematik.de/docs/gemSpec/gemSpec_TI-M_Basis/gemSpec_TI-M_Basis_V1.1.1/#A_25537
        self._fetch_federation_list.cache_clear()
        fed_list = await self._fetch_federation_list()
        return fed_list.allowed(domain)

    async def is_domain_insurance(self, domain: str) -> bool:
        """See if a domain was considered an insurance domain per the Federation List"""
        fed_list = await self._fetch_federation_list()
        return fed_list.is_insurance(domain)

    async def on_upgrade_room(
        self, _: Requester, room_version: RoomVersion, is_requester_admin: bool = False
    ) -> None:
        if (
            not is_requester_admin
            and room_version.identifier not in self.config.allowed_room_versions
        ):
            raise SynapseError(
                400,
                f"Room version ('{room_version}') not allowed",
                errors.Codes.FORBIDDEN,
            )

    async def user_may_join_room(
        self, user: str, room_id: str, is_invited: bool
    ) -> Literal["NOT_SPAM"] | errors.Codes:
        """
        This is used to check that a local user can join a room. Invites to remote
        public rooms MUST be denied. Invites to local rooms are allowed(unless it is an
        EPA server, in which case it should not get here)
        Args:
            user:
            room_id:
            is_invited:

        Returns:

        """
        if not is_invited:
            # Do we have the creation event of the room state?
            state_mapping: StateMap[EventBase] = (
                await self.api._storage_controllers.state.get_current_state(
                    room_id,
                    StateFilter.from_types(
                        [(EventTypes.Create, None), (EventTypes.JoinRules, None)]
                    ),
                )
            )

            creation_event = state_mapping.get((EventTypes.Create, ""))
            if not creation_event:
                # This happens because we do not have the state of the room. If this was
                # an invite(which includes 'invite_room_state') we would not be here. It
                # is highly likely that this means the room is remote. Since remote
                # rooms with no invite are not allowed, deny the request. Local rooms
                # that do not have state should be in the act of purging, in which case
                # we do not want to allow that join anyway.
                logger.debug(
                    "Denying join of '%s' to room '%s' because local server has no state(which represents a remote room)",
                    user,
                    room_id,
                )
                return errors.Codes.FORBIDDEN

            # There was no invite, but we already have the state of the room. Deny
            # public rooms if the room's creator's domain isn't the same as the local
            # server
            room_creator = UserID.from_string(creation_event.sender)
            if room_creator.domain != self.server_name:
                join_rules = state_mapping.get((EventTypes.JoinRules, ""))
                # all rooms should have join_rules, make sure
                if join_rules is None:
                    logger.warning(
                        "Room state of '%s' does not contain 'join_rules", room_id
                    )
                    return errors.Codes.FORBIDDEN

                if join_rules.content["join_rule"] == JoinRules.PUBLIC:
                    # There are no public remote rooms.
                    logger.debug(
                        "Forbidding join of '%s' to remote PUBLIC room '%s'",
                        user,
                        room_id,
                    )
                    return errors.Codes.FORBIDDEN

            # Room was created by a local user
            return NOT_SPAM

        else:
            # Try and see if the invite event had any initial room state data. For now,
            # this requires a database call, but if https://github.com/element-hq/synapse/issues/18230
            # becomes a thing, we won't need it anymore. It is possible that room_data
            # can be None. Logically however, it would only be None if there was no
            # invite. Since those conditions are checked for above, this should be safe
            room_data = await self.api._store.get_invite_for_local_user_in_room(
                user, room_id
            )
            if room_data is None:
                # If for some reason this data is missing, deny and bail. Someone is doing
                # something fishy
                logger.warning(
                    "Forbidding join of '%s' to room '%s' because invite data could not be found",
                    user,
                    room_id,
                )
                return errors.Codes.FORBIDDEN

            invite_event = await self.api._store.get_event(room_data.event_id)

            create_event_senders_domain = None
            is_public = True

            # Sort out the conditions
            for _event in invite_event.unsigned.get("invite_room_state", []):
                if (
                    _event["type"] == EventTypes.JoinRules
                    and _event["content"]["join_rule"] != JoinRules.PUBLIC
                ):
                    is_public = False
                if _event["type"] == EventTypes.Create:
                    create_event_senders_domain = UserID.from_string(
                        _event["sender"]
                    ).domain

            if is_public and create_event_senders_domain != self.server_name:
                logger.debug(
                    "Forbidding joining '%s' to invited room '%s' because room is PUBLIC",
                    user,
                    room_id,
                )
                return errors.Codes.FORBIDDEN

            return NOT_SPAM

    async def check_event_allowed(
        self, event: EventBase, context: StateMap[EventBase]
    ) -> tuple[bool, dict | None]:
        """
        Check the 'event' to see if it is allowed to exist. This takes place before
        the event is actually stored.
        Args:
            event: The unpersisted EventBase for the new Event
            context: The StateMapping for the new Event, from just before the new Event

        Returns: tuple of bool, for if the Event is 'allowed' and an optional dict of the
        replacement to use for the new event, in case modification is needed. WARNING:
        this has hazardous potential to break federation, and it is extremely unlikely
        we will ever use it

        Raises: SynapseError(400, M_BAD_JSON) if a reaction annotation has more than a
            single grapheme cluster when this restriction is enabled in settings
        """
        # This call check has many places it can be used, short-circuit out as swiftly
        # as is feasible
        # Never touch anything from another server
        if not self.api.is_mine(event.sender):
            return True, None

        if not event.is_state():
            # Only judge m.reaction when it is not a state event
            if self.config.limit_reactions and event.type == EventTypes.Reaction:
                key: str = event.content["m.relates_to"]["key"]

                # Using `is_emoji()` will not check for emoji variations(such as skin
                # tone or gender identifiers), but `purely_emoji()` does. So, first
                # check that it is an emoji(which will exclude normal numbers and
                # letters) and then check that there is only a single emoji(while
                # accommodating the aforementioned emoji variations). `emoji_list()`
                # does seem to handle the variations correctly(based on some limited
                # testing)
                if not emoji.purely_emoji(key) or len(emoji.emoji_list(key)) > 1:
                    # Normally with this API, it is expected to return a bool to
                    # indicate a failure to comply, however this raises a 403 error with
                    # the FORBIDDEN code, and gematik wants it to be a 400 with BAD_JSON.
                    raise SynapseError(
                        400,
                        "Only single emoji reactions are allowed",
                        errors.Codes.BAD_JSON,
                    )

            # Otherwise, we only check state events
            return True, None
        # Important Note: This callback also runs during room creation, and may end up
        # being appropriate for checking the same things we check in `on_create_room()`.
        # However, this callback is run for *every single event created* and should be
        # kept as "light weight" as possible

        # Forbid "m.room.join_rules" being anything but "private" for EPA, and only being
        # "public" on PRO if "m.federate" is set to True in the creation event
        if (
            event.type == EventTypes.JoinRules
            and event.content["join_rule"] == JoinRules.PUBLIC
        ):
            # EPA gets no public rooms, full stop
            if self.config.tim_type == TimType.EPA:
                return False, None
            creation_event = context.get((EventTypes.Create, ""))
            # `m.federate` defaults to True if unspecified
            if creation_event and creation_event["content"]:
                federated_flag = creation_event["content"].get(
                    EventContentFields.FEDERATE, True
                )
            # Remember to account for the override disabler
            # TODO: fix this possible reference before assignment
            if federated_flag and self.config.override_public_room_federation:
                return False, None

        # If configured, forbid "m.room.history_visibility" to be set as "world_readable"
        elif (
            self.config.prohibit_world_readable_rooms
            and event.type == EventTypes.RoomHistoryVisibility
            and event.content["history_visibility"] == HistoryVisibility.WORLD_READABLE
        ):
            return False, None

        return True, None

    async def on_create_room(
        self,
        requester: Requester,
        request_content: dict[str, Any],
        is_request_admin: bool,
    ) -> None:
        """
        Raise a SynapseError if creating a room should be denied. Currently, this checks
        * invites
        * room version
        * room public-ness via room creation presets
        """
        # visibility can be either "public" or "private". If not included, it defaults to "private"
        room_visibility: str = request_content.get("visibility", "private")
        # preset can be any of "private_chat", "trusted_private_chat" or "public_chat"
        # Do not allow "public_chat". Default is based on setting of visibility
        room_preset: str = request_content.get(
            "preset",
            (
                RoomCreationPreset.PUBLIC_CHAT
                if room_visibility == "public"
                else RoomCreationPreset.PRIVATE_CHAT
            ),
        )
        # Determine based on above that the room is probably public
        is_public = (
            room_preset == RoomCreationPreset.PUBLIC_CHAT or room_visibility == "public"
        )

        if self.config.tim_type == TimType.PRO:
            creation_content = request_content.get("creation_content", {})
            # m.federate defaults to True if unspecified
            can_federate = creation_content.get("m.federate", True)

            if can_federate and is_public:
                if self.config.override_public_room_federation:
                    logger.debug("Overriding `m.room.create` to disable federation")
                    request_content.setdefault("creation_content", {}).update(
                        {"m.federate": False}
                    )
                else:
                    logger.warning(
                        "Room creation with a public room allowed to federate detected."
                    )

        # Forbid EPA servers from creating any kind of public room
        if self.config.tim_type == TimType.EPA and is_public:
            raise SynapseError(
                400,
                "Creation of a public room is not allowed",
                errors.Codes.FORBIDDEN,
            )

        if is_request_admin:
            return

        # Unlike `user_may_invite()`, `on_create_room()` only runs with the inviter being
        # a local user; the invitee can be local/remote. Unfortunately, the spam check module
        # function `user_may_create_room()` only accepts the user creating the room and
        # has no other information provided.

        invite_list: list[str] = request_content.get("invite", [])
        # Per A_25538, only a single additional user may be invited to a room during
        # creation. See:
        # https://gemspec.gematik.de/docs/gemSpec/gemSpec_TI-M_Basis/gemSpec_TI-M_Basis_V1.1.1/#A_25538
        # Interesting potential error here, they display an http error code of 400, but
        # then say to use "M_FORBIDDEN". Pretty sure that is a typo
        if len(invite_list) > 1:
            raise SynapseError(
                403,
                "When creating a room, a maximum of one participant can be invited directly",
                errors.Codes.FORBIDDEN,
            )

        inviter = requester.user.to_string()
        for invitee in invite_list:
            res = await self.user_may_invite(inviter, invitee)
            if res != "NOT_SPAM":
                raise SynapseError(
                    403,
                    f"Room not created as user ({invitee}) is not allowed to be invited",
                    errors.Codes.FORBIDDEN,
                )

        # The room version should always be a string to accommodate arbitrary unstable
        # room versions. If it was not explicitly requested, the homeserver defaults
        # will be used. Make sure to check that instance as well
        room_version: str = request_content.get(
            "room_version", self.api._hs.config.server.default_room_version.identifier
        )

        if room_version not in self.config.allowed_room_versions:
            raise SynapseError(
                400,
                f"Room version ('{room_version}') not allowed",
                errors.Codes.FORBIDDEN,
            )

    async def check_login_for_spam(
        self,
        user_id: str,
        _device_id: str | None,
        _initial_display_name: str | None,
        _request_info: Collection[tuple[str | None, str]],
        _auth_provider_id: str | None = None,
    ) -> Literal["NOT_SPAM"] | errors.Codes:
        # Default permissions are populated automatically when fetching them. This
        # ensures users can see the default permissions in their client when they sign
        # in.
        await self.permissions_handler.get_permissions(user_id)
        return NOT_SPAM

    async def user_may_invite(
        self, inviter: str, invitee: str, room_id: str | None = None
    ) -> Literal["NOT_SPAM"] | errors.Codes:
        # Verify that local users can't invite into their DMs as verified by a few
        # tests in the Testsuite. In the context of calling this directly from
        # `on_create_room()` above, there may not be a room_id yet.
        if self.api.is_mine(inviter) and room_id and self.config.block_invites_into_dms:
            direct = await self.api.account_data_manager.get_global(
                inviter, AccountDataTypes.DIRECT
            )
            if direct:
                for user, roomids in direct.items():
                    if room_id in roomids and user != invitee:
                        # Can't invite to DM!
                        logger.debug(
                            "Preventing invite since %s already has a DM with %s",
                            inviter,
                            invitee,
                        )
                        return errors.Codes.FORBIDDEN

        inviter_domain = UserID.from_string(inviter).domain
        invitee_domain = UserID.from_string(invitee).domain

        # Step 1a, check federation allow list. See:
        # https://gemspec.gematik.de/docs/gemSpec/gemSpec_TI-M_Basis/gemSpec_TI-M_Basis_V1.1.1/#A_25534
        if not (
            await self.is_domain_allowed(inviter_domain)
            and await self.is_domain_allowed(invitee_domain)
        ):
            logger.warning(
                "Discarding invite between domains: (%s) and (%s)",
                inviter_domain,
                invitee_domain,
            )
            return errors.Codes.FORBIDDEN

        # Step 1b
        # Per AF_10233: Deny incoming remote invites if in ePA mode(which means the
        # local user is an 'insured') and if the remote domain is type 'insurance'.
        if await self.is_domain_insurance(
            inviter_domain
        ) and await self.is_domain_insurance(invitee_domain):
            logger.warning(
                "Discarding invite from between insured users: %s and %s",
                inviter,
                invitee,
            )
            return errors.Codes.FORBIDDEN

        # Find out if this is a public room
        # The domains are different, or the first section would have caught it. The same
        # context as above applies, there may not yet be a room_id if this is a room
        # creation in progress
        if room_id and (not self.api.is_mine(inviter) or not self.api.is_mine(invitee)):
            state_mapping: StateMap[EventBase] = (
                await self.api._storage_controllers.state.get_current_state(
                    room_id,
                    StateFilter.from_types([(EventTypes.JoinRules, None)]),
                )
            )
            event = state_mapping.get((EventTypes.JoinRules, ""))
            if event and event.content["join_rule"] == JoinRules.PUBLIC:
                logger.debug(
                    "Forbidding invite to a local public room to a remote user (%s -> %s)",
                    inviter,
                    invitee,
                )
                return errors.Codes.FORBIDDEN

        # Step 2, check invite settings
        # Skip remote users as we can't check their account data
        if self.api.is_mine(invitee):
            if not await self.api.check_user_exists(invitee):
                logger.warning(
                    "Blocking invite to non-existent local user '%s'", invitee
                )
                return errors.Codes.FORBIDDEN

            if not await self.permissions_handler.is_user_allowed(invitee, inviter):
                logger.debug(
                    "Not allowing invite since local user (%s) did not allow the remote user (%s) in their permissions",
                    invitee,
                    inviter,
                )
                return errors.Codes.FORBIDDEN

        logger.debug(
            "Allowing invite since no other permission checks block. (%s -> %s)",
            invitee,
            inviter,
        )

        return NOT_SPAM

    async def get_all_room_ids(self) -> set[str]:
        """Retrieve all room IDS."""

        # There is an PRIMARY index on room_id
        def f(txn: LoggingTransaction) -> set[str]:
            sql = "SELECT room_id FROM rooms"
            txn.execute(sql)
            return {room_id for (room_id,) in txn.fetchall()}

        return await self.api._store.db_pool.runInteraction("get_rooms", f)

    @measure_func("get_timestamps_from_eligible_events_for_epa_room_purge")
    async def get_timestamps_from_eligible_events_for_epa_room_purge(
        self, room_id
    ) -> EpaRoomTimestampResults:
        """
        Retrieve and parse the room PRO members that left into a timestamp of the
        latest event, or the timestamp of the create event if there were no PRO members
        in the room

        Returns None when no events were found for a room
        """
        state_mapping: StateMap[EventBase] = (
            await self.api._storage_controllers.state.get_current_state(
                room_id,
                StateFilter.from_types(
                    [(EventTypes.Member, None), (EventTypes.Create, None)]
                ),
            )
        )

        leave_event_timestamps = set()
        invite_event_timestamps = set()
        create_event_ts = None

        for (state_type, state_key), event in state_mapping.items():
            if state_type == EventTypes.Create:
                create_event_ts = event.origin_server_ts

            elif state_type == EventTypes.Member:
                users_domain = UserID.from_string(state_key).domain
                if not await self.is_domain_insurance(users_domain):
                    if event.membership == Membership.LEAVE:
                        leave_event_timestamps.add(event.origin_server_ts)

                    elif event.membership == Membership.INVITE:
                        invite_event_timestamps.add(event.origin_server_ts)

        return EpaRoomTimestampResults(
            max(invite_event_timestamps) if invite_event_timestamps else None,
            max(leave_event_timestamps) if leave_event_timestamps else None,
            create_event_ts,
        )

    @measure_func("get_timestamp_of_last_eligible_activity_in_room")
    async def get_timestamp_of_last_eligible_activity_in_room(
        self, room_id: str
    ) -> int | None:
        """
        A two-staged approach to finding the last activity in a room.
        First, search a room for the last message(either encrypted or plaintext) or
        creation event timestamp in that room(which ever is found to be most recent).
        This approach works best for local only rooms or rooms that were initialized
        locally.

        Second, if none of those were found, it's likely this room is from a remote
        server and it's events are still outliers. Try to find membership events that
        do not have a matching state_key and sender, as these are most likely invite
        events. The possibility of them being a kick or ban is there, but unlikely as
        the previous stage would have caught the creation event instead

        Returns None when no events were found for a room
        """
        # Including a type doesn't guarantee that at least one of each is present in the result
        filter_json = {
            "types": [EventTypes.Message, EventTypes.Encrypted, EventTypes.Create]
        }

        events = await self._get_filtered_events_from_pagination(room_id, filter_json)

        collected_timestamps = {event_base.origin_server_ts for event_base in events}
        if collected_timestamps:
            return max(collected_timestamps)

        # So, maybe this is a remote invite situation. The pagination handler does not
        # pick up outliers and out-of-band memberships until they have been de-outliered
        # such as through backfill. Retrieve these manually. As an additional note: the
        # get_current_state() used in
        # get_timestamp_from_eligible_events_for_epa_room_purge() also does not appear
        # to get outlier events, neither did the partial_state variant.

        # This will either have the timestamp or be None if none was found
        return await self._last_explicit_membership_ts_in_room(room_id)

    async def _get_filtered_events_from_pagination(
        self, room_id: str, filter_json: dict[str, list[str]]
    ) -> list[EventBase]:
        """
        Providing a room_id and a json Filter will retrieve a list of(at most) 5
        EventBases from the newest Events in that room.

        Args:
            room_id: The room to target
            filter_json: The filter json as a dict to use

        Returns: list of EventBases

        """
        event_filter = Filter(self.api._hs, filter_json)

        from_token = (
            await self.api._hs.get_event_sources().get_current_token_for_pagination(
                room_id
            )
        )

        (
            events,
            next_key,
            _,
        ) = await self.api._store.paginate_room_events_by_topological_ordering(
            room_id=room_id,
            from_key=from_token.room_key,
            # When going backwards, to_key is not important
            to_key=None,
            direction=Direction.BACKWARDS,
            # With the filter below, 5 should be more than enough
            limit=5,
            event_filter=event_filter,
        )

        return events

    async def _last_explicit_membership_ts_in_room(self, room_id: str) -> int | None:
        """
        Retrieve the newest origin_server_ts for a membership event in a given room when
        the sender key does not match the state_key. This is going to be most likely
        an invite
        """
        # TODO: this function needs a better name
        # Unfortunately, there does not appear to be a nice helper to select a row when
        # the condition needs to have a `!=` compare clause
        sql = """
        SELECT MAX(origin_server_ts)
        FROM events
        WHERE room_id = ? AND type = 'm.room.member' AND sender != state_key
        """
        rows = cast(
            list[tuple[int]],
            await self.api._store.db_pool.execute(
                "_last_explicit_membership_ts_in_room", sql, room_id
            ),
        )

        for (origin_server_ts,) in rows:
            # There should only ever be one row, because of the MAX() in the sql
            return origin_server_ts

        # It is increasingly probable that this can never happen now. Local rooms will
        # have had a creation event to fallback on, and remote rooms will be private and
        # therefore require an invite. Leave it in for now, just in case a broken room
        # still can come along from a remote server. It is logged by room_scan().
        return None

    async def get_delete_tasks_by_room(self, room_id: str) -> list[ScheduledTask]:
        """Get scheduled or active delete tasks by room

        Args:
            room_id: room_id that is being targeted
        """
        # We specifically ignore "COMPLETED" and "FAILED" so they can be tried again
        # if the room scan found them still hanging around. This should only occur for
        # ridiculously complex rooms and should not be an issue in the gematik federation
        statuses = [TaskStatus.ACTIVE, TaskStatus.SCHEDULED]

        return await self.task_scheduler.get_tasks(
            actions=[SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME],
            resource_id=room_id,
            statuses=statuses,
        )

    async def kick_all_local_users(self, room_id: str) -> None:
        """
        First block the room from further interaction from this server, then kick all
        local members

        Args:
            room_id:
        """
        requester_user_id = (
            f"@_synapse-invite-checker:{self.api._hs.config.server.server_name}"
        )

        # Block the room, this prevents inadvertent rejoins and stray events/messages
        # from becoming part of the room after the fact but will still allow the user
        # leaving to occur.
        # NOTE: This call is idempotent, so even if some unforeseen error occurs that
        # causes the user to fail to leave the room, it will still be blocked and
        # calling this again won't unblock it or otherwise interfere.
        await self.api._store.block_room(room_id, requester_user_id)

        users = await self.api._store.get_local_users_related_to_room(room_id)
        for user_id, membership in users:
            # If the user is not in the room (or is banned), nothing to do.
            if membership not in (Membership.JOIN, Membership.INVITE, Membership.KNOCK):
                continue

            logger.info("Kicking %s from %s...", user_id, room_id)
            # Use the actual user as a puppet. Don't use the auto-kicker
            # user id above, as it won't pass room auth
            target_requester = create_requester(user_id, authenticated_entity=user_id)

            try:
                # Kick users from room
                (
                    _,
                    stream_id,
                ) = await self.api._hs.get_room_member_handler().update_membership(
                    requester=target_requester,
                    target=target_requester.user,
                    room_id=room_id,
                    action=Membership.LEAVE,
                    content={},
                    ratelimit=False,
                    require_consent=False,
                )

            except Exception:
                logger.exception(
                    "Failed to kick user '%s' from room %s", user_id, room_id
                )

    async def schedule_room_for_purge(self, room_id: str) -> None:
        """
        Schedules the deletion of a room from Synapse's database after kicking all users

        If the room has already been scheduled or is actively being deleted, do nothing.
        If the room was purged already in the past, but for some reason is still hanging
        around in the database, try it again
        """
        if len(await self.get_delete_tasks_by_room(room_id)) > 0:
            logger.warning("Purge already in progress or scheduled for %s", room_id)
            return

        shutdown_params = ShutdownRoomParams(
            new_room_user_id=None,
            new_room_name=None,
            message=None,
            requester_user_id=None,
            block=False,
            purge=True,  # <- to remove the room from the database
            force_purge=True,  # <- to force kick anyone else still in the room
        )

        delete_id = await self.task_scheduler.schedule_task(
            SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME,
            resource_id=room_id,
            params=shutdown_params,
            # Set the time to start to now, as we have already waited the requested time
            timestamp=self.api._hs.get_clock().time_msec(),
        )

        logger.info(
            "Scheduling shutdown and purge on room '%s' with delete_id '%s'",
            room_id,
            delete_id,
        )

    async def room_scan(self) -> None:
        """
        Scan all rooms for eligible conditions to shutdown and purge a room.
        """
        # Changed for version 0.4.2
        # To help mitigate the potential racing of a room scan during a room creation,
        # we will keep track that we already looked at this room. The next room scan
        # should pick up on this and then force the kick/purge if it still does not meet
        # the criteria. If this legitimately was a seriously broken room, the inactive
        # purge below will still completely remove it.

        all_room_ids = await self.get_all_room_ids()

        logger.debug("Detected %d total rooms", len(all_room_ids))

        server_notice_rooms = set()
        # On servers that don't have server notices set up, the mxid will be None
        if self.api._hs.config.servernotices.server_notices_mxid is not None:
            # This database call was chosen over `is_server_notice_room()` as batching
            # the data should be much more efficient than calling the latter for every
            # single room
            server_notice_rooms_list: list[RoomsForUser] = (
                await self.api._store.get_rooms_for_local_user_where_membership_is(
                    self.api._hs.config.servernotices.server_notices_mxid,
                    [Membership.JOIN],
                    [],
                )
            )
            # Simplify notice room list for fast lookup
            server_notice_rooms = {room.room_id for room in server_notice_rooms_list}

        if self.config.insured_room_scan_options.enabled:
            # grab a couple of references, this will be used frequently and helps make
            # the below conditions more readable.
            # XXX: should we do the same for 'current_time'?
            invites_grace_period_ms = (
                self.config.insured_room_scan_options.invites_grace_period_ms
            )
            grace_period_ms = self.config.insured_room_scan_options.grace_period_ms

            for room_id in all_room_ids:
                # Server notice rooms are exempt, don't want to necessarily hide that
                # a notice showed up before the user has a chance to see it.
                if room_id in server_notice_rooms:
                    continue

                # only shut down rooms that only have EPA hosts in them
                if await self.have_all_pro_hosts_left(room_id):
                    epa_room_results = await self.get_timestamps_from_eligible_events_for_epa_room_purge(
                        room_id
                    )
                    current_time = self.api._hs.get_clock().time_msec()

                    # Invites(if found) are ignored if the invites_grace_period is 0 or
                    # if the invites_grace_period + the actual timestamp of the invite
                    # are greater than now
                    if (
                        epa_room_results.last_invite_in_room is not None
                        and (
                            invites_grace_period_ms == 0
                            or (
                                epa_room_results.last_invite_in_room
                                + invites_grace_period_ms
                                > current_time
                            )
                        )
                        # Leaves(if found) are ignored if the grace_period + timestamp are
                        # greater than now
                        or (
                            epa_room_results.last_leave_in_room is not None
                            and epa_room_results.last_leave_in_room + grace_period_ms
                            > current_time
                        )
                        # There is not always a create event available, but if there is and
                        # its timestamp + grace_period are greater than now, then it is ignored
                        or epa_room_results.room_creation_ts is not None
                        and (
                            epa_room_results.room_creation_ts + grace_period_ms
                            > current_time
                        )
                    ):
                        pass

                    # In the unlikely event that all of the above did not happen, warn.
                    # Recall that we only get to this place if there are no Pro hosts in
                    # the room, so either an invite or a leave has to have occurred and
                    # in their absence we use the create event. So if there is no create
                    # event, then it is likely this room is broken somehow.
                    elif epa_room_results.room_creation_ts is None:
                        logger.warning(
                            "Not kicking users from room during ePA user room scan because it contained no events: %s",
                            room_id,
                        )
                    else:
                        await self.kick_all_local_users(room_id)

        if self.config.inactive_room_scan_options.enabled:
            for room_id in all_room_ids:
                last_eligible_event_ts = (
                    await self.get_timestamp_of_last_eligible_activity_in_room(room_id)
                )
                if last_eligible_event_ts is None:
                    logger.warning(
                        "A room was found that contained no events, skipping purge for: %s",
                        room_id,
                    )

                elif (
                    last_eligible_event_ts
                    + self.config.inactive_room_scan_options.grace_period_ms
                    <= self.api._hs.get_clock().time_msec()
                ):
                    await self.schedule_room_for_purge(room_id)

    async def have_all_pro_hosts_left(self, room_id: str) -> bool:
        """
        Retrieves all hosts that have a member in a given room, and filters them to
        decide if any of them are non-Epa servers.
        Args:
            room_id:

        Returns: bool representing if the hosts present are all non-Pro servers

        """
        hosts = await self.api._store.get_current_hosts_in_room(room_id=room_id)  # type: ignore[call-arg]
        for host in hosts:
            if not await self.is_domain_insurance(host):
                return False

        return True
