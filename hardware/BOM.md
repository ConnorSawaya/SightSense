# Bill of materials

Everything the cane is built from, collected from the pages in this folder. Each line says where it comes from, so a change there can be made here too.

No prices or shop links are listed: the team's orders are not recorded in this repository. Sizes marked "not measured" come from seller listings or drawings.

## Electronics

| Qty | Item | Details | State | From |
| --- | --- | --- | --- | --- |
| 1 | iPhone 16 Pro | Camera, LiDAR and position. Strapped into the phone cradle | In use | [`../README.md`](../README.md) |
| 1 | ASUS Ascent GX10 | Ran the AI models and the obstacle check at the hackathon. Stayed off the cane. Borrowed from ASUS for the event; dropped from the plan on October 14, when the phone took over the obstacle check | Not used since the event | [`../README.md`](../README.md) |
| 1 | Raspberry Pi 5 | Motor controller. `wiring.md` lists it in a case with the active cooler; the printed mount takes the bare board on standoffs | In use | [`wiring.md`](wiring.md) |
| 1 | microSD card | For the Pi | In use | [`../pi/`](../pi/) |
| 1 | Battery, 12 V 3 Ah | Li-ion pack, three cells in a row (3S1P), on a barrel plug lead. 55.2 mm wide, measured; about 70 × 19.5 mm, not measured | Not checked under load | [`wiring.md`](wiring.md) |
| 1 | Barrel-to-screw adapter | The green one. The battery's power splits two ways here | Not checked | [`wiring.md`](wiring.md) |
| 1 | Converter, 12 V to 5 V | 5 A, with a USB-C plug. Powers the Pi from the battery | Not checked | [`wiring.md`](wiring.md) |
| 1 | Motor driver, IBT-2 | BTS7960 board, 50 × 50 × 43 mm. No mount is designed for it yet | Six signal wires fitted | [`wiring.md`](wiring.md) |
| 1 | Gearmotor, 12 V 120 rpm | Greartisan worm gear motor (JGY-370), 6 mm D-shaft. Sizes from a published drawing, not measured | Not checked | [`wiring.md`](wiring.md) |
| 1 | Omni wheel, 85 mm | Plastic, with rubber rollers; sold with a 5 mm coupling, which does not fit the motor's 6 mm shaft, so it goes on the printed adapter. 12 mm hex socket and 10 mm centre hole, measured. The 85 mm is from the seller's listing; other pages here still draw it at 58 mm and sometimes call it a mecanum wheel | On the motor, as the team reported on October 11 | [`wheel-adapter/`](wheel-adapter/) |
| 6 | Jumper wire | A socket on each end. Brown, red, black, orange, yellow, green | Fitted | [`wiring.md`](wiring.md) |
| 1 | Talk button | 7 mm momentary push button with two leads (PBS-110 type) and its nut | Wired: the Pi logged presses on October 11 | [`../pi/README.md`](../pi/README.md) |
| 2 | Wire for the talk button | Handle to the Pi, a socket on the Pi end of each | Wired, as above | [`wiring.md`](wiring.md) |
| 3 | Limit microswitch | For the earlier position-steering modes. Direct wheel drive does not use them | Not fitted | [`wiring.md`](wiring.md) |
| — | Hook-up wire | 12 V from the adapter to the driver, and the driver to the motor | | [`wiring.md`](wiring.md) |

## Cane

| Qty | Item | Details | From |
| --- | --- | --- | --- |
| 4 | Carbon-fibre tube | 18 mm outside, 16 mm inside, 400 mm long | [`assembly/`](assembly/) |
| 1 | Shock cord | 1/8 in (3.2 mm), through the couplers so the cane folds like a tent pole | [`cane-coupler/`](cane-coupler/) |

## Printed parts

Rigid parts in PETG-CF. None has been printed and fitted in its current version.

| Qty | Part | Folder |
| --- | --- | --- |
| 1 | Handle | [`handle-phone-mount/`](handle-phone-mount/) |
| 1 | Handle plug, glued in the tube | [`handle-phone-mount/`](handle-phone-mount/) |
| 1 | Camera collar | [`handle-phone-mount/`](handle-phone-mount/) |
| 1 | Phone cradle | [`handle-phone-mount/`](handle-phone-mount/) |
| 3 | Coupler main insert v3 | [`cane-coupler/`](cane-coupler/) |
| 3 | Coupler receiver v3 | [`cane-coupler/`](cane-coupler/) |
| 1 | Main insert v4 | [`cane-coupler/`](cane-coupler/) |
| 3 | Joint sleeve, one per joint | [`joint-sleeve/`](joint-sleeve/) |
| 1 | Motor mount 2 | [`motor-mount-2/`](motor-mount-2/) |
| 1 | Wheel adapter | [`wheel-adapter/`](wheel-adapter/) |
| 1 | Wheel cap | [`wheel-adapter/`](wheel-adapter/) |
| 1 | Electronics mount, Raspberry Pi half | [`electronics-mount/`](electronics-mount/) |
| 1 | Electronics mount, battery half | [`electronics-mount/`](electronics-mount/) |

19 pieces in all.

## Screws and nuts

| Qty | Item | Where |
| --- | --- | --- |
| 18 | M3 × 20 socket-head screw | Handle and phone mount 4, electronics mount 4, joint sleeves 9, motor mount cross bolt 1 |
| 1 | M3 × 10 socket-head screw | Wheel adapter's clamp on the shaft. It must be 10 mm |
| 1 | M3 socket-head screw, length to suit the wheel | Holds the wheel on. 15 mm of it is inside the adapter |
| 2 | M3 × 12 to 16 screw | Motor mount's front wall into the gearbox |
| 1 | M3 × 6 to 8 screw | Tube lock in the handle socket. It cuts its own thread |
| 20 | M3 nut | One for each M3 × 20, the M3 × 10 and the wheel screw |
| 4 | M2.5 × 12 screw | Raspberry Pi to its standoffs |
| 4 | M2.5 nut | Inside the Pi half's plate |

## Tape, straps and glue

| Item | Where |
| --- | --- |
| Epoxy | Coupler inserts and the handle plug into the tubes |
| Hook-and-loop cinch strap, 20 mm wide, about 250 mm | Holds the phone in the cradle |
| Foam tape and hook-and-loop | Battery to its plate |
| Tape | A turn or two round the tube under each clamp, for grip |
| Zip tie | Backup round the battery and its plate |
