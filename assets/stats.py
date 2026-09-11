#!/usr/bin/env python3
"""Render the profile's contribution heatmap as a local SVG.

The third-party activity-graph deployment the README used now answers
`402 DEPLOYMENT_DISABLED`, and shared README-stats instances are routinely
rate limited, so this card is generated here and committed as
assets/stats-{dark,light}.svg. The workflow refreshes it alongside the robot.

    GH_TOKEN=$(gh auth token) python stats.py
"""
import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(first: 100, ownerAffiliations: [OWNER], isFork: false) {
      totalCount
    }
  }
}
"""

# ---- Nord card palettes ----
NORD = {
    "dark": {
        "bg": "#2E3440", "border": "#3B4252", "title": "#88C0D0",
        "text": "#ECEFF4", "subtext": "#81A1C1",
        "empty": "#3B4252", "levels": ["#434C5E", "#5E81AC", "#88C0D0", "#8FBCBB"],
    },
    "light": {
        "bg": "#ECEFF4", "border": "#D8DEE9", "title": "#5E81AC",
        "text": "#2E3440", "subtext": "#4C566A",
        "empty": "#D8DEE9", "levels": ["#81A1C1", "#5E81AC", "#4C566A", "#2E3440"],
    },
}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

W, H = 856, 250
CARD_X = 32
CARD_W = 792          # 53 weeks x STEP - GAP, so the grid pads evenly on both sides
CELL, GAP = 12, 3
STEP = CELL + GAP
TITLE_Y = 40
HEAD_Y = 76           # "Contributions" baseline; month labels sit below it
HEAT_Y = 100          # top of the heatmap grid (7 rows)
LEGEND_Y = HEAT_Y + 7 * STEP + 18
FONT = "ui-sans-serif, system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif"


def graphql(token, login):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-stats",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        payload = json.load(res)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    user = payload.get("data", {}).get("user")
    if not user:
        raise RuntimeError(f"no such user: {login}")
    return user


def collect(user):
    cc = user["contributionsCollection"]
    cal = cc["contributionCalendar"]
    return {
        "repos": user["repositories"]["totalCount"],
        "contributions": cal["totalContributions"],
        "weeks": [w["contributionDays"] for w in cal["weeks"]],
        "days": [d for w in cal["weeks"] for d in w["contributionDays"]],
    }


def thresholds(days):
    """Quartile cutoffs over counted days, like GitHub's own heatmap legend."""
    vals = sorted(d["contributionCount"] for d in days if d["contributionCount"] > 0)
    if not vals:
        return [1, 2, 3]
    return [max(1, vals[int(len(vals) * q)]) for q in (0.25, 0.5, 0.75)]


def level(count, cuts):
    if count <= 0:
        return 0
    return 1 + sum(count > c for c in cuts)


def month_labels(weeks, x0, sub):
    out, seen = [], None
    for i, week in enumerate(weeks):
        if not week:
            continue
        m = int(week[0]["date"][5:7])
        if m != seen:
            seen = m
            out.append(f'<text x="{x0 + i * STEP}" y="{HEAD_Y + 17}" '
                       f'fill="{sub}" font-size="11">{MONTHS[m - 1]}</text>')
    return out


def render(data, theme="dark", login="Zewang0217"):
    c = NORD.get(theme, NORD["dark"])
    cuts = thresholds(data["days"])
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" font-family="{FONT}" '
        f'aria-label="Contribution activity for {login}">',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" '
        f'fill="{c["bg"]}" stroke="{c["border"]}"/>',
        f'<text x="{CARD_X}" y="{TITLE_Y}" fill="{c["title"]}" font-size="18" '
        f'font-weight="600">{login}\'s Contribution Activity</text>',
        f'<line x1="{CARD_X}" y1="{TITLE_Y + 14}" x2="{CARD_X + CARD_W}" '
        f'y2="{TITLE_Y + 14}" stroke="{c["border"]}"/>',
        f'<text x="{CARD_X}" y="{HEAD_Y}" fill="{c["text"]}" font-size="13" '
        f'font-weight="600">Contributions</text>',
        f'<text x="{CARD_X + CARD_W}" y="{HEAD_Y}" fill="{c["subtext"]}" font-size="12" '
        f'text-anchor="end">{data["contributions"]:,} in the last year</text>',
    ]

    p.extend(month_labels(data["weeks"], CARD_X, c["subtext"]))
    for wi, week in enumerate(data["weeks"]):
        for di, day in enumerate(week):
            x = CARD_X + wi * STEP
            y = HEAT_Y + di * STEP
            count = day["contributionCount"]
            fill = c["empty"] if count == 0 else c["levels"][level(count, cuts) - 1]
            p.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                     f'fill="{fill}"><title>{day["date"]}: {count} contribution'
                     f'{"" if count == 1 else "s"}</title></rect>')

    # legend, mirrored against the provenance note on the left
    lx = CARD_X + CARD_W - (6 * STEP + 26)
    p.append(f'<text x="{lx - 6}" y="{LEGEND_Y + CELL - 3}" fill="{c["subtext"]}" '
             f'font-size="11" text-anchor="end">Less</text>')
    for i, fill in enumerate([c["empty"], *c["levels"]]):
        p.append(f'<rect x="{lx + i * STEP}" y="{LEGEND_Y}" width="{CELL}" '
                 f'height="{CELL}" rx="2.5" fill="{fill}"/>')
    p.append(f'<text x="{lx + 5 * STEP + 6}" y="{LEGEND_Y + CELL - 3}" '
             f'fill="{c["subtext"]}" font-size="11">More</text>')

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    p.append(f'<text x="{CARD_X}" y="{LEGEND_Y + CELL - 3}" fill="{c["subtext"]}" '
             f'font-size="11">{data["repos"]} public repos · updated {stamp}</text>')
    p.append("</svg>")
    return "\n".join(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="assets/stats", help="output prefix")
    ap.add_argument("-u", "--user", default=os.environ.get("GH_USERNAME", "Zewang0217"))
    args = ap.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        # Never fail the scheduled job just because the token is missing:
        # keep the previously committed SVGs.
        print("[stats] no GH_TOKEN, keeping existing SVGs", file=sys.stderr)
        return 0

    data = collect(graphql(token, args.user))
    for theme in ("dark", "light"):
        svg = render(data, theme=theme, login=args.user)
        path = f"{args.out}-{theme}.svg"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"[stats] wrote {path} ({len(svg)} bytes)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
