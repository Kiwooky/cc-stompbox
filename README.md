# cc-stompbox

**A small, chainable stompbox for MOD devices. One encoder, one footswitch, one screen that tells you exactly what you're touching.**

```
+--------------------------+
| <       PAGE 1/3       > |
| CANABYSS                 |
| D-TIME            500ms  |
+--------------------------+
| TAJMAHAL                 |
| BYPASS                ON |
+--------------------------+
```

Every MOD Duo, Duo X and Dwarf has a **Control Chain** port: MOD's own bus for
external controllers. Unlike MIDI, it tells the controller *what* it's
controlling: the parameter's name, range, unit and current value. That's what lets
this box show `CANABYSS / D-TIME 500ms` at your feet instead of `CC 14`.

The port has been quiet for years. MOD's Arduino shield is no longer sold, and its
library is stuck on a 2017 protocol version, which is why forum threads ask "is it
abandoned?". But the protocol code MOD ships in the Duo today is current, and it
works. This project builds on that code directly.

## Status

| | |
|---|---|
| ✅ Protocol | MOD's current master and device libraries (protocol 0.7) talking, proven in emulation on Linux and macOS |
| ✅ Chaining | Identical boxes number themselves; no channel switches. Up to 8 devices per chain in software |
| ✅ Display | Effect, parameter and value from each assignment, including the Duo's default bypass labels |
| ✅ Two layouts | LIST (encoder cycles parameters, footswitch fixed) or PAGES (whole box flips), chosen in the box's settings |
| ✅ Gestures | Push, double-click (reset to default), long press (settings) |
| 🔧 Hardware | Parts chosen, wiring drawn, boards on order |
| ⏳ Firmware | RP2040 port of the emulator, next |
| ⏳ On a Duo | First real-world test |

## Try it now, no hardware needed

The [emulator](emulator/) runs the box firmware on your computer against MOD's real
master software, with a stand-in for the Duo's web UI:

    cd emulator
    make deps && make
    # then five terminal tabs — see emulator/README.md

## Read more

- [Design](docs/design.md): the box, the display, LIST vs PAGES, gestures, settings
- [Hardware](docs/hardware.md): parts, RJ45 pinout, transceiver and RP2040 wiring
- [Protocol notes](docs/protocol-notes.md): how Control Chain and the Duo behave in practice, found by reading MOD's code
- [Firmware](firmware/): the RP2040 plan
- [Log](docs/log.md): what was found, in order

## Credits and licences

Built on MOD Audio's [cc-master](https://github.com/mod-audio/cc-master) and
[cc-slave](https://github.com/mod-audio/cc-slave) (LGPL-3.0). They're fetched at
build time, not copied here. The hardware notes draw on MOD's open-hardware
[Arduino shield](https://github.com/mod-archive/mod-cc-hw-arduino-shield) (CC BY-SA).

This project's own code is MIT licensed (see [LICENSE](LICENSE)). It's not
affiliated with MOD Audio.
