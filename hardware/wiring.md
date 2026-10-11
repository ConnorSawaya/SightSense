# Wiring

Wiring for the cane, for the parts the team has. Not yet built or tested. Power everything off before changing a wire.

## Parts

| Part | Notes |
| --- | --- |
| Battery | 12 V 3 Ah Li-ion pack (3S1P), on a barrel plug lead |
| Motor driver | IBT-2 board (BTS7960). The plan said L298N; this is what the team has. |
| Motor | Greartisan 12 V 120 rpm worm gear motor |
| Converter | 12 V to 5 V, 5 A, with a USB-C plug. Powers the Pi from the same battery. |
| Barrel-to-screw adapter | The green one. This is where the battery's power splits two ways. |

## Power

```
12 V battery ──► green screw adapter ──┬──► 12 V to 5 V converter ──► USB-C ──► Raspberry Pi 5
                                       │
                                       └──► fuse (5 A) ──► kill switch ──► IBT-2 B+
battery (−), at the adapter ──► converter (−) and IBT-2 B−
IBT-2 M+ and M− ──► motor
```

- Two wires go under each screw of the green adapter: one to the converter, one toward the IBT-2.
- Check which screw is positive with a multimeter before connecting the IBT-2. It has no protection against a reversed battery.
- The fuse and kill switch are in the motor's branch only, so stopping the motor does not switch the Pi off.
- The kill switch must be within the user's reach.
- The IBT-2 has its own capacitor. No extra one is needed.

The earlier plan gave the Pi its own power bank, so the motor could not disturb it. If the Pi resets or reports under-voltage when the motor runs, go back to that.

## Signals

GPIO numbers are BCM numbers. The header pin is the position on the 40-pin header.

| Raspberry Pi | Header pin | Connects to |
| --- | --- | --- |
| GPIO18 | 12 | IBT-2 R_EN |
| GPIO23 | 16 | IBT-2 RPWM |
| 3.3 V | 17 | IBT-2 VCC |
| GPIO24 | 18 | IBT-2 LPWM |
| GND | 20 | IBT-2 GND |
| GPIO25 | 22 | IBT-2 L_EN |
| GPIO5 | 29 | Left limit switch |
| GPIO6 | 31 | Right limit switch |
| GPIO13 | 33 | Centre limit switch |
| GND | 39 | The other leg of all three switches |

- Leave R_IS and L_IS empty.
- VCC goes to the Pi's 3.3 V pin, not 5 V. The board's user guide lists VCC as +5 V, for a 5 V Arduino, and its control inputs as 3.3 to 5 V. Its buffer chip is a 74HC244, which only reads a 3.3 V signal within its guaranteed range when the chip itself runs on 3.3 V. This has not been tried on the team's board yet.

### The IBT-2's pins

Seen from above, with the screw terminals along the top edge and the 2 × 4 header at the bottom right:

| | Left | | | Right |
| --- | --- | --- | --- | --- |
| Top row | VCC | R_IS | R_EN | RPWM |
| Bottom row | GND | L_IS | L_EN | LPWM |

- The board prints the same eight names in a table to the left of the header, in the same rows and the same order. "7" and "8" are printed at the header's left end, "1" and "2" at its right end.
- Screw terminals, left to right starting beside the capacitor: B−, B+, M+, M−. The names are printed on the underside, next to the solder joints.

Checked against the [Handson Technology user guide](https://cdn.hackaday.io/files/1936598285506656/BTS7960%20Motor%20Driver.pdf) (pin table, pin photo and mechanical drawing) and a photo of the team's own board. The Pi's header pins were checked against gpiozero's board data for the Pi 5.

### Finding the pins

- Pin 1 is at the SD card end of the board, on the row nearer the middle. Pin 2 is beside it, on the row at the board's edge.
- Odd numbers run down the inner row, even numbers down the edge row. Pins 39 and 40 are at the USB ports end.
- Pins 12, 16, 18, 20 and 22 are close together on the edge row. Pin 17 is on the inner row, opposite pin 18.
- Pins 25, 30 and 34 are also ground, if each switch gets its own ground wire.

### Limit switches

Use the switch's COM and NO legs: NO to the GPIO pin, COM to ground. The Pi's built-in pull-up holds the pin high, and pressing the switch pulls it low.

## Wiring order

1. Unplug the Pi, unplug the battery, kill switch off.
2. The six wires from the Pi's header to the IBT-2's pins.
3. The three switches.
4. Motor to M+ and M−. Either way round; `cane.py --swap` reverses it.
5. Battery side: adapter to the converter, and adapter through the fuse and kill switch to B+ and B−.
6. Check the polarity at B+ and B− with a multimeter, then plug the battery in last, with the kill switch off.

Then check it from the Pi, as in [`../pi/README.md`](../pi/README.md): switches first, which moves nothing, then one short motor pulse each way with a hand on the kill switch.

## What damages the parts

- A 12 V wire touching any Pi pin.
- The battery connected backwards to the IBT-2.
- 5 V from anywhere onto a Pi GPIO pin.

## Limits to respect

- The IBT-2 passes the full 12 V and far more current than the motor needs, so the software limits are the only limits: motor power is capped at 25%, and each steering move is cut off after 0.4 seconds.
- No command from the GX10 for 0.4 seconds: motor driver off.
- The motor has a worm gear, so it holds its position when the power is off. With the driver off the steering stays where it was; it does not swing back to centre.
- Use the `gpiozero` library. `RPi.GPIO` and `pigpio` do not work on a Raspberry Pi 5.

## Suggested, not yet tried

When the controller exits, the Pi's motor pins go back to inputs with no pull, which was seen on the Pi. If the IBT-2 has no pull-downs of its own, floating enable pins may read as "on". A 10 kΩ resistor from each of R_EN and L_EN to GND would hold the driver off whenever the Pi is not driving them.
