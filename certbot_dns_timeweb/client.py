"""Minimal Timeweb Cloud API client used by the DNS authenticator."""

from __future__ import annotations

import logging
from typing import Any

import requests
from certbot import errors

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.timeweb.cloud/api/v1"
DEFAULT_TIMEOUT = 30
DOMAINS_PAGE_SIZE = 100
MAX_DOMAINS_PAGES = 100


class TimewebAPIError(errors.PluginError):
    pass


class TimewebClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = API_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        user_agent: str = "certbot-dns-timeweb",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "User-Agent": user_agent,
            }
        )

    def list_domains(self) -> list[str]:
        domains: list[str] = []
        offset = 0
        for _ in range(MAX_DOMAINS_PAGES):
            payload = self._request(
                "GET",
                "/domains",
                params={"limit": DOMAINS_PAGE_SIZE, "offset": offset},
            )
            page = payload.get("domains") or []
            domains.extend(item["fqdn"] for item in page if item.get("fqdn"))
            total = (payload.get("meta") or {}).get("total")
            offset += DOMAINS_PAGE_SIZE
            if len(page) < DOMAINS_PAGE_SIZE or (total is not None and offset >= total):
                break
        else:
            logger.warning("Stopped listing Timeweb domains after %d pages.", MAX_DOMAINS_PAGES)
        return domains

    def add_txt_record(self, zone: str, subdomain: str, value: str) -> int:
        """Create a TXT record inside ``zone`` and return its identifier.

        ``subdomain`` is the *full* name of the record (for example
        ``_acme-challenge.dev.example.com``), not the label relative to the
        zone -- that is what the Timeweb API expects despite the field name.
        """
        payload = self._request(
            "POST",
            f"/domains/{zone}/dns-records",
            json={"type": "TXT", "value": value, "subdomain": subdomain},
        )
        record = payload.get("dns_record") or {}
        record_id = record.get("id")
        if record_id is None:
            raise TimewebAPIError(f"Timeweb API did not return an id for the created record: {payload}")
        return int(record_id)

    def delete_record(self, zone: str, record_id: int) -> None:
        self._request("DELETE", f"/domains/{zone}/dns-records/{record_id}")

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            response = self._session.request(method, url, timeout=self._timeout, **kwargs)
        except requests.RequestException as error:
            raise TimewebAPIError(
                f"Error communicating with the Timeweb Cloud API ({method} {path}): {error}"
            ) from error

        if not response.ok:
            raise TimewebAPIError(
                f"Timeweb Cloud API returned HTTP {response.status_code} for {method} {path}: "
                f"{_error_message(response)}"
            )

        if not response.content:
            return {}
        try:
            payload = response.json()
        except ValueError as error:
            raise TimewebAPIError(
                f"Timeweb Cloud API returned a malformed response for {method} {path}: {error}"
            ) from error
        return payload if isinstance(payload, dict) else {}


def _error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip() or "<empty response>"

    if not isinstance(payload, dict):
        return str(payload)

    message = payload.get("message")
    if isinstance(message, list):
        message = "; ".join(str(item) for item in message)
    error_code = payload.get("error_code")
    parts = [str(part) for part in (message, error_code) if part]
    return " ".join(parts) or str(payload)
