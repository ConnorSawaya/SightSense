"""Writes viewer.html: a self-contained 3D viewer for the parts (no internet needed).

Run after walking_stick.py:  python viewer.py     then open viewer.html in a browser.
Drag to rotate, scroll to zoom, right-drag or shift-drag to pan.
"""

import base64
import json
import sys
from pathlib import Path

import numpy as np

import walking_stick as ws

T = ws.PHONE_TILT_DEG


def mesh(shape):
    shapes = shape if isinstance(shape, (list, tuple)) else [shape]
    tris = []
    for s in shapes:
        verts, faces = s.tessellate(0.08, 0.3)
        v = np.array([(p.X, p.Y, p.Z) for p in verts], dtype=np.float32)
        tris.append(v[np.array(faces)])
    tris = np.concatenate(tris)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    pos = tris.reshape(-1, 3).astype(np.float32)
    nor = np.repeat(n, 3, axis=0).astype(np.float32)
    return base64.b64encode(pos.tobytes()).decode(), base64.b64encode(nor.tobytes()).decode()


def build():
    parts = ws.printable_parts()
    at = ws.cradle_location(T)
    scene = [
        ("Handle", (0.20, 0.47, 0.80), True, parts["stick_handle"]),
        ("Camera collar", (0.95, 0.55, 0.15), True, ws.collar_location() * parts["camera_collar"]),
        ("Phone cradle", (0.25, 0.68, 0.45), True, at * parts["phone_cradle"]),
        ("Screws and nuts (reference)", (0.82, 0.80, 0.72), True, ws.ref_hardware(T)),
        ("Pole (reference)", (0.55, 0.56, 0.60), True, ws.ref_stick()),
        ("Phone (reference, UNCONFIRMED size)", (0.36, 0.38, 0.44), True, at * ws.ref_phone()),
        ("Strap (reference)", (0.75, 0.25, 0.30), False, at * ws.ref_strap()),
    ]
    out = []
    for name, color, visible, shape in scene:
        pos, nor = mesh(shape)
        out.append({"name": name, "color": color, "visible": visible, "pos": pos, "nor": nor})
    return out


# Page content without the document wrapper, so the same markup can be published as a hosted page.
HTML = r"""<title>Walking Stick CAD</title>
<style>
  /* layout: full-window 3D canvas, one floating control panel top-left, hint bottom-left */
  :root { --bg: #eef0f3; --panel: #ffffff; --fg: #1c2530; --muted: #56616f; --line: #c9cfd8; --hover: #e3e9f5; --accent: #2f6fc4; }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #23272e; --panel: #2d323b; --fg: #e8ebf0; --muted: #a9b2bf; --line: #4a515d; --hover: #3a4150; --accent: #7fb0f0; color-scheme: dark } }
  :root[data-theme="dark"] { --bg: #23272e; --panel: #2d323b; --fg: #e8ebf0; --muted: #a9b2bf; --line: #4a515d; --hover: #3a4150; --accent: #7fb0f0; color-scheme: dark }
  html, body { height: 100%; }
  body { margin: 0; background: var(--bg); color: var(--fg); font: 14px/1.4 -apple-system, system-ui, "Segoe UI", sans-serif; overflow: hidden; position: relative; }
  canvas { display: block; width: 100%; height: 100%; touch-action: none; cursor: grab; }
  #panel { position: absolute; top: 12px; left: 16px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 8px 12px 10px; width: 280px; max-width: calc(100% - 32px); box-sizing: border-box; max-height: calc(100% - 60px); overflow-y: auto; }
  summary { font-size: 15px; font-weight: 600; cursor: pointer; padding: 2px 0; }
  #list { margin-top: 6px; }
  label { display: flex; align-items: center; gap: 7px; padding: 2px 0; cursor: pointer; min-width: 0; }
  .sw { width: 12px; height: 12px; border-radius: 3px; flex: none; border: 1px solid var(--line); }
  .row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
  button { font: inherit; color: var(--fg); padding: 4px 9px; border: 1px solid var(--line); border-radius: 6px; background: var(--panel); cursor: pointer; }
  button:hover { background: var(--hover); }
  button:focus-visible, summary:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  #size { margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--line); font-variant-numeric: tabular-nums; }
  #help { position: absolute; bottom: 10px; left: 16px; right: 16px; color: var(--muted); font-size: 13px; pointer-events: none; }
</style>
<canvas id="c"></canvas>
<div id="panel"><details open id="parts"><summary>Walking stick CAD</summary><div id="list"></div>
  <div class="row"><button id="only">Printed parts only</button><button id="all">Show all</button><button id="lean">Lean pole: off</button></div></details>
  <div class="row"><button id="fit">Fit view</button><button id="zin" aria-label="Zoom in">Zoom +</button><button id="zout" aria-label="Zoom out">Zoom −</button></div>
  <div id="size"></div></div>
<div id="help">Drag to rotate · scroll to zoom · right-drag or Shift-drag to pan</div>
<script>
const PARTS = __DATA__;
const LEAN = __LEAN__ * Math.PI / 180;
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl', {antialias: true, alpha: true, premultipliedAlpha: false});
const dec = s => new Float32Array(Uint8Array.from(atob(s), c => c.charCodeAt(0)).buffer);
function shader(type, src) { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; }
const prog = gl.createProgram();
gl.attachShader(prog, shader(gl.VERTEX_SHADER, `attribute vec3 p, n; uniform mat4 mvp; uniform mat3 rot; varying vec3 vn;
  void main(){ vn = rot * n; gl_Position = mvp * vec4(p, 1.0); }`));
gl.attachShader(prog, shader(gl.FRAGMENT_SHADER, `precision mediump float; varying vec3 vn; uniform vec3 col;
  void main(){ vec3 n = normalize(vn); float d = abs(dot(n, normalize(vec3(0.35, 0.55, 0.75))));
    float rim = abs(n.z); gl_FragColor = vec4(col * (0.30 + 0.62 * d + 0.12 * rim), 1.0); }`));
gl.linkProgram(prog); gl.useProgram(prog);
const loc = {p: gl.getAttribLocation(prog, 'p'), n: gl.getAttribLocation(prog, 'n'), mvp: gl.getUniformLocation(prog, 'mvp'),
             rot: gl.getUniformLocation(prog, 'rot'), col: gl.getUniformLocation(prog, 'col')};
for (const part of PARTS) {
  const pos = dec(part.pos), nor = dec(part.nor);
  part.count = pos.length / 3;
  part.min = [1e9, 1e9, 1e9]; part.max = [-1e9, -1e9, -1e9];
  for (let i = 0; i < pos.length; i += 3) for (let k = 0; k < 3; k++) {
    part.min[k] = Math.min(part.min[k], pos[i + k]); part.max[k] = Math.max(part.max[k], pos[i + k]); }
  part.pb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, part.pb); gl.bufferData(gl.ARRAY_BUFFER, pos, gl.STATIC_DRAW);
  part.nb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, part.nb); gl.bufferData(gl.ARRAY_BUFFER, nor, gl.STATIC_DRAW);
}
// camera: orbit around target; model Z is up
let yaw = -0.9, pitch = 0.25, dist = 600, target = [0, 0, 0], lean = false;
function bounds() {
  const lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
  for (const p of PARTS) if (p.visible) for (let k = 0; k < 3; k++) { lo[k] = Math.min(lo[k], p.min[k]); hi[k] = Math.max(hi[k], p.max[k]); }
  return [lo, hi];
}
function leanPoint(v) { if (!lean) return v; const c = Math.cos(-LEAN), s = Math.sin(-LEAN); return [v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c]; }
function fit() {
  const [lo, hi] = bounds(); if (lo[0] > hi[0]) return;
  target = leanPoint([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2]);
  dist = 1.5 * Math.hypot(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]) + 20; draw();
}
function sizeText() {
  const [lo, hi] = bounds(); const el = document.getElementById('size');
  if (lo[0] > hi[0]) { el.textContent = 'Nothing shown'; return; }
  el.innerHTML = 'Size of what is shown:<br><b>' + (hi[0] - lo[0]).toFixed(1) + ' × ' + (hi[1] - lo[1]).toFixed(1) + ' × ' + (hi[2] - lo[2]).toFixed(1) + ' mm</b>';
}
function mul(a, b) { const o = new Float32Array(16); for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { let s = 0; for (let k = 0; k < 4; k++) s += a[k * 4 + j] * b[i * 4 + k]; o[i * 4 + j] = s; } return o; }
function draw() {
  const dpr = window.devicePixelRatio || 1, w = canvas.clientWidth * dpr, h = canvas.clientHeight * dpr;
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  gl.viewport(0, 0, w, h); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT); gl.enable(gl.DEPTH_TEST);
  const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
  // view basis in model space (Z up): right, up, back
  const r = [cy, sy, 0], bk = [sy * cp, -cy * cp, sp], up = [-sy * sp, cy * sp, cp];
  const L = lean ? -LEAN : 0, cl = Math.cos(L), sl = Math.sin(L);
  // model matrix: optional lean about Y, column-major
  const M = new Float32Array([cl, 0, -sl, 0, 0, 1, 0, 0, sl, 0, cl, 0, 0, 0, 0, 1]);
  const t = target, dotT = v => v[0] * t[0] + v[1] * t[1] + v[2] * t[2];
  const V = new Float32Array([r[0], up[0], bk[0], 0, r[1], up[1], bk[1], 0, r[2], up[2], bk[2], 0, -dotT(r), -dotT(up), -dotT(bk) - dist, 1]);
  const f = 1 / Math.tan(0.35 / 2 * 2), near = Math.max(dist / 50, 1), far = dist * 6 + 2000, asp = w / h;
  const P = new Float32Array([f / asp, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) / (near - far), -1, 0, 0, 2 * far * near / (near - far), 0]);
  const VM = mul(V, M);
  gl.uniformMatrix4fv(loc.mvp, false, mul(P, VM));
  gl.uniformMatrix3fv(loc.rot, false, new Float32Array([VM[0], VM[1], VM[2], VM[4], VM[5], VM[6], VM[8], VM[9], VM[10]]));
  for (const p of PARTS) { if (!p.visible) continue;
    gl.uniform3fv(loc.col, p.color);
    gl.bindBuffer(gl.ARRAY_BUFFER, p.pb); gl.enableVertexAttribArray(loc.p); gl.vertexAttribPointer(loc.p, 3, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, p.nb); gl.enableVertexAttribArray(loc.n); gl.vertexAttribPointer(loc.n, 3, gl.FLOAT, false, 0, 0);
    gl.drawArrays(gl.TRIANGLES, 0, p.count); }
  canvas._basis = {r, up};
}
const list = document.getElementById('list');
PARTS.forEach((p, i) => {
  const l = document.createElement('label'), c = document.createElement('input'), sw = document.createElement('span');
  c.type = 'checkbox'; c.checked = p.visible; c.onchange = () => { p.visible = c.checked; sizeText(); draw(); };
  p.box = c; sw.className = 'sw'; sw.style.background = 'rgb(' + p.color.map(v => Math.round(v * 255)).join(',') + ')';
  l.append(c, sw, document.createTextNode(p.name)); list.append(l);
});
function setVisible(fn) { PARTS.forEach((p, i) => { p.visible = fn(p, i); p.box.checked = p.visible; }); sizeText(); fit(); }
document.getElementById('only').onclick = () => setVisible((p, i) => i < 3);
document.getElementById('all').onclick = () => setVisible(() => true);
document.getElementById('fit').onclick = fit;
const zoom = k => { dist = Math.max(20, Math.min(5000, dist * k)); draw(); };
document.getElementById('zin').onclick = () => zoom(0.8);
document.getElementById('zout').onclick = () => zoom(1.25);
if (window.matchMedia('(max-width: 560px)').matches) document.getElementById('parts').open = false;
document.getElementById('lean').onclick = e => { lean = !lean; e.target.textContent = 'Lean pole: ' + (lean ? 'on' : 'off'); fit(); };
let drag = null;
canvas.addEventListener('contextmenu', e => e.preventDefault());
canvas.addEventListener('pointerdown', e => { drag = {x: e.clientX, y: e.clientY, pan: e.button === 2 || e.shiftKey}; canvas.setPointerCapture(e.pointerId); canvas.style.cursor = 'grabbing'; });
canvas.addEventListener('pointerup', () => { drag = null; canvas.style.cursor = 'grab'; });
canvas.addEventListener('pointermove', e => { if (!drag) return; const dx = e.clientX - drag.x, dy = e.clientY - drag.y; drag.x = e.clientX; drag.y = e.clientY;
  if (drag.pan) { const k = dist * 0.72 / canvas.clientHeight, {r, up} = canvas._basis; for (let i = 0; i < 3; i++) target[i] += (-dx * r[i] + dy * up[i]) * k; }
  else { yaw -= dx * 0.008; pitch = Math.max(-1.55, Math.min(1.55, pitch + dy * 0.008)); }
  draw(); });
canvas.addEventListener('wheel', e => { e.preventDefault(); dist = Math.max(20, Math.min(5000, dist * Math.exp(e.deltaY * 0.0012))); draw(); }, {passive: false});
window.addEventListener('resize', draw);
sizeText(); fit();
</script>
"""

WRAP = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>\n{}</body></html>\n'

if __name__ == "__main__":
    out = Path(__file__).parent / "viewer.html"
    page = HTML.replace("__DATA__", json.dumps(build())).replace("__LEAN__", str(ws.STICK_LEAN_DEG))
    out.write_text(WRAP.format(page))
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    if len(sys.argv) > 1:  # optional second copy without the wrapper, for hosting as a page fragment
        Path(sys.argv[1]).write_text(page)
