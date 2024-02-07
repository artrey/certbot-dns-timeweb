import os

from certbot._internal import main

main.main(
    "certonly -v --dry-run"
    " --logs-dir=$PWD/data/logs"
    " --work-dir=$PWD/data/data"
    " --config-dir=$PWD/data/config"
    " --authenticator dns-timeweb"
    " --dns-timeweb-credentials=$PWD/data/timeweb-creds.ini"
    " --dns-timeweb-propagation-seconds=15"
    " -d <desired_domain>".replace("$PWD", os.path.dirname(__file__)).split()
)
