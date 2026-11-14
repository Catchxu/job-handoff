#!/usr/bin/env python3
"""Generate the README diagrams.

    python3 assets/make_diagrams.py

Writes banner.svg plus flow-<lang>-<theme>.svg and layers-<lang>-<theme>.svg
next to this file. Edit the TEXT table to change wording; both languages and
both themes are drawn from the same layout.
"""
from pathlib import Path

OUT = Path(__file__).parent
SANS = ('-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, '
        '"PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif')
MONO = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'

THEMES = {
    "light": dict(fg="#1f2328", muted="#59636e", line="#d1d9e0", card="#ffffff", life="#afb8c1",
                  blue="#0969da", purple="#8250df", green="#1a7f37", soft=0.07, chip="#eff2f5"),
    "dark": dict(fg="#f0f6fc", muted="#9198a1", line="#3d444d", card="#0d1117", life="#484f58",
                 blue="#4493f8", purple="#ab7df8", green="#3fb950", soft=0.13, chip="#212830"),
}

TEXT = {
    "en": dict(
        lanes=[("Your laptop", "agent + handoff"),
               ("Watch host", "the compute host, or a relay"),
               ("Compute host", "SSH server or SLURM")],
        job_start="Job starts, detached",
        watcher="Watcher starts",
        closed="Laptop closed",
        closed_sub="nothing runs here",
        l1_tag="LAYER 1 · HANDOFF",
        follow="follows the job until it ends",
        playbook="runs your playbook",
        followup="Follow-up run",
        l2_tag="LAYER 2 · WAKE · opt-in",
        wake="Agent wakes, writes a report",
        act="act mode: may request a run",
        back="Report + results",
        takeover="you take over again",
        layers=[
            dict(tag="LAYER 1", badge="default", title="Handoff",
                 sub="A small watcher script. No AI runs.",
                 rows=["The job survives the closed laptop",
                       "Notes and state let any session resume",
                       "Your playbook handles what you foresaw",
                       "One command returns report and results"],
                 needs="Needs SSH access to the compute host"),
            dict(tag="LAYER 2", badge="opt-in", title="Wake",
                 sub="Judgment for what you did not foresee.",
                 rows=["Everything in Layer 1",
                       "An agent wakes when the job chain ends",
                       "report mode: reads the logs, writes a report",
                       "act mode: inspects, requests a follow-up run"],
                 needs="Needs Claude Code or Codex on the watch host"),
        ],
    ),
    "zh": dict(
        lanes=[("你的电脑", "agent + handoff"),
               ("守望机", "计算服务器本身，或一台中转机"),
               ("计算服务器", "SSH 服务器或 SLURM")],
        job_start="任务脱离终端启动",
        watcher="守望脚本启动",
        closed="电脑合上",
        closed_sub="这里什么都不运行",
        l1_tag="第一层 · 交接",
        follow="跟踪任务直到结束",
        playbook="执行你的预案",
        followup="再跑一轮",
        l2_tag="第二层 · 唤醒 · 需主动开启",
        wake="唤醒 agent，写报告",
        act="act 模式：可申请再跑一轮",
        back="报告 + 结果",
        takeover="你重新接手",
        layers=[
            dict(tag="第一层", badge="默认开启", title="交接",
                 sub="一个很小的守望脚本，没有 AI。",
                 rows=["合上电脑，任务照常运行",
                       "交接说明和状态让任何会话都能接上",
                       "预案处理你预见到的情况",
                       "回来一条命令拿到报告和结果"],
                 needs="需要：能 SSH 登录计算服务器"),
            dict(tag="第二层", badge="需主动开启", title="唤醒",
                 sub="应对你没预见到的情况。",
                 rows=["包含第一层的全部功能",
                       "任务链结束时唤醒一个 agent",
                       "report 模式：读日志，写报告",
                       "act 模式：查看服务器，申请再跑一轮"],
                 needs="需要：守望机上装有 Claude Code 或 Codex"),
        ],
    ),
}

ICONS = {
    "laptop": '<rect x="4" y="5" width="16" height="11" rx="1.5"/><path d="M2 19.5h20"/>',
    "eye": '<path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="2.8"/>',
    "server": '<rect x="3" y="4" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><path d="M7 7.5h.01M7 16.5h.01"/>',
    "moon": '<path d="M20.5 14.2A8.5 8.5 0 1 1 9.8 3.5a6.8 6.8 0 0 0 10.7 10.7z"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
}


def icon(name, x, y, color, size=24, width=1.8):
    s = size / 24
    return (f'<g transform="translate({x},{y}) scale({s})" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')


def text(x, y, s, size=15, fill="#000", weight=400, anchor="middle", font=SANS, spacing=0):
    extra = f' letter-spacing="{spacing}"' if spacing else ""
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return (f'<text x="{x}" y="{y}" font-family=\'{font}\' font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{extra}>{s}</text>')


def width_of(s, size, latin=0.52):
    """Rough rendered width: CJK glyphs are one em, the rest about half an em."""
    return sum(size if ord(c) > 0x2E7F else size * latin for c in s)


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            + "".join(body) + "</svg>\n")


def tag(x, y, label, color):
    """Solid pill with white small-caps text; x is the left edge, y the centre."""
    w = width_of(label, 12, 0.66) + 12 * 0.08 * len(label) + 22
    return (f'<rect x="{x}" y="{y - 11}" width="{w:.0f}" height="22" rx="11" fill="{color}"/>'
            + text(x + w / 2, y + 4.2, label, 12, "#ffffff", 700, spacing="0.08em"))


# --------------------------------------------------------------------- flow

def flow(lang, theme):
    t, c = TEXT[lang], THEMES[theme]
    W, H = 1000, 668
    X = [165, 500, 835]
    b = [f'<defs>' + "".join(
        f'<marker id="a-{k}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7.5" markerHeight="7.5" '
        f'orient="auto-start-reverse"><path d="M1 1.5L8.5 5L1 8.5" fill="none" stroke="{c[k]}" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></marker>'
        for k in ("fg", "muted", "blue", "purple")) + "</defs>"]

    def arrow(x1, x2, y, color="fg", dashed=False, both=False):
        dash = ' stroke-dasharray="5 5"' if dashed else ""
        start = f' marker-start="url(#a-{color})"' if both else ""
        return (f'<path d="M{x1} {y}H{x2}" stroke="{c[color]}" stroke-width="1.8" fill="none"'
                f'{dash}{start} marker-end="url(#a-{color})"/>')

    def card(cx, cy, label, color="line", w=230, h=40, dot=None):
        out = (f'<rect x="{cx - w / 2}" y="{cy - h / 2}" width="{w}" height="{h}" rx="10" '
               f'fill="{c["card"]}" stroke="{c[color]}" stroke-width="1.5"/>')
        tx = cx
        if dot:
            lw = width_of(label, 14.5)
            out += f'<circle cx="{cx - lw / 2 - 4}" cy="{cy}" r="4.5" fill="{c[dot]}"/>'
            tx = cx + 7
        return out + text(tx, cy + 5, label, 14.5, c["fg"], 600)

    def chip(cx, cy, label):
        w = len(label) * 13.5 * 0.61 + 20
        return (f'<rect x="{cx - w / 2:.0f}" y="{cy - 13}" width="{w:.0f}" height="26" rx="6" '
                f'fill="{c["chip"]}" stroke="{c["line"]}"/>'
                + text(cx, cy + 4.6, label, 13.5, c["fg"], 600, font=MONO))

    def band(y1, y2, color):
        return (f'<rect x="345" y="{y1}" width="635" height="{y2 - y1}" rx="14" fill="{c[color]}" '
                f'fill-opacity="{c["soft"]}" stroke="{c[color]}" stroke-opacity="0.45" stroke-width="1.2"/>')

    # bands sit behind everything else
    b.append(band(252, 418, "blue"))
    b.append(band(446, 530, "purple"))

    # lifelines; the laptop's is interrupted by the "closed" block
    for x, (y1, y2) in ((X[0], (96, 236)), (X[0], (538, H - 18)), (X[1], (96, H - 18)), (X[2], (96, H - 18))):
        b.append(f'<path d="M{x} {y1}V{y2}" stroke="{c["life"]}" stroke-width="1.5" stroke-dasharray="2 6" '
                 f'stroke-linecap="round"/>')

    b.append(tag(363, 252, t["l1_tag"], c["blue"]))
    b.append(tag(363, 446, t["l2_tag"], c["purple"]))

    # lane headers
    for x, (title, sub), ic in zip(X, t["lanes"], ("laptop", "eye", "server")):
        b.append(f'<rect x="{x - 150}" y="18" width="300" height="78" rx="14" fill="{c["card"]}" '
                 f'stroke="{c["line"]}" stroke-width="1.5"/>')
        tw = max(width_of(title, 17), width_of(sub, 13))
        left = x - (tw + 40) / 2
        b.append(icon(ic, left, 43, c["blue"], 28))
        b.append(text(left + 40, 53, title, 17, c["fg"], 700, "start"))
        b.append(text(left + 40, 74, sub, 13, c["muted"], 400, "start"))

    mid = (X[0] + X[1]) / 2
    chip_x = X[0] + 112

    # 1. launch
    b.append(arrow(X[0], X[2] - 119, 140))
    b.append(chip(chip_x, 140 - 20, "handoff launch"))
    b.append(card(X[2], 140, t["job_start"], dot="green"))

    # 2. leave
    b.append(arrow(X[0], X[1] - 119, 206))
    b.append(chip(chip_x, 206 - 20, "handoff leave"))
    b.append(card(X[1], 206, t["watcher"]))

    # laptop closed
    b.append(f'<rect x="55" y="244" width="220" height="286" rx="14" fill="{c["muted"]}" fill-opacity="{c["soft"]}" '
             f'stroke="{c["life"]}" stroke-width="1.5" stroke-dasharray="6 6"/>')
    b.append(icon("moon", X[0] - 17, 334, c["muted"], 34, 1.6))
    b.append(text(X[0], 398, t["closed"], 16, c["fg"], 700))
    b.append(text(X[0], 420, t["closed_sub"], 13, c["muted"]))

    # layer 1
    gap = (X[1] + X[2]) / 2
    b.append(arrow(X[1] + 6, X[2] - 6, 312, "blue", dashed=True, both=True))
    b.append(text(gap, 312 - 11, t["follow"], 14, c["fg"], 500))
    b.append(arrow(X[1] + 6, X[2] - 119, 378, "blue"))
    b.append(text((X[1] + X[2] - 115) / 2, 378 - 11, t["playbook"], 14, c["fg"], 500))
    b.append(card(X[2], 378, t["followup"], "blue"))
    for y in (312, 378):
        b.append(f'<circle cx="{X[1]}" cy="{y}" r="4.5" fill="{c["blue"]}"/>')
    b.append(f'<circle cx="{X[2]}" cy="312" r="4.5" fill="{c["blue"]}"/>')

    # layer 2
    b.append(card(X[1], 492, t["wake"], "purple", w=236))
    b.append(arrow(X[1] + 124, X[2] - 6, 492, "purple", dashed=True))
    b.append(text((X[1] + 124 + X[2]) / 2, 492 - 12, t["act"], 13, c["muted"], 500))
    b.append(f'<circle cx="{X[2]}" cy="492" r="4.5" fill="{c["purple"]}"/>')

    # back
    b.append(arrow(X[0], X[1] - 119, 582))
    b.append(chip(chip_x, 582 - 20, "handoff back"))
    b.append(card(X[1], 582, t["back"], dot="green"))
    b.append(arrow(X[1] - 6, X[0] + 6, 630, "muted", dashed=True))
    b.append(text(mid, 630 - 11, t["takeover"], 14, c["muted"], 500))
    for y in (140, 206, 582):
        b.append(f'<circle cx="{X[0]}" cy="{y}" r="4.5" fill="{c["fg"]}"/>')
    return svg(W, H, b)


# ------------------------------------------------------------------- layers

def layers(lang, theme):
    t, c = TEXT[lang], THEMES[theme]
    W, H = 1000, 368
    b = []
    for i, (layer, color) in enumerate(zip(t["layers"], ("blue", "purple"))):
        x = 16 + i * 508
        w = 460
        b.append(f'<rect x="{x}" y="14" width="{w}" height="{H - 28}" rx="18" fill="{c[color]}" '
                 f'fill-opacity="{c["soft"]}" stroke="{c[color]}" stroke-opacity="0.5" stroke-width="1.4"/>')
        b.append(tag(x + 28, 52, layer["tag"], c[color]))
        bw = width_of(layer["badge"], 12.5) + 22
        b.append(f'<rect x="{x + w - 28 - bw:.0f}" y="41" width="{bw:.0f}" height="22" rx="11" fill="none" '
                 f'stroke="{c[color]}" stroke-width="1.2"/>')
        b.append(text(x + w - 28 - bw / 2, 56.4, layer["badge"], 12.5, c[color], 600))
        b.append(text(x + 28, 104, layer["title"], 27, c["fg"], 700, "start"))
        b.append(text(x + 28, 131, layer["sub"], 14.5, c["muted"], 400, "start"))
        b.append(f'<path d="M{x + 28} 152H{x + w - 28}" stroke="{c[color]}" stroke-opacity="0.3"/>')
        for k, row in enumerate(layer["rows"]):
            y = 184 + k * 33
            b.append(icon("check", x + 28, y - 16, c[color], 20, 2.4))
            b.append(text(x + 58, y, row, 15, c["fg"], 500, "start"))
        b.append(text(x + 28, H - 38, layer["needs"], 13, c["muted"], 500, "start"))
    # plus sign between the cards
    cx, cy = W / 2, H / 2
    b.append(f'<circle cx="{cx}" cy="{cy}" r="17" fill="{c["card"]}" stroke="{c["line"]}" stroke-width="1.5"/>')
    b.append(f'<path d="M{cx - 7} {cy}h14M{cx} {cy - 7}v14" stroke="{c["muted"]}" stroke-width="2" stroke-linecap="round"/>')
    return svg(W, H, b)


# ------------------------------------------------------------------- banner

def banner():
    W, H = 1000, 250
    white = "#ffffff"
    b = [
        '<defs>'
        '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#0b2a6f"/><stop offset="0.55" stop-color="#3b3fd1"/>'
        '<stop offset="1" stop-color="#7c3aed"/></linearGradient>'
        '<radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">'
        '<stop offset="0" stop-color="#ffffff" stop-opacity="0.22"/>'
        '<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>'
        '<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
        '<circle cx="2" cy="2" r="1.1" fill="#ffffff" fill-opacity="0.10"/></pattern>'
        '<clipPath id="clip"><rect width="1000" height="250" rx="22"/></clipPath>'
        '</defs>',
        '<g clip-path="url(#clip)">',
        f'<rect width="{W}" height="{H}" fill="url(#g)"/>',
        f'<rect width="{W}" height="{H}" fill="url(#dots)"/>',
        '<circle cx="840" cy="30" r="230" fill="url(#glow)"/>',
        '<circle cx="130" cy="260" r="200" fill="url(#glow)"/>',
        '</g>',
    ]
    # laptop -> server, a baton travelling along the dotted path
    y = 62
    b.append(icon("laptop", 352, y, white, 56, 1.5))
    b.append(icon("moon", 398, y - 16, white, 20, 2))
    b.append(icon("server", 592, y, white, 56, 1.5))
    b.append(f'<path d="M424 {y + 30}H576" stroke="{white}" stroke-opacity="0.75" stroke-width="2.4" '
             f'stroke-dasharray="1 9" stroke-linecap="round"/>')
    b.append(f'<path d="M566 {y + 23}l9 7l-9 7" fill="none" stroke="{white}" stroke-width="2.4" '
             f'stroke-linecap="round" stroke-linejoin="round"/>')
    b.append(f'<circle cx="500" cy="{y + 30}" r="7" fill="{white}"/>')
    b.append(f'<circle cx="652" cy="{y + 2}" r="5" fill="#4ade80"/>')
    b.append(text(W / 2, 190, "job-handoff", 50, white, 700, font=MONO, spacing="-0.01em"))
    return svg(W, H, b)


if __name__ == "__main__":
    (OUT / "banner.svg").write_text(banner(), encoding="utf-8")
    for lang in TEXT:
        for theme in THEMES:
            (OUT / f"flow-{lang}-{theme}.svg").write_text(flow(lang, theme), encoding="utf-8")
            (OUT / f"layers-{lang}-{theme}.svg").write_text(layers(lang, theme), encoding="utf-8")
    print("wrote", len(list(OUT.glob("*.svg"))), "svg files to", OUT)
