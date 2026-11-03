# Design

## The box

- One **push encoder**, one **footswitch**, one **0.96" 128×64 OLED**
- An **RP2040** (Pro Micro size) running MOD's cc-slave library
- Two **RJ45** jacks: MAIN (from the Duo or the previous box) and NEXT (to the next box)
- Powered by the Duo over the cable; no power supply per box

Boxes are identical, with the same firmware and no channel switch. The Duo numbers
them as they connect.

## The display

```
+--------------------------+
| <       PAGE 1/3       > |   header: page or list position, only when there's more than one
| CANABYSS                 |   encoder: effect
| D-TIME            500ms  |            parameter + value
+--------------------------+
| TAJMAHAL                 |   footswitch: effect
| BYPASS                ON |               parameter + state
+--------------------------+
```

A Control Chain assignment carries **one label** (16 characters max), plus unit,
range and value. There's no separate field for the effect. So the box uses a
convention:

- **`EFFECT|PARAM`** splits into two lines: `CANABYSS|D-TIME` → `CANABYSS` / `D-TIME`.
  For now you type this in the label field of the Duo's assign dialog. A small
  mod-ui patch could fill it in automatically.
- **A toggle labelled with just a plugin name** is what the Duo sends for a
  plugin's on/off control by default. The box shows it as that plugin's `BYPASS`,
  so footswitches get the effect name with no typing at all.
- **Bypass is shown the way you'd read it on stage:** the Duo sends 1 for
  *bypassed*, and the box shows `ON` when the effect is running.
- Toggles show `ON`/`OFF`. Values get their unit, with decimals chosen by range
  (`500ms`, `4.0s`, `45%`).

## Two layouts: LIST or PAGES

Chosen per box in its settings. Both are useful; they suit different rigs.

| | **LIST** (default) | **PAGES** |
|---|---|---|
| Push does | next parameter on the encoder | next page (encoder **and** footswitch) |
| The Duo sees | `Encoder`, `Footswitch` | `Encoder Page #1..#N`, `Footswitch Page #1..#N` |
| Assigning | up to 4 parameters on the encoder | one parameter per numbered control |
| Footswitch | stays put | different job on each page |
| Good for | one stomp you always need + several knobs | complete scenes |

**Why both:** on the Duo, a parameter can be assigned to only **one** control at a
time, and the master only sends the *current* page to a box. So in PAGES mode, a
stomp on page 1 can't be reached from page 2. If you always need that stomp, use
LIST.

**Switching layout resets all bindings.** The box declares its layout when it
connects, so changing it means the box reconnects and the Duo sees a different set
of controls. The box asks first:

```
| SWITCH TO PAGES?         |
| BOX RECONNECTS           |
| ALL BINDINGS RESET       |
| PUSH: YES       HOLD: NO |
```

A page change takes about 0.2 s: the box can only ask for a page on the master's
periodic sync, and then the new page's assignments are sent.

## Gestures

All on the **encoder push**. Never on the footswitch, where a long press happens by
accident mid-song.

| Gesture | Does |
|---|---|
| Push | next parameter (LIST) or next page (PAGES) |
| Double-click | reset the parameter on screen to its default (the plugin author's value, sent with every assignment) |
| Long press (0.6 s) | settings |

A single push acts after a 250 ms pause, so the box can tell it apart from a
double-click.

Switching parameters doesn't make values jump: an encoder only reports movement,
so you carry on from the new parameter's current value.

## Settings

Saved per box in flash.

| Setting | Options |
|---|---|
| Mode | LIST / PAGES (confirm: resets bindings) |
| Pages | 2–4 (PAGES mode; confirm: resets bindings) |
| Speed | slow / normal / fast encoder steps (applies immediately) |

Planned: USB MIDI mode, MIDI channel and CCs, brightness, display flip, footswitch
latch or momentary, lock.

## Bigger boxes

One RP2040 can run several encoder, footswitch and display sets as **one** Control
Chain device, much like MOD's own 4-switch footswitch. On the Duo it uses one
device slot instead of four.

- Two displays per I2C bus (addresses 0x3C/0x3D), two buses, so 4 displays with no
  extra parts
- A Pro Micro has pins for about 2 sets; a full-size Pico, about 4
- LIST works per encoder; PAGES flips all sets together (that's how the protocol
  defines pages)
