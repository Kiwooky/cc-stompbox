#!/usr/bin/env python3
"""Virtual Control Chain bus for desktop testing.

Emulates the full-duplex RS-485 wiring: the master's TX line reaches every box,
and every box's TX line reaches the master (boxes don't hear each other).

Usage: python3 vbus.py [N]   (default 2 boxes)

Writes the port paths to .bus next to this script, and deletes it on exit, so
./master.sh and ./box.sh always use the live ports and never a stale one
(a stale path can belong to a Terminal tab, which then fills with garbage).
"""
import atexit, os, pty, select, signal, sys, tty

HERE = os.path.dirname(os.path.abspath(__file__))
BUSFILE = os.path.join(HERE, ".bus")

n = int(sys.argv[1]) if len(sys.argv) > 1 else 2

def mkpty():
    m, s = pty.openpty()
    tty.setraw(s)
    return m, os.ttyname(s), s

master = mkpty()
boxes = [mkpty() for _ in range(n)]

def remove_busfile():
    try:
        os.remove(BUSFILE)
    except FileNotFoundError:
        pass

def on_signal(*_):
    remove_busfile()
    print("\nVirtual bus stopped.")
    os._exit(0)

atexit.register(remove_busfile)
signal.signal(signal.SIGINT, on_signal)
signal.signal(signal.SIGTERM, on_signal)
signal.signal(signal.SIGHUP, on_signal)

with open(BUSFILE, "w") as f:
    f.write(f"MASTER={master[1]}\n")
    for i, b in enumerate(boxes):
        f.write(f"BOX{i+1}={b[1]}\n")

print(f"Virtual bus up with {n} box slot(s). Leave this running; Ctrl-C to stop.", flush=True)
print("Next:  ./master.sh     then in other tabs:  ./box.sh 1   ./box.sh 2 ...", flush=True)

fds = [master[0]] + [b[0] for b in boxes]
while True:
    r, _, _ = select.select(fds, [], [])
    for fd in r:
        try:
            data = os.read(fd, 4096)
        except OSError:
            continue
        if not data:
            continue
        if fd == master[0]:
            for b in boxes:              # master -> every box
                os.write(b[0], data)
        else:
            os.write(master[0], data)    # box -> master
