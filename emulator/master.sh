#!/bin/sh
# Start the emulated Duo (cc-master) on the live virtual bus.
cd "$(dirname "$0")" || exit 1
if [ ! -f .bus ]; then
  echo "No virtual bus running. Start it first in another tab:  python3 vbus.py 2"
  exit 1
fi
. ./.bus
rm -f /tmp/control-chain.soc   # leftover from the old macOS socket bug
echo "Master on $MASTER"
LIBCONTROLCHAIN_DEBUG=1 exec ./controlchaind "$MASTER" -f
