#!/usr/bin/env python3
"""Generate the profile README and its SVG cards.

Every card comes in four variants: desktop and mobile layouts, each in light and dark.
The README picks one with <picture> media queries, so phones get a narrow layout drawn
close to actual size instead of a shrunken desktop card.

Safari notes that shape this file:
- Safari lays out SVG text at its on-screen size, where the system font's letter spacing
  is wider, so a heavily scaled-down card overflows. Hence the mobile layouts, and text
  wrapping that assumes a wide font (SANS_EM).
- Safari rasterises gradient-filled text at low resolution, so it looks blurred. Gradient
  text is drawn instead as one solid colour per letter (grad_text), which stays sharp.

Run from the repo root:  python3 scripts/build_assets.py
Every figure below comes from the resume or from the linked project repos.
"""
import math
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

SANS = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Roboto Mono', monospace"
GRAD = ("#0090f7", "#5c6cff", "#a94ef5")  # same gradient as kmehul.github.io

# Width estimates used for wrapping. Deliberately wide (system fonts run ~0.5em per
# character) so text still fits under Safari's looser spacing or a wider fallback font.
SANS_EM, MONO_EM = 0.6, 0.62

DESKTOP_W, MOBILE_W = 840, 360
MOBILE_QUERY = "(max-width: 600px)"

THEMES = {
    "light": dict(card="#f5f5f7", stroke="none", text="#1d1d1f", sub="#6e6e73", line="#d2d2d7",
                  blue="#0071e3", chip="#ffffff", chip2="#e8e8ed", tint="#e6f0fd",
                  term="#1d1d1f", term_stroke="none"),
    "dark": dict(card="#161b22", stroke="#30363d", text="#f0f6fc", sub="#8b949e", line="#30363d",
                 blue="#2997ff", chip="#21262d", chip2="#21262d", tint="#0f2a4d",
                 term="#0b0f14", term_stroke="#30363d"),
}

# Animations only ever move content *in*: every element's resting state is its final,
# visible state, and `both` fill applies the hidden start state during the delay.
# A renderer that skips CSS animation therefore shows the finished card, not a blank one.
BASE_CSS = """
text{font-family:%(sans)s}
.m{font-family:%(mono)s}
.a{animation:up .7s cubic-bezier(.2,.8,.2,1) both}
.f{animation:fade .35s ease both}
.gy{transform-box:fill-box;transform-origin:50%% 100%%;animation:gy .9s cubic-bezier(.2,.8,.2,1) both}
.gx{transform-box:fill-box;transform-origin:0 50%%;animation:gx 1.1s cubic-bezier(.2,.8,.2,1) both}
.d{animation:draw 1.4s ease both}
.pulse{transform-box:fill-box;transform-origin:center;animation:pulse 1.8s ease-out infinite}
@keyframes up{from{opacity:0;transform:translateY(10px)}}
@keyframes fade{from{opacity:0}}
@keyframes gy{from{transform:scaleY(0)}}
@keyframes gx{from{transform:scaleX(0)}}
@keyframes draw{from{stroke-dashoffset:var(--l)}}
@keyframes pulse{from{transform:scale(1);opacity:.55}to{transform:scale(3.2);opacity:0}}
@keyframes blink{0%%{opacity:1}50%%{opacity:0}}
@keyframes cv{0%%,99%%{opacity:1}100%%{opacity:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
""" % {"sans": SANS, "mono": MONO}


# ---------------------------------------------------------------- primitives
def svg(w, h, body, label, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h:.0f}" viewBox="0 0 {w} {h:.0f}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f'<defs><style>{BASE_CSS}</style>{defs}</defs>{body}</svg>\n')


def grad_def(gid, x1, x2):
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="0" x2="{x2}" y2="0">'
            f'<stop offset="0" stop-color="{GRAD[0]}"/><stop offset=".5" stop-color="{GRAD[1]}"/>'
            f'<stop offset="1" stop-color="{GRAD[2]}"/></linearGradient>')


def grad_color(p):
    """Colour at position p (0..1) along the site gradient."""
    p = min(max(p, 0.0), 1.0)
    a, b, f = (GRAD[0], GRAD[1], p * 2) if p <= 0.5 else (GRAD[1], GRAD[2], (p - 0.5) * 2)
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * f):02x}" for x, y in zip(ca, cb))


def card(t, w, h):
    sw = "" if t["stroke"] == "none" else f' stroke="{t["stroke"]}"'
    return f'<rect x=".5" y=".5" width="{w-1}" height="{h-1:.0f}" rx="20" fill="{t["card"]}"{sw}/>'


def est(s, size, mono=False):
    return len(s) * size * (MONO_EM if mono else SANS_EM)


def wrap(s, size, maxw, mono=False):
    lines, cur = [], ""
    for word in filter(None, s.split(" ")):  # not split(): that also breaks at no-break spaces
        trial = f"{cur} {word}".strip()
        if cur and est(trial, size, mono) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur] if cur else lines


def anim(cls, delay):
    return f' class="{cls}" style="animation-delay:{delay:.2f}s"'


def txt(x, y, s, size, fill, weight=400, delay=0.0, anchor="start", extra="", cls="a"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{anim(cls, delay)}{extra}>{escape(s)}</text>')


def grad_text(x, y, s, size, weight, p0, p1, delay, extra=""):
    """Gradient-looking text that stays sharp in Safari: one solid colour per letter."""
    groups = []
    for ch in s:
        if ch == " " and groups:
            groups[-1] += ch
        else:
            groups.append(ch)
    n = max(len(groups) - 1, 1)
    spans = "".join(f'<tspan fill="{grad_color(p0 + (p1 - p0) * i / n)}">{escape(g)}</tspan>'
                    for i, g in enumerate(groups))
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" xml:space="preserve"'
            f'{anim("a", delay)}{extra}>{spans}</text>')


def para(x, y, s, size, fill, maxw, lh, delay, weight=400, extra=""):
    """Wrapped paragraph. Returns (svg, baseline of the last line)."""
    out = []
    for i, line in enumerate(wrap(s, size, maxw)):
        out.append(txt(x, y + i * lh, line, size, fill, weight, delay + i * 0.04, extra=extra))
    return "".join(out), y + (len(out) - 1) * lh


def eyebrow(t, x, y, s, delay=0.0, anchor="start"):
    return txt(x, y, s.upper(), 12, t["blue"], 600, delay, anchor, ' letter-spacing="1.4"')


def title(t, x, y, s, size, maxw, delay):
    return para(x, y, s, size, t["text"], maxw, size * 1.18, delay, 700, f' letter-spacing="{-size/60:.2f}"')


def chips(t, x, y, names, delay, maxw, size=13):
    """Flowing pill chips that wrap onto new rows. Returns (svg, bottom edge)."""
    out, cx, cy, h = [], x, y, size + 15
    for i, n in enumerate(names):
        w = est(n, size) + 22
        if cx > x and cx + w > x + maxw:
            cx, cy = x, cy + h + 8
        out.append(f'<g{anim("a", delay + i*0.05)}><rect x="{cx:.1f}" y="{cy}" width="{w:.0f}" height="{h}" '
                   f'rx="{h/2}" fill="{t["chip"]}"/><text x="{cx + w/2:.1f}" y="{cy + h/2}" font-size="{size}" '
                   f'font-weight="500" fill="{t["text"]}" text-anchor="middle" dominant-baseline="central">{escape(n)}</text></g>')
        cx += w + 8
    return "".join(out), cy + h


def band(i, n):
    """Slice of the gradient for the i-th of n side-by-side stats."""
    return i / n, (i + 1) / n


def stat(t, x, y, num, label, delay, size, label_w, p):
    """Big gradient number with a wrapped label under it. Returns (svg, last label baseline)."""
    lab, last = para(x, y + 21, label, 13, t["sub"], label_w, 17, delay)
    return grad_text(x, y, num, size, 700, *p, delay, ' letter-spacing="-0.6"') + lab, last


def stat_row(t, x, y, num, label, delay, p):
    """Mobile stat: number on the left, label beside it."""
    return (grad_text(x, y, num, 24, 700, *p, delay, ' letter-spacing="-0.5"') +
            txt(x + 112, y - 1, label, 14, t["sub"], 400, delay))


def draw_attrs(length, delay, dur=1.4):
    return (f'stroke-dasharray="{length:.0f}" style="--l:{length:.0f};animation-delay:{delay:.2f}s;'
            f'animation-duration:{dur}s" class="d"')


# ---------------------------------------------------------------- header
def header(t, mobile):
    heights = [46, 70, 58, 96, 82, 118, 104, 146, 130, 176]
    if mobile:
        W, H = MOBILE_W, 372
        x0, step, bw, base, k = 26, 31, 20, 344, 0.55
        b = [card(t, W, H)]
        b.append(eyebrow(t, 24, 46, "Hello, I'm", 0.1))
        b.append(txt(22, 94, "Kumar Mehul", 40, t["text"], 700, 0.2, extra=' letter-spacing="-1"'))
        b.append(grad_text(23, 132, "Data Analyst", 30, 700, 0, 1, 0.3, ' letter-spacing="-0.5"'))
        s, last = para(24, 166, "I turn messy data into decisions people trust.", 15, t["sub"], 312, 21, 0.4)
        b.append(s)
        b.append(txt(24, last + 28, "SQL · Python · Tableau · Power BI", 13, t["sub"], 500, 0.5))
        grid = (16, 236, 328, 116)
    else:
        W, H = DESKTOP_W, 330
        x0, step, bw, base, k = 524, 28, 20, 282, 1.0
        b = [card(t, W, H)]
        b.append(eyebrow(t, 56, 104, "Hello, I'm", 0.1))
        b.append(txt(54, 164, "Kumar Mehul", 60, t["text"], 700, 0.2, extra=' letter-spacing="-1.5"'))
        b.append(grad_text(55, 216, "Data Analyst", 42, 700, 0, 1, 0.32, ' letter-spacing="-0.8"'))
        b.append(txt(56, 256, "I turn messy data into decisions people trust.", 16, t["sub"], 400, 0.45))
        b.append(txt(56, 284, "SQL  ·  Python  ·  Tableau  ·  Power BI", 15, t["sub"], 500, 0.55))
        grid = (500, 30, 320, 270)
    gx, gy, gw, gh = grid
    b.append(f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" fill="url(#dots)"/>')
    x_end = x0 + 9 * step + bw
    for i in range(4):
        y = base - 45 * k * (i + 1)
        b.append(f'<line x1="{x0-10}" x2="{x_end+10}" y1="{y:.0f}" y2="{y:.0f}" stroke="{t["line"]}" stroke-dasharray="3 5"{anim("f", 0.2)}/>')
    b.append(f'<line x1="{x0-10}" x2="{x_end+10}" y1="{base}" y2="{base}" stroke="{t["line"]}"/>')
    pts = []
    for i, h0 in enumerate(heights):
        h = h0 * k
        x = x0 + i * step
        b.append(f'<rect x="{x}" y="{base-h:.1f}" width="{bw}" height="{h:.1f}" rx="5" fill="url(#bg)"{anim("gy", 0.35 + i*0.07)}/>')
        pts.append((x + bw / 2, base - h - 16 * max(k, 0.8)))
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    length = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    b.append(f'<path d="{d}" fill="none" stroke="{t["text"]}" stroke-width="2.5" stroke-linejoin="round" '
             f'stroke-linecap="round" {draw_attrs(length, 1.2)}/>')
    ex, ey = pts[-1]
    b.append(f'<g{anim("f", 2.5)}><circle cx="{ex}" cy="{ey:.1f}" r="5" fill="{GRAD[2]}" class="pulse"/>'
             f'<circle cx="{ex}" cy="{ey:.1f}" r="5.5" fill="{GRAD[2]}" stroke="{t["card"]}" stroke-width="2"/></g>')
    defs = (grad_def("bg", x0, x_end) +
            f'<pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.1" fill="{t["line"]}"/></pattern>')
    return svg(W, H, "".join(b), "Kumar Mehul, Data Analyst. SQL, Python, Tableau, Power BI.", defs=defs)


# ---------------------------------------------------------------- buttons (fixed size, fine on any screen)
def button(t, label, primary):
    size, h = 15, 40
    w = round(est(label, size) + 44)
    fill = t["blue"] if primary else t["chip2"]
    fg = "#ffffff" if primary else t["text"]
    body = (f'<rect width="{w}" height="{h}" rx="20" fill="{fill}"/>'
            f'<text x="{w/2}" y="{h/2}" font-size="{size}" font-weight="600" fill="{fg}" text-anchor="middle" dominant-baseline="central">{escape(label)}</text>')
    return svg(w, h, body, label)


# ---------------------------------------------------------------- terminal
KW, ID, STR, PUN, PROMPT, KEY, VAL, DIM = "#ff7b72", "#d2a8ff", "#a5d6ff", "#e6edf3", "#7ee787", "#79c0ff", "#e6edf3", "#6e7681"
RECORD = [
    ("name", "Kumar Mehul"),
    ("role", "Data Analyst"),
    ("based_in", "India, open to relocation"),
    ("education", "MS Information Systems, Northeastern University"),
    ("stack", "SQL, Python, Tableau, Power\u00a0BI"),
    ("strengths", "data quality, ETL, dimensional modeling, dashboards"),
    ("latest", "Jersey City last-mile mobility analysis"),
]


def terminal(t, mobile):
    W = MOBILE_W if mobile else DESKTOP_W
    size, lh, x0, bar = (13, 21, 16, 38) if mobile else (15, 25, 30, 44)
    cw = size * 0.6  # nominal monospace advance, used to place the prompt and cursor
    max_chars = int((W - 2 * x0) / (size * MONO_EM))
    query = [
        ("kmehul=# ", [("SELECT", KW), (" *", PUN)]),
        ("kmehul-# ", [("FROM", KW), ("   analysts", ID)]),
        ("kmehul-# ", [("WHERE", KW), ("  github ", ID), ("=", PUN), (" 'kmehul'", STR), (";", PUN)]),
    ]
    kw = max(len(k) for k, _ in RECORD)
    rows = []  # (key or "", value) after wrapping long values onto continuation lines
    for k, v in RECORD:
        for i, part in enumerate(wrap(v, size, (max_chars - kw - 3) * size * MONO_EM, mono=True)):
            rows.append((k if i == 0 else "", part))
    top = bar + 34
    n_lines = len(query) + 1 + 1 + len(rows) + 1 + 1 + 1
    H = top + (n_lines - 1) * lh + 22
    sw = "" if t["term_stroke"] == "none" else f' stroke="{t["term_stroke"]}"'
    b = [f'<rect x=".5" y=".5" width="{W-1}" height="{H-1:.0f}" rx="16" fill="{t["term"]}"{sw}/>',
         f'<line x1="0" x2="{W}" y1="{bar}" y2="{bar}" stroke="#ffffff" stroke-opacity=".08"/>']
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        b.append(f'<circle cx="{20 + i*19}" cy="{bar/2}" r="5.5" fill="{c}"/>')
    b.append(f'<text x="{W/2}" y="{bar/2 + 4.5}" font-size="12.5" fill="#8b949e" text-anchor="middle" font-weight="500">psql  ·  about_me</text>')

    y, clock, per_char = top, 0.5, 0.055
    for n, (prompt, parts) in enumerate(query):
        line = "".join(s for s, _ in parts)
        spans = "".join(f'<tspan fill="{c}">{escape(s)}</tspan>' for s, c in parts)
        px = x0 + len(prompt) * cw
        dur = len(line) * per_char
        mw = len(line) * size * MONO_EM + 10
        b.append(f'<text x="{x0}" y="{y}" font-size="{size}" class="m f" fill="{PROMPT}" '
                 f'style="animation-delay:{clock:.2f}s;animation-duration:.01s">{escape(prompt)}</text>')
        b.append(f'<text x="{px:.1f}" y="{y}" font-size="{size}" class="m" xml:space="preserve">{spans}</text>')
        # Typing mask: rests outside the card (text visible); the animation starts it over the
        # text, steps it right one character at a time, then parks it off the card again.
        b.append(f'<style>@keyframes tm{n}{{from{{transform:translateX(0);animation-timing-function:steps({len(line)},end)}}'
                 f'99%{{transform:translateX({mw:.1f}px);animation-timing-function:step-end}}to{{transform:translateX({W}px)}}}}</style>'
                 f'<g transform="translate({W} 0)" style="animation:tm{n} {dur:.2f}s linear {clock:.2f}s both">'
                 f'<rect x="{px-1:.1f}" y="{y-size-3}" width="{mw:.1f}" height="{size+9}" fill="{t["term"]}"/>'
                 f'<rect x="{px:.1f}" y="{y-size+1}" width="{cw:.1f}" height="{size+3}" fill="{PROMPT}" opacity="0" '
                 f'style="animation:cv {dur:.2f}s linear {clock:.2f}s forwards"/></g>')
        clock += dur + 0.3
        y += lh
    y += lh
    clock += 0.2
    sep = "-[ RECORD 1 ]" + "-" * max(0, min(max_chars, kw + 3 + 46) - 13)
    b.append(f'<text x="{x0}" y="{y}" font-size="{size}" class="m f" fill="{DIM}" style="animation-delay:{clock:.2f}s">{sep}</text>')
    y += lh
    for k, v in rows:
        clock += 0.08
        b.append(f'<text x="{x0}" y="{y}" font-size="{size}" class="m f" xml:space="preserve" style="animation-delay:{clock:.2f}s">'
                 f'<tspan fill="{KEY}">{escape(k.ljust(kw))}</tspan><tspan fill="{DIM}"> | </tspan><tspan fill="{VAL}">{escape(v)}</tspan></text>')
        y += lh
    clock += 0.15
    b.append(f'<text x="{x0}" y="{y}" font-size="{size}" class="m f" fill="{DIM}" style="animation-delay:{clock:.2f}s">(1 row)</text>')
    y += lh * 2
    clock += 0.3
    b.append(f'<text x="{x0}" y="{y}" font-size="{size}" class="m f" fill="{PROMPT}" style="animation-delay:{clock:.2f}s">kmehul=# </text>')
    b.append(f'<rect x="{x0 + 9*cw:.1f}" y="{y-size+1}" width="{cw:.1f}" height="{size+3}" fill="{PROMPT}" '
             f'style="animation:fade .01s {clock:.2f}s both, blink 1.1s step-end {clock:.2f}s infinite"/>')
    label = ("psql query: SELECT * FROM analysts WHERE github = 'kmehul'. Result: " +
             "; ".join(f"{k}: {v}" for k, v in RECORD))
    return svg(W, H, "".join(b), label)


# ---------------------------------------------------------------- experience
EXP_STATS = [("~8,000", "foundation records audited"),
             ("~6,300", "sorted into a 12-month grant pipeline"),
             ("~80%", "submission-ready before deadlines")]
EXP_DESC = ("Built a grants intelligence dataset from IRS 990 filings and foundation websites, then audited, "
            "gap-analyzed and enriched it into submission-ready grant packages for the team.")


def stat_tile(t, x, y, w, num, label, delay, size, p, h=None):
    """Number-and-label tile. Pass `h` to force a height so a row of tiles matches."""
    lab = wrap(label, 13, w - 36)
    h = h or 50 + 17 * len(lab)
    return (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="14" fill="{t["chip"]}"{anim("a", delay)}/>' +
            grad_text(x + 18, y + 36, num, size, 700, *p, delay, ' letter-spacing="-0.5"') +
            "".join(txt(x + 18, y + 58 + j * 17, s, 13, t["sub"], 400, delay) for j, s in enumerate(lab))), h


def experience(t, mobile):
    b = []
    if mobile:
        W, P = MOBILE_W, 20
        inner = W - 2 * P
        b += [eyebrow(t, P, 42, "Experience", 0.05),
              txt(P, 62, "Oct 2024 – May 2025", 13, t["sub"], 500, 0.05)]
        s, y = title(t, P, 98, "Data Analyst", 26, inner, 0.1); b.append(s)
        s, y = para(P, y + 26, "Rebecca Everlene Trust Company", 15, t["sub"], inner, 20, 0.15, 500); b.append(s)
        s, y = para(P, y + 20, "Chicago, USA (Remote)", 15, t["sub"], inner, 20, 0.17, 500); b.append(s)
        s, y = para(P, y + 32, EXP_DESC, 15, t["text"], inner, 22, 0.22); b.append(s)
        y += 22
        for i, (n, l) in enumerate(EXP_STATS):
            s, h = stat_tile(t, P, y, inner, n, l, 0.4 + i * 0.1, 24, band(i, 3)); b.append(s)
            y += h + 10
        H = y + 10
    else:
        W, P = DESKTOP_W, 44
        inner = W - 2 * P
        b += [eyebrow(t, P, 56, "Experience", 0.05),
              txt(W - P, 56, "Oct 2024 – May 2025", 14, t["sub"], 500, 0.05, "end")]
        s, y = title(t, P, 96, "Data Analyst", 30, inner, 0.1); b.append(s)
        b.append(txt(P, y + 28, "Rebecca Everlene Trust Company  ·  Chicago, USA (Remote)", 16, t["sub"], 500, 0.18))
        s, y = para(P, y + 64, EXP_DESC, 15, t["text"], inner, 22, 0.26); b.append(s)
        y += 24
        gap = 16
        tw = (inner - 2 * gap) / 3
        lines = max(len(wrap(l, 13, tw - 36)) for _, l in EXP_STATS)
        th = 50 + 17 * lines
        for i, (n, l) in enumerate(EXP_STATS):
            x = P + i * (tw + gap)
            s, _ = stat_tile(t, x, y, tw, n, l, 0.4 + i * 0.1, 26, band(i, 3), th)
            b.append(s)
        H = y + th + 30
    return svg(W, H, card(t, W, H) + "".join(b),
               "Experience: Data Analyst at Rebecca Everlene Trust Company, Oct 2024 to May 2025. "
               "About 8,000 foundation records audited, about 6,300 sorted into a 12-month grant pipeline, "
               "about 80% submission-ready before deadlines.")


# ---------------------------------------------------------------- CitiBike (featured)
CB_DESC = ("Which stations run out of bikes, and when? Cleaned 95,350 trips in pandas, modeled station flow "
           "and imbalance in PostgreSQL, and mapped all 108 stations in Tableau with two city-separated "
           "rebalancing routes.")
CB_STATS = [("94,689", "verified trips"), ("10", "priority stations"), ("17.8%", "peak daily imbalance")]
CB_NOTE = ("Independent AI code review caught a NULL bug and a sign error in 44 of 81 stations, "
           "both fixed before publishing.")


def ride_panel(t, px, py, pw, delay):
    """Average ride length, from the project's Findings: members 8 min, casual 15 min."""
    ph = 230
    b = [f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="16" fill="{t["chip"]}"{anim("a", delay)}/>',
         txt(px + 20, py + 34, "Average ride length", 14, t["text"], 600, delay + 0.05)]
    s, sub_end = para(px + 20, py + 54, "Members commute; casual riders linger.", 12.5, t["sub"], pw - 40, 16, delay + 0.08)
    b.append(s)
    extra = sub_end - (py + 54)  # 0 when the subtitle fits on one line
    ph += extra
    b[0] = f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="16" fill="{t["chip"]}"{anim("a", delay)}/>'
    py += extra
    scale = (pw - 40 - 64) / 15
    for i, (who, mins, col) in enumerate((("Member", 8, GRAD[0]), ("Casual", 15, GRAD[2]))):
        ly = py + 92 + i * 50
        b.append(txt(px + 20, ly, who, 13, t["sub"], 500, delay + 0.15))
        b.append(f'<rect x="{px+20}" y="{ly+8}" width="{mins*scale:.0f}" height="22" rx="6" fill="{col}"{anim("gx", delay + 0.3 + i*0.15)}/>')
        b.append(txt(px + 28 + mins * scale, ly + 25, f"{mins} min", 14, t["text"], 700, delay + 0.9 + i * 0.15))
    b.append(f'<line x1="{px+20}" x2="{px+pw-20}" y1="{py+184}" y2="{py+184}" stroke="{t["line"]}"/>')
    b.append(txt(px + 20, py + 210, "Busiest station", 13, t["sub"], 500, delay + 0.3))
    b.append(txt(px + pw - 20, py + 210, "Grove St PATH", 14, t["text"], 700, delay + 0.3, "end"))
    return "".join(b), py - extra + ph


def callout(t, x, y, w, s, delay):
    lines = wrap(s, 13, w - 58)
    h = 20 + 18 * len(lines)
    out = [f'<g{anim("a", delay)}><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{t["tint"]}"/>',
           f'<circle cx="{x+20}" cy="{y+19}" r="8" fill="{t["blue"]}"/>',
           f'<path d="M{x+16} {y+19.2} l2.8 2.8 l5-5.4" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>']
    out += [f'<text x="{x+38}" y="{y+23.5+i*18}" font-size="13" fill="{t["text"]}">{escape(l)}</text>' for i, l in enumerate(lines)]
    return "".join(out) + "</g>", y + h


def citibike(t, mobile):
    b = []
    if mobile:
        W, P = MOBILE_W, 20
        inner = W - 2 * P
        b += [eyebrow(t, P, 42, "Featured project", 0.05), txt(P, 62, "Jun – Jul 2026", 13, t["sub"], 500, 0.05)]
        s, y = title(t, P, 98, "Jersey City Last-Mile Mobility", 26, inner, 0.1); b.append(s)
        s, y = para(P, y + 26, "A CitiBike demand and rebalancing analysis", 15, t["sub"], inner, 20, 0.16, 500); b.append(s)
        s, y = para(P, y + 32, CB_DESC, 15, t["text"], inner, 22, 0.22); b.append(s)
        s, y = chips(t, P, y + 18, ["PostgreSQL", "pandas", "Tableau"], 0.35, inner); b.append(s)
        y += 36
        for i, (n, l) in enumerate(CB_STATS):
            b.append(stat_row(t, P, y + i * 38, n, l, 0.45 + i * 0.08, band(i, 3)))
        y += 2 * 38 + 22
        s, y = ride_panel(t, P, y, inner, 0.5); b.append(s)
        s, y = callout(t, P, y + 16, inner, CB_NOTE, 0.7); b.append(s)
        H = y + 20
    else:
        W, P = DESKTOP_W, 44
        inner = W - 2 * P
        b += [eyebrow(t, P, 58, "Featured project", 0.05), txt(W - P, 58, "Jun – Jul 2026", 14, t["sub"], 500, 0.05, "end")]
        s, y = title(t, P, 98, "Jersey City Last-Mile Mobility", 30, inner, 0.1); b.append(s)
        b.append(txt(P, y + 28, "A CitiBike demand and rebalancing analysis", 17, t["sub"], 500, 0.16))
        top = y + 52
        pw = 330
        colw = inner - pw - 32
        s, yl = para(P, top + 20, CB_DESC, 15, t["text"], colw, 22, 0.22); b.append(s)
        s, yl = chips(t, P, yl + 20, ["PostgreSQL", "pandas", "Tableau"], 0.35, colw); b.append(s)
        s, yr = ride_panel(t, W - P - pw, top, pw, 0.3); b.append(s)
        y = max(yl, yr) + 46
        cw = inner / 3
        for i, (n, l) in enumerate(CB_STATS):
            s, _ = stat(t, P + i * cw, y, n, l, 0.5 + i * 0.08, 28, cw - 20, band(i, 3)); b.append(s)
        s, y = callout(t, P, y + 42, inner, CB_NOTE, 0.75); b.append(s)
        H = y + 26
    return svg(W, H, card(t, W, H) + "".join(b),
               "Featured project: Jersey City Last-Mile Mobility, a CitiBike analysis. 94,689 verified trips, "
               "10 priority stations, 17.8% peak daily imbalance. Members average 8 minute rides, casual riders 15. "
               "Busiest station: Grove St PATH.")


# ---------------------------------------------------------------- IMDB / California food
def schema(t, x, y, w, h, facts, left, right, delay):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{t["chip"]}"{anim("a", delay)}/>']
    cx, cy = x + w / 2, y + h / 2
    pad, ph, fs = 12, 24, 10
    dw = max(len(n) for n in left + right) * fs * MONO_EM + 14
    fw = max(len(n) for n in facts) * fs * MONO_EM + 18
    if 2 * dw + fw + 2 * pad + 16 > w:  # too wide: shrink the type to fit
        k = (w - 2 * pad - 16) / (2 * dw + fw)
        dw, fw, fs = dw * k, fw * k, round(fs * k, 1)
    fy0 = cy - (len(facts) * ph + (len(facts) - 1) * 10) / 2

    def col(names, side):
        n, span = len(names), h - 2 * pad - ph
        return [((x + pad) if side == "l" else (x + w - pad - dw),
                 y + pad + (span * i / (n - 1) if n > 1 else span / 2), nm) for i, nm in enumerate(names)]
    dims = col(left, "l") + col(right, "r")
    for i, (xx, yy, nm) in enumerate(dims):
        left_side = xx < cx
        sx = xx + dw if left_side else xx
        tx = cx - fw / 2 if left_side else cx + fw / 2
        ln = abs(tx - sx) + abs(cy - (yy + ph / 2)) * 1.1
        out.append(f'<path d="M{sx:.1f} {yy+ph/2:.1f} C{(sx+tx)/2:.1f} {yy+ph/2:.1f} {(sx+tx)/2:.1f} {cy:.1f} {tx:.1f} {cy:.1f}" '
                   f'fill="none" stroke="{t["line"]}" stroke-width="1.5" {draw_attrs(ln, delay + 0.4 + i*0.06, 0.8)}/>')
    for i, (xx, yy, nm) in enumerate(dims):
        out.append(f'<g{anim("a", delay + 0.2 + i*0.06)}><rect x="{xx:.1f}" y="{yy:.1f}" width="{dw:.1f}" height="{ph}" rx="7" '
                   f'fill="{t["card"]}" stroke="{t["line"]}"/><text x="{xx+dw/2:.1f}" y="{yy+ph/2:.1f}" dominant-baseline="central" font-size="{fs}" class="m" '
                   f'fill="{t["sub"]}" text-anchor="middle">{nm}</text></g>')
    for i, nm in enumerate(facts):
        yy = fy0 + i * (ph + 10)
        out.append(f'<g{anim("a", delay + 0.1 + i*0.08)}><rect x="{cx-fw/2:.1f}" y="{yy:.1f}" width="{fw:.1f}" height="{ph}" rx="7" '
                   f'fill="url(#sg)"/><text x="{cx:.1f}" y="{yy+ph/2:.1f}" dominant-baseline="central" font-size="{fs}" class="m" font-weight="600" '
                   f'fill="#ffffff" text-anchor="middle">{nm}</text></g>')
    return "".join(out)


PROJECTS = {
    "imdb": dict(
        when="Dec 2023 – Apr 2024", title="IMDB Movie Data Analysis",
        desc=("Loaded ~1M records from 17 heterogeneous sources (SQL tables, JSON and TSV files) with Talend "
              "into a 12-table dimensional warehouse on Azure SQL, then built Tableau dashboards on ratings, "
              "revenue, genres and release seasons."),
        tags=["E/R Studio", "Talend", "Alteryx", "Azure SQL", "Tableau"],
        facts=["fct_ratings", "fct_movierevenue"],
        left=["dim_movies", "dim_person", "dim_genre"], right=["dim_region", "dim_date", "dim_profession"],
        stats=[("12", "warehouse tables"), ("~8.9M", "warehouse rows"), ("17", "source files")],
        label=("IMDB Movie Data Analysis: about 1 million source records from 17 sources loaded with Talend into "
               "a 12-table dimensional warehouse of about 8.9 million rows on Azure SQL.")),
    "food": dict(
        when="Oct – Nov 2023", title="California Food Inspections",
        desc=("Modeled Sonoma County food facility inspections as a 5-table star schema: profiled in Alteryx, "
              "loaded into Azure SQL with Talend, and visualized in Tableau down to a geographic risk map."),
        tags=["E/R Studio", "Talend", "Alteryx", "Azure SQL", "Tableau"],
        facts=["fct_inspection", "fct_insp_violation"],
        left=["dim_business", "dim_date"], right=["dim_violation"],
        stats=[("5", "tables in a star schema"), ("2", "fact tables"), ("3", "dimensions")],
        label=("California Food Inspection Analysis: a 5-table star schema of Sonoma County food facility "
               "inspections, profiled in Alteryx, loaded into Azure SQL with Talend, visualized in Tableau.")),
}


def project(t, key, mobile):
    p = PROJECTS[key]
    b = []
    if mobile:
        W, P = MOBILE_W, 20
        inner = W - 2 * P
        b.append(schema(t, 10, 10, W - 20, 150, p["facts"], p["left"], p["right"], 0.0))
        b.append(eyebrow(t, P, 194, p["when"], 0.3))
        s, y = title(t, P, 228, p["title"], 24, inner, 0.35); b.append(s)
        s, y = para(P, y + 30, p["desc"], 15, t["text"], inner, 22, 0.4); b.append(s)
        y += 42
        for i, (n, l) in enumerate(p["stats"]):
            b.append(stat_row(t, P, y + i * 38, n, l, 0.5 + i * 0.08, band(i, 3)))
        y += 2 * 38 + 22
        s, y = chips(t, P, y, p["tags"], 0.6, inner, 12); b.append(s)
        H = y + 22
    else:
        W, P = DESKTOP_W, 44
        inner = W - 2 * P
        b.append(eyebrow(t, P, 56, p["when"], 0.05))
        s, y = title(t, P, 96, p["title"], 28, inner, 0.1); b.append(s)
        dw = 372
        colw = inner - dw - 32
        top = y + 30
        s, yl = para(P, top + 14, p["desc"], 15, t["text"], colw, 22, 0.2); b.append(s)
        b.append(schema(t, W - P - dw, top - 4, dw, 164, p["facts"], p["left"], p["right"], 0.15))
        y = max(yl + 50, top + 196)
        cw = inner / 3
        for i, (n, l) in enumerate(p["stats"]):
            s, _ = stat(t, P + i * cw, y, n, l, 0.4 + i * 0.08, 26, cw - 20, band(i, 3)); b.append(s)
        s, y = chips(t, P, y + 42, p["tags"], 0.55, inner, 12); b.append(s)
        H = y + 30
    return svg(W, H, card(t, W, H) + "".join(b), p["label"], defs=grad_def("sg", 0, W))


# ---------------------------------------------------------------- Apple Music tracker (side project)
TR_DESC = ("Apple Music's new-release alerts kept missing drops, so this polls the iTunes API every 6 hours "
           "and sends a phone push and an email the moment a release goes live.")
TR_VIBE = "Built entirely by prompting AI: I directed and tested it."
TR_STATS = [("53", "artists watched"), ("4,808", "releases logged"), ("0", "pip dependencies")]
TR_NOTES = [("ntfy", "New release", "New music from your list"),
            ("Gmail", "Release alert", "Out now on Apple Music")]


def vibe_badge(x, y, delay):
    return (f'<g{anim("a", delay)}><rect x="{x}" y="{y}" width="140" height="24" rx="12" fill="url(#vg)"/>'
            f'<text x="{x+70}" y="{y+12}" font-size="11" font-weight="700" fill="#fff" text-anchor="middle" '
            f'letter-spacing="0.6" dominant-baseline="central">100% VIBE CODED</text></g>')


def notification(t, x, y, w, app, head, body, delay):
    return (f'<g{anim("a", delay)}><rect x="{x}" y="{y}" width="{w}" height="68" rx="16" fill="{t["chip"]}" stroke="{t["line"]}"/>'
            f'<rect x="{x+14}" y="{y+16}" width="36" height="36" rx="9" fill="url(#vg)"/>'
            f'<path d="M{x+28} {y+41} V{y+25} L{x+38} {y+23} V{y+39}" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>'
            f'<circle cx="{x+25.5}" cy="{y+41}" r="2.8" fill="#fff"/><circle cx="{x+35.5}" cy="{y+39}" r="2.8" fill="#fff"/>'
            f'<text x="{x+62}" y="{y+29}" font-size="13" font-weight="600" fill="{t["text"]}">{escape(head)}</text>'
            f'<text x="{x+w-14}" y="{y+29}" font-size="11" fill="{t["sub"]}" text-anchor="end">{app} · now</text>'
            f'<text x="{x+62}" y="{y+49}" font-size="12" fill="{t["sub"]}">{escape(body)}</text></g>')


def tracker(t, mobile):
    b = []
    if mobile:
        W, P = MOBILE_W, 20
        inner = W - 2 * P
        b += [eyebrow(t, P, 42, "Side project", 0.05), vibe_badge(W - P - 140, 26, 0.1)]
        s, y = title(t, P, 92, "Apple Music Release Tracker", 26, inner, 0.12); b.append(s)
        s, y = para(P, y + 32, TR_DESC, 15, t["text"], inner, 22, 0.2); b.append(s)
        s, y = para(P, y + 26, TR_VIBE, 14, t["sub"], inner, 20, 0.3, extra=' font-style="italic"'); b.append(s)
        y += 44
        for i, (n, l) in enumerate(TR_STATS):
            b.append(stat_row(t, P, y + i * 38, n, l, 0.4 + i * 0.08, band(i, 3)))
        y += 2 * 38 + 24
        for i, (app, head, body) in enumerate(TR_NOTES):
            b.append(notification(t, P, y + i * 80, inner, app, head, body, 0.6 + i * 0.3))
        H = y + 80 + 68 + 20
    else:
        W, P = DESKTOP_W, 44
        inner = W - 2 * P
        nw = 296
        colw = inner - nw - 40
        b += [eyebrow(t, P, 56, "Side project", 0.05), vibe_badge(W - P - 140, 40, 0.1)]
        s, y = title(t, P, 98, "Apple Music Release Tracker", 28, colw + 40, 0.12); b.append(s)
        s, y = para(P, y + 34, TR_DESC, 15, t["text"], colw, 22, 0.2); b.append(s)
        s, y = para(P, y + 24, TR_VIBE, 14, t["sub"], colw, 20, 0.3, extra=' font-style="italic"'); b.append(s)
        y += 48
        sw = colw / 3
        for i, (n, l) in enumerate(TR_STATS):
            s, _ = stat(t, P + i * sw, y, n, l, 0.4 + i * 0.08, 26, sw - 12, band(i, 3)); b.append(s)
        H = max(y + 52, 300)
        ny = (H - 2 * 68 - 16) / 2 + 12
        for i, (app, head, body) in enumerate(TR_NOTES):
            b.append(notification(t, W - P - nw, ny + i * 84, nw, app, head, body, 0.7 + i * 0.35))
    defs = (f'<linearGradient id="vg" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="#fa2d48"/><stop offset="1" stop-color="{GRAD[2]}"/></linearGradient>')
    return svg(W, H, card(t, W, H) + "".join(b),
               "Side project, 100% vibe coded: Apple Music Release Tracker. Polls the iTunes API every 6 hours for "
               "53 artists and sends a push and an email on new releases. 4,808 releases logged, no pip dependencies.",
               defs=defs)


# ---------------------------------------------------------------- toolkit
TOOLS = [("Query & code", [("SQL", "#0090f7"), ("Python", "#3776ab"), ("pandas", "#e70488"),
                           ("matplotlib", "#4c72b0"), ("seaborn", "#5a9bd4")]),
         ("Databases", [("PostgreSQL", "#336791"), ("SQL Server", "#cc2927"), ("Azure SQL", "#0078d4"), ("MySQL", "#00758f")]),
         ("BI & visualization", [("Tableau", "#e97627"), ("Power BI", "#f2c811")]),
         ("Prep & modeling", [("Alteryx", "#0078c0"), ("Talend", "#ff6d70"), ("E/R Studio", "#94c941")])]


def tool_chip(t, x, y, w, name, colr, delay):
    """Pill with a coloured dot and a label, centred together as one line of text."""
    return (f'<g{anim("a", delay)}><rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="34" rx="17" fill="{t["chip"]}"/>'
            f'<text x="{x + w/2:.1f}" y="{y+17}" font-size="13.5" font-weight="500" fill="{t["text"]}" '
            f'text-anchor="middle" dominant-baseline="central"><tspan fill="{colr}" font-size="15">●</tspan>'
            f'<tspan dx="7">{escape(name)}</tspan></text></g>')


def toolkit(t, mobile):
    b, k = [], 0
    if mobile:
        W, P = MOBILE_W, 20
        inner = W - 2 * P
        b.append(eyebrow(t, P, 42, "Toolkit", 0.05))
        y = 76
        for head, items in TOOLS:
            b.append(txt(P, y, head, 13, t["sub"], 600, 0.1 + k * 0.02))
            cx, cy = P, y + 12
            for name, colr in items:
                w = est(name, 13.5) + 44
                if cx > P and cx + w > P + inner:
                    cx, cy = P, cy + 42
                b.append(tool_chip(t, cx, cy, w, name, colr, 0.15 + k * 0.04))
                cx += w + 8
                k += 1
            y = cy + 34 + 34
        H = y - 12
    else:
        W, P = DESKTOP_W, 44
        inner = W - 2 * P
        b += [eyebrow(t, P, 56, "Toolkit", 0.05), txt(W - P, 56, "Built with, shipped with", 14, t["sub"], 500, 0.05, "end")]
        gap = 12
        cw = (inner - 3 * gap) / 4
        for i, (head, items) in enumerate(TOOLS):
            x = P + i * (cw + gap)
            b.append(txt(x, 94, head, 13, t["sub"], 600, 0.1 + i * 0.05))
            for j, (name, colr) in enumerate(items):
                b.append(tool_chip(t, x, 108 + j * 44, cw, name, colr, 0.2 + k * 0.04))
                k += 1
        H = 108 + max(len(it) for _, it in TOOLS) * 44 + 20
    return svg(W, H, card(t, W, H) + "".join(b),
               "Toolkit. " + ". ".join(f"{h}: " + ", ".join(n for n, _ in it) for h, it in TOOLS) + ".")


# ---------------------------------------------------------------- education
EDU = [("Sep 2022 – May 2024", "MS, Information Systems", "Northeastern University", "Boston, USA"),
       ("Jul 2016 – May 2020", "B.Tech, Information Technology", "SRM Institute of Science and Technology", "Chennai, India")]


def education(t, mobile):
    b = []
    if mobile:
        W, P = MOBILE_W, 20
        b.append(eyebrow(t, P, 42, "Education", 0.05))
        y, lx, tx = 78, P + 6, P + 28
        inner = W - tx - P
        ys = []
        for i, (when, deg, school, place) in enumerate(EDU):
            d = 0.3 + i * 0.25
            ys.append(y)
            b.append(eyebrow(t, tx, y + 4, when, d))
            s, yy = para(tx, y + 32, deg, 18, t["text"], inner, 22, d + 0.05, 700); b.append(s)
            s, yy = para(tx, yy + 24, school, 15, t["text"], inner, 20, d + 0.1, 500); b.append(s)
            b.append(txt(tx, yy + 21, place, 13, t["sub"], 400, d + 0.15))
            y = yy + 21 + 40
        H = y - 14
        ln = ys[-1] - ys[0]
        b.insert(1, f'<line x1="{lx}" x2="{lx}" y1="{ys[0]}" y2="{ys[-1]}" stroke="url(#vline)" stroke-width="2" {draw_attrs(ln, 0.15)}/>')
        for i, yy in enumerate(ys):
            b.append(f'<circle cx="{lx}" cy="{yy}" r="6" fill="{GRAD[i*2]}" stroke="{t["card"]}" stroke-width="3"{anim("f", 0.3 + i*0.25)}/>')
        defs = (f'<linearGradient id="vline" gradientUnits="userSpaceOnUse" x1="0" y1="{ys[0]}" x2="0" y2="{ys[-1]}">'
                f'<stop offset="0" stop-color="{GRAD[0]}"/><stop offset="1" stop-color="{GRAD[2]}"/></linearGradient>')
    else:
        W, P = DESKTOP_W, 44
        b += [eyebrow(t, P, 56, "Education", 0.05),
              f'<line x1="{P}" x2="{W-P}" y1="92" y2="92" stroke="url(#ng)" stroke-width="2" {draw_attrs(W - 2*P, 0.15)}/>']
        colw = (W - 2 * P) / 2
        bottoms = []
        for i, (when, deg, school, place) in enumerate(EDU):
            x = P + i * colw
            d = 0.35 + i * 0.25
            b.append(f'<circle cx="{x+6}" cy="92" r="6" fill="{GRAD[i*2]}" stroke="{t["card"]}" stroke-width="3"{anim("f", d)}/>')
            b.append(eyebrow(t, x, 130, when, d + 0.05))
            s, yy = para(x, 160, deg, 20, t["text"], colw - 24, 24, d + 0.1, 700); b.append(s)
            s, yy = para(x, yy + 26, school, 15, t["text"], colw - 24, 20, d + 0.15, 500); b.append(s)
            b.append(txt(x, yy + 22, place, 13, t["sub"], 400, d + 0.2))
            bottoms.append(yy + 22)
        H = max(bottoms) + 30
        defs = grad_def("ng", P, W - P)
    return svg(W, H, card(t, W, H) + "".join(b),
               "Education: MS Information Systems, Northeastern University, 2022 to 2024. "
               "B.Tech Information Technology, SRM Institute of Science and Technology, 2016 to 2020.",
               defs=defs)


# ---------------------------------------------------------------- README
CARDS = {"header": header, "about": terminal, "experience": experience, "citibike": citibike,
         "imdb": lambda t, m: project(t, "imdb", m), "food": lambda t, m: project(t, "food", m),
         "tracker": tracker, "toolkit": toolkit, "education": education}
BUTTONS = {"linkedin": ("LinkedIn", True), "portfolio": ("Portfolio", False), "email": ("Email", False),
           "dashboard": ("Live dashboard", True), "repo": ("View repository", False)}
LINKS = {"linkedin": "https://linkedin.com/in/kmehul992", "portfolio": "https://kmehul.github.io",
         "email": "mailto:kumar-mehul_1@outlook.com",
         "dashboard": "https://public.tableau.com/shared/WW7ZSRM8C?:display_count=n&:origin=viz_share_link",
         "citibike": "https://github.com/kmehul/citibike-jc-mobility-analysis",
         "imdb": "https://github.com/kmehul/IMDB-Movie-Data-Analysis",
         "food": "https://github.com/kmehul/California-Food-Inspection-Analysis",
         "tracker": "https://github.com/kmehul/apple-music-release-tracker"}
ALT = {
    "header": "Kumar Mehul, Data Analyst. SQL, Python, Tableau, Power BI.",
    "about": "About me, as a SQL query result: Kumar Mehul, Data Analyst, based in India and open to relocation. "
             "MS Information Systems, Northeastern University. Stack: SQL, Python, Tableau, Power BI.",
    "experience": "Experience: Data Analyst at Rebecca Everlene Trust Company, Oct 2024 to May 2025. About 8,000 "
                  "foundation records audited, about 6,300 sorted into a 12-month grant pipeline, about 80% "
                  "submission-ready before deadlines.",
    "citibike": "Featured project: Jersey City Last-Mile Mobility, a CitiBike analysis. 94,689 verified trips, "
                "10 priority stations, 17.8% peak daily imbalance.",
    "imdb": PROJECTS["imdb"]["label"], "food": PROJECTS["food"]["label"],
    "tracker": "Side project, 100% vibe coded: Apple Music Release Tracker. Polls the iTunes API every 6 hours "
               "for 53 artists and sends a push and an email on new releases.",
    "toolkit": "Toolkit: " + ", ".join(n for _, it in TOOLS for n, _ in it) + ".",
    "education": "Education: MS Information Systems, Northeastern University, 2022 to 2024. B.Tech Information "
                 "Technology, SRM Institute of Science and Technology, 2016 to 2020.",
}


def pic_card(name):
    return ("<p>\n<picture>\n"
            f'  <source media="{MOBILE_QUERY} and (prefers-color-scheme: dark)" srcset="assets/m/{name}-dark.svg">\n'
            f'  <source media="{MOBILE_QUERY}" srcset="assets/m/{name}-light.svg">\n'
            f'  <source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">\n'
            f'  <img alt="{escape(ALT[name])}" src="assets/{name}-light.svg" width="100%">\n'
            "</picture>\n</p>")


def btn(slug, href):
    label = BUTTONS[slug][0]
    return (f'<a href="{escape(href)}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/btn-{slug}-dark.svg">'
            f'<img alt="{label}" src="assets/btn-{slug}-light.svg" height="40"></picture></a>')


def btn_row(*pairs):
    return '<p align="center">\n  ' + "\n  &nbsp;\n  ".join(btn(s, h) for s, h in pairs) + "\n</p>"


def readme():
    contact = btn_row(*((s, LINKS[s]) for s in ("linkedin", "portfolio", "email")))
    parts = [pic_card("header"), contact, pic_card("about"), pic_card("experience"),
             pic_card("citibike"), btn_row(("dashboard", LINKS["dashboard"]), ("repo", LINKS["citibike"])),
             pic_card("imdb"), btn_row(("repo", LINKS["imdb"])),
             pic_card("food"), btn_row(("repo", LINKS["food"])),
             pic_card("tracker"), btn_row(("repo", LINKS["tracker"])),
             pic_card("toolkit"), pic_card("education"), contact]
    return "<!-- Generated by scripts/build_assets.py. Edit the script, not this file. -->\n\n" + "\n\n".join(parts) + "\n"


def main():
    for old in list(OUT.glob("*.svg")) + list((OUT / "m").glob("*.svg")):
        old.unlink()
    (OUT / "m").mkdir(parents=True, exist_ok=True)
    for theme, t in THEMES.items():
        for name, fn in CARDS.items():
            (OUT / f"{name}-{theme}.svg").write_text(fn(t, False))
            (OUT / "m" / f"{name}-{theme}.svg").write_text(fn(t, True))
        for slug, (label, primary) in BUTTONS.items():
            (OUT / f"btn-{slug}-{theme}.svg").write_text(button(t, label, primary))
    (ROOT / "README.md").write_text(readme())
    print("wrote", len(list(OUT.rglob("*.svg"))), "SVGs and README.md")


if __name__ == "__main__":
    main()
