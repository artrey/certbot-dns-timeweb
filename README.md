# certbot-dns-timeweb

Timeweb DNS Authenticator plugin for Certbot

## Installation

```bash
pip install certbot-dns-timeweb
```

## Getting started

Get Timeweb Cloud [access token](https://timeweb.cloud/my/api-keys) and fill credentials configuration.

Then issue a certificate with command like:

```bash
certbot certonly --authenticator dns-timeweb \
    --dns-timeweb-credentials /etc/letsencrypt/timeweb-creds.ini \
    -d example.org -d *.example.org
```

## Plugin arguments

- `--dns-timeweb-credentials` - path to Credentials configuration.
- `--dns-timeweb-propagation-seconds` - seconds when DNS record is propagated (default: 10)

## Configuration example

```ini
# /etc/letsencrypt/timeweb-creds.ini is a suggested path for
# configuration file. You may place him in any place.
dns_timeweb_api_key = XXXXXXXXXXXXXXXXXXX
```

## Development

### Local debugging

1. Install the plugin in developer mode

```bash
pip install --editable ./
```

2. Run (or debug) `main.py` script
