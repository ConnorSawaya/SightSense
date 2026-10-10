# Wiring

Planned wiring for the cane. Not yet built or tested. Power everything off before changing a wire.

## Power

```
12 V battery (+) ──► fuse (5 A) ──► kill switch ──► L298N 12 V terminal
12 V battery (−) ──────────────────────────────────► L298N GND ──► Pi GND
USB-C power bank ──► Raspberry Pi 5
```

- The Pi has its own power bank. Do not power it from the L298N's 5 V pin.
- All grounds are joined: battery negative, L298N GND and a Pi ground pin. The L298N's GND terminal takes two wires.
- A 1000 µF capacitor (25 V or more) goes across the L298N's 12 V and GND terminals, stripe side to GND.
- The kill switch must be within the user's reach.

## Signals

GPIO numbers are BCM numbers. The header pin is the position on the 40-pin header.

| Raspberry Pi | Header pin | Connects to |
| --- | --- | --- |
| GPIO18 | 12 | L298N ENA (remove the ENA jumper first) |
| GND | 14 | L298N GND |
| GPIO23 | 16 | L298N IN1 |
| GPIO24 | 18 | L298N IN2 |
| GPIO5 | 29 | Left limit switch |
| GPIO6 | 31 | Right limit switch |
| GPIO13 | 33 | Centre limit switch |
| GND | 39 | The other leg of all three switches |

Motor on L298N OUT1 and OUT2. Leave the L298N's 5 V regulator jumper on.

### Finding the pins

- Pin 1 is at the SD card end of the board, on the row nearer the middle. Pin 2 is beside it, on the row at the board's edge.
- Odd numbers run down the inner row, even numbers down the edge row. Pins 39 and 40 are at the USB ports end.
- Pins 12, 14, 16 and 18 are next to each other on the edge row, so the four L298N wires go in one block.
- Pins 25, 30 and 34 are also ground, if each switch gets its own ground wire.

### Limit switches

Use the switch's COM and NO legs: NO to the GPIO pin, COM to ground. The Pi's built-in pull-up holds the pin high, and pressing the switch pulls it low.

## Wiring order

1. Unplug the Pi, disconnect the battery, kill switch off.
2. Pull the ENA jumper off the L298N. Leave the other jumpers.
3. Pins 12, 14, 16 and 18 to ENA, GND, IN1 and IN2.
4. The three switches.
5. Motor to OUT1 and OUT2. Either way round; `cane.py --swap` reverses it.
6. Capacitor across the 12 V and GND terminals.
7. Battery through the fuse and kill switch, last, with the kill switch off.

Then check it from the Pi, as in [`../pi/README.md`](../pi/README.md): switches first, which moves nothing, then one short motor pulse each way with a hand on the kill switch.

## What damages the Pi

- The L298N's 5 V terminal connected to the Pi.
- A 12 V wire touching any Pi pin.
- The ENA jumper left on, which puts 5 V on pin 12.

## Limits to respect

- The L298N handles about 2 A per channel and loses about 2 V, so the motor sees roughly 10 V. It runs hot.
- Motor power is capped at 25% in software, and each steering move is cut off after 0.4 seconds.
- No command from the GX10 for 0.4 seconds: motor driver off.
- Use the `gpiozero` library. `RPi.GPIO` and `pigpio` do not work on a Raspberry Pi 5.

## Suggested, not yet tried

When the controller exits, pins 12, 16 and 18 go back to inputs with no pull, which was seen on the Pi. A floating ENA may read as "on" at the L298N. A 10 kΩ resistor from ENA to GND would hold the driver off whenever the Pi is not driving the pin.
