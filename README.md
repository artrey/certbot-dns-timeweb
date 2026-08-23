# certbot-dns-timeweb

[![PyPI](https://img.shields.io/pypi/v/certbot-dns-timeweb)](https://pypi.org/project/certbot-dns-timeweb/)
[![Python versions](https://img.shields.io/pypi/pyversions/certbot-dns-timeweb)](https://pypi.org/project/certbot-dns-timeweb/)
[![License](https://img.shields.io/pypi/l/certbot-dns-timeweb)](LICENSE)

Timeweb Cloud DNS Authenticator plugin for [Certbot](https://certbot.eff.org/).

It automates the `dns-01` challenge by creating and then removing TXT records
through the [Timeweb Cloud API](https://timeweb.cloud/api-docs), which makes it
possible to issue wildcard certificates.

## Requirements

- Python 3.10+
- Certbot 2.8 or newer (including the 3.x, 4.x and 5.x lines)
- A domain hosted on the Timeweb Cloud account the API key belongs to

The plugin depends only on `certbot` and `requests`, so installing it never
forces a downgrade of certbot or of anything else in the same environment.

## Installation

```bash
pip install certbot-dns-timeweb
```

The plugin has to live in the same Python environment as certbot itself.
If certbot was installed from a distribution package or into a virtualenv, use
that environment's `pip`:

```bash
/opt/certbot/bin/pip install certbot-dns-timeweb
```

There is no snap of this plugin, so a snap-installed certbot cannot load it —
install certbot with `pip` instead.

For images that bundle certbot (nginx-proxy-manager, NPMplus and friends) the
plugin is installed next to the bundled certbot and, since it no longer pins an
upper bound on certbot, it will not downgrade the one already in the image.

## Getting started

1. Create an [access token](https://timeweb.cloud/my/api-keys) in the Timeweb
   Cloud control panel.
2. Put it into a credentials file, for example `/etc/letsencrypt/timeweb-creds.ini`:

   ```ini
   dns_timeweb_api_key = XXXXXXXXXXXXXXXXXXX
   ```

3. Restrict its permissions — certbot refuses to use world-readable credentials:

   ```bash
   chmod 600 /etc/letsencrypt/timeweb-creds.ini
   ```

4. Issue a certificate:

   ```bash
   certbot certonly \
       --authenticator dns-timeweb \
       --dns-timeweb-credentials /etc/letsencrypt/timeweb-creds.ini \
       -d example.org -d '*.example.org'
   ```

Subdomains and wildcards on subdomains work the same way:

```bash
certbot certonly \
    --authenticator dns-timeweb \
    --dns-timeweb-credentials /etc/letsencrypt/timeweb-creds.ini \
    -d dev.example.org -d '*.dev.example.org'
```

The plugin looks up which of the domains on your account owns the name being
validated, so only the parent domain (`example.org` here) has to be registered
in Timeweb Cloud.

## Plugin arguments

| Argument | Description | Default |
| --- | --- | --- |
| `--dns-timeweb-credentials` | Path to the credentials INI file. | — |
| `--dns-timeweb-propagation-seconds` | How long to wait for the TXT record to propagate before the ACME server checks it. | `60` |

## Troubleshooting

**`Unable to determine the Timeweb Cloud zone for ...`** — the domain is not
present on the account the API key belongs to. Check
[timeweb.cloud/my/domains](https://timeweb.cloud/my/domains) and make sure the
domain's DNS is served by Timeweb.

**`Timeweb Cloud API returned HTTP 401`** — the API key is wrong, expired or
was revoked. Issue a new one.

**The ACME server does not see the TXT record** — increase
`--dns-timeweb-propagation-seconds`.

To see exactly which API calls are made, add `-v` to the certbot command and
look at `/var/log/letsencrypt/letsencrypt.log`.

## Development

The project uses [uv](https://docs.astral.sh/uv/) and [ruff](https://docs.astral.sh/ruff/).

```bash
uv venv
uv pip install -e . --group dev

uv run pytest            # tests
uv run ruff check .      # lint
uv run ruff format .     # format
```

### Debugging against the ACME staging environment

```bash
export TIMEWEB_API_KEY=XXXXXXXXXXXXXXXXXXX
uv run python scripts/debug_issue.py example.org '*.example.org'
```

The script runs `certbot certonly --dry-run` with all of its state confined to
the git-ignored `data/` directory.

## License

[MIT](LICENSE)
