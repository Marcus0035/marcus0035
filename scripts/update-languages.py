#!/usr/bin/env python3
"""Draws assets/languages-light.svg and assets/languages-dark.svg: the share of each language in all my repositories
(public and private, forks left out), by bytes of code. Needs the GitHub CLI logged in with access to the private ones:

    python3 scripts/update-languages.py
"""
import json
import subprocess
from collections import Counter
from pathlib import Path

OWNER = "Marcus0035"
SHOWN = 5  # the biggest ones, the rest is "Other"

THEMES = {
    # GitHub's own text colors, so the chart sits quietly in the page; one hue for the bars
    "light": {"bar": "#2a78d6", "text": "#1f2328", "muted": "#59636e", "line": "#d1d9e0"},
    "dark": {"bar": "#3987e5", "text": "#f0f6fc", "muted": "#9198a1", "line": "#3d444d"},
}


def gh(*args: str):
    return json.loads(subprocess.check_output(["gh", *args]))


def language_bytes() -> Counter:
    total: Counter = Counter()
    for repo in gh("repo", "list", OWNER, "--limit", "200", "--json", "name,isFork"):
        if not repo["isFork"]:
            total.update(gh("api", f"repos/{OWNER}/{repo['name']}/languages"))
    return total


def rows(total: Counter) -> list[tuple[str, float]]:
    everything = sum(total.values())
    biggest = total.most_common(SHOWN)
    other = everything - sum(size for _, size in biggest)
    shares = [(name, 100 * size / everything) for name, size in biggest]
    return shares + ([("Other", 100 * other / everything)] if other > 0 else [])


def svg(shares: list[tuple[str, float]], colors: dict[str, str]) -> str:
    width, label_w, row, bar_h, top = 560, 96, 34, 14, 8
    scale = (width - label_w - 64) / max(share for _, share in shares)
    height = top * 2 + row * len(shares)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Share of code by language: {", ".join(f"{n} {s:.0f} %" for n, s in shares)}">',
        '<style>text{font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;font-size:14px}</style>',
        f'<line x1="{label_w}" y1="{top}" x2="{label_w}" y2="{height - top}" stroke="{colors["line"]}" stroke-width="1"/>',
    ]
    for i, (name, share) in enumerate(shares):
        y = top + i * row + (row - bar_h) / 2
        w = max(share * scale, 6)
        # square at the baseline, 4px rounded at the end of the bar
        path = f"M{label_w} {y} h{w - 4} a4 4 0 0 1 4 4 v{bar_h - 8} a4 4 0 0 1 -4 4 h-{w - 4} z"
        out.append(f'<text x="{label_w - 12}" y="{y + bar_h / 2 + 5}" text-anchor="end" fill="{colors["text"]}">{name}</text>')
        out.append(f'<path d="{path}" fill="{colors["bar"]}"/>')
        out.append(f'<text x="{label_w + w + 10}" y="{y + bar_h / 2 + 5}" fill="{colors["muted"]}">{share:.0f} %</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    shares = rows(language_bytes())
    for mode, colors in THEMES.items():
        Path(f"assets/languages-{mode}.svg").write_text(svg(shares, colors) + "\n", encoding="utf-8")
    print(", ".join(f"{name} {share:.1f} %" for name, share in shares))
