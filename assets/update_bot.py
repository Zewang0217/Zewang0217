#!/usr/bin/env python3
"""Self-updating profile bot.

Pipeline: fetch recent public GitHub activity -> ask an LLM (OpenAI-compatible
chat/completions) to pick a pose and write a one-liner -> render the robot SVG
-> refresh the README timestamp block. Pure stdlib, no dependencies.

Env:
  LLM_API_KEY   absent => skip LLM, use rule-based fallback
  LLM_BASE_URL  default https://api.openai.com/v1
  LLM_MODEL     default gpt-4o-mini
  GH_USERNAME   default Zewang0217
  GH_TOKEN      optional, raises events API rate limit
"""
import importlib.util
import json
import os
import random
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = Path(__file__).resolve().parent
USERNAME = os.environ.get("GH_USERNAME", "Zewang0217")
TZ = timezone(timedelta(hours=8))  # Asia/Shanghai
ACTIONS = ["idle", "wave", "coding", "thinking", "running",
           "celebrating", "building", "ship", "sleeping"]

BOT_BEGIN = "<!--BOT_META-->"
BOT_END = "<!--ENDBOT-->"

SYSTEM = """你是 Zewang（GitHub: Zewang0217）个人主页里住着的一个小机器人 agent。
根据主人最近的 GitHub 活动，挑一个最贴切的"动作"，并写一句它会对访客说的话。

主人人设：大三在读，主攻 AI Agent / 全栈，信奉"优雅 > 复杂、逻辑 > 补丁"，中文，带一点极客幽默。
只能从这些动作里选一个：idle / wave / coding / thinking / running / celebrating / building / ship / sleeping。
动作含义：idle=待机 wave=打招呼 coding=写代码 thinking=思考 running=乱跑/多线程忙碌
celebrating=庆祝 building=搭新东西 ship=发布上线 sleeping=深夜该睡了。

要求：
- 台词不超过 40 个字，中文，有性格（可以是机器人第一人称，也可以替主人念叨）。
- 不要说"我是 AI/作为AI"；不要堆感叹号；不要喊口号。
- 若当前是深夜（23:00~6:00 北京时间），优先 sleeping。
- 只输出一行 JSON，不要 markdown 代码块： {"action": "...", "line": "..."}"""

FALLBACK = {
    "idle": ["待机中，摸鱼也是一种效率。", "等下一个灵感自己掉下来。", "今天也是平静的一天。"],
    "wave": ["嗨，欢迎来我主页逛逛。", "你来啦，随便看看。", "嘿，看到你了。"],
    "coding": ["正在和一个奇怪的 bug 对线。", "刚把召回延迟压下去一点，爽。", "键盘冒烟中，请勿打扰。", "又在重构，这次真的是最后一次。"],
    "thinking": ["让我想想…这个抽象是不是有点过度了。", "纠结一个命名已经半小时了。", "理论上能跑。理论上。"],
    "running": ["同时在三件事上反复横跳。", "今天的事项列表长得像论文。", "跑是跑起来了，但不知道跑去哪。"],
    "celebrating": ["终于把那个坑填上了！", "又上线了一个小玩意，耶。", "从第一个 commit 到闭环，成了。"],
    "building": ["在搭一个新模块，还没敢跑。", "从零开始最上头。", "砌砖中，进度 1%。"],
    "ship": ["刚部署完，心里有点慌。", "上线了，希望今晚不用回滚。", "发布了，快去试试！"],
    "sleeping": ["深夜了，该睡了，bug 交给明天的我。", "zZ… 代码不会自己跑掉。", "先睡为敬。"],
}


def now():
    return datetime.now(TZ)


def log(msg):
    print(f"[bot] {msg}", file=sys.stderr)


def fetch_activity():
    url = f"https://api.github.com/users/{USERNAME}/events/public?per_page=30"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-bot",
    })
    token = os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            events = json.load(r)
    except Exception as e:
        return f"(拉取活动失败: {e})"
    msgs = []
    for ev in events:
        t = ev.get("type")
        repo = ev.get("repo", {}).get("name", "")
        if t == "PushEvent":
            for c in (ev.get("payload", {}).get("commits") or [])[:2]:
                m = (c.get("message") or "").splitlines()[0][:60]
                if m:
                    msgs.append(f"- [{repo}] push: {m}")
        elif t == "PullRequestEvent":
            msgs.append(f"- [{repo}] PR: {ev.get('payload',{}).get('action','')}")
        elif t == "ReleaseEvent":
            msgs.append(f"- [{repo}] release")
        elif t == "CreateEvent":
            msgs.append(f"- [{repo}] create {ev.get('payload',{}).get('ref_type','')}")
        if len(msgs) >= 8:
            break
    return "\n".join(msgs) if msgs else "(最近没有公开活动)"


def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except Exception:
        return None
    action = obj.get("action", "idle")
    if action not in ACTIONS:
        action = "idle"
    line = (obj.get("line") or "").strip().replace("\n", " ")
    if not line:
        return None
    return action, line[:60]


def ask_llm(activity):
    key = os.environ.get("LLM_API_KEY")
    if not key:
        log("no LLM_API_KEY -> fallback")
        return None
    base = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    n = now()
    user = (f"当前北京时间 {n:%Y-%m-%d %H:%M} (周{'一二三四五六日'[n.weekday()]})。\n"
            f"最近活动:\n{activity}\n请输出 JSON。")
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": user}],
        "temperature": 0.85,
        "max_tokens": 140,
    }).encode()
    req = urllib.request.Request(f"{base}/chat/completions", data=body, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": "profile-bot",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        text = data["choices"][0]["message"]["content"]
    except Exception as e:
        log(f"LLM call failed: {e}")
        return None
    res = parse_json(text)
    if not res:
        log(f"LLM output unparseable: {text[:120]}")
    return res


def fallback():
    h = now().hour
    if h >= 23 or h < 6:
        action = "sleeping"
    elif h in (9, 10, 11, 14, 15, 16):
        action = random.choices(["coding", "building", "thinking"], weights=[5, 2, 2])[0]
    elif h in (19, 20, 21):
        action = random.choice(["running", "ship", "coding"])
    else:
        action = random.choice(ACTIONS[:8])
    return action, random.choice(FALLBACK[action])


def load_robot():
    spec = importlib.util.spec_from_file_location("robot", ASSETS / "robot.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def update_readme(robot, action, line):
    # render both themes so <picture> can auto-switch in GitHub dark/light mode
    svg_dark = robot.render_svg(action, line, theme="dark")
    svg_light = robot.render_svg(action, line, theme="light")
    (ASSETS / "robot.svg").write_text(svg_dark, encoding="utf-8")
    (ASSETS / "robot-light.svg").write_text(svg_light, encoding="utf-8")
    readme = ROOT / "README.md"
    txt = readme.read_text(encoding="utf-8")
    ts = now().strftime("%Y-%m-%d %H:%M")
    block = (f'{BOT_BEGIN}\n'
             f'<p align="center"><sub>🤖 上次自主思考 · {ts} (UTC+8) · '
             f'状态: <code>{action}</code></sub></p>\n{BOT_END}')
    if BOT_BEGIN in txt and BOT_END in txt:
        txt = re.sub(re.escape(BOT_BEGIN) + r".*?" + re.escape(BOT_END),
                     lambda _: block, txt, flags=re.S)
    else:
        txt = txt.rstrip() + "\n\n" + block + "\n"
    readme.write_text(txt, encoding="utf-8")
    return len(svg_dark)


def main():
    robot = load_robot()
    activity = fetch_activity()
    log(f"activity:\n{activity}")
    res = ask_llm(activity) or fallback()
    action, line = res
    n = update_readme(robot, action, line)
    log(f"done: action={action} line={line!r} svg={n}B")


if __name__ == "__main__":
    main()
