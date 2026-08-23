from unittest import mock

import pytest

from certbot_dns_timeweb.authenticator import Authenticator

API_BASE_URL = "https://api.timeweb.cloud/api/v1"


@pytest.fixture
def authenticator():
    auth = Authenticator(config=mock.MagicMock(), name="timeweb")
    auth.credentials = mock.MagicMock()
    auth.credentials.conf.return_value = "secret-api-key"
    return auth


@pytest.fixture
def fake_client():
    client = mock.MagicMock()
    client.list_domains.return_value = ["example.com", "example.org", "dev.example.net"]
    client.add_txt_record.return_value = 1
    return client
