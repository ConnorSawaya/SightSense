# Wiring

Planned wiring for the cane. Not yet built or tested. Power everything off before changing a wire.

## Power

```
12 V battery (+) ──► fuse (5 A) ──► kill switch ──► L298N 12 V terminal
12 V battery (−) ──────────────────────────────────► L298N GND ──► Pi GND
USB-C power bank ──► Raspberry Pi 5
```

- The Pi has its own power bank. Do not power it from the L298N's 5 V pin.
- All grounds are joined: battery negative, L298N GND and a Pi ground pin.
- A 1000 µF capacitor (25 V or more) goes across the L298N's 12 V and GND terminals, stripe side to GND.
- The kill switch must be within the user's reach.

## Signals

GPIO numbers are BCM numbers, not positions on the header.

| Raspberry Pi | Connects to |
| --- | --- |
| GPIO23 | L298N IN1 |
| GPIO24 | L298N IN2 |
| GPIO18 | L298N ENA (remove the ENA jumper first) |
| GPIO5 | Left limit switch (other leg to GND) |
| GPIO13 | Centre limit switch (other leg to GND) |
| GPIO6 | Right limit switch (other leg to GND) |
| GND | L298N GND |

Motor on L298N OUT1 and OUT2. Leave the L298N's 5 V regulator jumper on.

## Limits to respect

- The L298N handles about 2 A per channel and loses about 2 V, so the motor sees roughly 10 V. It runs hot.
- Motor power is capped at 25% in software, and each steering move is cut off after 0.4 seconds.
- No command from the GX10 for 0.4 seconds: motor driver off.
- Use the `gpiozero` library. `RPi.GPIO` and `pigpio` do not work on a Raspberry Pi 5.
