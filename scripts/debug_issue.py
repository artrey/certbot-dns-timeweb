#!/usr/bin/env python3
"""Issue a certificate against the ACME staging environment for local debugging.

Usage::

    export TIMEWEB_API_KEY=...
    python scripts/debug_issue.py example.com '*.example.com'

Everything certbot writes (config, logs, work dir) lands in ``./data`` which is
git-ignored, so the script never touches the system-wide certbot state.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CREDENTIALS_PATH = DATA_DIR / "timeweb-creds.ini"


def main(domains: list[str]) -> int:
    if not domains:
        print(f"usage: {sys.argv[0]} DOMAIN [DOMAIN ...]", file=sys.stderr)
        return 2

    DATA_DIR.mkdir(exist_ok=True)
    api_key = os.environ.get("TIMEWEB_API_KEY")
    if api_key:
        CREDENTIALS_PATH.write_text(f"dns_timeweb_api_key = {api_key}\n")
        CREDENTIALS_PATH.chmod(0o600)
    elif not CREDENTIALS_PATH.exists():
        print(
            f"Set TIMEWEB_API_KEY or create {CREDENTIALS_PATH} with a 'dns_timeweb_api_key = ...' line.",
            file=sys.stderr,
        )
        return 2

    from certbot._internal import main as certbot_main

    args = [
        "certonly",
        "--dry-run",
        "-v",
        "--agree-tos",
        "--register-unsafely-without-email",
        f"--config-dir={DATA_DIR / 'config'}",
        f"--work-dir={DATA_DIR / 'work'}",
        f"--logs-dir={DATA_DIR / 'logs'}",
        "--authenticator=dns-timeweb",
        f"--dns-timeweb-credentials={CREDENTIALS_PATH}",
        "--dns-timeweb-propagation-seconds=30",
    ]
    for domain in domains:
        args += ["-d", domain]

    certbot_main.main(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
