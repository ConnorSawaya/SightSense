# Raspberry Pi

The motor controller on the cane. It receives one word from the GX10 and turns the steering wheel to match.

Wiring is in [`../hardware/wiring.md`](../hardware/wiring.md). The command format is in [`../contracts/MESSAGES.md`](../contracts/MESSAGES.md).

## Status

Runs on the Pi: the tests pass there, the simulated wheel follows typed commands, and the real GPIO pins open with the switches reading "none pressed". Not yet run with a real motor or switches wired up.

## Behaviour

- Connects to `ws://<GX10>:8766` and reconnects if the link drops.
- Three positions: `LEFT`, `CENTER`, `RIGHT`.
- To move: run the motor toward the target at 25% power or less until that position's limit switch trips, or 0.4 seconds pass. `LEFT` to `RIGHT` is two moves, through centre.
- If the time limit is hit first, the position is unknown: home to centre before the next move.
- `STOP`: return to centre.
- `FREE`, or any error: motor driver off.
- No command for 0.4 seconds: motor driver off. A longer `ttl_ms` in a message is cut to 0.4 seconds.
- On start, and after the driver has been off: home to centre.
- The motor is only powered while moving. Once in position the driver is off.

Homing with no switch pressed: short pulses left, right, right, left until a switch trips. If the wheel has not reached where it should be after six motor runs, the driver goes off for 3 seconds before it tries again. Two switches pressed at once is treated the same way.

## Files

| File | What it is |
| --- | --- |
| `cane.py` | The program to run |
| `steering.py` | The steering rules. No GPIO, so it runs anywhere. |
| `hardware.py` | The real motor and switches, and a simulated wheel |
| `fake_gx10.py` | Stands in for the GX10's command port |
| `test_steering.py` | Tests |

## Setup

Raspberry Pi OS Lite (64-bit) on a Raspberry Pi 5.

```bash
sudo apt install -y python3-gpiozero python3-lgpio python3-websockets
```

Use `gpiozero`. `RPi.GPIO` and `pigpio` do not work on a Pi 5.

## Running

On the Pi, from this folder:

```bash
python3 cane.py --gx10 192.168.8.10
```

The address can also come from the `SIGHTSENSE_GX10` environment variable. Add `--swap` if "left" turns the wheel right, and `--duty 0.15` for less power.

## Testing without the GX10

Type the commands yourself. The last one typed is repeated 15 times a second, like the GX10 would:

```bash
python3 cane.py --typed
```

Type `left`, `center`, `right`, `stop` or `free`. `silence` stops sending, as if the link had dropped. `quit` finishes.

To test the network link as well, run the fake GX10 on a laptop and point the Pi at the laptop:

```bash
python3 fake_gx10.py
```

```bash
python3 cane.py --gx10 <laptop address>
```

## Testing without the Pi

Add `--sim` to use a simulated wheel. This runs on any computer and needs no GPIO:

```bash
python3 cane.py --typed --sim
```

The tests use the same simulated wheel:

```bash
python3 -m unittest -v
```

## Checking the wiring

Print each switch as it is pressed:

```bash
python3 cane.py --bench switches
```

One 0.3 second pulse each way. Keep a hand on the kill switch:

```bash
python3 cane.py --bench motor
```
