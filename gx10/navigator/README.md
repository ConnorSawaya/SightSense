# navigator

Voice commands, "guide me to the apple" and "take me to Safeway". Standard library only; nothing to install.

It only produces a **desired bearing**. Whether that way is clear is decided by the obstacle check from depth, and the obstacle check wins. The vision-language model only supplies a box around the object; the distance comes from the LiDAR depth inside that box.

## Use

From `gx10/`:

```python
import vlm
from navigator import Navigator, decode

vlm.warm()
nav = Navigator(vlm)

nav.on_voice(msg["text"])       # {"text": ...} from the phone
nav.on_route(msg)               # the route message from the phone
g = nav.on_frame(decode(raw))   # every frame (or pass any object with the Frame fields)

g.desired_bearing   # degrees, positive right, None = no preference -> obstacle check
g.hold_center       # route: user is facing the wrong way and should turn on the spot
g.stop              # the object is within reach
g.speech            # put in the guidance message's "speech" field
g.lookup            # send {"lookup": g.lookup} to the phone
g.mode, g.state, g.distance_m   # for the dashboard
```

`on_frame` never waits for the model. `find`, `describe` and `read` run on a background thread on one frame, and their answers are used when they arrive.

## For the obstacle check

- Use `g.desired_bearing` as the desired bearing in the cost `|heading − desired| + 0.5 · |heading − last choice|`. `None` means 0 (straight ahead).
- `g.hold_center`: send `CENTER` while the user turns on the spot (the route says they face the wrong way). Depth still wins: blocked is still `STOP`.
- `g.stop`: the object is within reach; send `STOP`. This only ever adds a stop; it never clears one.
- Put `g.speech` in the guidance message's `speech` field. It is set on one frame only, so it is said once.

## Voice commands

| Said | Does |
| --- | --- |
| "guide me to the apple", "take me to the door", "find a chair", "where is the exit" | Guide to an object |
| "take me to Safeway", "take me to the train station" | Look up a place, then follow the route |
| "what's in front of me", "describe" | Describe |
| "read the sign", "what does it say" | Read |
| "am I going the right way", "how far is it", "where is it", "which way" | Status from the navigator: direction and distance (LiDAR) to the object, or on/off the route and metres to go |
| "is the path clear", "is it safe to walk", "anything in front of me", "can I keep going" | Answered by the frame service from the LiDAR obstacle check, never the model. Never says "safe" |
| Any other question ("is there a chair here?", "what colour is the door?") | `vlm.ask`: the model answers in under 20 words; it is told not to give distances or judge safety, and any sentence with a distance is dropped |
| "yes" / "no" | Answer "Say yes to go." |
| "stop", "cancel", "never mind" | Stop guiding |
| Anything the rules cannot place, and requests worded as questions ("could you point me toward the exit") | `vlm.interpret` (text only, about 0.4 s) picks one of the commands above: "bring me over toward the red cup" → object, "I need to get to the Starbucks on Main Street" → place, "hold on stop for a second" → cancel. It only picks a command; it never steers, and "path" is still answered from depth |
| Anything else | "Sorry, I didn't catch that. You can say: what's in front of me, read the sign, or guide me to the apple." |

"Am I going the right way" got "didn't catch that" three times in the first iPhone test (October 10); that is why status, path and free questions were added.

Object or place: a known room object ("door", "red cup") is an object; a place word ("station", "store") or a capitalised name ("Safeway") is a place; otherwise "the ..." is an object and a bare word is a place. The lists are in `commands.py`.

## Guide to an object

1. Look for it: `find()` every 1.5 s. "I can't see the apple yet. Turn slowly to scan." every 10 s; give up after 30 s.
2. Found: distance = median depth in the middle half of the box. Says "Apple, 2.5 metres, slightly left. Say yes to go." No steering until "yes".
3. Guiding: the object is stored as a point in the ARKit world, so its bearing is recomputed from the pose every frame, even when it is out of view. `find()` runs again every 2 s to refresh it.
4. Under 1.2 m (floor distance): `stop` and "The apple is within reach." It was 0.8 m, the same as the obstacle stop, so an apple on a table was never reached: the edge of the table stopped the cane first.
5. Tracking reset (`tracking` is `notAvailable` or `relocalizing`, or the camera jumps more than 0.5 m between frames): the stored point is dropped. Not seen again for 10 s: "I lost the apple."

Bearings are worked out in the room's floor plane from the pose, so "left" is the user's left however the phone sits in its mount and however far the cane is tilted. The obstacle check's headings must use the same convention (0 ahead, positive right, as the user sees it).

## Follow a route

Once a second, from the newest frame's GPS and compass: nearest point on the route, then the point 12 m further on; desired bearing = bearing to it − heading. More than 60° off: `hold_center` and "Turn left/right." Each step is spoken within 10 m. Arrived within 15 m. Off the route by more than max(15 m, 2 × GPS accuracy) for 5 s: "Rerouting." and a new lookup. GPS accuracy worse than 25 m: no bearing, "GPS is weak."

All numbers are starting values from AGENTS.md, at the top of each file.

## Tests

```bash
python3 -m unittest navigator.test_navigator   # fake room, no phone or model
python3 -m navigator.check_live                # real model on the vlm test pictures, fake depth
```

`fake.py` builds a fake room: camera poses (including a phone turned sideways in its mount), depth frames with an object at a known point, and a fake `find()`.

`check_live.py` result on the GX10 with `qwen3.6:35b`, October 10:

```
"guide me to the apple" on apple_left.jpg
   1.83s  [CONFIRMING] says: 'Apple, 2.5 metres, slightly left. Say yes to go.'
  guiding, desired bearing -17.5  ->  PASS (apple is left)
"guide me to the apple" on apple_right.jpg
   3.38s  [CONFIRMING] says: 'Apple, 2.5 metres, slightly right. Say yes to go.'
  guiding, desired bearing +17.3  ->  PASS (apple is right)
"guide me to the apple" on empty_room.jpg: still SEARCHING after 5 s  ->  PASS
"what's in front of me" on street.jpg:  0.74s 'A blue and white bus with people walking in front of it.'
"read the sign" on sign_exit.jpg:       0.67s 'EXIT. Room 204'
```

Not yet tried with real phone frames, a real walk or GPS.
