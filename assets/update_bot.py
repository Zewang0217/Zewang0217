#!/usr/bin/env python3
"""Self-updating profile bot.

Pipeline: fetch recent GitHub activity + Hacker News headlines -> ask an LLM
(OpenAI-compatible chat/completions) to pick a pose and write a witty one-liner
-> render the robot SVG -> refresh the README timestamp block. Pure stdlib.

LLM 不可用或没 key 时,退回语料库 / HN 标题兜底。

Env:
  LLM_API_KEY   absent => skip LLM, use fallback corpus
  LLM_BASE_URL  default https://api.deepseek.com
  LLM_MODEL     default deepseek-v4-flash
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
根据主人最近的 GitHub 活动 + 你刚刷到的 Hacker News 热榜，挑一个最贴切的"动作"，
并写一句它会对访客说的话。

主人人设：大三在读，主攻 AI Agent / 全栈，信奉"优雅 > 复杂、逻辑 > 补丁"，中文，
带一点极客幽默。说话是程序员冷笑话那种：一本正经地吐槽，不尬笑、不喊口号、不油腻。

动作只能选：idle / wave / coding / thinking / running / celebrating / building / ship / sleeping。
含义：idle=待机 wave=打招呼 coding=写代码 thinking=思考 running=乱跑/多线程忙碌
celebrating=庆祝 building=搭新东西 ship=发布上线 sleeping=深夜该睡了。

怎么把台词说"有意思"：
- 如果"新闻/活动"里有料（大模型发布、GitHub 整活、神 bug、离谱提案……），拿它开刀，
  角度要刁钻：可以吐槽、可以捧、可以一本正经讲歪理，但必须扣住那条具体的事，别写
  "AI 真厉害"这种正确的废话。不确定的细节别编，就调侃标题本身。
- 如果没料，就吐槽主人的活动，或讲程序员日常的黑色幽默。宁可自嘲，不要客套。
- 用"机器人第一人称"或者"替主人念叨"都行，像主页上的活人，不像客服。
- 句子要有画面或反转；避免"今天也要加油鸭"式空话。

硬约束：
- 整句 ≤ 44 个字符（渲染会截断），中文为主。
- 不要说"我是 AI/作为 AI/语言模型"；别堆感叹号；别喊口号。
- 深夜（23:00~6:00 北京时间）优先 sleeping。
- 只输出一行 JSON，不要 markdown 代码块： {"action": "...", "line": "..."}"""


FALLBACK = {
    "idle": [
        "待机中，摸鱼也是一种效率。",
        "等灵感自己掉下来，像等 CI 变绿。",
        "今天也是平静的一天，除了隔壁在烧核弹。",
        "没有新消息，说明 bug 还没发现我。",
    ],
    "wave": [
        "嗨，你也是来 GitHub 摸鱼的吗？",
        "来都来了，star 一个再走呗。",
        "小心点，这个仓库的主人在看着你。",
        "欢迎参观，唯一在运行的东西是我。",
    ],
    "coding": [
        "正在和一个神秘的 bug 对线，它说我这边没问题。",
        "刚把召回延迟压下去一点，爽，像拆了颗雷。",
        "键盘冒烟中。注释欠的债，都是要还的。",
        "这次重构绝对是最后一次了。上次我也是这么说的。",
        "删除线 > 新增线，删代码才是真重构。",
    ],
    "thinking": [
        "让我想想…这个抽象是不是有点过度了。",
        "纠结命名半小时了。变量一时爽，重构火葬场。",
        "理论上能跑。理论上的问题不大。",
        "为什么睡前总想起三年前没修的 TODO。",
    ],
    "running": [
        "同时在三件事上反复横跳，多线程本线。",
        "今天的事项列表长得像论文，还是没结论那种。",
        "跑是跑起来了，但不知道跑去哪，像我的 side project。",
        "忙到把 coffee 拼成 coffe，还 commit 了。",
    ],
    "celebrating": [
        "终于把那个坑填上了！填坑一时爽，一直填坑一直爽。",
        "我的 PR 合并了，代码终于找到新家了。",
        "从第一个 commit 到闭环，成了，今晚加鸡腿。",
        "CI 绿了。这一刻的幸福感仅次于发工资。",
    ],
    "building": [
        "在搭一个新模块，还没敢跑，怕一跑就露馅。",
        "从零开始最上头，像打开一个新世界的作弊器。",
        "砌砖中，进度 1%。这 1% 是 README。",
    ],
    "ship": [
        "刚部署完，心里有点慌，希望今晚不用回滚。",
        "上线了。现在压力来到了监控大屏这边。",
        "发布了！如果崩了，那一定是用户姿势不对。",
    ],
    "sleeping": [
        "深夜了，该睡了。bug 交给明天的我，他会感谢现在的我。",
        "zZ… 梦里还在给变量取名。",
        "先睡为敬。今天的 bug 就当我没看见。",
    ],
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


def fetch_hacker_news(n=3):
    """Fresh headlines from Hacker News (public Firebase API, no key)."""
    try:
        req = urllib.request.Request(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers={"User-Agent": "profile-bot"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            ids = json.load(r)[:30]
    except Exception as e:
        log(f"HN fetch failed: {e}")
        return ""
    titles = []
    for sid in ids:
        try:
            req = urllib.request.Request(
                f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                headers={"User-Agent": "profile-bot"},
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                item = json.load(r)
            if not item or item.get("type") != "story" or item.get("dead"):
                continue
            t = (item.get("title") or "").strip()
            if t:
                titles.append(t[:100])
        except Exception:
            continue
        if len(titles) >= n:
            break
    return "\n".join(f"- {t}" for t in titles)


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


def ask_llm(activity, news=""):
    key = os.environ.get("LLM_API_KEY")
    if not key:
        log("no LLM_API_KEY -> fallback")
        return None
    base = (os.environ.get("LLM_BASE_URL") or "https://api.deepseek.com").rstrip("/")
    model = os.environ.get("LLM_MODEL") or "deepseek-v4-flash"
    n = now()
    user = (f"当前北京时间 {n:%Y-%m-%d %H:%M} (周{'一二三四五六日'[n.weekday()]})。\n"
            f"最近活动:\n{activity}\n"
            f"Hacker News 头条:\n{news or '(没刷到,空)'}\n"
            f"请输出 JSON。")
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": user}],
        "temperature": 0.9,
        "max_tokens": 160,
        "response_format": {"type": "json_object"},
    }
    # DeepSeek V4 默认开 thinking 推理;一句台词用不上,关掉省 token 并让 temperature 生效
    if "deepseek" in model:
        payload["thinking"] = {"type": "disabled"}
    body = json.dumps(payload).encode()
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
    news = fetch_hacker_news(3)
    if news:
        log(f"hacker news:\n{news}")
    res = ask_llm(activity, news) or fallback()
    action, line = res
    n = update_readme(robot, action, line)
    log(f"done: action={action} line={line!r} svg={n}B")


if __name__ == "__main__":
    main()
