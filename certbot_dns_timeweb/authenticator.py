"""Timeweb Cloud DNS Authenticator for Certbot."""

from __future__ import annotations

import collections
import functools
import logging
from collections.abc import Callable

from certbot import errors
from certbot.plugins import dns_common

from certbot_dns_timeweb.client import TimewebClient

logger = logging.getLogger(__name__)

DEFAULT_PROPAGATION_SECONDS = 60


class Authenticator(dns_common.DNSAuthenticator):
    """Timeweb Cloud DNS Authenticator.

    This Authenticator uses the Timeweb Cloud API to fulfill a DNS-01 challenge.
    """

    description = "Obtain certificates using a DNS TXT record using the Timeweb Cloud DNS API."

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.credentials = None
        self._for_cleanup: dict[str, list[tuple[str, int]]] = collections.defaultdict(list)

    @classmethod
    def add_parser_arguments(
        cls,
        add: Callable[..., None],
        default_propagation_seconds: int = DEFAULT_PROPAGATION_SECONDS,
    ) -> None:
        super().add_parser_arguments(add, default_propagation_seconds)
        add("credentials", help="Timeweb Cloud credentials INI file.")

    def more_info(self) -> str:
        return "This plugin configures a DNS TXT record to respond to a DNS-01 challenge using the Timeweb API."

    def _setup_credentials(self) -> None:
        self.credentials = self._configure_credentials(
            "credentials",
            "Timeweb Cloud credentials INI file",
            {"api_key": "Timeweb Cloud API key, obtained from https://timeweb.cloud/my/api-keys"},
        )

    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        zone = self._find_zone(validation_name)
        logger.debug("Creating TXT record %s in zone %s", validation_name, zone)
        # The Timeweb API field is called "subdomain", but it expects the full
        # name of the record rather than the label relative to the zone.
        record_id = self._client.add_txt_record(zone=zone, subdomain=validation_name, value=validation)
        self._for_cleanup[validation_name].append((zone, record_id))

    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        for zone, record_id in self._for_cleanup.pop(validation_name, []):
            logger.debug("Removing TXT record %s (id %s) from zone %s", validation_name, record_id, zone)
            try:
                self._client.delete_record(zone, record_id)
            except errors.PluginError as error:
                # Never let cleanup abort the run: the certificate may already
                # be issued and a stale challenge record is harmless.
                logger.warning("Could not remove TXT record %s (id %s): %s", validation_name, record_id, error)

    @functools.cached_property
    def _client(self) -> TimewebClient:
        if self.credentials is None:  # pragma: no cover - guarded by certbot's own flow
            raise errors.PluginError("Timeweb Cloud credentials have not been configured yet.")
        return TimewebClient(api_key=self.credentials.conf("api_key"))

    @functools.cached_property
    def _zones(self) -> set[str]:
        zones = {zone.lower().rstrip(".") for zone in self._client.list_domains()}
        logger.debug("Found %d domain(s) on the Timeweb Cloud account", len(zones))
        return zones

    def _find_zone(self, validation_name: str) -> str:
        """Return the account domain that hosts ``validation_name``."""
        for candidate in dns_common.base_domain_name_guesses(validation_name.lower().rstrip(".")):
            if candidate in self._zones:
                return candidate
        raise errors.PluginError(
            f"Unable to determine the Timeweb Cloud zone for {validation_name}. "
            "Make sure the domain is added to the account the API key belongs to "
            "(https://timeweb.cloud/my/domains) and that its DNS is served by Timeweb."
        )
