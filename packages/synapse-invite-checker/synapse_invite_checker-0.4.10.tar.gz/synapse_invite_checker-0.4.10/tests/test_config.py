# Copyright (C) 2020, 2024 Famedly
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
import re
from typing import Any, ClassVar
from unittest import TestCase

import pytest
from synapse.config import ConfigError

from synapse_invite_checker import InviteChecker
from synapse_invite_checker.types import DefaultPermissionConfig, TimType


class ConfigParsingTestCase(TestCase):
    """
    Test that parsing the config can generate Exceptions.

    We start with a basic configuration, and copy it for each test. That is then
    modified to generate the Exceptions.

    An empty string was chosen to represent a 'falsy' value, but removing the
    key has the same effect. May use either interchangeably
    """

    config: ClassVar[dict[str, Any]] = {
        "tim-type": "pro",
        "federation_list_url": "https://localhost:8080",
        "federation_list_client_cert": "tests/certs/client.pem",
        "gematik_ca_baseurl": "https://download-ref.tsl.ti-dienste.de/",
        "allowed_room_versions": ["9", "10"],
    }

    def test_tim_type_is_not_case_sensitive(self) -> None:
        test_config = self.config.copy()
        test_config.update({"tim-type": "ePA"})
        assert InviteChecker.parse_config(test_config).tim_type == TimType.EPA

    def test_tim_type_defaults_to_pro_mode(self) -> None:
        test_config = self.config.copy()
        test_config.pop("tim-type")
        assert InviteChecker.parse_config(test_config).tim_type == TimType.PRO

    def test_incorrect_tim_type_raises(self) -> None:
        test_config = self.config.copy()
        test_config.update({"tim-type": "fake"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

    def test_missing_fed_list_or_gematik_ca_url_raises(self) -> None:
        test_config = self.config.copy()
        test_config.update({"federation_list_url": ""})
        with pytest.raises(Exception, match="Incomplete federation list config"):
            InviteChecker.parse_config(test_config)

        test_config = self.config.copy()
        test_config.update({"gematik_ca_baseurl": ""})
        with pytest.raises(Exception, match="Incomplete federation list config"):
            InviteChecker.parse_config(test_config)

    def test_missing_fed_list_client_certs_raises(self) -> None:
        """
        Test that missing client certs for the Federation List raises an exception
        when using HTTPS with default mTLS settings (required)
        """
        test_config = self.config.copy()
        test_config.update({"federation_list_client_cert": ""})
        with pytest.raises(
            Exception,
            match=re.escape(
                "Federation list config requires an mtls (PEM) cert for https connections when mTLS is required"
            ),
        ):
            InviteChecker.parse_config(test_config)

    def test_missing_fed_list_client_certs_with_mtls_disabled(self) -> None:
        """
        Test that missing client certs for the Federation List is accepted
        when using HTTPS but mTLS is disabled
        """
        test_config = self.config.copy()
        test_config.update(
            {
                "federation_list_client_cert": "",
                "federation_list_require_mtls": False,
            }
        )
        # Should not raise an exception
        assert InviteChecker.parse_config(test_config)

    def test_federation_list_require_mtls_defaults_to_true(self) -> None:
        """
        Test that federation_list_require_mtls defaults to True for backward compatibility
        """
        test_config = self.config.copy()
        config = InviteChecker.parse_config(test_config)
        assert (
            config.federation_list_require_mtls
        ), "federation_list_require_mtls should default to True"

    def test_missing_fed_list_client_certs_is_accepted_if_fed_scheme_is_http(
        self,
    ) -> None:
        """
        'federation_list_url' must be 'http' if Federation List Client certs are missing.
        """
        test_config = self.config.copy()
        test_config.update(
            {
                "federation_list_client_cert": "",
                "federation_list_url": "http://localhost:8080",
            }
        )

        assert InviteChecker.parse_config(test_config), "Exception maybe?"

    def test_allowed_room_versions_is_not_a_list(self) -> None:
        test_config = self.config.copy()

        assert InviteChecker.parse_config(test_config)

        # Nope, not a list
        test_config.update({"allowed_room_versions": "9"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

        # Nope, not a list
        test_config.update({"allowed_room_versions": "{9}"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

        # Nope, not a recognized list
        test_config.update({"allowed_room_versions": "9, 10"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

        # Nope, not a list
        test_config.update({"allowed_room_versions": "9 10"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

        # This one is okay, these are integers and can be coerced into strings
        test_config.update({"allowed_room_versions": [9, 10]})
        assert InviteChecker.parse_config(test_config)

        # This is allowed
        test_config.update({"allowed_room_versions": ["8"]})
        assert InviteChecker.parse_config(test_config)

    def test_parse_duration_parameters(self) -> None:
        test_config = self.config.copy()
        test_config.update({"room_scan_run_interval": "bad value"})
        # After Synapse release 1.124.0, this became a TypeError
        with pytest.raises((ValueError, TypeError)):
            InviteChecker.parse_config(test_config)

        test_config = self.config.copy()
        # Specifically use a word that has a final letter that matches one recognized
        # by parse_duration()
        test_config.update({"room_scan_run_interval": "why"})
        with pytest.raises(
            ValueError, match=re.escape("invalid literal for int() with base 10: 'wh'")
        ):
            InviteChecker.parse_config(test_config)

    def test_dict_unexpectedly_is_something_else_raises(self) -> None:
        test_config = self.config.copy()
        # Shouldn't work if set to a string
        test_config.update({"insured_only_room_scan": "bad value"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

        # Shouldn't work if set to a list of strings
        test_config.update({"insured_only_room_scan": ["what", "is", "a", "list?"]})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

        test_config = self.config.copy()
        # Shouldn't work if set to a string
        test_config.update({"inactive_room_scan": "not a dict"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

        # Shouldn't work if set to a list of strings
        test_config.update(
            {"inactive_room_scan": ["lists", "are", "only", "good", "on", "mondays"]}
        )
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

    def test_public_room_override_defaults_to_true(self) -> None:
        test_config = self.config.copy()
        config = InviteChecker.parse_config(test_config)
        assert (
            config.override_public_room_federation
        ), "`override_public_room_federation` should default to 'True'"

    def test_public_room_override_can_be_disabled(self) -> None:
        test_config = self.config.copy()
        test_config.update({"override_public_room_federation": False})
        config = InviteChecker.parse_config(test_config)
        assert (
            config.override_public_room_federation is False
        ), "`override_public_room_federation` should be `False`'"

    def test_public_room_override_raises(self) -> None:
        test_config = self.config.copy()
        # Although a boolean is an int, an int is not a boolean
        test_config.update({"override_public_room_federation": "0"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

        # No silly strings. Shame, really....
        test_config = self.config.copy()
        test_config.update({"override_public_room_federation": "nope"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

    def test_prohibit_world_readable_rooms_override_defaults_to_true(self) -> None:
        test_config = self.config.copy()
        config = InviteChecker.parse_config(test_config)
        assert (
            config.prohibit_world_readable_rooms
        ), "`prohibit_world_readable_rooms` should default to 'True'"

    def test_prohibit_world_readable_rooms_override_can_be_disabled(self) -> None:
        test_config = self.config.copy()
        test_config.update({"prohibit_world_readable_rooms": False})
        config = InviteChecker.parse_config(test_config)
        assert (
            config.prohibit_world_readable_rooms is False
        ), "`prohibit_world_readable_rooms` should be `False`'"

    def test_prohibit_world_readable_rooms_override_raises(self) -> None:
        test_config = self.config.copy()
        # Although a boolean is an int, an int is not a boolean
        test_config.update({"prohibit_world_readable_rooms": "1"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

        # No silly strings. Shame, really....
        test_config = self.config.copy()
        test_config.update({"prohibit_world_readable_rooms": "hi_mom!"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

    def test_federation_list_require_mtls_raises_for_non_boolean(self) -> None:
        """Verify that non-boolean values for federation_list_require_mtls raise ConfigError"""
        test_config = self.config.copy()
        # String that's not a boolean
        test_config.update({"federation_list_require_mtls": "maybe"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

        # Integer is not a boolean
        test_config = self.config.copy()
        test_config.update({"federation_list_require_mtls": 1})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

    def test_invalid_url_scheme_raises(self) -> None:
        """
        Test that using an invalid URL scheme (neither http nor https) raises an exception
        when creating an MtlsPolicy
        """
        from synapse_invite_checker.config import InviteCheckerConfig
        from synapse_invite_checker.invite_checker import MtlsPolicy

        # Create a config with an invalid URL scheme
        config = InviteCheckerConfig(DefaultPermissionConfig())
        config.federation_list_url = "ftp://localhost:8080"
        with pytest.raises(Exception, match="URL scheme must be either http or https"):
            MtlsPolicy(config)

        config.federation_list_url = "ws://localhost:8080"
        with pytest.raises(Exception, match="URL scheme must be either http or https"):
            MtlsPolicy(config)

        config.federation_list_url = "file:///etc/passwd"
        with pytest.raises(Exception, match="URL scheme must be either http or https"):
            MtlsPolicy(config)

    def test_mtls_policy_creator_for_netloc_bytes_hostname(self) -> None:
        """
        Test that creatorForNetloc correctly handles bytes hostname by encoding url.hostname to UTF-8
        """
        from synapse_invite_checker.config import InviteCheckerConfig
        from synapse_invite_checker.invite_checker import MtlsPolicy

        # Create a config with valid URL
        config = InviteCheckerConfig(DefaultPermissionConfig())
        config.federation_list_url = "https://example.com:8443"
        config.federation_list_client_cert = ""
        config.federation_list_require_mtls = False

        policy = MtlsPolicy(config)

        # Test with matching bytes hostname (that corresponds to the encoded url.hostname) and port
        options = policy.creatorForNetloc(b"example.com", 8443)
        assert options == policy.options

        # Test with non-matching bytes hostname
        with pytest.raises(Exception, match="Invalid connection attempt"):
            policy.creatorForNetloc(b"other.com", 8443)

        # Test with invalid bytes hostname
        invalid_bytes = b"\xff\xfe\xfd\xfc"  # Not valid UTF-8
        with pytest.raises(Exception, match="Invalid connection attempt"):
            policy.creatorForNetloc(invalid_bytes, 8443)

    def test_unexpected_non_booleans(self) -> None:
        test_config = self.config.copy()
        # Although a boolean is an int, an int is not a boolean
        test_config.update({"limit_reactions": "1"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)

        test_config = self.config.copy()
        # Although a boolean is an int, an int is not a boolean
        test_config.update({"limit_reactions": 1})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)
        test_config = self.config.copy()

        # Although a boolean is an int, an int is not a boolean
        test_config.update({"limit_reactions": "hi mom!"})
        with pytest.raises(ConfigError):
            InviteChecker.parse_config(test_config)
