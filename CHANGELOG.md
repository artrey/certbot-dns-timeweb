# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-08-23

### Fixed

- Certificates can be issued for subdomains again ([#5](https://github.com/artrey/certbot-dns-timeweb/issues/5)).
  The Timeweb API field named `subdomain` expects the *full* name of the record
  (`_acme-challenge.dev.example.com`), not the label relative to the zone. The
  API accepted the old short form silently and created the record on the apex,
  so validation never succeeded. Same root cause and same fix as
  [go-acme/lego#2845](https://github.com/go-acme/lego/pull/2845).
- Cleanup failures are logged instead of aborting the certbot run, so a
  successfully issued certificate is no longer lost to an API hiccup.

### Changed

- **Dependency on certbot is now `>=2.8` with no upper bound**
  ([#4](https://github.com/artrey/certbot-dns-timeweb/issues/4),
  [#6](https://github.com/artrey/certbot-dns-timeweb/issues/6),
  [#7](https://github.com/artrey/certbot-dns-timeweb/issues/7)). Installing the
  plugin no longer downgrades certbot 3.x/4.x/5.x to 2.x. Tested against
  certbot 2.8.0 and the latest release on Python 3.10–3.13.
- Dropped the `timeweb-cloud` SDK in favour of a small `requests`-based client.
  The SDK pinned `httpx <0.24` and `pydantic <2`, which conflicted with other
  packages sharing the environment. The plugin now only needs `certbot` and
  `requests` (a certbot dependency itself).
- Dropped the `tld` dependency. The DNS zone is now resolved against the list of
  domains on the account instead of a bundled public-suffix list, which also
  handles subdomains registered as separate domains in Timeweb Cloud.
- Default `--dns-timeweb-propagation-seconds` raised from `10` to `60`.
- API errors are reported with the message returned by Timeweb Cloud instead of
  a bare exception.

### Added

- Test suite covering the API client and the challenge flow.
- CI matrix over Python 3.10–3.13 and over the oldest and newest supported
  certbot releases.

### Removed

- `main.py` debug helper, replaced by `scripts/debug_issue.py`.

## [1.0.1] - 2024-02-08

### Fixed

- Certificates for subdomains: the DNS record is created on the registrable
  domain rather than on the subdomain
  ([#2](https://github.com/artrey/certbot-dns-timeweb/issues/2)).

## [1.0.0] - 2024-01-21

- Initial public release.

[2.0.0]: https://github.com/artrey/certbot-dns-timeweb/releases/tag/v2.0.0
[1.0.1]: https://github.com/artrey/certbot-dns-timeweb/releases/tag/v1.0.1
[1.0.0]: https://github.com/artrey/certbot-dns-timeweb/releases/tag/v1.0.0
