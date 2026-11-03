# Log

What was found, in order. Newest at the bottom.

## Is Control Chain abandoned?

The MOD Arduino shield is out of production, and the forum asks whether Control Chain
is dead. Reading the code: MOD's Arduino library is stuck on a 2017 snapshot
(protocol 0.5), but the master in the Duo and the current device library are both on
0.7 and match. So the port isn't dead. Its hobbyist toolkit is out of date.

Plan: skip the Arduino library and run the current device library on an RP2040.

## Limits

The master allows 8 devices per chain. MOD's "4 per Duo" is most likely a power
budget. A 9-box emulator test: 8 register, and the 9th retries forever without
being added.

## Building MOD's master on a desktop

cc-master's build tool no longer runs on modern Python, so it's compiled directly.
libserialport refuses virtual serial ports, so a small stand-in replaces it for
desktop tests.

## First contact

A desktop "fake stompbox" running the real cc-slave registered with the real
master: handshake on protocol 0.7, descriptor with two controls. Three identical
boxes on a virtual bus numbered themselves 0, 1, 2. No channel switches needed.

## macOS

Three bugs in cc-master on macOS, all patched at build time: no unnamed semaphores;
`-f` ignored (the server silently went to the background); socket address one byte
short (binding `/tmp/control-chain.soc`). After that, the full setup ran on a Mac.

## Round trip

A stand-in for the Duo's web UI, using the master's socket API, assigned
parameters. Boxes showed them, encoder turns came back as values, and unassigning
cleared them.

## What does the box know?

A Control Chain assignment has no field for the effect name. Only a 16-character
label, unit, range and value. Hence the `EFFECT|PARAM` label convention. mod-ui's
default bypass label is the plugin's name, so footswitches get it for free.

## Cycling parameters

The master accepts several assignments on one encoder, but cc-slave only keeps the
newest active. The firmware keeps the list and re-points the encoder on each push.

## LIST vs PAGES

Protocol pages flip the whole box, and mod-ui allows a parameter on only one control.
So with pages, a page-1 stomp is unreachable from page 2. Both layouts are offered,
chosen in the box's settings, with a warning that switching resets all bindings.
Proven in the emulator: switching modes, reconnecting, and paging forward and back.

## Hardware

Read MOD's shield design for the details: full-duplex RS-485 (ISL83491), 12 V on
RJ45 pins 4/5, termination switched in on the last box. The RP2040 board needs a
12 V → 5 V buck. The transceiver is a MAX3491 (DIP-14).
