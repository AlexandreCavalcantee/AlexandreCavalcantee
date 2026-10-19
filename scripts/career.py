"""Render assets/career.svg: my career as a `git log --graph`.

Edit COMMITS (newest first) and run `python3 scripts/career.py`.
"""
import hashlib
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets" / "career.svg"

# (lane, kind, refs, message, date, details)
#   lane 0 = main, 1 = feature branch; kind: "commit" | "merge" | "fork"
COMMITS = [
    (0, "commit", "HEAD -> main", "feat: Full Stack Developer @ Prudêncio Advogados", "Apr 2026",
     "WhatsJud (legal CRM + AI) · QuitePay (fintech/BaaS) · Pix ITP via Celcoin · HMAC webhooks · Gemini/Claude"),
    (0, "merge", "tag: junior", "merge: promoted early to Junior Full Stack @ MedSafe", "Nov 2025", None),
    (1, "commit", "", "perf: refactor MySQL queries, -35% DB response time", "", None),
    (1, "commit", "", "test: JUnit unit + integration suites, Clean Code", "", None),
    (1, "commit", "", "feat: RESTful APIs in Spring Boot + Angular screens", "", None),
    (0, "fork", "", "feat: Full Stack intern @ MedSafe — GitLab MRs, Scrum/Kanban", "May 2025", None),
    (0, "commit", "", "hack: ChurnInsight @ Hackathon ONE — Spring Boot + FastAPI ML", "Jan 2025", None),
    (0, "commit", "", "feat: urban traffic manager — real-time YOLO vehicle counting", "Jan 2025", None),
    (0, "commit", "", "feat: Projeto AMA — React + Firebase platform for kids with ASD (NGO)", "Aug 2024", None),
    (0, "commit", "", "chore: start B.Sc. Software Engineering @ iCEV", "", None),
    (0, "commit", "tag: v0.1", "init: first program in Scratch, at age 14", "", None),
]

C = {"bg": "#0d1117", "bar": "#161b22", "border": "#30363d", "dim": "#6e7681", "text": "#c9d1d9",
     "hash": "#d29922", "head": "#39c5cf", "tag": "#a78bfa", "main": "#3fb950", "branch": "#f778ba"}
LANE_X = (34, 54)


def main():
    width, row, top = 980, 24, 66
    y = top
    rows = []  # (y, lane, kind, refs, msg, date, is_detail)
    for lane, kind, refs, msg, date, details in COMMITS:
        rows.append((y, lane, kind, refs, msg, date, False))
        y += row
        if details:
            rows.append((y, lane, "detail", "", details, "", True))
            y += row
    height = y + 10

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text{font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;font-size:13px;white-space:pre}",
        ".r{opacity:0;animation:in .3s ease-out forwards}",
        "@keyframes in{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}",
        ".g{stroke-dasharray:2000;stroke-dashoffset:2000;animation:draw 3.5s ease-in-out .3s forwards}",
        "@keyframes draw{to{stroke-dashoffset:0}}",
        "</style>",
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10" fill="{C["bg"]}" stroke="{C["border"]}"/>',
        f'<path d="M.5 30V10.5a10 10 0 0 1 10-10h{width - 21}a10 10 0 0 1 10 10V30z" fill="{C["bar"]}"/>',
        '<circle cx="20" cy="15" r="6" fill="#ff5f56"/><circle cx="40" cy="15" r="6" fill="#ffbd2e"/>'
        '<circle cx="60" cy="15" r="6" fill="#27c93f"/>',
        f'<text x="{width / 2}" y="19" fill="{C["dim"]}" text-anchor="middle">alexandre@github: ~/career — git log --graph --oneline</text>',
    ]

    # Graph lines: main lane runs top to bottom, the feature branch forks off and merges back.
    commits = [r for r in rows if not r[6]]
    first_y, last_y = commits[0][0] - 4, commits[-1][0] - 4
    out.append(f'<path class="g" d="M{LANE_X[0]} {last_y}V{first_y}" stroke="{C["main"]}" stroke-width="2" fill="none"/>')
    branch = [r[0] - 4 for r in commits if r[1] == 1]
    merge_y = next(r[0] - 4 for r in commits if r[2] == "merge")
    fork_y = next(r[0] - 4 for r in commits if r[2] == "fork")
    out.append(f'<path class="g" d="M{LANE_X[0]} {fork_y}C{LANE_X[0]} {fork_y - 12} {LANE_X[1]} {fork_y - 10} {LANE_X[1]} {fork_y - 20}'
               f'V{min(branch)}C{LANE_X[1]} {merge_y + 10} {LANE_X[0]} {merge_y + 12} {LANE_X[0]} {merge_y}" '
               f'stroke="{C["branch"]}" stroke-width="2" fill="none"/>')

    delay = 0.3
    for y_, lane, kind, refs, msg, date, detail in rows:
        x0 = 78
        parts = []
        if detail:
            parts.append(f'<tspan fill="{C["dim"]}">└ {escape(msg)}</tspan>')
        else:
            color = C["branch"] if lane else C["main"]
            dot = (f'<circle cx="{LANE_X[lane]}" cy="{y_ - 4}" r="{6 if kind == "merge" else 5}" fill="{C["bg"]}" '
                   f'stroke="{color}" stroke-width="2.5"/>')
            sha = hashlib.sha1(msg.encode()).hexdigest()[:7]
            parts.append(f'<tspan fill="{C["hash"]}">{sha}</tspan> ')
            if refs:
                ref_color = C["head"] if refs.startswith("HEAD") else C["tag"]
                parts.append(f'<tspan fill="{C["hash"]}">(</tspan><tspan fill="{ref_color}" font-weight="700">{escape(refs)}</tspan>'
                             f'<tspan fill="{C["hash"]}">)</tspan> ')
            head, _, rest = msg.partition(":")
            parts.append(f'<tspan fill="{C["branch"] if lane else C["main"]}">{escape(head)}:</tspan>'
                         f'<tspan fill="{C["text"]}">{escape(rest)}</tspan>')
        out.append(f'<g class="r" style="animation-delay:{delay:.2f}s">')
        if not detail:
            out.append(dot)
        out.append(f'<text x="{x0}" y="{y_}" xml:space="preserve">{"".join(parts)}</text>')
        if date:
            out.append(f'<text x="{width - 20}" y="{y_}" fill="{C["dim"]}" text-anchor="end">{date}</text>')
        out.append("</g>")
        delay += 0.28
    out.append("</svg>")
    OUT.write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
