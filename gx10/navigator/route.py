"""Follow a walking route ("take me to Safeway"), following AGENTS.md.

Takes the route message from the phone (contracts/MESSAGES.md) and, about once a
second, the GPS fix and compass heading from the newest frame. Produces a
desired bearing for the obstacle check, plus anything to say. The obstacle check
still decides whether that way is clear.
"""

import math
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

# Starting values from AGENTS.md, to tune
LOOKAHEAD_M = 12.0
TURN_IN_PLACE_DEG = 60.0
STEP_SPEAK_M = 10.0
ARRIVE_M = 15.0
OFF_ROUTE_MIN_M = 15.0
OFF_ROUTE_FOR_S = 5.0
BAD_GPS_M = 25.0
REPEAT_TURN_S = 4.5  # added: how often to repeat "Turn left". Above the phone's hold on a repeated sentence (2 s; 4 s in older builds)
REROUTE_EVERY_S = 15.0  # added: at most one new lookup this often

EARTH_R = 6371000.0


@dataclass
class RouteStep:
    desired_bearing: Optional[float] = None  # degrees, positive right; None = no preference
    hold_center: bool = False  # True: user should turn on the spot; keep the wheel centred
    turn: Optional[str] = None  # "left" or "right" when hold_center
    speech: Optional[str] = None
    lookup: Optional[str] = None  # send {"lookup": ...} to the phone for a new route
    arrived: bool = False
    off_route_m: Optional[float] = None
    remaining_m: Optional[float] = None


def wrap180(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


class RouteFollower:
    def __init__(self, route: dict, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self.dest = route.get("dest") or "your destination"
        pts = route.get("polyline") or []
        if len(pts) < 2:
            raise ValueError("route needs at least two points")
        self._lat0, self._lon0 = pts[0]
        self._xy = [self._to_xy(lat, lon) for lat, lon in pts]
        self._cum = [0.0]
        for a, b in zip(self._xy, self._xy[1:]):
            self._cum.append(self._cum[-1] + math.dist(a, b))
        self._steps = [(self._to_xy(s["lat"], s["lon"]), s.get("text", "")) for s in route.get("steps") or []]
        self._spoken = set()
        self._off_since = None
        self._last_turn = -1e9
        self._last_reroute = -1e9
        self._bad_gps_said = False
        self._no_heading_said = False
        self.done = False

    def _to_xy(self, lat, lon):
        """Metres east and north of the route's first point. Fine over a few km."""
        x = math.radians(lon - self._lon0) * EARTH_R * math.cos(math.radians(self._lat0))
        y = math.radians(lat - self._lat0) * EARTH_R
        return (x, y)

    def _nearest(self, p):
        """(distance from the route, distance along the route) of the nearest point on it."""
        best = (float("inf"), 0.0)
        for i, (a, b) in enumerate(zip(self._xy, self._xy[1:])):
            dx, dy = b[0] - a[0], b[1] - a[1]
            seg2 = dx * dx + dy * dy
            t = 0.0 if seg2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / seg2))
            q = (a[0] + t * dx, a[1] + t * dy)
            d = math.dist(p, q)
            if d < best[0]:
                best = (d, self._cum[i] + t * math.sqrt(seg2))
        return best

    def _point_at(self, s):
        s = max(0.0, min(self._cum[-1], s))
        for i in range(len(self._cum) - 1):
            if s <= self._cum[i + 1]:
                seg = self._cum[i + 1] - self._cum[i]
                t = 0.0 if seg == 0 else (s - self._cum[i]) / seg
                a, b = self._xy[i], self._xy[i + 1]
                return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        return self._xy[-1]

    def update(self, lat, lon, gps_acc_m, heading_deg) -> RouteStep:
        now = self._clock()
        if self.done:
            return RouteStep(arrived=True)
        if lat is None or lon is None or gps_acc_m is None or gps_acc_m > BAD_GPS_M:
            speech = None
            if not self._bad_gps_said:
                self._bad_gps_said, speech = True, "GPS is weak. Route guidance paused."
            return RouteStep(speech=speech)
        if self._bad_gps_said:
            self._bad_gps_said = False

        p = self._to_xy(lat, lon)
        off, along = self._nearest(p)
        remaining = math.dist(p, self._xy[-1])
        out = RouteStep(off_route_m=off, remaining_m=remaining)

        if remaining <= ARRIVE_M:
            self.done = True
            out.arrived, out.speech = True, f"You have arrived at {self.dest}."
            return out

        # Off route for long enough: ask the phone for a new route
        if off > max(OFF_ROUTE_MIN_M, 2 * gps_acc_m):
            self._off_since = self._off_since if self._off_since is not None else now
            if now - self._off_since >= OFF_ROUTE_FOR_S and now - self._last_reroute >= REROUTE_EVERY_S:
                self._last_reroute = now
                out.lookup, out.speech = self.dest, "Rerouting."
        else:
            self._off_since = None

        # Speak each step once, when within range of it
        for i, (xy, text) in enumerate(self._steps):
            if i not in self._spoken and text and math.dist(p, xy) <= STEP_SPEAK_M:
                self._spoken.add(i)
                out.speech = out.speech or text
                break

        if heading_deg is None:
            if not self._no_heading_said and not out.speech:  # said on the first update with nothing else to say
                self._no_heading_said, out.speech = True, "No compass heading. Route guidance paused."
            return out
        self._no_heading_said = False
        target = self._point_at(along + LOOKAHEAD_M)
        compass = math.degrees(math.atan2(target[0] - p[0], target[1] - p[1]))  # 0 north, 90 east
        desired = wrap180(compass - heading_deg)
        if abs(desired) > TURN_IN_PLACE_DEG:
            out.hold_center = True
            out.turn = "right" if desired > 0 else "left"
            if now - self._last_turn >= REPEAT_TURN_S:
                self._last_turn = now
                out.speech = out.speech or ("Turn right." if desired > 0 else "Turn left.")
        else:
            out.desired_bearing = desired
        return out
