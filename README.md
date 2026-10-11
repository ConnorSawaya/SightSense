# SightSense

A smart guide cane for people who are blind or have low vision. You say where you want to go ("guide me to the apple", "take me to the door"), and a small wheel at the tip of the cane steers you there while avoiding obstacles.

Built at the UCSC AI Hackathon @ SF Tech Week, October 10–11, 2026, for the ASUS Local AI track.

> Experimental prototype. It does not replace a white cane or a guide dog, and it has not been tested with blind users.

## How it works

```
iPhone (on the cane)        ASUS GX10 (on the table)           Raspberry Pi (on the cane)
camera + LiDAR + position ─► obstacle check, AI models, ─────► drives the wheel motor
        ▲                    route following                    │
        └── beeps and speech ◄──────┘                           ▼
                                                          mecanum wheel
```

1. The iPhone sends a picture, a LiDAR distance map and its position about 15 times a second.
2. The GX10 checks seven directions for clear space and picks the one closest to where you want to go.
3. The GX10 sends one word to the Pi: `LEFT`, `CENTER`, `RIGHT` or `STOP`.
4. The Pi directly drives the mecanum wheel in opposite directions for LEFT/RIGHT. CENTER/STOP/FREE switch it off. If it hears nothing for 0.4 seconds, it switches the motor off.
5. A vision-language model on the GX10 finds named objects, reads signs and answers questions. It never controls the wheel.

AI and guidance run locally on the GX10. The current devices communicate through the existing Tailscale network; a private router was the original plan. Place lookup uses Apple Maps.

## Repository layout

| Folder | What goes here | Owner |
| --- | --- | --- |
| [`contracts/`](contracts/) | The agreed message formats between the phone, the GX10 and the Pi | Everyone |
| [`ios-app/`](ios-app/) | The iPhone app: capture, sending, speech, voice, maps | iPhone app |
| [`gx10/`](gx10/) | Everything that runs on the GX10: receiving frames, obstacle check, AI models, dashboard | GX10 + models, obstacle check |
| [`pi/`](pi/) | The Raspberry Pi motor controller | Cane + Pi |
| [`hardware/`](hardware/) | 3D-printable parts, wiring and build notes for the cane | Cane + Pi |
| [`docs/`](docs/) | Team handbook link, disclosure of tools and prior work | Team lead |

## Hardware

- iPhone 16 Pro (camera, LiDAR, ARKit)
- ASUS Ascent GX10 (borrowed from ASUS for the event)
- Raspberry Pi 5
- 12 V 120 rpm DC worm gear motor driving the mecanum wheel, IBT-2 (BTS7960) motor driver
- 12 V 3 Ah battery pack, fuse, kill switch
- 18 mm carbon-fibre tube cane with a printed keyed coupler (see [`hardware/cane-coupler/`](hardware/cane-coupler/))

## Status

The iPhone and GX10 application code is in. The Pi has direct wheel mode and a one-time SD installer. Software tests use synthetic phone frames, real local WebSockets and mock GPIO. Actual wheel direction, RPM and updated Pi boot remain physical checks; see [`pi/README.md`](pi/README.md).

## Team

Add the four team members and their roles here.
