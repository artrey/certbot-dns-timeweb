"""Tests for the Timeweb Cloud API client."""

import json

import pytest
import requests
import responses

from certbot_dns_timeweb.client import API_BASE_URL, TimewebAPIError, TimewebClient


@pytest.fixture
def client():
    return TimewebClient(api_key="secret-api-key")


def _domains_page(fqdns, total):
    return {"domains": [{"id": i, "fqdn": fqdn} for i, fqdn in enumerate(fqdns)], "meta": {"total": total}}


@responses.activate
def test_list_domains_sends_the_token(client):
    responses.get(f"{API_BASE_URL}/domains", json=_domains_page(["example.com"], 1))

    assert client.list_domains() == ["example.com"]
    assert responses.calls[0].request.headers["Authorization"] == "Bearer secret-api-key"


@responses.activate
def test_list_domains_follows_pagination(client):
    first_page = [f"domain{i}.com" for i in range(100)]
    responses.get(f"{API_BASE_URL}/domains", json=_domains_page(first_page, 101))
    responses.get(f"{API_BASE_URL}/domains", json=_domains_page(["last.com"], 101))

    assert client.list_domains() == [*first_page, "last.com"]
    assert len(responses.calls) == 2
    assert "offset=100" in responses.calls[1].request.url


@responses.activate
def test_list_domains_stops_on_a_short_page(client):
    responses.get(f"{API_BASE_URL}/domains", json={"domains": [{"fqdn": "example.com"}]})

    assert client.list_domains() == ["example.com"]
    assert len(responses.calls) == 1


@responses.activate
def test_add_txt_record(client):
    responses.post(
        f"{API_BASE_URL}/domains/example.com/dns-records",
        json={"dns_record": {"id": 80752125, "type": "TXT"}},
        status=201,
    )

    record_id = client.add_txt_record(
        zone="example.com",
        subdomain="_acme-challenge.dev.example.com",
        value="token-value",
    )

    assert record_id == 80752125
    assert json.loads(responses.calls[0].request.body) == {
        "type": "TXT",
        "value": "token-value",
        "subdomain": "_acme-challenge.dev.example.com",
    }


@responses.activate
def test_add_txt_record_without_an_id(client):
    responses.post(f"{API_BASE_URL}/domains/example.com/dns-records", json={"dns_record": {}}, status=201)

    with pytest.raises(TimewebAPIError, match="did not return an id"):
        client.add_txt_record(zone="example.com", subdomain="_acme-challenge.example.com", value="v")


@responses.activate
def test_delete_record_tolerates_an_empty_body(client):
    responses.delete(f"{API_BASE_URL}/domains/example.com/dns-records/42", body="", status=204)

    client.delete_record("example.com", 42)

    assert len(responses.calls) == 1


@responses.activate
def test_api_errors_are_reported_with_their_message(client):
    responses.post(
        f"{API_BASE_URL}/domains/example.com/dns-records",
        json={"status_code": 400, "message": "Bad DNS record type", "error_code": "bad_dns_record"},
        status=400,
    )

    with pytest.raises(TimewebAPIError, match=r"HTTP 400.*Bad DNS record type bad_dns_record"):
        client.add_txt_record(zone="example.com", subdomain="_acme-challenge.example.com", value="v")


@responses.activate
def test_api_errors_with_a_list_of_messages(client):
    responses.get(f"{API_BASE_URL}/domains", json={"message": ["first", "second"]}, status=403)

    with pytest.raises(TimewebAPIError, match="first; second"):
        client.list_domains()


@responses.activate
def test_api_errors_with_a_non_json_body(client):
    responses.get(f"{API_BASE_URL}/domains", body="<html>502 Bad Gateway</html>", status=502)

    with pytest.raises(TimewebAPIError, match="502 Bad Gateway"):
        client.list_domains()


@responses.activate
def test_connection_errors_are_wrapped(client):
    responses.get(f"{API_BASE_URL}/domains", body=requests.ConnectionError("no route to host"))

    with pytest.raises(TimewebAPIError, match="Error communicating with the Timeweb Cloud API"):
        client.list_domains()


@responses.activate
def test_malformed_success_body_is_reported(client):
    responses.get(f"{API_BASE_URL}/domains", body="not json", status=200)

    with pytest.raises(TimewebAPIError, match="malformed response"):
        client.list_domains()
