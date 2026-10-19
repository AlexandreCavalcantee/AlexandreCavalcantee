"""Render assets/boot.svg: the profile header styled as a Spring Boot startup log.

Stats come from the GitHub API when GITHUB_TOKEN is set; otherwise placeholders are used.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "boot.svg"
USER = "AlexandreCavalcantee"

BANNER = r"""
  .          _                          _            __ _ _
 /\\    __ _| | _____  ____ _ _ __   __| |_ __ ___  \ \ \ \
( ( )  / _` | |/ _ \ \/ / _` | '_ \ / _` | '__/ _ \  \ \ \ \
 \\/  | (_| | |  __/>  < (_| | | | | (_| | | |  __/   ) ) ) )
  '    \__,_|_|\___/_/\_\__,_|_| |_|\__,_|_|  \___|  / / / /
 ===================================================/_/_/_/
""".strip("\n").splitlines()

C = {
    "bg": "#0d1117", "bar": "#161b22", "border": "#30363d", "dim": "#6e7681", "text": "#c9d1d9",
    "green": "#3fb950", "yellow": "#d29922", "cyan": "#39c5cf", "purple": "#a78bfa", "spring": "#6db33f",
}


def gh(path):
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def stats():
    if not os.environ.get("GITHUB_TOKEN"):
        return {"repos": "?", "followers": "?", "stars": "?", "commits": "?"}
    user = gh(f"users/{USER}")
    repos = gh(f"users/{USER}/repos?per_page=100&type=owner")
    commits = gh(f"search/commits?q=author:{USER}&per_page=1")["total_count"]
    return {
        "repos": user["public_repos"],
        "followers": user["followers"],
        "stars": sum(r["stargazers_count"] for r in repos),
        "commits": commits,
    }


def log_lines(st):
    return [
        ("INFO", "AlexandreApplication", "Starting AlexandreApplication on teresina-pi (Java 21 · Node · Deno)"),
        ("INFO", "CareerService", "Full Stack Developer @ Prudêncio Advogados (since Apr 2026)"),
        ("INFO", "ProjectRegistry", "Shipping WhatsJud (legal CRM + AI) & QuitePay (fintech/BaaS)"),
        ("INFO", "CareerHistory", "Previously @ MedSafe: intern → Junior Full Stack (Java + Angular)"),
        ("INFO", "SkillsConfiguration", "Loaded beans: [TS, React, Java, Spring, Supabase, Postgres]"),
        ("INFO", "EducationService", "B.Sc. Software Engineering @ iCEV — graduating Dec 2027"),
        ("INFO", "GitHubStatsService", f"{st['repos']} public repos · {st['commits']} commits · {st['stars']} stars · {st['followers']} followers"),
        ("INFO", "HobbyScheduler", "Registered tasks: [chess, rubik-cube] — brain warmed up"),
        ("INFO", "CertificationLoader", "OCI · AWS Academy · Red Hat Linux · English C1 (Cambridge)"),
        ("WARN", "CoffeeMonitor", "Caffeine below threshold. Brewing another cup..."),
        ("INFO", "ContactEndpoint", "Exposed at linkedin.com/in/alexandrecavalcantee"),
        ("INFO", "AlexandreApplication", "Started AlexandreApplication — coding since age 14 🚀"),
    ]


def main():
    st = stats()
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d %H:%M:%S")
    font, lh, cw = 13, 19, 7.85
    width = 980
    top = 52
    lines = []  # (y, svg tspans, delay)
    y = top

    for i, row in enumerate(BANNER):
        lines.append((y, f'<tspan fill="{C["spring"]}">{escape(row)}</tspan>', 0.15 + i * 0.07))
        y += lh
    lines.append((y, f'<tspan fill="{C["spring"]}"> :: Alexandre Cavalcante ::</tspan>'
                     f'<tspan fill="{C["dim"]}">      (v3.0.0-SNAPSHOT · Full Stack Developer)</tspan>', 0.7))
    y += lh * 1.6

    delay = 1.2
    for level, logger, msg in log_lines(st):
        lvl_color = C["yellow"] if level == "WARN" else C["green"]
        msg_color = C["yellow"] if level == "WARN" else C["text"]
        spans = (f'<tspan fill="{C["dim"]}">{stamp} </tspan>'
                 f'<tspan fill="{lvl_color}">{level:<5}</tspan>'
                 f'<tspan fill="{C["purple"]}"> {escape(logger[:22]):>22}</tspan>'
                 f'<tspan fill="{C["dim"]}"> : </tspan>'
                 f'<tspan fill="{msg_color}">{escape(msg)}</tspan>')
        lines.append((y, spans, delay))
        y += lh
        delay += 0.45 if level != "WARN" else 0.9

    height = int(y + 26)
    cursor_y = y - lh + 4
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        f"text{{font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;font-size:{font}px;white-space:pre}}",
        ".l{opacity:0;animation:in .25s ease-out forwards}",
        "@keyframes in{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:none}}",
        ".cur{opacity:0;animation:blink 1s step-end infinite}",
        "@keyframes blink{0%,100%{opacity:0}50%{opacity:1}}",
        "</style>",
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10" fill="{C["bg"]}" stroke="{C["border"]}"/>',
        f'<path d="M.5 30V10.5a10 10 0 0 1 10-10h{width - 21}a10 10 0 0 1 10 10V30z" fill="{C["bar"]}"/>',
        f'<circle cx="20" cy="15" r="6" fill="#ff5f56"/><circle cx="40" cy="15" r="6" fill="#ffbd2e"/>'
        f'<circle cx="60" cy="15" r="6" fill="#27c93f"/>',
        f'<text x="{width / 2}" y="19" fill="{C["dim"]}" text-anchor="middle">alexandre@github: ~/profile — ./mvnw spring-boot:run</text>',
    ]
    for y_, spans, d in lines:
        out.append(f'<text class="l" x="18" y="{y_:.0f}" xml:space="preserve" style="animation-delay:{d:.2f}s">{spans}</text>')
    out.append(f'<rect class="cur" x="18" y="{cursor_y + lh - 13:.0f}" width="{cw:.0f}" height="15" fill="{C["text"]}" '
               f'style="animation-delay:{delay:.2f}s"/>')
    out.append("</svg>")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
