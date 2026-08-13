#!/usr/bin/env python3
"""Robot SVG generator for the self-updating profile bot.

Renders a Nord-themed cartoon robot in one of several action poses with
inline SMIL animations (GitHub renders these inside <img>-embedded SVGs).
A speech bubble carries the agent's one-liner.

    python robot.py --action coding --line "重构记忆引擎中..." -o robot.svg
    python robot.py --preview            # render all poses side by side
"""
import argparse
import html

# ---- Palettes (Nord dark + light) ----
THEMES = {
    "dark": {
        "bg": "#2E3440", "panel": "#3B4252", "body": "#4C566A",
        "outline": "#88C0D0", "accent": "#5E81AC", "warm": "#D08770",
        "green": "#A3BE8C", "purple": "#B48EAD", "text": "#ECEFF4",
        "screen": "#2E3440", "dot": "#3B4252",
    },
    "light": {
        "bg": "#ECEFF4", "panel": "#E5E9F0", "body": "#D8DEE9",
        "outline": "#5E81AC", "accent": "#81A1C1", "warm": "#D08770",
        "green": "#A3BE8C", "purple": "#B48EAD", "text": "#2E3440",
        "screen": "#2E3440", "dot": "#D8DEE9",
    },
}


def _apply_theme(name):
    """Swap the module-level color globals; f-strings resolve them at call time."""
    g = globals()
    p = THEMES[name if name in THEMES else "dark"]
    for k, v in p.items():
        g[k.upper()] = v          # bg -> BG, dot -> DOT, etc.
    g["TEXT_LT"] = "#FFFFFF" if name == "light" else "#ECEFF4"


# initial palette (dark)
_apply_theme("dark")

W, H = 480, 360
FONT = "ui-sans-serif, system-ui, 'PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif"
MONO = "ui-monospace, 'JetBrains Mono', 'Cascadia Code', Consolas, monospace"

ACTIONS = ["idle", "wave", "coding", "thinking", "running",
           "celebrating", "building", "ship", "sleeping"]


def esc(s):
    return html.escape(str(s), quote=True)


def wrap_text(text, width=13, max_lines=4):
    text = (text or "").replace("\r", "").strip()
    lines = []
    for raw in text.split("\n"):
        i = 0
        while i < len(raw) and len(lines) < max_lines:
            lines.append(raw[i:i + width])
            i += width
        if len(lines) >= max_lines:
            break
    return lines or ["…"]


def _stage():
    return (
        f'<rect x="0" y="0" width="{W}" height="{H}" rx="24" fill="{BG}"/>'
        # faint grid dots for depth
        f'<g fill="{DOT}" opacity="0.55">'
        + "".join(
            f'<circle cx="{x}" cy="{y}" r="1.6"/>'
            for x in range(24, W, 28)
            for y in range(24, H, 28)
        )
        + "</g>"
    )


def _shadow():
    return '<ellipse cx="180" cy="328" rx="74" ry="10" fill="#000" opacity="0.28"/>'


def _head(sleepy=False):
    if sleepy:
        eyes = (
            f'<path d="M155 150 q8 6 16 0" stroke="{OUTLINE}" stroke-width="3" fill="none" stroke-linecap="round"/>'
            f'<path d="M189 150 q8 6 16 0" stroke="{OUTLINE}" stroke-width="3" fill="none" stroke-linecap="round"/>'
        )
    else:
        eyes = (
            f'<ellipse cx="163" cy="148" rx="8" ry="8" fill="{OUTLINE}">'
            f'<animate attributeName="ry" values="8;8;8;1;8" keyTimes="0;0.8;0.88;0.92;1" dur="4.5s" repeatCount="indefinite"/>'
            f'</ellipse>'
            f'<ellipse cx="197" cy="148" rx="8" ry="8" fill="{OUTLINE}">'
            f'<animate attributeName="ry" values="8;8;8;1;8" keyTimes="0;0.8;0.88;0.92;1" dur="4.5s" repeatCount="indefinite"/>'
            f'</ellipse>'
        )
    return f"""
    <g id="head">
      <line x1="180" y1="116" x2="180" y2="86" stroke="{OUTLINE}" stroke-width="4" stroke-linecap="round"/>
      <circle cx="180" cy="80" r="7" fill="{WARM}">
        <animate attributeName="opacity" values="1;0.25;1" dur="1.6s" repeatCount="indefinite"/>
      </circle>
      <rect x="138" y="116" width="84" height="70" rx="18" fill="{PANEL}" stroke="{OUTLINE}" stroke-width="3"/>
      {eyes}
      <circle cx="150" cy="166" r="4" fill="{WARM}" opacity="0.65"/>
      <circle cx="210" cy="166" r="4" fill="{WARM}" opacity="0.65"/>
      <path id="mouth" d="M170 170 Q180 178 190 170" stroke="{OUTLINE}" stroke-width="3" fill="none" stroke-linecap="round"/>
    </g>"""


def _body(icon, accent=ACCENT):
    return f"""
    <g id="body">
      <rect x="122" y="186" width="116" height="100" rx="22" fill="{BODY}" stroke="{OUTLINE}" stroke-width="3"/>
      <rect x="146" y="206" width="68" height="46" rx="9" fill="{SCREEN}" stroke="{accent}" stroke-width="2"/>
      <text x="180" y="238" font-family="{esc(MONO)}" font-size="20" font-weight="700"
            fill="{OUTLINE}" text-anchor="middle">{esc(icon)}</text>
      <circle cx="180" cy="270" r="6" fill="{GREEN}">
        <animate attributeName="opacity" values="0.35;1;0.35" dur="2.1s" repeatCount="indefinite"/>
      </circle>
    </g>"""


# ---- limbs (static pose via transform, or motion via animateTransform) ----

def _static_arm(side, angle, hand="circle"):
    sx, sy = (130, 194) if side == "L" else (230, 194)
    hx = sx + (-16 if side == "L" else 16)
    hy = sy + 58
    dot = f'<circle cx="{hx}" cy="{hy}" r="8" fill="{WARM}"/>' if hand == "circle" else ""
    inner = (f'<line x1="{sx}" y1="{sy}" x2="{hx}" y2="{hy}" stroke="{OUTLINE}" stroke-width="9" stroke-linecap="round"/>{dot}')
    return f'<g transform="rotate({angle} {sx} {sy})">{inner}</g>'


def _leg(side, x2, y2, foot=True):
    hx = 158 if side == "L" else 202
    hy = 286
    f = f'<ellipse cx="{x2}" cy="{y2 + 3}" rx="11" ry="5" fill="{OUTLINE}"/>' if foot else ""
    return (f'<line x1="{hx}" y1="{hy}" x2="{x2}" y2="{y2}" stroke="{OUTLINE}" stroke-width="10" stroke-linecap="round"/>{f}')


# ---- per-action decorations ----
def _deco_thinking():
    return f"""
    <g>
      <circle cx="226" cy="100" r="5" fill="{PURPLE}"><animate attributeName="opacity" values="0.2;1;0.2" dur="1.5s" repeatCount="indefinite" begin="0s"/></circle>
      <circle cx="242" cy="86" r="6" fill="{PURPLE}"><animate attributeName="opacity" values="0.2;1;0.2" dur="1.5s" repeatCount="indefinite" begin="0.3s"/></circle>
      <circle cx="262" cy="70" r="8" fill="{WARM}"><animate attributeName="opacity" values="0.2;1;0.2" dur="1.5s" repeatCount="indefinite" begin="0.6s"/></circle>
    </g>"""


def _deco_celebrating():
    sparks = ""
    pts = [(150, 70, GREEN), (210, 60, WARM), (250, 96, PURPLE),
           (120, 110, OUTLINE), (270, 70, GREEN)]
    for i, (x, y, c) in enumerate(pts):
        sparks += (
            f'<g><path d="M{x} {y} l4 8 l8 4 l-8 4 l-4 8 l-4 -8 l-8 -4 l8 -4 z" fill="{c}">'
            f'<animateTransform attributeName="transform" type="rotate" values="0 {x} {y};180 {x} {y};360 {x} {y}" dur="3s" repeatCount="indefinite" begin="{i*0.2}s"/>'
            f'<animate attributeName="opacity" values="1;0.3;1" dur="1.2s" repeatCount="indefinite" begin="{i*0.2}s"/></path></g>'
        )
    return sparks


def _deco_running():
    lines = ""
    for i, y in enumerate((170, 200, 230, 260)):
        lines += (
            f'<line x1="70" y1="{y}" x2="110" y2="{y}" stroke="{OUTLINE}" stroke-width="4" stroke-linecap="round" opacity="0.8">'
            f'<animate attributeName="x1" values="90;40;90" dur="0.5s" repeatCount="indefinite" begin="{i*0.08}s"/>'
            f'<animate attributeName="opacity" values="0.9;0.1;0.9" dur="0.5s" repeatCount="indefinite" begin="{i*0.08}s"/></line>'
        )
    return f'<g>{lines}</g>'


def _deco_sleeping():
    zzz = ""
    for i, (x, y, s) in enumerate([(236, 96, 16), (252, 76, 22), (270, 54, 28)]):
        zzz += (
            f'<text x="{x}" y="{y}" font-family="{esc(MONO)}" font-size="{s}" font-weight="800" fill="{OUTLINE}" opacity="0.9">'
            f'z<animate attributeName="opacity" values="0;1;0" dur="3s" repeatCount="indefinite" begin="{i*0.7}s"/>'
            f'<animate attributeName="y" values="{y+6};{y-14}" dur="3s" repeatCount="indefinite" begin="{i*0.7}s"/></text>'
        )
    moon = (
        f'<path d="M404 70 a26 26 0 1 0 18 -44 a20 20 0 1 1 -18 44 z" fill="{OUTLINE}" opacity="0.85"/>'
        f'<circle cx="398" cy="66" r="3" fill="{BG}"/><circle cx="406" cy="74" r="2" fill="{BG}"/>'
    )
    return f'<g>{moon}{zzz}</g>'


def _deco_ship():
    # little flag + exhaust on the right side
    return (
        f'<g>'
        f'<path d="M300 150 q22 -10 44 0 q-22 6 -44 0 z" fill="{WARM}">'
        f'<animate attributeName="opacity" values="0.5;1;0.5" dur="0.6s" repeatCount="indefinite"/></path>'
        f'<path d="M250 250 l26 0 l-13 22 z" fill="{WARM}"><animateTransform attributeName="transform" type="scale" additive="sum" values="1;1.15;1" dur="0.4s" repeatCount="indefinite"/></path>'
        f'</g>'
    )


def _deco_building():
    # bricks + sparks near right hand
    return (
        f'<g>'
        f'<rect x="288" y="246" width="26" height="12" rx="2" fill="{PURPLE}"/>'
        f'<rect x="292" y="232" width="26" height="12" rx="2" fill="{ACCENT}"/>'
        f'<circle cx="280" cy="248" r="3" fill="{WARM}"><animate attributeName="opacity" values="1;0;1" dur="0.4s" repeatCount="indefinite"/></circle>'
        f'</g>'
    )


def _deco_coding():
    # floating code symbols above head + rotating gear
    gear = (
        f'<g transform="translate(250 96)">'
        f'<animateTransform attributeName="transform" type="rotate" values="0 0 0;360 0 0" dur="6s" repeatCount="indefinite"/>'
        f'<path d="M0 -12 l3 0 l2 -4 l5 3 l-2 4 l2 3 l4 0 l0 6 l-4 0 l-2 3 l2 4 l-5 3 l-2 -4 l-3 0 l-2 4 l-5 -3 l2 -4 l-2 -3 l-4 0 l0 -6 l4 0 l2 -3 l-2 -4 l5 -3 z" fill="{GREEN}"/>'
        f'<circle r="4" fill="{BG}"/></g>'
    )
    syms = ""
    for i, (sym, x, y) in enumerate([("{", 138, 92), ("}", 232, 88)]):
        syms += (f'<text x="{x}" y="{y}" font-family="{esc(MONO)}" font-size="22" font-weight="800" fill="{ACCENT}">'
                 f'{esc(sym)}<animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite" begin="{i*0.4}s"/></text>')
    return gear + syms


# ---- assemble a pose ----
def _pose(action):
    """Return (head, body_icon, body_accent, arms_svg, legs_svg, deco_svg, tilt, sleepy)."""
    if action == "idle":
        return (_head(), "♥", GREEN,
                _static_arm("L", 8) + _static_arm("R", -8),
                _leg("L", 154, 322) + _leg("R", 206, 322),
                "", "0", False)
    if action == "wave":
        sx, sy = 230, 194
        rarm = (
            f'<g><animateTransform attributeName="transform" type="rotate" '
            f'values="-150 {sx} {sy};-118 {sx} {sy};-150 {sx} {sy}" dur="0.9s" repeatCount="indefinite"/>'
            f'<line x1="{sx}" y1="{sy}" x2="244" y2="136" stroke="{OUTLINE}" stroke-width="9" stroke-linecap="round"/>'
            f'<circle cx="244" cy="136" r="8" fill="{WARM}"/></g>'
        )
        return (_head(), ":)", ACCENT,
                _static_arm("L", 8) + rarm,
                _leg("L", 154, 322) + _leg("R", 206, 322),
                "", "0", False)
    if action == "coding":
        sx, sy = 130, 194
        sx2, sy2 = 230, 194
        larm = (f'<g><animateTransform attributeName="transform" type="rotate" '
                f'values="70 {sx} {sy};78 {sx} {sy};70 {sx} {sy}" dur="0.5s" repeatCount="indefinite"/>'
                f'<line x1="{sx}" y1="{sy}" x2="150" y2="250" stroke="{OUTLINE}" stroke-width="9" stroke-linecap="round"/>'
                f'<circle cx="150" cy="250" r="8" fill="{WARM}"/></g>')
        rarm = (f'<g><animateTransform attributeName="transform" type="rotate" '
                f'values="-70 {sx2} {sy2};-78 {sx2} {sy2};-70 {sx2} {sy2}" dur="0.5s" repeatCount="indefinite" begin="0.25s"/>'
                f'<line x1="{sx2}" y1="{sy2}" x2="210" y2="250" stroke="{OUTLINE}" stroke-width="9" stroke-linecap="round"/>'
                f'<circle cx="210" cy="250" r="8" fill="{WARM}"/></g>')
        return (_head(), "&lt;/&gt;", GREEN, larm + rarm,
                _leg("L", 154, 322) + _leg("R", 206, 322), _deco_coding(), "0", False)
    if action == "thinking":
        # right hand rests under chin (drawn as bent two-segment arm)
        rarm = (
            f'<line x1="230" y1="194" x2="214" y2="168" stroke="{OUTLINE}" stroke-width="9" stroke-linecap="round"/>'
            f'<line x1="214" y1="168" x2="196" y2="160" stroke="{OUTLINE}" stroke-width="9" stroke-linecap="round"/>'
            f'<circle cx="196" cy="160" r="8" fill="{WARM}"/>'
        )
        return (_head(), "?", PURPLE,
                _static_arm("L", 10) + rarm,
                _leg("L", 154, 322) + _leg("R", 206, 322),
                _deco_thinking(), "0", False)
    if action == "running":
        lleg = (f'<g><animateTransform attributeName="transform" type="rotate" '
                f'values="-26 158 286;26 158 286;-26 158 286" dur="0.45s" repeatCount="indefinite"/>'
                f'{_leg("L", 158, 322, foot=False)}<ellipse cx="150" cy="325" rx="11" ry="5" fill="{OUTLINE}"/></g>')
        rleg = (f'<g><animateTransform attributeName="transform" type="rotate" '
                f'values="26 202 286;-26 202 286;26 202 286" dur="0.45s" repeatCount="indefinite"/>'
                f'{_leg("R", 202, 322, foot=False)}<ellipse cx="210" cy="325" rx="11" ry="5" fill="{OUTLINE}"/></g>')
        sx, sy = 130, 194
        larm = (f'<g><animateTransform attributeName="transform" type="rotate" '
                f'values="40 {sx} {sy};70 {sx} {sy};40 {sx} {sy}" dur="0.45s" repeatCount="indefinite"/>'
                f'<line x1="{sx}" y1="{sy}" x2="120" y2="240" stroke="{OUTLINE}" stroke-width="9" stroke-linecap="round"/>'
                f'<circle cx="120" cy="240" r="8" fill="{WARM}"/></g>')
        sx2 = 230
        rarm = (f'<g><animateTransform attributeName="transform" type="rotate" '
                f'values="-40 {sx2} {sy};-70 {sx2} {sy};-40 {sx2} {sy}" dur="0.45s" repeatCount="indefinite"/>'
                f'<line x1="{sx2}" y1="{sy}" x2="240" y2="240" stroke="{OUTLINE}" stroke-width="9" stroke-linecap="round"/>'
                f'<circle cx="240" cy="240" r="8" fill="{WARM}"/></g>')
        return (_head(), ">>", WARM, larm + rarm, lleg + rleg, _deco_running(), "-7", False)
    if action == "celebrating":
        sx, sy = 130, 194
        larm = (f'<g><animateTransform attributeName="transform" type="rotate" '
                f'values="150 {sx} {sy};170 {sx} {sy};150 {sx} {sy}" dur="0.6s" repeatCount="indefinite"/>'
                f'<line x1="{sx}" y1="{sy}" x2="116" y2="140" stroke="{OUTLINE}" stroke-width="9" stroke-linecap="round"/>'
                f'<circle cx="116" cy="140" r="8" fill="{WARM}"/></g>')
        sx2 = 230
        rarm = (f'<g><animateTransform attributeName="transform" type="rotate" '
                f'values="-150 {sx2} {sy};-170 {sx2} {sy};-150 {sx2} {sy}" dur="0.6s" repeatCount="indefinite" begin="0.3s"/>'
                f'<line x1="{sx2}" y1="{sy}" x2="244" y2="140" stroke="{OUTLINE}" stroke-width="9" stroke-linecap="round"/>'
                f'<circle cx="244" cy="140" r="8" fill="{WARM}"/></g>')
        return (_head(), "★", WARM, larm + rarm,
                _leg("L", 154, 322) + _leg("R", 206, 322),
                _deco_celebrating(), "0", False)
    if action == "building":
        sx2, sy2 = 230, 194
        # hammer arm swinging down
        rarm = (f'<g><animateTransform attributeName="transform" type="rotate" '
                f'values="-30 {sx2} {sy2};-75 {sx2} {sy2};-30 {sx2} {sy2}" dur="0.7s" repeatCount="indefinite"/>'
                f'<line x1="{sx2}" y1="{sy2}" x2="262" y2="238" stroke="{OUTLINE}" stroke-width="9" stroke-linecap="round"/>'
                f'<rect x="252" y="226" width="24" height="12" rx="3" fill="{ACCENT}" stroke="{OUTLINE}" stroke-width="2"/></g>')
        return (_head(), "#", PURPLE,
                _static_arm("L", 12) + rarm,
                _leg("L", 154, 322) + _leg("R", 206, 322),
                _deco_building(), "0", False)
    if action == "ship":
        sx2, sy2 = 230, 194
        rarm = (f'<g transform="rotate(-120 {sx2} {sy2})">'
                f'<line x1="{sx2}" y1="{sy2}" x2="246" y2="150" stroke="{OUTLINE}" stroke-width="9" stroke-linecap="round"/>'
                f'<rect x="244" y="138" width="4" height="30" fill="{OUTLINE}"/>'
                f'<path d="M248 138 l22 8 l-22 8 z" fill="{WARM}"/></g>')
        return (_head(), "^", WARM,
                _static_arm("L", 12) + rarm,
                _leg("L", 154, 322) + _leg("R", 206, 322),
                _deco_ship(), "0", False)
    if action == "sleeping":
        return (_head(sleepy=True), "z", PURPLE,
                _static_arm("L", 6) + _static_arm("R", -6),
                _leg("L", 154, 322) + _leg("R", 206, 322),
                _deco_sleeping(), "0", True)
    # default idle
    return _pose("idle")


def _bubble(line):
    lines = wrap_text(line, width=13, max_lines=4)
    n = len(lines)
    bw = 198
    bh = 30 + n * 24
    bx = 262
    by = 70
    cx = bx + bw // 2
    texts = ""
    start = by + 26
    for i, ln in enumerate(lines):
        y = start + i * 24
        texts += (f'<text x="{cx}" y="{y}" font-family="{esc(FONT)}" font-size="16" font-weight="600" '
                  f'fill="{SCREEN}" text-anchor="middle">{esc(ln)}</text>')
    tail = (f'<path d="M{bx+10} {by+bh-14} L{bx-14} {by+bh+6} L{bx+30} {by+bh-2} Z" fill="{TEXT_LT}" '
            f'stroke="{OUTLINE}" stroke-width="2" stroke-linejoin="round"/>')
    return (
        f'<g id="bubble">'
        f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="16" fill="{TEXT_LT}" stroke="{OUTLINE}" stroke-width="2"/>'
        f'{tail}{texts}</g>'
    )


def render_svg(action="idle", line="Hello!", accent=None, theme="dark"):
    _apply_theme(theme)
    action = action if action in ACTIONS else "idle"
    head, icon, body_accent, arms, legs, deco, tilt, sleepy = _pose(action)
    ac = accent or body_accent
    floaty = "" if sleepy else (
        '<animateTransform attributeName="transform" type="translate" '
        'values="0 0;0 -5;0 0" dur="3.2s" repeatCount="indefinite" additive="sum"/>'
    )
    robot = (
        f'<g id="robot">'
        f'<g transform="rotate({tilt} 180 300)">'
        f'<g>{floaty}'
        f'{_shadow()}'
        f'{head}'
        f'{_body(icon, ac)}'
        f'{arms}'
        f'{legs}'
        f'</g></g></g>'
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{esc(FONT)}">',
        _stage(),
        deco,
        robot,
        _bubble(line),
        f'<text x="{W-14}" y="{H-12}" font-family="{esc(MONO)}" font-size="11" '
        f'fill="{OUTLINE}" opacity="0.5" text-anchor="end">Zewang&apos;s bot · {esc(action)}</text>',
        '</svg>',
    ]
    return "\n".join(parts)


def _preview_svg():
    """Render all 9 actions in both dark and light themes, stacked."""
    themes = ["dark", "light"]
    cols = len(themes) * 3
    cw, ch = W, H
    rows = (len(ACTIONS) + 2) // 3          # 3 rows per theme band
    pad = 16
    band_h = rows * ch + (rows + 1) * pad
    pw = cols * cw + (cols + 1) * pad
    ph = band_h * 2 + pad * 3
    cells = []
    for band, theme in enumerate(themes):
        yoff = pad + band * (band_h + pad)
        for i, a in enumerate(ACTIONS):
            r, c = divmod(i, 3)
            x = pad + (c + band * 3) * (cw + pad)
            y = yoff + pad + r * (ch + pad)
            inner = render_svg(a, f"{a} · {theme}", theme=theme)
            inner = inner.split(">", 1)[1].rsplit("</svg>", 1)[0]
            cells.append(f'<g transform="translate({x} {y})">{inner}</g>')
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{pw}" height="{ph}" '
            f'viewBox="0 0 {pw} {ph}" font-family="{esc(FONT)}">'
            f'<rect width="{pw}" height="{ph}" fill="#0d1117"/>')
    return "\n".join([head] + cells + ["</svg>"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--action", default="idle", choices=ACTIONS)
    ap.add_argument("--line", default="Hello!")
    ap.add_argument("--theme", default="dark", choices=["dark", "light"])
    ap.add_argument("-o", "--out", default="robot.svg")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    svg = _preview_svg() if args.preview else render_svg(args.action, args.line, theme=args.theme)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {args.out} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
