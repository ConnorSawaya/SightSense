# Raspberry Pi

The motor controller on the cane. The motor directly drives the mecanum wheel: LEFT and RIGHT spin opposite ways, and CENTER, STOP and FREE switch it off.

Wiring is in [`../hardware/wiring.md`](../hardware/wiring.md). The command format is in [`../contracts/MESSAGES.md`](../contracts/MESSAGES.md).

## Status

Runs on the Pi: the tests pass there, the simulated wheel follows typed commands, and the real GPIO pins open with the switches reading "none pressed". Not yet run with a real motor or switches wired up.

## Direct wheel mode

The user confirmed the direct-drive wheel on October 11. Use `--wheel-drive`.

| GX10 command | Pi action |
| --- | --- |
| LEFT | RPWM GPIO23, opposite PWM off |
| RIGHT | LPWM GPIO24, opposite PWM off |
| CENTER, STOP, FREE | Both PWM signals and both enables off |

Add `--swap` if the fitted wheel's left/right effect is reversed. The motor direction and lateral effect must be observed on the actual assembly.

- No homing, steering position or limit-switch inputs in this mode.
- Starts with the driver off and waits for a valid command.
- Power is capped at 25%. Each pulse lasts at most 400 ms, followed by a 50 ms rest. Continuing heartbeats allow another pulse.
- STOP switches off immediately. A reversal switches off first and waits 50 ms.
- Command TTL is finite, positive and capped at 400 ms. Queued time is subtracted from it. A disconnected command socket releases the motor; silence also expires the watchdog.
- Network messages retain the agreed `seq`, `cmd`, `ttl_ms` fields and never set motor power.

### RPM

The motor label is 120 rpm at 12 V. At 25% duty, the code logs a **rough, unmeasured 30 rpm estimate while powered**. PWM duty does not guarantee RPM under load; the pauses also lower average speed. There is no encoder in the current wiring.

Mark the wheel, count output-shaft turns in a timed video, and calculate the actual average over that interval:

```bash
python3 rpm.py --turns 2 --seconds 4
# 30 rpm for those supplied measurements
```

The calculator does not operate the motor. Use `--duty 0.15` to reduce power; values above 0.25 are capped. `--rated-rpm` changes the label-based estimate, not the measured speed or power cap.

## Position steering modes

The earlier position-steering controller is retained for a mechanism with a steering axis. Running without `--wheel-drive` selects it:

- Connects to `ws://<GX10>:8766` and reconnects if the link drops.
- Three positions: `LEFT`, `CENTER`, `RIGHT`.
- To move: run the motor toward the target at 25% power or less until that position's limit switch trips, or 0.4 seconds pass. `LEFT` to `RIGHT` is two moves, through centre.
- If the time limit is hit first, the position is unknown: home to centre before the next move.
- `STOP`: return to centre.
- `FREE`, or any error: motor driver off.
- No command for 0.4 seconds: motor driver off. A longer `ttl_ms` in a message is cut to 0.4 seconds.
- On start, and after the driver has been off: home to centre.
- The motor is only powered while moving. Once in position the driver is off.
- The motor has a worm gear, so with the driver off the steering stays where it was. It does not swing back to centre.

Homing with no switch pressed: short pulses left, right, right, left until a switch trips. If the wheel has not reached where it should be after six motor runs, the driver goes off for 3 seconds before it tries again. Two switches pressed at once is treated the same way.

## Files

| File | What it is |
| --- | --- |
| `cane.py` | The program to run |
| `wheel_drive.py` | Direct wheel rotation, watchdog, pulse limits and reversal pause |
| `steering.py` | Earlier position-steering rules and shared command validation |
| `hardware.py` | The real motor and switches, and a simulated wheel |
| `fake_gx10.py` | Stands in for the GX10's command port |
| `talk_button.py`, `test_talk_button.py` | The talk button in the handle: tells the GX10 when it goes down and up |
| `test_steering.py` | Tests |
| `spin_test.py` | Bench test: ramps the motor from stopped to full power once |
| `sightsense-spin-test.service` | Runs the bench test once at start-up |
| `test_spin.py` | Tests for the bench test |
| `test_with_gx10.py` | Runs the GX10's real pipeline against the steering rules |
| `sightsense-cane.service` | Starts the controller when the Pi starts |
| `sightsense.env.example` | Direct wheel settings and GX10 address |
| `stage_sd.py`, `install_from_boot.sh` | Back up and stage the update; install once on the Pi |
| `sightsense-setup.service`, `prepare_runtime.sh` | Check/install the already declared Pi dependencies |
| `test_network.py`, `test_wheel_drive.py`, `test_stage_sd.py` | Real local transport, mock motor and SD staging tests |
| `rpm.py` | Calculate RPM from counted turns and elapsed time |

## Setup

Raspberry Pi OS Lite (64-bit) on a Raspberry Pi 5.

```bash
sudo apt install -y python3-gpiozero python3-lgpio python3-websockets
```

Use `gpiozero`. `RPi.GPIO` and `pigpio` do not work on a Pi 5.

## The team's Pi

Set up on October 10, 2026.

| | |
| --- | --- |
| Board | Raspberry Pi 5, 8 GB |
| OS | Raspberry Pi OS Lite 64-bit, 2026-10-06 release (Debian 13) |
| Bootloader | 2026-09-25, rewritten with the recovery files (see below) |
| Name and user | `sightsense.local`, user `sightsense` |
| Login | SSH key from the team lead's laptop; the password also works |
| Network | `Bono` Wi-Fi, verified October 11. Tailscale `100.75.181.48`; Wi-Fi LAN `192.168.1.227` at that check (DHCP can change it). Credentials stay outside Git. |
| Installed | `python3-gpiozero`, `python3-lgpio`, `python3-websockets`, `git` |
| Motor driver | IBT-2 (BTS7960), wired as in `../hardware/wiring.md` |
| Code | `~/SightSense/pi`, copied from this folder |

The name `sightsense.local` does not always resolve. If it fails, use `ssh sightsense@100.75.181.48` over Tailscale, or the current LAN address from the router's list of connected devices.

The Pi has to be on a network that can reach the GX10's command port.

### Power

The Pi logged under-voltage several times on its first day, on a weak supply. It runs like that but can reset. Use the official 27 W supply, or a strong charger or power bank with a short cable. Check with:

```bash
vcgencmd get_throttled
```

`throttled=0x0` is good. Anything else means the supply dipped.

### Fan

The fan stays off below 50 °C. That is normal.

### If the Pi will not start

Count the green light's blinks. Three long and one short means a bootloader error, reported before the Pi reads the SD card. This Pi did that until its bootloader was rewritten:

1. Download the newest `rpi-boot-eeprom-recovery-…-2712-sd.zip` from the [rpi-eeprom releases](https://github.com/raspberrypi/rpi-eeprom/releases). Raspberry Pi Imager's "Bootloader (Pi 5 family)" option uses the same image.
2. Copy `recovery.bin`, `pieeprom.bin` and `pieeprom.sig` from it onto the SD card's boot partition.
3. Power the Pi and wait for the green light to blink fast and steadily.
4. Delete those three files from the card, or the Pi repeats the recovery and never starts the OS.

## Running

On the Pi, from this folder:

```bash
python3 cane.py --wheel-drive --gx10 100.108.5.67:8766
```

The address can also come from the `SIGHTSENSE_GX10` environment variable. Add `--swap` if "left" turns the wheel right, and `--duty 0.15` for less power.

If the controller is already running as a service (the SD installer enables it), stop it first. Two copies cannot hold the motor pins, and the second should stop with a `GPIO busy` error (from how the pin library works; not tried on the Pi). This applies to the bench checks below as well.

```bash
sudo systemctl stop sightsense-cane.service
```

Start it again with `sudo systemctl start sightsense-cane.service`.

## Following the GX10

The GX10's frame service ([`../gx10/ingest/`](../gx10/ingest/)) sends the Pi one command for every frame it processes. The command comes from the obstacle check on depth, steered toward what the navigator wants: an object found by the vision model and YOLO, a route, or straight ahead. The Pi only has to connect:

```bash
python3 cane.py --wheel-drive --gx10 100.108.5.67:8766
```

The GX10's Tailscale address and port 8766 were checked from the laptop on October 11. The dashboard is port 8000; it is not the Pi command port. The existing Pi Tailscale node is `100.75.181.48`. Preserve its login and network state.

The updated GX10 server discards expired frames and subtracts processing time from the command TTL. The Pi switches off when that TTL expires. The server update must also be run on the GX10 for this receive-time budget to apply; the running GX10 was not changed by staging the Pi SD card.

What has been run: the service, its fake phone and this controller together on a laptop, with a simulated wheel, the vision model stubbed out and YOLO off. As the fake phone walked at a wall the commands went CENTER, a turn while the obstacle check steered away from the wall, then STOP close to it, and the driver went off when the frames stopped. `test_with_gx10.py` repeats that. `test_whole_system.py` does the same in direct wheel mode on mock motor pins, with typed voice, a place, the talk button and the dashboard. It has not been run on the cane, or against the service on the GX10.

## Timed position steering

`--open-loop` is for a position-steering mechanism with no limit switches fitted. The direct wheel uses `--wheel-drive` and does not need it. The controller works out where the wheel is from how long the motor has run, and reads no switches.

```bash
python3 cane.py --gx10 169.233.72.156:8766 --open-loop
```

- Put the wheel at centre by hand before starting. The controller assumes it is there.
- `--travel 0.25` is the time from centre to one side, in seconds. Change it until the wheel turns as far as you want. It cannot be set above 0.35.
- Nothing checks where the wheel really is, so it drifts. Re-centre it by hand now and then.
- The 25% power cap, the 0.4 second limit and the 0.4 second silence rule all still apply.
- Tested on a simulated motor only.

## Starting by itself

`sightsense-cane.service` starts the controller when the Pi starts, and starts it again if it stops. It reads the GX10's address from a file on the SD card's boot partition, so the address can be changed from any computer.

```bash
sudo install -m 644 sightsense-cane.service /etc/systemd/system/
sudo cp sightsense.env.example /boot/firmware/sightsense.env
sudo systemctl enable --now sightsense-cane.service
```

- Edit `/boot/firmware/sightsense.env` to set the address and any options, then run `sudo systemctl restart sightsense-cane.service`. Delete it and the controller no longer starts by itself.
- The direct wheel starts off and only runs while valid LEFT or RIGHT heartbeats arrive.
- The controller was installed over SSH on October 11. Its live GX10 connection was verified with Ethernet disabled, then automatic Wi-Fi and controller startup were verified after reboot. GPIO outputs were low while receiving STOP; physical lateral direction and actual RPM remain unmeasured.

Watch what it is doing:

```bash
journalctl -u sightsense-cane.service -f
```

## Testing without the GX10

Type the commands yourself. The last one typed is repeated 15 times a second, like the GX10 would:

```bash
python3 cane.py --typed --wheel-drive
```

Type `left`, `center`, `right`, `stop` or `free`. `silence` stops sending, as if the link had dropped. `quit` finishes.

To test the network link as well, run the fake GX10 on a laptop and point the Pi at the laptop:

```bash
python3 fake_gx10.py
```

```bash
python3 cane.py --wheel-drive --gx10 <laptop address>
```

## Testing without the Pi

Add `--sim` to use a simulated wheel. This runs on any computer and needs no GPIO:

```bash
python3 cane.py --typed --sim --wheel-drive
```

The tests use the same simulated wheel:

```bash
python3 -m unittest -v
```

## Start-up motor test

The SD updater removes its enable marker, removes the old cloud-init bench commands and masks this service. The direct-drive wheel must not run the full-power boot ramp. The following describes the separate bench script.

For the bench only. It is a way to see the motor turn without logging in to the Pi.

When the Pi has been on for 15 seconds, the motor ramps from stopped to full power over 10 seconds, holds for 2 seconds, and switches off. It does this once each time the Pi starts.

- The motor must be free to turn. Do not run this with the motor fitted to the steering: it goes past the 25% power cap and the 0.4 second limit that the controller keeps.
- If limit switches are fitted, it does not start, and it stops at once, when one is pressed.
- It needs 12 V at the driver. With the battery unplugged nothing moves.
- If three runs in a row do not finish, it stops trying. That is in case the motor starting makes the Pi lose power and restart. Deleting `~/.sightsense-spin-test` on the Pi resets it.
- Written and tested on mock pins. Not yet run on the Pi.

To switch it off, delete the file `spin-test-enabled` from the SD card's boot partition, on any computer. On the Pi that is:

```bash
sudo rm /boot/firmware/spin-test-enabled
```

If the motor does not turn, look at why, and reset the count of unfinished runs:

```bash
journalctl -u sightsense-spin-test -b
rm ~/.sightsense-spin-test
```

When it finishes, the Pi lets go of the motor pins. It is not holding the driver off after that, so unplug the battery from the driver.

To run it by hand (Ctrl+C stops it):

```bash
python3 spin_test.py
```

To install it on a Pi that does not have it:

```bash
sudo install -D -m 755 spin_test.py /opt/sightsense/spin_test.py
sudo install -m 644 sightsense-spin-test.service /etc/systemd/system/
sudo touch /boot/firmware/spin-test-enabled
sudo systemctl enable sightsense-spin-test.service
```

Switch it off before starting `cane.py` by hand in the first half minute after start-up; the two cannot hold the motor pins at the same time.

## Talk button

A push button in the handle, between GPIO17 (header pin 11) and ground (pin 9). Press it, then say a command. Wiring is in [`../hardware/wiring.md`](../hardware/wiring.md).

- While it follows the GX10, the controller tells it when the button goes down and up: `{"button": "down"}`, then `{"button": "up"}`. The GX10 tells the phone to listen. The Pi does no listening.
- A change has to last 0.03 seconds to count, so a bouncing contact or a spike on the long wire is ignored.
- It is read by default. With no button wired the pin reads "not pressed". `--no-button` leaves the pin alone.
- It cannot reach the motor. A fault in the button code stops the button only.
- Tested on mock pins and with a stand-in for the link. Not yet tried with a real button, or with the GX10 and the phone.
- To check a fitted button: with the controller following the GX10, press it and look at the GX10 dashboard's conversation. Each press adds `(talk button down: phone told to listen)`, or `no phone connected` when the app is not connected. Nothing appearing means the press is not reaching the GX10: check the two wires with `--bench button` below, and that the Pi shows as connected on the dashboard.

## Checking the wiring

Print the talk button as it is pressed and let go:

```bash
python3 cane.py --bench button
```

Print each switch as it is pressed:

```bash
python3 cane.py --bench switches
```

One 0.3 second pulse each way. Keep a hand on the stop: the kill switch, or the battery's barrel plug until the kill switch is fitted:

```bash
python3 cane.py --bench motor
```

## Updating the plugged-in SD card from Windows

`stage_sd.py` works on the existing FAT32 boot partition. It does not format the card. First verify its physical disk and root PARTUUID; the tool rejects a boot command line for a different UUID.

```powershell
python pi/stage_sd.py --boot E:/ --backup C:/Users/Connor.Sawaya29/.cache/sightsense-sd-update-backup --expected-root-partuuid 3a83263b-02 --gx10 100.108.5.67:8766
```

It backs up bootfs outside the card, writes and reads back SHA-256 hashes for the payload, repairs an empty `cmdline.txt` using its matching backup, and disables the old boot spin test. A Pi 5 `config.txt` entry sets the four motor pins low during firmware boot. That setting takes effect after firmware starts and can be overridden later; it does not replace the hardware pull-downs described in the wiring guide. See the [Raspberry Pi GPIO documentation](https://www.raspberrypi.com/documentation/computers/config_txt.html#gpio-control).

Add `--more-wifi-profile C:/private/other.nmconnection` (as many times as needed) for networks to fall back to; NetworkManager picks by each profile's `autoconnect-priority`. To add a Wi-Fi network, append `--wifi-profile C:/private/wifi.nmconnection` with a private [NetworkManager keyfile](https://www.networkmanager.dev/docs/api/latest/nm-settings-keyfile.html). The installer copies it to `/etc/NetworkManager/system-connections/sightsense-wifi.nmconnection`, owned by root with mode 600. NetworkManager reads it on the normal reboot, including on a Pi whose cloud-init setup has already run. Existing network profiles stay available. Keep the input outside the repo; `.nmconnection` files are ignored by Git. The copy on FAT32 bootfs is readable to anyone with the card.

Safely eject the card, put it back in the Pi and power it. On its first boot, a one-time installer copies the code and services into the Linux partition, backs up the previous Pi files, masks the boot spin service and enables the controller. It then restores the normal boot command line and reboots. Dependency setup runs on the normal boot and installs only the packages already listed above if missing. SSH credentials and the existing Tailscale identity are preserved. Wi-Fi settings stay as they were unless a profile is supplied.

The boot hook selects `systemd.unit=kernel-command-line.target` explicitly. This Pi OS has a local `default.target` pointing to `multi-user.target`, which bypassed the original hook's generated default. The installed Pi was recovered over Ethernet and SSH; the updater now selects the generated installer target directly.

Check after that reboot:

```bash
cat /boot/firmware/sightsense-install-status.txt
cat /boot/firmware/sightsense-install.log
systemctl status sightsense-setup sightsense-cane --no-pager
tailscale status
journalctl -u sightsense-cane -b --no-pager
vcgencmd get_throttled
```

`STAGED` means files are on bootfs but not yet installed into Linux. `INSTALLED` means the copy completed, not that the physical motor has been measured. A failed install writes its status and returns to a normal boot so SSH remains available. The installer log and staged files are left on bootfs for inspection.
