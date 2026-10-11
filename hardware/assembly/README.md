# Whole-cane assembly

An interactive 3D model of the whole cane with every printed part in place: the handle, the phone mount, the main insert, motor mount 2, the wheel adapter and its cap, and the battery and Raspberry Pi mount.

Experimental prototype. Nothing here has been printed, fitted or load tested. The model shows how the parts go together; it is not evidence that they work.

![The whole cane](previews/assembly_whole.png)

![The wheel end](previews/assembly_wheel_end.png)

## Opening it

`assembly_viewer.html` is one self-contained file of about 7 MB. It needs no internet connection. GitHub does not display it, so download it (or clone the repository) and open it in a browser.

- Drag to rotate, scroll to zoom, right-drag or Shift-drag to pan.
- **Whole cane**, **Handle and phone** and **Wheel end** jump to each view.
- The tick boxes show and hide each part. Hide the tube to see the main insert inside it.
- **Lean pole** switches between the pole leaning as it is held, standing on the ground, and the pole upright.

## What is in it

| Part | Printed? | Source |
| --- | --- | --- |
| Handle, camera collar, phone cradle | Yes | [`../handle-phone-mount/`](../handle-phone-mount/) |
| Main insert v4 | Yes | [`../cane-coupler/`](../cane-coupler/) |
| Motor mount 2 | Yes | [`../motor-mount-2/`](../motor-mount-2/) |
| Wheel adapter, wheel cap | Yes | [`../wheel-adapter/`](../wheel-adapter/) |
| Mount for the Raspberry Pi and the battery, two halves | Yes | [`../electronics-mount/`](../electronics-mount/) |
| Thumb button, phone, gearmotor, omni wheel, Raspberry Pi 5, battery pack, tube, screws and nuts | No | Drawn as plain shapes for reference |

Left out: the v4 motor receiver (motor mount 2 goes in the same place), the motor driver board, the wiring and the shock cord.

The Raspberry Pi is held by four M2.5 × 12 screws with nuts.

## What is a stand-in or an assumption

| Item | Drawn as | Why |
| --- | --- | --- |
| Tube length | 900 mm | Nominal. The tube is cut to suit the user. At this length the top of the tube is about 0.9 m above the ground |
| Lean of the pole | 30 degrees from upright | The angle the handle was designed for; not measured in use |
| Omni wheel | 58 mm across, 27 mm wide at the hub | Not measured. It looked 50 to 60 mm across in the team's photos |
| Phone | A generic phone | Not measured |
| Gearmotor | JGY-370 outline | From a published drawing, not from measuring this motor |
| Camera collar | 240 mm below the top of the tube | It can be clamped anywhere on the tube |

## Which way round the wheel end goes

The script checks which part reaches the ground first when the pole leans.

- **Motor on the user's side of the tube:** the wheel reaches the ground first, with 13.7 mm to spare. The model is drawn this way.
- **Motor in front of the tube:** the bottom edge of motor mount 2 is 15.2 mm lower than the wheel, so the mount would touch the ground before the wheel.

Both figures are for a 58 mm wheel and a 30 degree lean. They also assume the wheel's axle points along the walking direction, so that the wheel pushes the tip of the cane left and right.

The coupler's tongue is rectangular, so motor mount 2 goes onto it either way round. Fit it with the motor on the user's side.

Either way the wheel meets the ground tilted by the lean angle, because the motor sits parallel to the tube. Whether the wheel grips and rolls well like that has not been tested.

## Regenerating it

```
python assembly_viewer.py
```

This needs build123d and numpy. It imports each part from its own folder, prints the ground check above, and rewrites `assembly_viewer.html`. The page itself comes from `viewer.py` in [`../handle-phone-mount/`](../handle-phone-mount/).
