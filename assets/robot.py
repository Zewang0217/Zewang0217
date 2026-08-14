#!/usr/bin/env python3
"""Developer illustration + speech bubble for the self-updating profile.

Based on a ctrlv.design CC0 SVG (developer with headphones + laptop).
Converted: CSS animations → SMIL (GitHub <img> only supports inline SMIL),
indigo/rose palette → Nord. The agent's one-liner rides in a speech bubble.

    python robot.py --action coding --line "重构中..." -o robot.svg
    python robot.py --preview
"""
import argparse
import html

# ---- Nord palettes ----
NORD = {
    "dark": {
        "body":  "#5E81AC",   "head":  "#81A1C1",   "phone": "#4C566A",
        "cup":   "#88C0D0",   "laptop":"#4C566A",   "screen":"#2E3440",
        "base":  "#3B4252",   "code":  "#88C0D0",   "data":  "#5E81AC",
        "shadow":"#2E3440",   "bubble_bg":"#2E3440","bubble_bd":"#88C0D0",
        "text":  "#ECEFF4",   "subtext":"#81A1C1",
    },
    "light": {
        "body":  "#5E81AC",   "head":  "#81A1C1",   "phone": "#4C566A",
        "cup":   "#5E81AC",   "laptop":"#4C566A",   "screen":"#ECEFF4",
        "base":  "#81A1C1",   "code":  "#5E81AC",   "data":  "#81A1C1",
        "shadow":"#D8DEE9",   "bubble_bg":"#ECEFF4","bubble_bd":"#5E81AC",
        "text":  "#2E3440",   "subtext":"#4C566A",
    },
}

# action → bubble accent + prompt hint
PROMPTS = {
    "idle":        ("standby",          "#A3BE8C"),
    "wave":        ("hello --visitor",  "#EBCB8B"),
    "coding":      ("code --watch",     "#A3BE8C"),
    "thinking":    ("reason --deep",    "#B48EAD"),
    "running":     ("tasks --parallel", "#D08770"),
    "celebrating": ("ship --success",   "#EBCB8B"),
    "building":    ("scaffold --new",   "#5E81AC"),
    "ship":        ("release --prod",   "#A3BE8C"),
    "sleeping":    ("sleep 28800",      "#81A1C1"),
}
ACTIONS = list(PROMPTS.keys())

W, H = 440, 380
FONT = "ui-sans-serif, system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif"
MONO = "ui-monospace, 'JetBrains Mono', 'Cascadia Code', Consolas, monospace"


def esc(s):
    return html.escape(str(s), quote=True)


def wrap_text(text, width=22, max_lines=3):
    text = (text or "").replace("\r", "").strip()
    lines, cur, w = [], "", 0
    for ch in text:
        cw = 2 if ord(ch) > 0x2E80 else 1
        if ch == "\n":
            lines.append(cur); cur = ""; w = 0
            continue
        if w + cw > width and cur:
            lines.append(cur); cur = ch; w = cw
        else:
            cur += ch; w += cw
        if len(lines) >= max_lines:
            return lines[:max_lines]
    if cur:
        lines.append(cur)
    return lines or ["…"]


def _developer(action, line, theme="dark"):
    c = NORD.get(theme, NORD["dark"])
    hint, accent = PROMPTS.get(action, PROMPTS["idle"])

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" font-family="{esc(FONT)}">']

    # ---- speech bubble (top area) ----
    lines = wrap_text(line, width=22, max_lines=3)
    bw, bx, by = 380, 30, 16
    bh = 28 + len(lines) * 22
    cx = bx + bw // 2
    parts.append(f'<g id="bubble">')
    parts.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="14" '
                 f'fill="{c["bubble_bg"]}" stroke="{c["bubble_bd"]}" stroke-width="1.5" opacity="0.95"/>')
    # prompt line
    parts.append(f'<text x="{bx+14}" y="{by+18}" font-size="11" font-family="{esc(MONO)}" '
                 f'fill="{c["cup"]}" opacity="0.7">$ {esc(hint)}</text>')
    # dialogue lines
    for i, ln in enumerate(lines):
        y = by + 36 + i * 22
        parts.append(f'<text x="{cx}" y="{y}" font-size="14" font-weight="600" '
                     f'fill="{c["text"]}" text-anchor="middle">{esc(ln)}</text>')
    # tail pointing down to character
    parts.append(f'<path d="M{cx-8} {by+bh} L{cx} {by+bh+10} L{cx+8} {by+bh} Z" '
                 f'fill="{c["bubble_bg"]}" stroke="{c["bubble_bd"]}" stroke-width="1.5" '
                 f'stroke-linejoin="round"/>')
    # blinking cursor after last line
    last_y = by + 36 + (len(lines) - 1) * 22
    parts.append(f'<rect x="{cx+50}" y="{last_y-11}" width="8" height="14" rx="2" '
                 f'fill="{accent}">'
                 f'<animate attributeName="opacity" values="1;0.1;1" dur="1.1s" repeatCount="indefinite"/>'
                 f'</rect>')
    parts.append(f'</g>')

    # ---- illustration (bottom area, offset down for bubble) ----
    oy = 90  # vertical offset: push illustration below bubble
    parts.append(f'<g transform="translate(20 {oy})">')

    # shadow
    parts.append(f'<ellipse cx="200" cy="270" rx="130" ry="8" fill="{c["shadow"]}" opacity="0.4"/>')

    # background data matrix (anim-data: pulsing)
    parts.append(f'<g opacity="0.12" font-family="{esc(MONO)}" font-size="18" font-weight="bold" fill="{c["data"]}">'
                 f'<text x="60" y="70">10110</text>'
                 f'<text x="250" y="90">01001</text>'
                 f'<text x="100" y="150">110</text>'
                 f'<animate attributeName="opacity" values="0.06;0.18;0.06" dur="4s" repeatCount="indefinite"/>'
                 f'</g>')

    # character (anim-float: gentle bob)
    parts.append(f'<g>'
                 f'<animateTransform attributeName="transform" type="translate" '
                 f'values="0 0;0 -5;0 0" dur="3.5s" repeatCount="indefinite" additive="sum"/>'
                 # body
                 f'<path d="M130 260 C130 160 230 160 230 260 Z" fill="{c["body"]}"/>'
                 # head
                 f'<circle cx="180" cy="110" r="33" fill="{c["head"]}"/>'
                 # headphones band
                 f'<path d="M142 110 C142 72 218 72 218 110" stroke="{c["phone"]}" '
                 f'stroke-width="7" stroke-linecap="round" fill="none"/>'
                 # ear cups (with subtle pulse)
                 f'<rect x="135" y="100" width="10" height="25" rx="5" fill="{c["cup"]}">'
                 f'<animate attributeName="opacity" values="0.8;1;0.8" dur="2s" repeatCount="indefinite"/></rect>'
                 f'<rect x="215" y="100" width="10" height="25" rx="5" fill="{c["cup"]}">'
                 f'<animate attributeName="opacity" values="0.8;1;0.8" dur="2s" repeatCount="indefinite" begin="1s"/></rect>'
                 f'</g>')

    # laptop (anim-bounce + screen glow + code lines)
    parts.append(f'<g>'
                 f'<animateTransform attributeName="transform" type="translate" '
                 f'values="0 0;0 -3;0 0" dur="2.8s" repeatCount="indefinite" additive="sum" begin="0.2s"/>'
                 # screen housing
                 f'<path d="M180 230 H300 L280 160 H200 Z" fill="{c["laptop"]}"/>'
                 # screen (glow pulse)
                 f'<path d="M190 220 H285 L270 170 H210 Z" fill="{c["screen"]}">'
                 f'<animate attributeName="opacity" values="0.85;1;0.85" dur="3s" repeatCount="indefinite"/></path>'
                 # base bar
                 f'<path d="M160 240 H320" stroke="{c["base"]}" stroke-width="7" stroke-linecap="round"/>'
                 # code lines (draw animation: stroke-dashoffset)
                 f'<path d="M215 180 H250" stroke="{c["code"]}" stroke-width="4" stroke-linecap="round" '
                 f'stroke-dasharray="40" stroke-dashoffset="40">'
                 f'<animate attributeName="stroke-dashoffset" values="40;0;40" dur="2.5s" repeatCount="indefinite"/></path>'
                 f'<path d="M210 195 H265" stroke="{c["code"]}" stroke-width="4" stroke-linecap="round" '
                 f'stroke-dasharray="60" stroke-dashoffset="60">'
                 f'<animate attributeName="stroke-dashoffset" values="60;0;60" dur="2.5s" repeatCount="indefinite" begin="0.3s"/></path>'
                 f'<path d="M205 210 H240" stroke="{c["code"]}" stroke-width="4" stroke-linecap="round" '
                 f'stroke-dasharray="40" stroke-dashoffset="40">'
                 f'<animate attributeName="stroke-dashoffset" values="40;0;40" dur="2.5s" repeatCount="indefinite" begin="0.6s"/></path>'
                 f'</g>')

    parts.append(f'</g>')  # close illustration translate

    # ---- status footer ----
    parts.append(f'<g>'
                 f'<circle cx="38" cy="{H-22}" r="4" fill="{accent}">'
                 f'<animate attributeName="opacity" values="0.4;1;0.4" dur="2s" repeatCount="indefinite"/></circle>'
                 f'<text x="50" y="{H-18}" font-size="10" font-family="{esc(MONO)}" fill="{c["subtext"]}" opacity="0.7">'
                 f'{esc(hint)}</text>'
                 f'<text x="{W-14}" y="{H-18}" font-size="10" font-family="{esc(MONO)}" fill="{c["subtext"]}" '
                 f'opacity="0.5" text-anchor="end">auto-sync 4h</text>'
                 f'</g>')

    parts.append('</svg>')
    return "\n".join(parts)


def render_svg(action="idle", line="Hello!", accent=None, theme="dark"):
    return _developer(action, line, theme=theme)


SAMPLES = {
    "idle": "待机中，摸鱼也是一种效率。",
    "wave": "嗨，欢迎来我主页逛逛。",
    "coding": "正在重构，这次真的是最后一次。",
    "thinking": "纠结一个命名已经半小时了。",
    "running": "同时在三件事上反复横跳。",
    "celebrating": "终于把那个坑填上了！",
    "building": "在搭一个新模块，还没敢跑。",
    "ship": "刚部署完，希望今晚不用回滚。",
    "sleeping": "深夜了，bug 交给明天的我。",
}


def _preview_svg():
    cols, pad = 3, 14
    cw, ch = W, H
    rows = (len(ACTIONS) + cols - 1) // cols
    pw = cols * cw + (cols + 1) * pad
    ph = rows * ch + (rows + 1) * pad
    cells = []
    for i, a in enumerate(ACTIONS):
        r, c = divmod(i, cols)
        x = pad + c * (cw + pad)
        y = pad + r * (ch + pad)
        inner = render_svg(a, SAMPLES[a])
        inner = inner.split(">", 1)[1].rsplit("</svg>", 1)[0]
        cells.append(f'<g transform="translate({x} {y})">{inner}</g>')
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{pw}" height="{ph}" '
            f'viewBox="0 0 {pw} {ph}"><rect width="{pw}" height="{ph}" fill="#1a1a2e"/>')
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
