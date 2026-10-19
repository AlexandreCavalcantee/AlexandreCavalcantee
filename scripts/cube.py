"""Community Rubik's cube for the profile README.

Usage:
  cube.py move "<issue title>" <github user>   apply a move coming from an issue
  cube.py render                               regenerate the SVG and README section
  cube.py reset                                start over with a fresh scramble
"""
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "cube" / "state.json"
SVG = ROOT / "cube" / "cube.svg"
README = ROOT / "README.md"
REPO = "AlexandreCavalcantee/AlexandreCavalcantee"

FACES = "URFDLB"
COLORS = {
    "U": "#f5f5f5",  # white
    "R": "#e0303c",  # red
    "F": "#1fae5b",  # green
    "D": "#ffd23f",  # yellow
    "L": "#ff8a1f",  # orange
    "B": "#2c6ff2",  # blue
}
# For each face: outward normal, then the "right" and "down" vectors as the face is seen in the standard net.
GEOMETRY = {
    "U": ((0, 1, 0), (1, 0, 0), (0, 0, 1)),
    "R": ((1, 0, 0), (0, 0, -1), (0, -1, 0)),
    "F": ((0, 0, 1), (1, 0, 0), (0, -1, 0)),
    "D": ((0, -1, 0), (1, 0, 0), (0, 0, -1)),
    "L": ((-1, 0, 0), (0, 0, 1), (0, -1, 0)),
    "B": ((0, 0, -1), (-1, 0, 0), (0, -1, 0)),
}
MOVE_RE = re.compile(r"^([URFDLB])(['2]?)$")


def add(*vs):
    return tuple(sum(c) for c in zip(*vs))


def mul(v, k):
    return tuple(c * k for c in v)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def sticker_pos(face, i):
    n, r, d = GEOMETRY[face]
    row, col = divmod(i, 3)
    return add(n, mul(r, col - 1), mul(d, row - 1))


def locate(pos, normal):
    for face, (n, _, _) in GEOMETRY.items():
        if n == normal:
            for i in range(9):
                if sticker_pos(face, i) == pos:
                    return face, i
    raise ValueError((pos, normal))


def quarter_turn(stickers, face):
    """Turn one face 90 degrees clockwise (as seen looking at that face)."""
    axis = GEOMETRY[face][0]
    # Clockwise seen from outside = -90 degrees around the outward normal.
    rot = lambda v: add(mul(cross(axis, v), -1), mul(axis, dot(axis, v)))
    new = {f: list(s) for f, s in stickers.items()}
    for f in FACES:
        for i in range(9):
            pos = sticker_pos(f, i)
            if dot(pos, axis) != 1:
                continue
            nf, ni = locate(rot(pos), rot(GEOMETRY[f][0]))
            new[nf][ni] = stickers[f][i]
    return {f: "".join(s) for f, s in new.items()}


def apply(stickers, move):
    face, suffix = MOVE_RE.match(move).groups()
    for _ in range({"": 1, "2": 2, "'": 3}[suffix]):
        stickers = quarter_turn(stickers, face)
    return stickers


def solved_cube():
    return {f: f * 9 for f in FACES}


def is_solved(stickers):
    return all(len(set(s)) == 1 for s in stickers.values())


def scramble():
    moves, last = [], None
    while len(moves) < 20:
        face = random.choice(FACES)
        if face == last:
            continue
        moves.append(face + random.choice(["", "'", "2"]))
        last = face
    stickers = solved_cube()
    for m in moves:
        stickers = apply(stickers, m)
    return stickers, " ".join(moves)


def new_state(previous=None):
    stickers, seq = scramble()
    return {
        "stickers": stickers,
        "scramble": seq,
        "moves": 0,
        "history": [],
        "solves": (previous or {}).get("solves", []),
        "players": (previous or {}).get("players", {}),
        "total_moves": (previous or {}).get("total_moves", 0),
    }


# ---------- rendering ----------

C30 = 0.8660254


def project(p, ox, oy, scale):
    x, y, z = p
    return ox + (x - z) * C30 * scale, oy + ((x + z) * 0.5 - y) * scale


def view_polys(stickers, transform, ox, oy, scale):
    polys = []
    for f in FACES:
        n, r, d = GEOMETRY[f]
        tn = transform(n)
        if tn not in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            continue
        for i in range(9):
            c = sticker_pos(f, i)
            corners = []
            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                # Shrink each sticker a bit so the black plastic shows between them.
                p = add(c, mul(r, a * 0.43), mul(d, b * 0.43))
                p = transform(add(mul(p, 1), mul(n, 0.5)))
                corners.append(project(p, ox, oy, scale))
            polys.append((COLORS[stickers[f][i]], corners))
    return polys


def body(transform, ox, oy, scale):
    faces = []
    for n, r, d in GEOMETRY.values():
        if transform(n) not in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            continue
        c = mul(n, 1.5)
        pts = [project(transform(add(c, mul(r, a * 1.5), mul(d, b * 1.5))), ox, oy, scale)
               for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        faces.append(pts)
    return faces


def poly(points, **attrs):
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    extra = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<polygon points="{pts}" {extra}/>'


def render_svg(state):
    stickers = state["stickers"]
    solved = is_solved(stickers)
    views = [
        ("FRONT · U F R", lambda v: v, 190),
        # 180 degree turn around the (1,0,-1) axis shows D on top with L and B facing us.
        ("BACK · D L B", lambda v: (-v[2], -v[1], -v[0]), 530),
    ]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="340" viewBox="0 0 720 340">',
        "<style>",
        ".float{animation:float 4s ease-in-out infinite}",
        ".float2{animation:float 4s ease-in-out infinite;animation-delay:-2s}",
        "@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}",
        "text{font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace}",
        ".pulse{animation:pulse 1.6s ease-in-out infinite}",
        "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.45}}",
        "</style>",
        '<rect width="720" height="340" rx="14" fill="#0d1117" stroke="#30363d"/>',
    ]
    for k, (label, tf, ox) in enumerate(views):
        out.append(f'<g class="{"float" if k == 0 else "float2"}">')
        out.append(f'<ellipse cx="{ox}" cy="305" rx="95" ry="12" fill="#000" opacity=".45"/>')
        for pts in body(tf, ox, 168, 44):
            out.append(poly(pts, fill="#111", stroke="#111", stroke_width=6, stroke_linejoin="round"))
        for color, pts in view_polys(stickers, tf, ox, 168, 44):
            out.append(poly(pts, fill=color, stroke="#000", stroke_opacity=".25", stroke_linejoin="round"))
        out.append("</g>")
        out.append(f'<text x="{ox}" y="330" fill="#8b949e" font-size="13" text-anchor="middle">{label}</text>')
    if solved:
        out.append('<text class="pulse" x="360" y="174" fill="#3fb950" font-size="20" font-weight="700" '
                   'text-anchor="middle">✔ SOLVED</text>')
    else:
        out.append(f'<text x="360" y="174" fill="#a78bfa" font-size="15" text-anchor="middle">'
                   f'move #{state["moves"]}</text>')
    out.append("</svg>")
    SVG.write_text("\n".join(out) + "\n")


def issue_link(move, label=None):
    title = quote(f"cube|{move}", safe="")
    body = quote("Just hit **Submit new issue** — a GitHub Action will turn the cube for you. 🧩", safe="")
    return f"[`{label or move}`](https://github.com/{REPO}/issues/new?title={title}&body={body})"


def render_readme(state):
    rows = []
    for suffix, name in (("", "clockwise"), ("'", "counter‑clockwise"), ("2", "180°")):
        rows.append(f"| **{name}** | " + " | ".join(issue_link(f + suffix) for f in FACES) + " |")
    history = state["history"][-5:][::-1]
    hist = "\n".join(f"| `{h['move']}` | [@{h['user']}](https://github.com/{h['user']}) | {h['date']} |"
                     for h in history) or "| — | nobody yet, be the first! | — |"
    top = sorted(state["players"].items(), key=lambda kv: -kv[1])[:5]
    leaders = "\n".join(f"| {i + 1} | [@{u}](https://github.com/{u}) | {n} |" for i, (u, n) in enumerate(top)) \
        or "| — | — | — |"
    solves = len(state["solves"])
    last_solve = (f"Last solved by [@{state['solves'][-1]['user']}](https://github.com/{state['solves'][-1]['user']})"
                  f" in {state['solves'][-1]['moves']} moves." if solves else "Nobody has solved it yet. 👀")

    section = f"""<!--CUBE_START-->
<p align="center"><img src="cube/cube.svg" width="640" alt="Community Rubik's cube"/></p>

<p align="center">
  <b>{state['moves']}</b> moves since the last scramble · <b>{state['total_moves']}</b> moves all‑time · solved <b>{solves}</b>×<br/>
  <sub>{last_solve}</sub>
</p>

| | U | R | F | D | L | B |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
{chr(10).join(rows)}

<details>
<summary>🎲 Recent moves & top cubers</summary>

| Move | Player | When (UTC) |
|:-:|:-|:-|
{hist}

| # | Player | Moves |
|:-:|:-|:-:|
{leaders}

Current scramble: `{state['scramble']}`
{"" if not is_solved(state['stickers']) else chr(10) + "Solved! " + issue_link("scramble", "🔀 scramble a new one")}
</details>
<!--CUBE_END-->"""
    text = README.read_text()
    text = re.sub(r"<!--CUBE_START-->.*<!--CUBE_END-->", lambda _: section, text, flags=re.S)
    README.write_text(text)


def render(state):
    render_svg(state)
    render_readme(state)


def load():
    return json.loads(STATE.read_text())


def save(state):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def main():
    cmd = sys.argv[1]
    if cmd == "reset":
        state = new_state(load() if STATE.exists() else None)
    elif cmd == "render":
        state = load()
    elif cmd == "move":
        title, user = sys.argv[2].strip(), sys.argv[3]
        move = title.split("|", 1)[1].strip() if "|" in title else ""
        state = load()
        if move == "scramble":
            if not is_solved(state["stickers"]):
                print("REJECTED: the cube can only be re-scrambled after it has been solved")
                sys.exit(2)
            state = new_state(state)
        elif MOVE_RE.match(move):
            state["stickers"] = apply(state["stickers"], move)
            state["moves"] += 1
            state["total_moves"] += 1
            state["players"][user] = state["players"].get(user, 0) + 1
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
            state["history"] = (state["history"] + [{"move": move, "user": user, "date": now}])[-20:]
            if is_solved(state["stickers"]):
                state["solves"].append({"user": user, "moves": state["moves"], "date": now})
                print("SOLVED")
        else:
            print(f"REJECTED: unknown move {move!r}")
            sys.exit(2)
    else:
        sys.exit(__doc__)
    save(state)
    render(state)


if __name__ == "__main__":
    main()
