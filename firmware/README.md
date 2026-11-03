# Firmware (RP2040), next up

The plan: take [`emulator/fakebox.c`](../emulator/fakebox.c) and replace only its
PLATFORM SHIM section. Gestures, settings, both layouts and the display layout
stay as they are.

| Desktop shim | RP2040 |
|---|---|
| serial port | UART0 (GPIO 0/1) via the MAX3491, DE on GPIO 2 |
| `clock_gettime` timer | hardware alarm, one-shot |
| keyboard push playback | GPIO 8 into the same gesture detector |
| `+` / `-` keys | encoder on GPIO 6/7 (PIO quadrature decoding is an option) |
| `f` key | GPIO 9 |
| settings file | last flash sector |
| `execv` restart | watchdog reset |
| terminal "OLED" | SSD1306 over I2C0 (GPIO 4/5) |

**Sending:** the RP2040's UART has no RS-485 mode, so the send hook raises DE,
writes the bytes, waits for the UART's busy flag to clear, then drops DE. That's
well within each box's 1 ms time slot. If a scope shows DE dropping late, a PIO UART
can drive DE in step with the data.

Toolchain: Pico SDK or the arduino-pico core, in C, with cc-slave compiled in
alongside.
