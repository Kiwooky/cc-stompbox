# Hardware

Based on MOD's open-hardware [Arduino shield](https://github.com/mod-archive/mod-cc-hw-arduino-shield)
(`hw-design/board`). Not built and tested yet: treat this as the plan.

## Parts

**Brains and controls**
- RP2040 Pro Micro (tested with a Tenstar RP2040 Pro Micro clone, on order)
- EC11 rotary encoder with push switch, plus knob
- **Momentary** soft-touch footswitch (not latching: the box does the toggling)
- 0.96" SSD1306 OLED, 128×64, **4-pin I2C** version

**The bus**
- **MAX3491** (DIP-14) or **ISL83491** (MOD's part, SOIC-14): 3.3 V, **full-duplex**
  RS-485. A half-duplex chip such as the MAX3485 won't work: Control Chain uses
  separate pairs in each direction.
- 14-pin DIP socket (cheap MAX3491 lots can be relabelled fakes, so test one first)
- 100 nF capacitor at the transceiver, 10k pull-down on DE
- 2× RJ45 jacks (MAIN, NEXT)
- 100 Ω resistor + "LAST" switch for termination on the last box

**Power** (the cable carries 12 V; the RP2040 board can't take that)
- Reverse-polarity diode (1N4007 or SS14)
- PTC resettable fuse (MOD uses 500 mA; ~200 mA is plenty for one box)
- 12 V → 5 V buck module (e.g. Pololu D24V5F5, MP1584 mini-buck)
- Schottky diode from the buck into the board's 5 V/RAW pin, so USB and bus power can coexist
- 10 µF bulk capacitor

**Build**
- 1590BB enclosure (1590B fits but is tight with two RJ45s and a display)
- Perfboard, hookup wire, M2 screws and standoffs, display window
- Short Cat5e patch cables between boxes

**For bring-up (optional)**
- 12 V bench supply
- USB to RS-422/485 **4-wire** adapter, so the emulator's master on a computer can
  talk to a real box before involving a Duo

## RJ45 pinout

MAIN and NEXT are wired straight through, pin for pin.

| Pin | Signal |
|---|---|
| 1 / 2 | RX+ / RX− (data from the Duo) |
| 3 / 6 | TX+ / TX− (data to the Duo) |
| 4, 5 | +12 V |
| 7, 8 | GND (on NEXT, pin 7 is the "next box present" sense line) |

**Termination:** 100 Ω across pins 1/2, on the **last** box only. MOD's shield does
this automatically: a MOSFET whose gate is pulled to 12 V, and pulled low through a
diode by NEXT pin 7 when a cable is plugged in. A "LAST" switch does the same job
with fewer parts.

## MAX3491 / ISL83491 (DIP-14) wiring

Same pinout as MOD's shield. Pin 1 is next to the notch.

| Pin | Name | Goes to |
|---|---|---|
| 2 | RO | RP2040 GPIO 1 (UART0 RX) |
| 3 | /RE | GND (always listening) |
| 4 | DE | RP2040 GPIO 2, plus 10k to GND |
| 5 | DI | RP2040 GPIO 0 (UART0 TX) |
| 6, 7 | GND | ground |
| 9 | Y | RJ45 pin 3 |
| 10 | Z | RJ45 pin 6 |
| 11 | B | RJ45 pin 2 |
| 12 | A | RJ45 pin 1 |
| 13, 14 | VCC | 3V3, with 100 nF to GND right at the pins |

**DE** switches the transmitter on only while the box is sending, because every
box shares the return pair. The 10k pull-down keeps it off while the RP2040 boots.

## RP2040 wiring

Pin numbers are the RP2040 GPIO numbers printed on the board. Check them against
your board: clones vary.

| RP2040 | Goes to |
|---|---|
| RAW | buck 5 V (through the Schottky) |
| GND | common ground: buck, RJ45 pins 7/8, everything |
| 3V3 | transceiver VCC, OLED VCC |
| 0 / 1 | transceiver DI / RO (UART0) |
| 2 | transceiver DE |
| 4 / 5 | OLED SDA / SCL (I2C0) |
| 6 / 7 | encoder A / B (common to GND) |
| 8 | encoder push (other leg to GND) |
| 9 | footswitch (other leg to GND) |
| 26 | status LED (optional, through a resistor) |

The RP2040's internal pull-ups cover the encoder and switches.

**Before wiring power:** with the board on USB, RAW should read about 5 V to GND
(4.7 V if there's a diode on board). The regulator near the USB port is usually
rated to about 6 V. **Never put 12 V on RAW.**

## Still to confirm

- The bus speed the Duo uses: the master code defaults to 115200 baud, MOD's wiki
  says 1 Mbit/s. The RP2040 handles either.
- Current per box, to see how many the Duo can power. MOD quoted 4 footswitches
  per Duo; the software limit is 8 devices.
