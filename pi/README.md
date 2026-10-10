# Raspberry Pi

The motor controller on the cane. It receives one word from the GX10 and turns the steering wheel to match.

Wiring is in [`../hardware/wiring.md`](../hardware/wiring.md). The command format is in [`../contracts/MESSAGES.md`](../contracts/MESSAGES.md).

## Behaviour

- Connects to `ws://<GX10>:8766` and reconnects if the link drops.
- Three positions: `LEFT`, `CENTER`, `RIGHT`.
- To move: run the motor toward the target at 25% power or less until that position's limit switch trips, or 0.4 seconds pass.
- If the time limit is hit first, the position is unknown: home to centre before the next move.
- `STOP`: return to centre.
- `FREE`, or any error: motor driver off.
- No command for 0.4 seconds: motor driver off.
- On start: home to centre.

## Setup

Raspberry Pi OS Lite (64-bit) on a Raspberry Pi 5.

```bash
sudo apt install -y python3-venv python3-pip python3-gpiozero python3-lgpio
```

Use `gpiozero`. `RPi.GPIO` and `pigpio` do not work on a Pi 5.
