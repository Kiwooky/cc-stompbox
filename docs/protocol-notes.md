# Protocol notes

What Control Chain and the Duo actually do, found by reading MOD's
[cc-master](https://github.com/mod-audio/cc-master),
[cc-slave](https://github.com/mod-audio/cc-slave) and
[mod-ui](https://github.com/mod-audio/mod-ui) source and confirmed in the emulator.

## Why the Arduino library seems broken

- cc-master and the current cc-slave both speak **protocol 0.7**.
- MOD's Arduino library pins a 2017 cc-slave snapshot at **protocol 0.5**, 29 commits
  behind. That gap explains the "buggy / abandoned" reputation.
- This project uses the current cc-slave directly and skips the Arduino library.

## Chaining

- **8 devices per chain** (`CC_MAX_DEVICES` in cc-master). Tested with 9 boxes in the
  emulator: 8 register, and the 9th gets a reply but is never added, retrying silently.
- MOD's "4 per Duo" figure is most likely a power budget for 12 V over the cable.
- **No channel switch needed:** the master gives each box of the same type the next
  free channel. Channel follows the order boxes finish registering, which can vary at
  power-up.
- A box that reconnects gets a new device number; the old one lingers until it times
  out.

## How the Duo assigns things

- Default label = the parameter's short name. For a plugin's bypass, the default
  label is **the plugin's name**, the mode is toggle + integer, and **1 = bypassed**.
- **One parameter, one control:** assigning a parameter somewhere else removes it
  from where it was.
- A box declares `max_assignments` per control. The master accepts several
  assignments on one control, but **cc-slave keeps only the newest one active**, so
  cycling between them is the firmware's job.
- Still to confirm on a real Duo: that the assign dialog actually offers several
  parameters on one Control Chain encoder.

## Pages

- A box declares a page count. The master duplicates every control per page and
  names them `Encoder Page #1`, `#2`, ….
- The box asks for a page with `cc_request_page(n)`, which is **1-based**. cc-slave
  clears its local assignments, and the master sends that page's set, renumbering the
  controls back to 0, 1, … so the box code is the same on every page.
- The request goes out on the master's next *handshake* sync (every 20 × 10 ms), so a
  page change takes about 0.2 s.

## Talking to cc-slave

| Hook | Notes |
|---|---|
| `cc_parse()` | feed it received bytes |
| send callback (via `cc_init`) | bytes out; on hardware, raise DE before sending and drop it once the UART has finished |
| event callback (via `cc_init`) | assignment (label, unit, min/max/default, value), unassignment, local updates |
| `timer_init` / `timer_set` | one-shot timer; the argument is **microseconds** despite the header's name |
| `delay_us`, `delay_ms` | busy waits |
| `cc_process()` | call from the main loop |

- When the Duo changes a value, the event id is `CC_CMD_SET_VALUE` (a command
  number, not one of the `CC_EV_*` events), and cc-slave doesn't apply the value
  itself. The firmware updates the assignment.
- Every handshake reply is reported as `CC_EV_HANDSHAKE_FAILED`; status 0 means OK.
- Current cc-slave won't compile without `MAX_PAGES` defined in `config.h`.
- cc-slave scales a continuous control to the parameter's range itself; the firmware
  works in 0–1.

## The master's socket API (what mod-ui uses)

Unix socket `/tmp/control-chain.sock`. JSON messages, each followed by a NUL byte:
`{"request": "<name>", "data": {...}}`.

| Request | Data |
|---|---|
| `device_list` | |
| `device_descriptor` | `device_id`. Returns label, uri, version, protocol and actuators (id, name, max_assignments) |
| `assignment` | `device_id, actuator_id, label, value, min, max, def, mode, steps, unit, options`. Numbers must be JSON **decimals** (`500.0`, not `500`), or they're read as 0 |
| `unassignment` | `device_id, assignment_id, assignment_pair_id` |
| `value_set` | `device_id, actuator_id, assignment_id, value` |
| `data_update` / `device_status` | `enable` (subscribe to events) |

- Assignment numbers are **per device**: every box starts at 0.
- `data_update` events: `device_id` plus base64 `raw_data` (a count byte, then
  assignment id (uint8) and value (float) pairs).
- `device_status` events: `device_id, status` (1 connected, 0 gone).
- Mode flags: toggle 0x001, trigger 0x002, options 0x004, tap tempo 0x008, real 0x010,
  integer 0x020, logarithmic 0x040, coloured 0x100, momentary 0x200, reverse 0x400.
