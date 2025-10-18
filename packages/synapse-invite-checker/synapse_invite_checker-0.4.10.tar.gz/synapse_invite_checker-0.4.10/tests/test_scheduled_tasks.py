# Copyright (C) 2025 Famedly
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
# mypy: disable-error-code=call-arg
from typing import Any

import pytest
from parameterized import parameterized
from synapse.api.constants import EventTypes, JoinRules, Membership
from synapse.api.errors import AuthError
from synapse.api.room_versions import KNOWN_ROOM_VERSIONS
from synapse.handlers.pagination import SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME
from synapse.server import HomeServer
from synapse.types import TaskStatus, UserID
from synapse.util.clock import Clock
from twisted.internet.testing import MemoryReactor

from tests.base import FederatingModuleApiTestCase
from tests.test_utils import (
    DOMAIN_IN_LIST,
    INSURANCE_DOMAIN_IN_LIST,
    INSURANCE_DOMAIN_IN_LIST_FOR_LOCAL,
    SERVER_NAME_FROM_LIST,
    event_injection,
)


class InsuredOnlyRoomScanTaskTestCase(FederatingModuleApiTestCase):
    """
    Test that insured only room scans are done, and required room kicks are done
    """

    # This test case will model being an EPA server on the federation list
    remote_pro_user = f"@mxid:{DOMAIN_IN_LIST}"
    remote_pro_user_2 = f"@a:{SERVER_NAME_FROM_LIST}"
    remote_epa_user = f"@alice:{INSURANCE_DOMAIN_IN_LIST}"
    remote_epa_user_2 = f"@bob:{INSURANCE_DOMAIN_IN_LIST}"
    # Our server name
    server_name_for_this_server = INSURANCE_DOMAIN_IN_LIST_FOR_LOCAL
    # The default "fake" remote server name that has its server signing keys auto-injected
    OTHER_SERVER_NAME = DOMAIN_IN_LIST

    def default_config(self) -> dict[str, Any]:
        conf = super().default_config()
        assert "modules" in conf, "modules missing from config dict during construction"

        # There should only be a single item in the 'modules' list, since this tests that module
        assert len(conf["modules"]) == 1, "more than one module found in config"

        conf["modules"][0].setdefault("config", {}).update({"tim-type": "epa"})
        conf["modules"][0].setdefault("config", {}).update(
            {"room_scan_run_interval": "1h"}
        )
        conf["modules"][0].setdefault("config", {}).update(
            {
                "insured_only_room_scan": {
                    "enabled": True,
                    "grace_period": "6h",
                    "invites_grace_period": "7h",
                },
                # Enabled to test broken rooms being ignored(but later purged correctly)
                # We don't worry about the grace_period as it will not apply
                "inactive_room_scan": {"enabled": True},
            }
        )
        conf["server_notices"] = {"system_mxid_localpart": "server", "auto_join": True}

        return conf

    def prepare(self, reactor: MemoryReactor, clock: Clock, homeserver: HomeServer):
        super().prepare(reactor, clock, homeserver)
        self.task_scheduler = self.hs.get_task_scheduler()

        self.user_d = self.register_user("d", "password")
        # Need the full UserID in a few places for sending a message into the room
        self.user_d_id = UserID.from_string(self.user_d)
        self.user_e = self.register_user("e", "password")
        self.login("d", "password")
        # Need this access token for the invite helper below
        self.access_token_e = self.login("e", "password")

        # OTHER_SERVER_NAME already has it's signing key injected into our database so
        # our server doesn't have to make that request. Add the other servers we will be
        # using as well
        self.inject_servers_signing_key(INSURANCE_DOMAIN_IN_LIST)
        self.inject_servers_signing_key(SERVER_NAME_FROM_LIST)

    @parameterized.expand(
        [
            ("pro_join_and_leave", True, True),
            ("pro_never_join", False, True),
            ("pro_never_invited_or_joined", False, False),
        ]
    )
    def test_room_scan_detects_epa_rooms(
        self, pro_activity: str, pro_join: bool, pro_invited: bool
    ) -> None:
        """
        Test that a room is handled as appropriately with a single EPA user and a single
        PRO user. Also test if the PRO user never joined/left(to test that 'maybe broken'
        rooms) and rooms with no invites at all.
        """
        # Make a room...
        room_id = self.create_local_room(self.user_d, [], is_public=False)
        assert room_id is not None, "Room should be created"

        # ...then (maybe) invite the doctor
        if pro_invited:
            self.helper.invite(
                room_id,
                self.user_d,
                self.remote_pro_user,
                tok=self.map_user_id_to_token[self.user_d],
            )
        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        # Needs to be either None or False
        assert not is_room_blocked, "Room should not be blocked yet(try 1)"

        # doctor joins
        if pro_join:
            self.send_join(self.remote_pro_user, room_id)

        # Send a junk hex message into the room, like a sentinel
        self.create_and_send_event(room_id, self.user_d_id)

        # doctor leaves room
        if pro_join:
            self.send_leave(self.remote_pro_user, room_id)

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked yet(try 2)"

        # The config gives 6 hours for leaves and 7 hours for joins. Depending on the test
        # we fast-forward an hour short of which one is expected.
        if pro_activity == "pro_never_join":
            # The 'pro_never_join' is specifically a test for an invite without a join
            self.reactor.advance(6 * 60 * 60)
        else:
            self.reactor.advance(5 * 60 * 60)

        # Room should still exist
        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked yet(try 3)"

        # The TaskScheduler has a heartbeat of 1 minute, give it that much
        self.reactor.advance(60 * 60)

        # Now the room should be gone
        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert is_room_blocked, "Room should be blocked now(try 4)"

        # Send a junk hex message into the room, like a sentinel
        # Inside EventCreationHandler.handle_new_client_event(), this raises as an
        # AuthError(which is a subclass of SynapseError). It appears to be annotated with a 403 as well
        with pytest.raises(AuthError):
            self.create_and_send_event(room_id, self.user_d_id)

    def test_room_scan_skips_incomplete_epa_rooms(self) -> None:
        """
        Test that a partially formed room does not break the room scanner, but instead
        is skipped and will not be purged(if enabled). Remember, rooms scans run every
        hour by default in this TestCase
        """
        # Make the bare minimum of a room, which is basically just a row in the `rooms` table
        room_version_id = self.hs.config.server.default_room_version.identifier

        room_version = KNOWN_ROOM_VERSIONS.get(room_version_id)
        assert room_version
        room_id = self.get_success_or_raise(
            self.hs.get_room_creation_handler()._generate_and_create_room_id(
                self.user_d, is_public=False, room_version=room_version
            )
        )
        assert room_id is not None, "Room should be partially created"

        # Even with an incomplete room, blocking should still work as expected. It will
        # be blocked as part of the insured kicking procedure. If it is not blocked, then
        # it is not scheduled for having members kicked out.
        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        # Needs to be either None or False
        assert not is_room_blocked, "Room should not be blocked yet(try 1)"

        current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
        assert current_rooms is not None, "Room should still exist(try 1)"

        # The config set up says it gets 1 hour for room scan frequency
        self.reactor.advance(60 * 60)

        # Normally, the room scan process would pick up the room here. But, we are
        # skipping the insured members kicking procedure, so it gets a second run
        # through before it is eligible for purge
        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked(try 2)"

        current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
        assert current_rooms is not None, "Room should still exist(try 2)"

        # try again, same setup
        self.reactor.advance(60 * 60)

        # The TaskScheduler has a heartbeat of 1 minute, give it that much
        self.reactor.advance(60)

        # The room will not register as blocked, since that only runs when the kicking
        # procedure is triggered
        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked(try 3)"

        current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
        assert current_rooms is not None, "Room should exist(try 3)"

    def test_room_scan_ignores_server_notices_rooms(self) -> None:
        """
        Test that a room is ignored when it is a server notices room
        """
        event_base = self.get_success_or_raise(
            self.hs.get_server_notices_manager().send_notice(
                self.user_d, {"body": "Server Notice message", "msgtype": "m.text"}
            )
        )
        room_id = event_base.room_id
        # Retrieving the room_id is a sign that the room was created, the user was
        # invited, and the message was sent
        assert room_id, "Server notices room should have been found"

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        # Needs to be either None or False
        assert not is_room_blocked, "Room should not be blocked yet(try 1)"

        self.reactor.advance(5 * 60 * 60)

        # Room should still exist
        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked yet(try 3)"

        # One more hour should be the 6 hours from settings
        self.reactor.advance(60 * 60)

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should still exist"

        # Message should succeed, showing the room has not yet been left
        self.get_success_or_raise(
            self.hs.get_server_notices_manager().send_notice(
                self.user_d, {"body": "Server Notice message #2", "msgtype": "m.text"}
            )
        )

    def test_room_scan_detects_only_epa_rooms_with_multiple_hosts(self) -> None:
        """
        Test that a room is not deleted until the last PRO user leaves a room
        """
        # Make a room and invite the doctor
        room_id = self.create_local_room(
            self.user_d, [self.remote_pro_user], is_public=False
        )
        assert room_id is not None

        # Will need this later to include the correct stripped state with an invite
        room_version = self.get_success(self.store.get_room_version(room_id))

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        # Needs to be either None or False
        assert not is_room_blocked, "Room should not be blocked yet(try 1)"

        # doctor joins
        self.send_join(self.remote_pro_user, room_id)

        # doctor invites 2 more patients, because the first patient isn't allowed. One
        # is remote and the other is from this EPA server
        self.get_success_or_raise(
            event_injection.inject_member_event(
                self.hs,
                room_id,
                self.remote_pro_user,
                Membership.INVITE,
                target=self.remote_epa_user,
            )
        )

        # other patient joins
        self.send_join(self.remote_epa_user, room_id)

        self.get_success_or_raise(
            event_injection.inject_member_event(
                self.hs,
                room_id,
                self.remote_pro_user,
                Membership.INVITE,
                target=self.user_e,
                unsigned={
                    "invite_room_state": [
                        {
                            "type": EventTypes.Create,
                            "sender": self.user_d_id.to_string(),
                            # starting in room version 11, the 'sender' field is used
                            # instead. For the moment, we are limited to versions "9"
                            # and "10"
                            "content": {
                                "creator": self.user_d_id.to_string(),
                                "room_version": room_version.identifier,
                            },
                            "state_key": "",
                        },
                        {
                            "type": EventTypes.JoinRules,
                            "sender": self.user_d_id.to_string(),
                            "content": {"join_rule": JoinRules.PRIVATE},
                            "state_key": "",
                        },
                    ]
                },
            )
        )

        self.helper.join(room_id, self.user_e, tok=self.access_token_e)

        # doctor invites another doctor. To properly test joining, the invite from the
        # doctor needs to include the 'stripped_state' like bits in the invite itself
        self.get_success_or_raise(
            event_injection.inject_member_event(
                self.hs,
                room_id,
                self.remote_pro_user,
                Membership.INVITE,
                target=self.remote_pro_user_2,
            )
        )

        # other doctor joins
        self.send_join(self.remote_pro_user_2, room_id)

        # Send a junk hex message into the room, like a sentinel
        self.create_and_send_event(room_id, self.user_d_id)

        # They all just found out a friend of the remote patient may have more info
        self.get_success_or_raise(
            event_injection.inject_member_event(
                self.hs,
                room_id,
                self.remote_pro_user,
                Membership.INVITE,
                target=self.remote_epa_user_2,
            )
        )

        # other patient joins
        self.send_join(self.remote_epa_user_2, room_id)

        # Original patient says "thanks you can go now"
        self.create_and_send_event(room_id, self.user_d_id)

        # friend of friend of patient leaves
        self.send_leave(self.remote_epa_user_2, room_id)

        # doctor 1 leaves room
        self.send_leave(self.remote_pro_user, room_id)

        # The other local insured leaves the room
        self.helper.leave(room_id, self.user_e, tok=self.access_token_e)

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked yet(try 2)"

        self.reactor.advance(5 * 60 * 60)

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked yet(try 3)"

        # Normally, this would trigger the auto-kicker. But the doctor hasn't left yet
        self.reactor.advance(60 * 60)

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked yet(try 4)"

        # doctor 2 leaves
        self.send_leave(self.remote_pro_user_2, room_id)

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked yet(try 5)"

        self.reactor.advance(5 * 60 * 60)

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked yet(try 6)"

        # One more hour should be the 6 hours from settings
        self.reactor.advance(60 * 60)

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert is_room_blocked, "Room should be blocked now"

        # Inside EventCreationHandler.handle_new_client_event(), this raises as an
        # AuthError(which is a subclass of SynapseError). It appears to be annotated with a 403 as well
        with pytest.raises(AuthError):
            self.create_and_send_event(room_id, self.user_d_id)

    def test_room_scan_detects_invites_as_participation(self) -> None:
        """
        Test that a room is not detected as inactive if one of two doctors never show up
        """
        # Make a room and invite the doctor
        room_id = self.create_local_room(self.user_d, [], is_public=False)
        assert room_id is not None

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        # Needs to be either None or False
        assert not is_room_blocked, "Room should not be blocked yet(try 1)"

        # Invite both pro users
        for remote_user in [self.remote_pro_user, self.remote_pro_user_2]:
            self.helper.invite(
                room_id,
                src=self.user_d,
                targ=remote_user,
                tok=self.map_user_id_to_token[self.user_d],
            )

        # doctor #1 joins
        self.send_join(self.remote_pro_user, room_id)

        # Send a junk hex message into the room, like a sentinel
        self.create_and_send_event(room_id, self.user_d_id)

        # doctor 1 leaves room, still have that pending invite for doctor #2
        self.send_leave(self.remote_pro_user, room_id)

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked yet(try 2)"

        self.reactor.advance(5 * 60 * 60)

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked yet(try 3)"

        # Normally, this would trigger the auto-kicker for leaves. But there is the
        # pending invite still waiting, which is configured to 7 hours and not 6
        self.reactor.advance(60 * 60)

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked yet(try 4)"

        # One more hour should be the 7 hours from settings
        self.reactor.advance(60 * 60)

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert is_room_blocked, "Room should be blocked now"

        # Inside EventCreationHandler.handle_new_client_event(), this raises as an
        # AuthError(which is a subclass of SynapseError). It appears to be annotated with a 403 as well
        with pytest.raises(AuthError):
            self.create_and_send_event(room_id, self.user_d_id)


class InsuredOnlyRoomScanIgnoreInvitesTaskTestCase(FederatingModuleApiTestCase):
    """
    Test that insured only room scans are done, and required room kicks are done. Unlike
    the previous test case above, this explicitly disables considering invites as part
    of the reasons to kick all users from a room
    """

    # This test case will model being an EPA server on the federation list
    remote_pro_user = f"@mxid:{DOMAIN_IN_LIST}"
    # Our server name
    server_name_for_this_server = INSURANCE_DOMAIN_IN_LIST_FOR_LOCAL
    # The default "fake" remote server name that has its server signing keys auto-injected
    OTHER_SERVER_NAME = DOMAIN_IN_LIST

    def default_config(self) -> dict[str, Any]:
        conf = super().default_config()
        assert "modules" in conf, "modules missing from config dict during construction"

        # There should only be a single item in the 'modules' list, since this tests that module
        assert len(conf["modules"]) == 1, "more than one module found in config"

        conf["modules"][0].setdefault("config", {}).update({"tim-type": "epa"})
        conf["modules"][0].setdefault("config", {}).update(
            {"room_scan_run_interval": "1h"}
        )
        conf["modules"][0].setdefault("config", {}).update(
            {
                "insured_only_room_scan": {
                    "enabled": True,
                    "grace_period": "6h",
                },
                # Enabled to test broken rooms being ignored(but later purged correctly)
                # We don't worry about the grace_period as it will not apply
                "inactive_room_scan": {"enabled": True},
            }
        )

        return conf

    def prepare(self, reactor: MemoryReactor, clock: Clock, homeserver: HomeServer):
        super().prepare(reactor, clock, homeserver)

        self.user_d = self.register_user("d", "password")
        # Need the full UserID in a few places for sending a message into the room
        self.user_d_id = UserID.from_string(self.user_d)
        self.login("d", "password")

    def test_room_scan_ignores_room_with_invite_grace_period_disabled(self) -> None:
        """
        Test that a room does not have epa members kicked if the invite remains pending
        with the invite grace period disabled.
        """
        # Make a room and invite the doctor
        room_id = self.create_local_room(
            self.user_d, [self.remote_pro_user], is_public=False
        )
        assert room_id is not None, "Room should be created"

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        # Needs to be either None or False
        assert not is_room_blocked, "Room should not be blocked yet(try 1)"

        # Send a junk hex message into the room, like a sentinel
        self.create_and_send_event(room_id, self.user_d_id)

        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked yet(try 2)"

        # The config gives 6 hours for leaves. Invites should count as joins and not
        # cause the users to be kicked out.
        self.reactor.advance(5 * 60 * 60)

        # Room should still exist
        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked yet(try 3)"

        # Give another hour
        self.reactor.advance(60 * 60)

        # Should still be here
        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked now(try 4)"

        # Give another hour
        self.reactor.advance(60 * 60)

        # Should still be here
        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked now(try 5)"

        # Give another hour
        self.reactor.advance(60 * 60)

        # Should still be here
        is_room_blocked = self.get_success_or_raise(self.store.is_room_blocked(room_id))
        assert not is_room_blocked, "Room should not be blocked now(try 6)"
        # Send a junk hex message into the room. Proof the room still exists
        self.create_and_send_event(room_id, self.user_d_id)


class InactiveRoomScanTaskTestCase(FederatingModuleApiTestCase):
    """
    Test that inactive room scans are done, and subsequent room purges are run
    """

    # This test case will model being an PRO server on the federation list
    # By default we are SERVER_NAME_FROM_LIST

    # Test with one other remote PRO server and one EPA server
    # The inactive grace period is going to be 6 hours, room scans run each hour
    remote_pro_user = f"@mxid:{DOMAIN_IN_LIST}"
    remote_epa_user = f"@alice:{INSURANCE_DOMAIN_IN_LIST}"
    # The default "fake" remote server name that has its server signing keys auto-injected
    OTHER_SERVER_NAME = DOMAIN_IN_LIST

    def default_config(self) -> dict[str, Any]:
        conf = super().default_config()
        assert "modules" in conf, "modules missing from config dict during construction"

        # There should only be a single item in the 'modules' list, since this tests that module
        assert len(conf["modules"]) == 1, "more than one module found in config"

        conf["modules"][0].setdefault("config", {}).update({"tim-type": "pro"})
        conf["modules"][0].setdefault("config", {}).update(
            {"room_scan_run_interval": "1h"}
        )
        conf["modules"][0].setdefault("config", {}).update(
            {
                "inactive_room_scan": {
                    "enabled": True,
                    "grace_period": "6h",
                }
            }
        )

        return conf

    def prepare(self, reactor: MemoryReactor, clock: Clock, homeserver: HomeServer):
        super().prepare(reactor, clock, homeserver)
        self.task_scheduler = self.hs.get_task_scheduler()

        self.user_a = self.register_user("a", "password")
        self.user_b = self.register_user("b", "password")
        self.user_c = self.register_user("c", "password")

        # Need this access token for the invite helper below
        self.access_token_a = self.login("a", "password")
        # Won't need access tokens for these users directly
        self.login("b", "password")
        self.login("c", "password")

        # OTHER_SERVER_NAME already has it's signing key injected into our database so
        # our server doesn't have to make that request. Add the other servers we will be
        # using as well
        self.inject_servers_signing_key(INSURANCE_DOMAIN_IN_LIST)

    def opinionated_join(self, room_id: str, user: str) -> None:
        """
        Helper to join a room whether this is a local or remote user
        """
        if self.module_api.is_mine(user):
            # local
            self.helper.join(room_id, user, tok=self.map_user_id_to_token[user])
        else:
            # remote
            self.send_join(user, room_id)

    def assert_task_status_for_room_is(
        self,
        room_id: str,
        task_name: str,
        status_list: list[TaskStatus],
        comment: str,
    ) -> None:
        """
        Assert that for a given room id, the Statuses listed have a single entry

        If the status_list is empty or None, there should be no tasks to find
        """
        purge_task_list = self.get_success_or_raise(
            self.task_scheduler.get_tasks(actions=[task_name], resource_id=room_id)
        )

        if status_list:
            assert (
                len(purge_task_list) > 0
            ), f"{comment} | GT status_list: {status_list}, purge_list: {purge_task_list}"
        else:
            assert (
                len(purge_task_list) == 0
            ), f"{comment} | EQ status_list: {status_list}, purge_list: {purge_task_list}"

        completed_task = [
            task for task in purge_task_list if task.status == TaskStatus.COMPLETE
        ]
        active_task = [
            task for task in purge_task_list if task.status == TaskStatus.ACTIVE
        ]
        scheduled_task = [
            task for task in purge_task_list if task.status == TaskStatus.SCHEDULED
        ]
        assert len(completed_task) == (
            1 if TaskStatus.COMPLETE in status_list else 0
        ), f"{comment} | completed {completed_task}"
        assert len(active_task) == (
            1 if TaskStatus.ACTIVE in status_list else 0
        ), f"{comment} | active {active_task}"
        assert len(scheduled_task) == (
            1 if TaskStatus.SCHEDULED in status_list else 0
        ), f"{comment} | scheduled {scheduled_task}"

    # test for private dm between two local users
    # test for private dm between a local and remote user
    # test for public room on local server
    # test for basic dm between a local and remote epa user

    # I'm not sure I like the hard coding of the user names here, but can not access
    # "self" to just reference it
    @parameterized.expand(
        [
            # (name to give the test, list of users to test with, is public room, any messages in room, should remote actually fully join?)
            (
                "private_room_2_local_users_with_messages",
                [f"@b:{SERVER_NAME_FROM_LIST}"],
                False,
                True,
                True,
            ),
            (
                "private_room_2_local_users_no_messages",
                [f"@b:{SERVER_NAME_FROM_LIST}"],
                False,
                False,
                True,
            ),
            (
                "private_room_1_local_user_1_remote_pro_user",
                [f"@mxid:{DOMAIN_IN_LIST}"],
                False,
                True,
                True,
            ),
            (
                "public_room_3_local_users",
                [f"@b:{SERVER_NAME_FROM_LIST}", f"@c:{SERVER_NAME_FROM_LIST}"],
                True,
                True,
                True,
            ),
            (
                "private_room_with_1_pro_1_epa",
                [f"@b:{SERVER_NAME_FROM_LIST}", f"@alice:{INSURANCE_DOMAIN_IN_LIST}"],
                False,
                True,
                True,
            ),
            (
                "private_room_with_1_pro_1_epa_that_does_not_join",
                [f"@b:{SERVER_NAME_FROM_LIST}", f"@alice:{INSURANCE_DOMAIN_IN_LIST}"],
                False,
                True,
                False,
            ),
        ]
    )
    def test(
        self,
        _: str,
        other_users: list[str],
        is_public: bool,
        send_messages: bool,
        remote_fully_join: bool,
    ) -> None:
        """
        Test that a room is deleted when a local PRO user and various others don't touch
        a room for "inactive_room_scan.grace_period" amount of time
        """
        # Make a room and invite the other occupant(s)
        room_id = self.create_local_room(self.user_a, [], is_public=is_public)
        assert room_id is not None, "Room should exist"

        for other_user in other_users:
            self.helper.invite(room_id, targ=other_user, tok=self.access_token_a)

        current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
        assert current_rooms is not None, "Room should exist from initial get_room()"

        # other user joins
        if remote_fully_join:
            for other_user in other_users:
                self.opinionated_join(room_id, other_user)

        # Send a junk hex message into the room, this is the message the scan will find
        if send_messages:
            self.create_and_send_event(room_id, UserID.from_string(self.user_a))

        # verify there are no shutdown tasks associated with this room
        self.assert_task_status_for_room_is(
            room_id, SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME, [], "first check"
        )

        # wait for cleanup, should take 6 hours(based on above configuration)
        count = 0
        while True:
            count += 1
            if count == 6:
                break

            # advance() is in seconds, this should be 1 hour
            self.reactor.advance(60 * 60)

            current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
            assert (
                current_rooms is not None
            ), f"Room should still exist at count: {count}"

            self.assert_task_status_for_room_is(
                room_id, SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME, [], f"loop count: {count}"
            )

        # Stopped the loop above before advancing the time, so advance() for one more
        # hour, which should allow the task to be scheduled
        self.reactor.advance(60 * 60)

        # Room should still exist
        current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
        assert current_rooms is not None, "Room should still exist after loop finished"

        self.assert_task_status_for_room_is(
            room_id,
            SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME,
            [TaskStatus.SCHEDULED],
            "after loop",
        )

        # The TaskScheduler has a heartbeat of 1 minute, give it that much
        self.reactor.advance(1 * 60)

        # Now the room should be gone
        current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
        assert current_rooms is None, f"Room should be gone now: {current_rooms}"

        # verify a scheduled task "completed" for this room
        self.assert_task_status_for_room_is(
            room_id, SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME, [TaskStatus.COMPLETE], "end"
        )

    def test_room_scan_purges_incomplete_inactive_rooms_after_skip(self) -> None:
        """
        Test that a partially formed room does not break the room scanner, but instead
        is skipped one time before being reconsidered. Remember, rooms scans run every
        hour by default in this TestCase
        """
        # Make the bare minimum of a room, which is basically just a row in the `rooms` table
        room_version_id = self.hs.config.server.default_room_version.identifier

        room_version = KNOWN_ROOM_VERSIONS.get(room_version_id)
        assert room_version
        room_id = self.get_success_or_raise(
            self.hs.get_room_creation_handler()._generate_and_create_room_id(
                self.user_a, is_public=False, room_version=room_version
            )
        )
        assert room_id is not None, "Room should be partially created"

        # verify there are no shutdown tasks associated with this room
        self.assert_task_status_for_room_is(
            room_id, SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME, [], "first check"
        )

        # Here's the first hour gone, the room scan should have ran at least once
        self.reactor.advance(60 * 60)

        current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
        assert current_rooms is not None, "Room should still exist(try 1)"

        self.assert_task_status_for_room_is(
            room_id, SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME, [], "first check"
        )

        # One more hour and the room scan should run again, which should allow the task
        # to be scheduled for purging
        self.reactor.advance(60 * 60)

        # Room should still exist
        current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
        assert current_rooms is not None, "Room should still exist(try 2)"

        self.assert_task_status_for_room_is(
            room_id, SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME, [], "second check"
        )

        # The TaskScheduler has a heartbeat of 1 minute, give it that much
        self.reactor.advance(60)

        # Room should still exist, since it will be ignored
        current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
        assert current_rooms is not None, "Room should still exist(try 3)"

        # verify a scheduled task "completed" for this room
        self.assert_task_status_for_room_is(
            room_id, SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME, [], "end"
        )

    def test_scheduling_a_room_delete_is_idempotent(self) -> None:
        room_id = f"!fake_room_name:{self.server_name_for_this_server}"
        pretest_delete_tasks = self.get_success_or_raise(
            self.inv_checker.get_delete_tasks_by_room(room_id)
        )
        assert len(pretest_delete_tasks) == 0

        self.get_success_or_raise(self.inv_checker.schedule_room_for_purge(room_id))
        delete_tasks = self.get_success_or_raise(
            self.inv_checker.get_delete_tasks_by_room(room_id)
        )
        assert len(delete_tasks) == 1
        delete_task_id = delete_tasks[0].id

        self.get_success_or_raise(self.inv_checker.schedule_room_for_purge(room_id))
        second_delete_tasks = self.get_success_or_raise(
            self.inv_checker.get_delete_tasks_by_room(room_id)
        )
        assert len(second_delete_tasks) == 1
        assert delete_task_id == second_delete_tasks[0].id

    # I'm not sure I like the hard coding of the usernames here, but can not access
    # "self" to just reference it
    @parameterized.expand(
        [
            # (name to give the test, remote user to test with, is public room, should remote actually fully join?)
            (
                "private_room_1_local_user_1_remote_pro_user",
                f"@mxid:{DOMAIN_IN_LIST}",  # self.remote_pro_user
                False,
                True,
            ),
            (
                "private_room_with_1_local_pro_1_remote_epa",
                f"@alice:{INSURANCE_DOMAIN_IN_LIST}",  # self.remote_epa_user
                False,
                True,
            ),
            (
                "private_room_with_1_local_pro_1_remote_epa_that_does_not_join",
                f"@alice:{INSURANCE_DOMAIN_IN_LIST}",
                False,
                False,
            ),
        ]
    )
    def test_remote(
        self,
        _: str,
        remote_user: str,
        is_public: bool,
        finish_join: bool,
    ) -> None:
        """
        Test that a room is not deleted prematurely when a local user attempts to join a
        remote room, including when it is only an invite and no other state is
        transferred.
        """
        # Make a remote room...
        room_id = self.create_remote_room(
            remote_user,
            self.hs.config.server.default_room_version.identifier,
            is_public=is_public,
        )
        assert room_id is not None, "Room should exist"

        # ...and invite our local user...
        self.do_remote_invite(self.user_a, remote_user, room_id)

        current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
        assert current_rooms is not None, "Room should exist from initial get_room()"

        # ...and maybe even make them join.
        if finish_join:
            self.do_remote_join(room_id, self.user_a)

        # Normally here we would inject a message into the room, so the scanner has
        # something to find. That infrastructure does not exist yet for the fake room.
        # We will rely on the invite and the room creation as the fallback for now.

        # verify there are no shutdown tasks associated with this room
        self.assert_task_status_for_room_is(
            room_id, SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME, [], "first check"
        )

        # wait for cleanup, should take 6 hours(based on above configuration)
        count = 0
        while True:
            count += 1
            if count == 6:
                break

            # advance() is in seconds, this should be 1 hour
            self.reactor.advance(60 * 60)

            current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
            assert (
                current_rooms is not None
            ), f"Room should still exist at count: {count}"

            self.assert_task_status_for_room_is(
                room_id, SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME, [], f"loop count: {count}"
            )

        # Stopped the loop above before advancing the time, so advance() for one more
        # hour, which should allow the task to be scheduled
        self.reactor.advance(60 * 60)

        # Room should still exist
        current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
        assert current_rooms is not None, "Room should still exist after loop finished"

        self.assert_task_status_for_room_is(
            room_id,
            SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME,
            [TaskStatus.SCHEDULED],
            "after loop",
        )

        # The TaskScheduler has a heartbeat of 1 minute, give it that much
        self.reactor.advance(1 * 60)

        # Now the room should be gone
        current_rooms = self.get_success_or_raise(self.store.get_room(room_id))
        assert current_rooms is None, f"Room should be gone now: {current_rooms}"

        # verify a scheduled task "completed" for this room
        self.assert_task_status_for_room_is(
            room_id, SHUTDOWN_AND_PURGE_ROOM_ACTION_NAME, [TaskStatus.COMPLETE], "end"
        )
