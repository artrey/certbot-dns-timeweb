"""
Timeweb DNS Authenticator
"""
import collections
import functools
import logging
from typing import Callable

from certbot.plugins import dns_common
from timeweb import Timeweb
from tld import get_fld

logger = logging.getLogger(__name__)


class Authenticator(dns_common.DNSAuthenticator):
    """
    Timeweb DNS Authenticator

    This Authenticator uses the Timeweb Cloud API to fulfill a DNS-01 challenge.
    """

    description = "Obtain certificates using a DNS TXT record using Timeweb DNS API."
    ttl = 300

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.credentials = None
        self._for_cleanup = collections.defaultdict(list)

    @classmethod
    def add_parser_arguments(cls, add: Callable[..., None], *args, **kwargs) -> None:
        super().add_parser_arguments(add, *args, **kwargs)
        add("credentials", help="Timeweb credentials INI file.")

    def more_info(self) -> str:
        return "This plugin configures a DNS TXT record to respond to a DNS-01 challenge using the Timeweb DNS API."

    def _setup_credentials(self) -> None:
        self.credentials = self._configure_credentials(
            "credentials",
            "Timeweb credentials INI file",
            {"api_key": "Timeweb API key"},
        )

    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        fqdn = self._root_domain(domain)
        response = self._timeweb_client.domains.add_dns_record(
            fqdn=fqdn,
            type="TXT",
            value=validation,
            subdomain=validation_name[: -len(fqdn)].rstrip("."),
        )
        self._for_cleanup[validation_name].append(response.dns_record.id)

    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        if validation_name not in self._for_cleanup:
            return
        fqdn = self._root_domain(domain)
        for record_id in self._for_cleanup.pop(validation_name):
            self._timeweb_client.domains.delete_dns_record(fqdn, record_id)

    @functools.cached_property
    def _timeweb_client(self) -> Timeweb:
        return Timeweb(token=self.credentials.conf("api_key"))

    def _root_domain(self, domain: str) -> str:
        return get_fld(domain, fix_protocol=True)
