#!/bin/sh
# Start fake stompbox number N on the live virtual bus:  ./box.sh 1 [name]
cd "$(dirname "$0")" || exit 1
N="${1:-1}"
NAME="${2:-Stompbox}"
if [ ! -f .bus ]; then
  echo "No virtual bus running. Start it first in another tab:  python3 vbus.py 2"
  exit 1
fi
. ./.bus
eval "PORT=\$BOX$N"
if [ -z "$PORT" ]; then
  echo "Bus has no box $N. Restart it with more slots, e.g.  python3 vbus.py 4"
  exit 1
fi
exec ./fakebox "$PORT" "$NAME" ".box$N.settings"
