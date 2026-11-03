# Emulator

Run a Control Chain stompbox on your computer, talking to MOD's real master
software, before any hardware exists. The box (`fakebox`) runs MOD's actual
`cc-slave` library; the master (`controlchaind`) is MOD's actual `cc-master`, the
same program that runs inside a Duo. They talk over a virtual cable, and
`assign.py` plays the part of the Duo's web UI.

```
[assign.py] --socket--> [controlchaind] <--virtual RS-485 bus--> [fakebox 1] [fakebox 2] ...
 (web UI's role)          (the Duo's master)    (vbus.py)           (the stompboxes)
```

Tested on Linux and macOS.

## Build

macOS:

    xcode-select --install                      # C compiler, if not installed
    brew install jansson libserialport pkg-config

Debian/Ubuntu:

    sudo apt install build-essential pkg-config libjansson-dev libserialport-dev

Then, from this folder:

    make deps      # fetches MOD's cc-master and cc-slave at the tested commits
    make

## Run — one terminal tab each, in this order

    python3 vbus.py 2      # 1. the cable (2 box slots); leave it running
    ./master.sh            # 2. the Duo's master
    ./box.sh 1             # 3. first box
    ./box.sh 2             # 4. second box
    python3 assign.py      # 5. the web UI: assigns parameters, prints changes

You'll know it works when the master prints `channel: 0` and `channel: 1`, the
boxes show their parameters, and turning a box's encoder prints the new value in
tab 5.

`vbus.py` writes the live port paths to `.bus` and deletes it when it stops, so
`master.sh` and `box.sh` can never pick up a stale port. Stop everything with
Ctrl-C, cable last.

## Box keys (no Return needed)

    + / -   turn the encoder
    p       push            next parameter (LIST) or next page (PAGES)
    d       double-click    reset the parameter on screen to its default
    l       long press      settings (turn to move, push to change, hold to leave)
    f       footswitch
    q       quit

Each box saves its settings in `.box1.settings`, `.box2.settings`, …
Delete the file to go back to defaults (LIST mode).

## Files

| File | What it is |
|---|---|
| `fakebox.c` | The stompbox firmware. Only the PLATFORM SHIM section at the top is desktop-specific; the rest is meant to move to the RP2040 unchanged. |
| `config.h` | cc-slave sizing (same on hardware). |
| `vbus.py` | Virtual full-duplex RS-485 bus: the master hears every box, boxes hear the master. |
| `master.sh`, `box.sh` | Start the master / box N on the live bus. |
| `assign.py` | Stand-in for the Duo's web UI, using the same socket API. Assigns each box as it connects (and again after a layout switch). |
| `spshim.c` | Desktop-only replacement for libserialport, which refuses virtual serial ports. |
| `portsem.h` | Semaphore replacement so cc-master builds on macOS. |

## Patches applied to MOD's master at build time

The Makefile copies two of cc-master's files and patches the copies; MOD's own
checkout is left untouched.

- **macOS option parsing:** BSD `getopt` stops at the port name, so `-f` (stay in
  the foreground) was ignored and the server silently went to the background.
- **macOS socket address:** the address-length calculation missed macOS's extra
  `sun_len` byte and bound to `/tmp/control-chain.soc`, which then broke every
  later start with "Address already in use".
- **macOS semaphores:** macOS has no unnamed POSIX semaphores (`portsem.h`).
- **Build system:** cc-master's bundled waf no longer runs on modern Python, so the
  Makefile compiles it directly.

## Other things worth knowing

- Give `controlchaind` the real `/dev/...` path, not a symlink, and keep it under
  64 characters.
- cc-slave reports *every* handshake reply as `CC_EV_HANDSHAKE_FAILED`; status 0
  means it succeeded.
- On a Mac you'll see `timedwait error 60` a few times while boxes register. It's
  a timeout and retry over the Python cable; registration still completes.
- Device numbers aren't reused: a box that reconnects gets a new number, and the
  old one lingers until the master times it out.
