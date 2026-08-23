"""Tests for the DNS-01 challenge handling."""

from unittest import mock

import pytest
from certbot import errors

from certbot_dns_timeweb.authenticator import DEFAULT_PROPAGATION_SECONDS, Authenticator


def test_more_info_is_a_string(authenticator):
    assert isinstance(authenticator.more_info(), str)


def test_parser_arguments_registers_credentials_and_propagation():
    add = mock.MagicMock()
    Authenticator.add_parser_arguments(add)

    add.assert_any_call("credentials", help=mock.ANY)
    add.assert_any_call(
        "propagation-seconds",
        type=int,
        default=DEFAULT_PROPAGATION_SECONDS,
        help=mock.ANY,
    )


@pytest.mark.parametrize(
    ("validation_name", "expected_zone"),
    [
        # Apex and wildcard on the apex share the same challenge name.
        ("_acme-challenge.example.com", "example.com"),
        # Regression test for the subdomain support (issue #5): the zone is the
        # registered domain, not the subdomain the certificate is issued for.
        ("_acme-challenge.dev.example.com", "example.com"),
        ("_acme-challenge.a.b.c.example.com", "example.com"),
        # A subdomain registered as a separate domain wins over its parent.
        ("_acme-challenge.dev.example.net", "dev.example.net"),
        # Case and trailing dots must not matter.
        ("_acme-challenge.DEV.Example.COM.", "example.com"),
    ],
)
def test_find_zone(authenticator, fake_client, validation_name, expected_zone):
    authenticator._client = fake_client

    assert authenticator._find_zone(validation_name) == expected_zone


def test_find_zone_lists_domains_only_once(authenticator, fake_client):
    authenticator._client = fake_client

    authenticator._find_zone("_acme-challenge.example.com")
    authenticator._find_zone("_acme-challenge.dev.example.com")

    fake_client.list_domains.assert_called_once()


def test_find_zone_fails_for_unknown_domain(authenticator, fake_client):
    authenticator._client = fake_client

    with pytest.raises(errors.PluginError, match="Unable to determine the Timeweb Cloud zone"):
        authenticator._find_zone("_acme-challenge.unknown.tld")


def test_perform_sends_the_full_record_name_as_subdomain(authenticator, fake_client):
    """The Timeweb "subdomain" field holds the full name, not the label."""
    authenticator._client = fake_client

    authenticator._perform("dev.example.com", "_acme-challenge.dev.example.com", "token-value")

    fake_client.add_txt_record.assert_called_once_with(
        zone="example.com",
        subdomain="_acme-challenge.dev.example.com",
        value="token-value",
    )


def test_cleanup_removes_created_records(authenticator, fake_client):
    authenticator._client = fake_client
    fake_client.add_txt_record.side_effect = [11, 22]

    # A certificate for both example.com and *.example.com yields two
    # challenges sharing one validation name.
    authenticator._perform("example.com", "_acme-challenge.example.com", "first")
    authenticator._perform("example.com", "_acme-challenge.example.com", "second")
    authenticator._cleanup("example.com", "_acme-challenge.example.com", "first")

    assert fake_client.delete_record.call_args_list == [
        mock.call("example.com", 11),
        mock.call("example.com", 22),
    ]

    # The second cleanup call for the same name must be a no-op.
    fake_client.delete_record.reset_mock()
    authenticator._cleanup("example.com", "_acme-challenge.example.com", "second")
    fake_client.delete_record.assert_not_called()


def test_cleanup_without_perform_does_nothing(authenticator, fake_client):
    authenticator._client = fake_client

    authenticator._cleanup("example.com", "_acme-challenge.example.com", "token-value")

    fake_client.delete_record.assert_not_called()


def test_cleanup_swallows_api_errors(authenticator, fake_client, caplog):
    authenticator._client = fake_client
    fake_client.delete_record.side_effect = errors.PluginError("boom")

    authenticator._perform("example.com", "_acme-challenge.example.com", "token-value")
    authenticator._cleanup("example.com", "_acme-challenge.example.com", "token-value")

    assert "Could not remove TXT record" in caplog.text


def test_client_is_built_from_the_credentials_file(authenticator):
    with mock.patch("certbot_dns_timeweb.authenticator.TimewebClient") as client_cls:
        assert authenticator._client is client_cls.return_value

    authenticator.credentials.conf.assert_called_once_with("api_key")
    client_cls.assert_called_once_with(api_key="secret-api-key")


def test_client_requires_configured_credentials():
    auth = Authenticator(config=mock.MagicMock(), name="timeweb")

    with pytest.raises(errors.PluginError, match="credentials have not been configured"):
        _ = auth._client
