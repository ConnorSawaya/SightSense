#!/bin/bash
# Install only the Pi dependencies already listed in README.md.
set -eu
if /usr/bin/python3 -c 'import gpiozero, lgpio, websockets'; then
    exit 0
fi
export DEBIAN_FRONTEND=noninteractive
apt-get -o DPkg::Lock::Timeout=120 -o Acquire::Retries=2 update
apt-get -o DPkg::Lock::Timeout=120 -o Acquire::Retries=2 install -y python3-gpiozero python3-lgpio python3-websockets
/usr/bin/python3 -c 'import gpiozero, lgpio, websockets'
