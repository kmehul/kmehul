#!/usr/bin/env python3
"""Generate the profile README's SVG cards, in a light and a dark variant each.

Run from the repo root:  python3 scripts/build_assets.py
Every figure below comes from the resume or from the linked project repos.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"

SANS = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"
GRAD = ("#0090f7", "#5c6cff", "#a94ef5")  # same gradient as kmehul.github.io

THEMES = {
    "light": dict(card="#f5f5f7", stroke="none", text="#1d1d1f", sub="#6e6e73", line="#d2d2d7",
                  blue="#0071e3", chip="#ffffff", chip2="#e8e8ed", tint="#e6f0fd",
                  term="#1d1d1f", term_stroke="none"),
    "dark": dict(card="#161b22", stroke="#30363d", text="#f0f6fc", sub="#8b949e", line="#30363d",
                 blue="#2997ff", chip="#21262d", chip2="#21262d", tint="#0f2a4d",
                 term="#0b0f14", term_stroke="#30363d"),
}

BASE_CSS = """
text{font-family:%(sans)s}
.m{font-family:%(mono)s}
.a{opacity:0;animation:up .7s cubic-bezier(.2,.8,.2,1) forwards}
.f{opacity:0;animation:fade .35s ease forwards}
.gy{transform-box:fill-box;transform-origin:50%% 100%%;transform:scaleY(0);animation:gy .9s cubic-bezier(.2,.8,.2,1) forwards}
.gx{transform-box:fill-box;transform-origin:0 50%%;transform:scaleX(0);animation:gx 1.1s cubic-bezier(.2,.8,.2,1) forwards}
.d{animation:draw 1.4s ease forwards}
.pulse{transform-box:fill-box;transform-origin:center;animation:pulse 1.8s ease-out infinite}
@keyframes up{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes gy{to{transform:scaleY(1)}}
@keyframes gx{to{transform:scaleX(1)}}
@keyframes draw{to{stroke-dashoffset:0}}
@keyframes pulse{0%%{transform:scale(1);opacity:.55}100%%{transform:scale(3.2);opacity:0}}
@keyframes blink{0%%{opacity:1}50%%{opacity:0}}
@media (prefers-reduced-motion:reduce){
 .a,.f,.gy,.gx,.d,.cur,.tg{animation:none!important;opacity:1!important;transform:none!important;stroke-dashoffset:0!important}
 .tm,.tc{display:none}
}
""" % {"sans": SANS, "mono": MONO}


def svg(w, h, body, label, css="", defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f'<defs><style>{BASE_CSS}{css}</style>{defs}</defs>{body}</svg>\n')


def grad_def(gid, x1, x2):
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="0" x2="{x2}" y2="0">'
            f'<stop offset="0" stop-color="{GRAD[0]}"/><stop offset=".5" stop-color="{GRAD[1]}"/>'
            f'<stop offset="1" stop-color="{GRAD[2]}"/></linearGradient>')


def card(t, w, h):
    sw = "" if t["stroke"] == "none" else f' stroke="{t["stroke"]}"'
    return f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="20" fill="{t["card"]}"{sw}/>'


def txt(x, y, s, size, fill, weight=400, cls="a", delay=0.0, anchor="start", extra=""):
    style = f' style="animation-delay:{delay:.2f}s"' if cls else ""
    c = f' class="{cls}"' if cls else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{c}{style}{extra}>{escape(s)}</text>')


def eyebrow(t, x, y, s, delay=0.0, anchor="start"):
    return txt(x, y, s.upper(), 12, t["blue"], 600, delay=delay, anchor=anchor, extra=' letter-spacing="1.4"')


def text_w(s, size, mono=False):
    """Rough rendered width, deliberately generous so boxes never clip."""
    return len(s) * size * (0.61 if mono else 0.56)


def chips(t, x, y, names, delay, size=13, fill=None):
    out, cx = [], x
    for i, n in enumerate(names):
        w = text_w(n, size) + 22
        out.append(f'<g class="a" style="animation-delay:{delay + i*0.06:.2f}s">'
                   f'<rect x="{cx}" y="{y}" width="{w:.0f}" height="{size+15}" rx="{(size+15)/2}" fill="{fill or t["chip"]}"/>'
                   f'<text x="{cx + w/2:.1f}" y="{y + size + 2.5}" font-size="{size}" font-weight="500" fill="{t["text"]}" text-anchor="middle">{escape(n)}</text></g>')
        cx += w + 8
    return "".join(out)


# ---------------------------------------------------------------- header
def header(t):
    W, H = 840, 330
    heights = [46, 70, 58, 96, 82, 118, 104, 146, 130, 176]
    base, x0, bw, step = 282, 500, 20, 30
    b = [card(t, W, H)]
    b.append(f'<rect x="470" y="30" width="350" height="270" fill="url(#dots)"/>')
    for i in range(4):
        y = base - 45 * (i + 1)
        b.append(f'<line x1="490" x2="800" y1="{y}" y2="{y}" stroke="{t["line"]}" stroke-dasharray="3 5" class="f" style="animation-delay:.2s"/>')
    b.append(f'<line x1="490" x2="800" y1="{base}" y2="{base}" stroke="{t["line"]}"/>')
    pts = []
    for i, h in enumerate(heights):
        x = x0 + i * step
        b.append(f'<rect x="{x}" y="{base-h}" width="{bw}" height="{h}" rx="5" fill="url(#bg)" class="gy" style="animation-delay:{0.35 + i*0.07:.2f}s"/>')
        pts.append((x + bw / 2, base - h - 16))
    d = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    length = sum(((pts[i+1][0]-pts[i][0])**2 + (pts[i+1][1]-pts[i][1])**2) ** .5 for i in range(len(pts)-1))
    b.append(f'<path d="{d}" fill="none" stroke="{t["text"]}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" '
             f'stroke-dasharray="{length:.0f}" stroke-dashoffset="{length:.0f}" class="d" style="animation-delay:1.2s"/>')
    ex, ey = pts[-1]
    b.append(f'<g class="f" style="animation-delay:2.5s"><circle cx="{ex}" cy="{ey}" r="5" fill="{GRAD[2]}" class="pulse"/>'
             f'<circle cx="{ex}" cy="{ey}" r="5.5" fill="{GRAD[2]}" stroke="{t["card"]}" stroke-width="2"/></g>')
    b.append(eyebrow(t, 56, 104, "Hello, I'm", 0.1))
    b.append(txt(54, 164, "Kumar Mehul", 60, t["text"], 700, delay=0.2, extra=' letter-spacing="-1.5"'))
    b.append(txt(55, 216, "Data Analyst", 42, "url(#tg)", 700, delay=0.32, extra=' letter-spacing="-0.8"'))
    b.append(txt(56, 258, "I turn messy data into decisions people trust.", 17, t["sub"], 400, delay=0.45))
    b.append(txt(56, 286, "SQL  ·  Python  ·  Tableau  ·  Power BI", 15, t["sub"], 500, delay=0.55))
    defs = (grad_def("tg", 55, 320) + grad_def("bg", 500, 790) +
            f'<pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.1" fill="{t["line"]}"/></pattern>')
    return svg(W, H, "".join(b), "Kumar Mehul, Data Analyst. SQL, Python, Tableau, Power BI.", defs=defs)


# ---------------------------------------------------------------- buttons
def button(t, label, primary):
    size, h = 15, 40
    w = round(len(label) * size * 0.54 + 48)
    fill = t["blue"] if primary else t["chip2"]
    fg = "#ffffff" if primary else t["text"]
    body = (f'<rect width="{w}" height="{h}" rx="20" fill="{fill}"/>'
            f'<text x="{w/2}" y="25.5" font-size="{size}" font-weight="600" fill="{fg}" text-anchor="middle">{escape(label)}</text>')
    return svg(w, h, body, label)


# ---------------------------------------------------------------- terminal
KW, ID, STR, PUN, PROMPT, KEY, VAL, DIM = "#ff7b72", "#d2a8ff", "#a5d6ff", "#e6edf3", "#7ee787", "#79c0ff", "#e6edf3", "#6e7681"


def terminal(t):
    W, size, lh, x0, cw = 840, 15, 25, 30, 9.1
    query = [  # (prompt, [(text, colour), ...])
        ("kmehul=# ", [("SELECT", KW), (" *", PUN)]),
        ("kmehul-# ", [("FROM", KW), ("   analysts", ID)]),
        ("kmehul-# ", [("WHERE", KW), ("  github ", ID), ("=", PUN), (" 'kmehul'", STR), (";", PUN)]),
    ]
    record = [
        ("name", "Kumar Mehul"),
        ("role", "Data Analyst"),
        ("based_in", "India, open to relocation"),
        ("education", "MS Information Systems, Northeastern University"),
        ("stack", "SQL, Python, Tableau, Power BI"),
        ("strengths", "data quality, ETL, dimensional modeling, dashboards"),
        ("latest", "Jersey City last-mile mobility analysis"),
    ]
    rows = len(query) + 1 + 1 + len(record) + 1 + 1
    top = 80
    H = top + rows * lh + 6
    sw = "" if t["term_stroke"] == "none" else f' stroke="{t["term_stroke"]}"'
    b = [f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="{t["term"]}"{sw}/>',
         f'<line x1="0" x2="{W}" y1="44" y2="44" stroke="#ffffff" stroke-opacity=".08"/>']
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        b.append(f'<circle cx="{24 + i*20}" cy="22" r="6" fill="{c}"/>')
    b.append(f'<text x="{W/2}" y="27" font-size="13" fill="#8b949e" text-anchor="middle" font-weight="500">psql  ·  about_me</text>')

    y, tclock, per_char = top, 0.5, 0.055
    for n, (prompt, parts) in enumerate(query):
        line = "".join(s for s, _ in parts)
        spans = "".join(f'<tspan fill="{c}">{escape(s)}</tspan>' for s, c in parts)
        px = x0 + len(prompt) * cw
        dur = len(line) * per_char
        mw = len(line) * cw + 8
        b.append(f'<text x="{x0}" y="{y}" font-size="{size}" class="m f" fill="{PROMPT}" style="animation-delay:{tclock:.2f}s;animation-duration:.01s">{escape(prompt)}</text>')
        b.append(f'<text x="{px:.1f}" y="{y}" font-size="{size}" class="m" xml:space="preserve">{spans}</text>')
        b.append(f'<g class="tm" style="animation:tm{n} {dur:.2f}s steps({len(line)},end) {tclock:.2f}s forwards">'
                 f'<rect x="{px-1:.1f}" y="{y-17}" width="{mw:.1f}" height="23" fill="{t["term"]}"/>'
                 f'<rect class="tc" x="{px:.1f}" y="{y-14}" width="9" height="18" fill="{PROMPT}" opacity="0" '
                 f'style="animation:cv {dur+0.25:.2f}s linear {tclock:.2f}s forwards"/></g>')
        b.append(f'<style>@keyframes tm{n}{{to{{transform:translateX({mw:.1f}px)}}}}</style>')
        tclock += dur + 0.3
        y += lh
    b.append('<style>@keyframes cv{0%,99%{opacity:1}100%{opacity:0}}</style>')
    y += lh
    tclock += 0.2
    sep = "-[ RECORD 1 ]" + "-" * 50
    b.append(f'<text x="{x0}" y="{y}" font-size="{size}" class="m f" fill="{DIM}" style="animation-delay:{tclock:.2f}s">{sep}</text>')
    y += lh
    kw = max(len(k) for k, _ in record)
    for k, v in record:
        tclock += 0.09
        b.append(f'<text x="{x0}" y="{y}" font-size="{size}" class="m f" xml:space="preserve" style="animation-delay:{tclock:.2f}s">'
                 f'<tspan fill="{KEY}">{escape(k.ljust(kw))}</tspan><tspan fill="{DIM}"> | </tspan><tspan fill="{VAL}">{escape(v)}</tspan></text>')
        y += lh
    tclock += 0.15
    b.append(f'<text x="{x0}" y="{y}" font-size="{size}" class="m f" fill="{DIM}" style="animation-delay:{tclock:.2f}s">(1 row)</text>')
    y += lh * 2
    tclock += 0.3
    b.append(f'<text x="{x0}" y="{y}" font-size="{size}" class="m f" fill="{PROMPT}" style="animation-delay:{tclock:.2f}s">kmehul=# </text>')
    b.append(f'<rect class="cur" x="{x0 + 9*cw:.1f}" y="{y-14}" width="9" height="18" fill="{PROMPT}" opacity="0" '
             f'style="animation:blink 1.1s step-end {tclock:.2f}s infinite"/>')
    body = "".join(b)
    label = ("psql query: SELECT * FROM analysts WHERE github = 'kmehul'. Result: " +
             "; ".join(f"{k}: {v}" for k, v in record))
    return svg(W, H, body, label)


# ---------------------------------------------------------------- experience
def experience(t):
    W, H = 840, 300
    b = [card(t, W, H), eyebrow(t, 44, 56, "Experience", 0.05),
         txt(796, 56, "Oct 2024 – May 2025", 14, t["sub"], 500, delay=0.05, anchor="end"),
         txt(44, 96, "Data Analyst", 30, t["text"], 700, delay=0.12, extra=' letter-spacing="-0.5"'),
         txt(44, 124, "Rebecca Everlene Trust Company  ·  Chicago, USA (Remote)", 16, t["sub"], 500, delay=0.18),
         txt(44, 160, "Built a grants intelligence dataset from IRS 990 filings and foundation websites, then", 15, t["text"], delay=0.26),
         txt(44, 182, "audited, gap-analyzed and enriched it into submission-ready grant packages for the team.", 15, t["text"], delay=0.3)]
    stats = [("~8,000", "foundation records audited"),
             ("~6,300", "sorted into a 12-month pipeline"),
             ("~80%", "submission-ready before deadlines")]
    tw, gap = (752 - 2 * 16) / 3, 16
    for i, (n, l) in enumerate(stats):
        x = 44 + i * (tw + gap)
        d = 0.4 + i * 0.1
        b.append(f'<g class="a" style="animation-delay:{d:.2f}s"><rect x="{x:.1f}" y="206" width="{tw:.1f}" height="70" rx="14" fill="{t["chip"]}"/>'
                 f'<text x="{x+18:.1f}" y="240" font-size="26" font-weight="700" fill="url(#ng)" letter-spacing="-0.5">{escape(n)}</text>'
                 f'<text x="{x+18:.1f}" y="262" font-size="13" fill="{t["sub"]}">{escape(l)}</text></g>')
    return svg(W, H, "".join(b),
               "Experience: Data Analyst at Rebecca Everlene Trust Company, Oct 2024 to May 2025. "
               "About 8,000 foundation records audited, about 6,300 sorted into a 12-month grant pipeline, "
               "about 80% submission-ready before deadlines.",
               defs=grad_def("ng", 44, 796))


# ---------------------------------------------------------------- featured project
def citibike(t):
    W, H = 840, 452
    b = [card(t, W, H), eyebrow(t, 44, 58, "Featured project", 0.05),
         txt(796, 58, "Jun – Jul 2026", 14, t["sub"], 500, delay=0.05, anchor="end"),
         txt(44, 98, "Jersey City Last-Mile Mobility", 30, t["text"], 700, delay=0.1, extra=' letter-spacing="-0.5"'),
         txt(44, 126, "A CitiBike demand and rebalancing analysis", 17, t["sub"], 500, delay=0.16)]
    desc = ["Which stations run out of bikes, and when?",
            "Cleaned 95,350 trips in pandas, modeled",
            "station flow and imbalance in PostgreSQL,",
            "and mapped all 108 stations in Tableau",
            "with two city-separated rebalancing routes."]
    for i, s in enumerate(desc):
        b.append(txt(44, 170 + i * 22, s, 15, t["text"] if i else t["text"], 600 if i == 0 else 400, delay=0.22 + i * 0.04))
    b.append(chips(t, 44, 284, ["PostgreSQL", "pandas", "Tableau"], 0.4))
    stats = [("94,689", "verified trips"), ("10", "priority stations"), ("17.8%", "peak daily imbalance")]
    for i, (n, l) in enumerate(stats):
        x = 44 + i * 132
        b.append(f'<g class="a" style="animation-delay:{0.5 + i*0.08:.2f}s">'
                 f'<text x="{x}" y="350" font-size="28" font-weight="700" fill="url(#ng)" letter-spacing="-0.6">{n}</text>'
                 f'<text x="{x}" y="370" font-size="13" fill="{t["sub"]}">{l}</text></g>')
    # right panel: ride length, figures from the project's Findings
    px, py, pw, ph = 456, 150, 340, 216
    b.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="16" fill="{t["chip"]}" class="a" style="animation-delay:.3s"/>')
    b.append(txt(px + 22, py + 34, "Average ride length", 14, t["text"], 600, delay=0.35))
    b.append(txt(px + 22, py + 53, "Members commute; casual riders linger.", 12.5, t["sub"], delay=0.38))
    scale = 220 / 15
    for i, (who, mins, col) in enumerate((("Member", 8, GRAD[0]), ("Casual", 15, GRAD[2]))):
        ly = py + 80 + i * 50
        b.append(txt(px + 22, ly, who, 13, t["sub"], 500, delay=0.45))
        b.append(f'<rect x="{px+22}" y="{ly+8}" width="{mins*scale:.0f}" height="22" rx="6" fill="{col}" class="gx" style="animation-delay:{0.6 + i*0.15:.2f}s"/>')
        b.append(txt(px + 30 + mins * scale, ly + 25, f"{mins} min", 14, t["text"], 700, delay=1.2 + i * 0.15))
    b.append(f'<line x1="{px+22}" x2="{px+pw-22}" y1="{py+176}" y2="{py+176}" stroke="{t["line"]}"/>')
    b.append(txt(px + 22, py + 200, "Busiest station", 13, t["sub"], 500, delay=0.6))
    b.append(txt(px + pw - 22, py + 200, "Grove St PATH", 14, t["text"], 700, delay=0.6, anchor="end"))
    # verification callout
    b.append(f'<g class="a" style="animation-delay:.75s"><rect x="44" y="396" width="752" height="36" rx="10" fill="{t["tint"]}"/>'
             f'<circle cx="64" cy="414" r="8" fill="{t["blue"]}"/>'
             f'<path d="M60 414.2 l2.8 2.8 l5-5.4" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
             f'<text x="82" y="418.5" font-size="13" fill="{t["text"]}">Independent AI code review caught a NULL bug and a sign error in 44 of 81 stations, both fixed before publishing.</text></g>')
    return svg(W, H, "".join(b),
               "Featured project: Jersey City Last-Mile Mobility, a CitiBike analysis. 94,689 verified trips, "
               "10 priority stations, 17.8% peak daily imbalance. Members average 8 minute rides, casual riders 15. "
               "Busiest station: Grove St PATH.",
               defs=grad_def("ng", 44, 420))


# ---------------------------------------------------------------- small project cards
def schema(t, x, y, w, h, facts, left, right, delay):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{t["chip"]}"/>']
    cx, cy = x + w / 2, y + h / 2
    fw, dw, ph = 128, 104, 24
    fy0 = cy - (len(facts) * ph + (len(facts) - 1) * 12) / 2

    def col(names, side):
        n = len(names)
        span = h - 36
        res = []
        for i, nm in enumerate(names):
            yy = y + 18 + (span - ph) * (i / (n - 1) if n > 1 else 0.5)
            xx = x + 14 if side == "l" else x + w - 14 - dw
            res.append((xx, yy, nm))
        return res
    dims = col(left, "l") + col(right, "r")
    for i, (xx, yy, nm) in enumerate(dims):
        sx = xx + dw if xx < cx else xx
        tx = cx - fw / 2 if xx < cx else cx + fw / 2
        ln = abs(tx - sx) + abs(cy - (yy + ph / 2))
        out.append(f'<path d="M{sx:.1f} {yy+ph/2:.1f} C{(sx+tx)/2:.1f} {yy+ph/2:.1f} {(sx+tx)/2:.1f} {cy:.1f} {tx:.1f} {cy:.1f}" '
                   f'fill="none" stroke="{t["line"]}" stroke-width="1.5" stroke-dasharray="{ln:.0f}" stroke-dashoffset="{ln:.0f}" '
                   f'class="d" style="animation-delay:{delay + 0.4 + i*0.06:.2f}s;animation-duration:.8s"/>')
    for i, (xx, yy, nm) in enumerate(dims):
        out.append(f'<g class="a" style="animation-delay:{delay + 0.2 + i*0.06:.2f}s"><rect x="{xx:.1f}" y="{yy:.1f}" width="{dw}" height="{ph}" rx="7" '
                   f'fill="{t["card"]}" stroke="{t["line"]}"/><text x="{xx+dw/2:.1f}" y="{yy+16:.1f}" font-size="10.5" class="m" '
                   f'fill="{t["sub"]}" text-anchor="middle">{nm}</text></g>')
    for i, nm in enumerate(facts):
        yy = fy0 + i * (ph + 12)
        out.append(f'<g class="a" style="animation-delay:{delay + 0.1 + i*0.08:.2f}s"><rect x="{cx-fw/2:.1f}" y="{yy:.1f}" width="{fw}" height="{ph}" rx="7" '
                   f'fill="url(#ng)"/><text x="{cx:.1f}" y="{yy+16:.1f}" font-size="10.5" class="m" font-weight="600" '
                   f'fill="#ffffff" text-anchor="middle">{nm}</text></g>')
    return "".join(out)


def small_card(t, when, title, desc, tags, facts, left, right, stats, label):
    W, H = 410, 452
    b = [card(t, W, H), schema(t, 20, 20, 370, 156, facts, left, right, 0.0),
         eyebrow(t, 26, 210, when, 0.3),
         txt(26, 242, title, 23, t["text"], 700, delay=0.35, extra=' letter-spacing="-0.4"')]
    for i, s in enumerate(desc):
        b.append(txt(26, 272 + i * 21, s, 14, t["text"], delay=0.4 + i * 0.04))
    for i, (n, l) in enumerate(stats):
        x = 26 + i * 124
        b.append(f'<g class="a" style="animation-delay:{0.5 + i*0.08:.2f}s">'
                 f'<text x="{x}" y="368" font-size="24" font-weight="700" fill="url(#ng)" letter-spacing="-0.5">{n}</text>'
                 f'<text x="{x}" y="386" font-size="12" fill="{t["sub"]}">{l}</text></g>')
    b.append(chips(t, 26, 408, tags, 0.6, size=12))
    return svg(W, H, "".join(b), label, defs=grad_def("ng", 26, 390))


def imdb(t):
    return small_card(
        t, "Dec 2023 – Apr 2024", "IMDB Movie Data Analysis",
        ["~1M records from 17 sources (SQL tables,",
         "JSON, TSV) loaded with Talend into a",
         "12-table warehouse on Azure SQL."],
        ["E/R Studio", "Talend", "Alteryx", "Tableau"],
        ["fct_ratings", "fct_movierevenue"],
        ["dim_movies", "dim_person", "dim_genre"], ["dim_region", "dim_date", "dim_profession"],
        [("12", "warehouse tables"), ("~8.9M", "warehouse rows"), ("17", "source files")],
        "IMDB Movie Data Analysis: about 1 million source records from 17 sources loaded with Talend into a "
        "12-table dimensional warehouse of about 8.9 million rows on Azure SQL.")


def food(t):
    return small_card(
        t, "Oct – Nov 2023", "California Food Inspections",
        ["Sonoma County facility inspections, profiled",
         "in Alteryx, loaded into Azure SQL with",
         "Talend, and mapped by risk in Tableau."],
        ["E/R Studio", "Talend", "Alteryx", "Tableau"],
        ["fct_inspection", "fct_insp_violation"],
        ["dim_business", "dim_date"], ["dim_violation"],
        [("5", "table star schema"), ("2", "fact tables"), ("3", "dimensions")],
        "California Food Inspection Analysis: a 5-table star schema of Sonoma County food facility inspections, "
        "profiled in Alteryx, loaded into Azure SQL with Talend, visualized in Tableau.")


# ---------------------------------------------------------------- side project
def tracker(t):
    W, H = 840, 300
    b = [card(t, W, H), eyebrow(t, 44, 56, "Side project", 0.05),
         f'<g class="a" style="animation-delay:.1s"><rect x="664" y="38" width="132" height="24" rx="12" fill="url(#vg)"/>'
         f'<text x="730" y="54.5" font-size="11" font-weight="700" fill="#fff" text-anchor="middle" letter-spacing="1">100% VIBE CODED</text></g>',
         txt(44, 98, "Apple Music Release Tracker", 28, t["text"], 700, delay=0.12, extra=' letter-spacing="-0.5"')]
    desc = ["Apple Music's new-release alerts kept missing drops, so",
            "this polls the iTunes API every 6 hours and sends a phone",
            "push and an email the moment a release goes live.",
            "Built entirely by prompting AI: I directed and tested it."]
    for i, s in enumerate(desc):
        b.append(txt(44, 132 + i * 22, s, 15, t["sub"] if i == 3 else t["text"], 400, delay=0.2 + i * 0.04,
                     extra=' font-style="italic"' if i == 3 else ""))
    for i, (n, l) in enumerate((("53", "artists watched"), ("4,808", "releases logged"), ("0", "pip dependencies"))):
        x = 44 + i * 132
        b.append(f'<g class="a" style="animation-delay:{0.4 + i*0.08:.2f}s">'
                 f'<text x="{x}" y="256" font-size="28" font-weight="700" fill="url(#ng)" letter-spacing="-0.6">{n}</text>'
                 f'<text x="{x}" y="276" font-size="13" fill="{t["sub"]}">{l}</text></g>')
    notes = [("ntfy", "New release", "An artist on your list dropped a single"),
             ("Gmail", "New release alert", "1 new release is out on Apple Music")]
    for i, (app, head, body) in enumerate(notes):
        x, y = 512, 108 + i * 84
        b.append(f'<g class="a" style="animation-delay:{0.7 + i*0.35:.2f}s"><rect x="{x}" y="{y}" width="284" height="68" rx="16" fill="{t["chip"]}" stroke="{t["line"]}"/>'
                 f'<rect x="{x+14}" y="{y+16}" width="36" height="36" rx="9" fill="url(#vg)"/>'
                 f'<path d="M{x+28} {y+41} V{y+25} L{x+38} {y+23} V{y+39}" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>'
                 f'<circle cx="{x+25.5}" cy="{y+41}" r="2.8" fill="#fff"/><circle cx="{x+35.5}" cy="{y+39}" r="2.8" fill="#fff"/>'
                 f'<text x="{x+62}" y="{y+29}" font-size="13" font-weight="600" fill="{t["text"]}">{escape(head)}</text>'
                 f'<text x="{x+270}" y="{y+29}" font-size="11" fill="{t["sub"]}" text-anchor="end">{app} · now</text>'
                 f'<text x="{x+62}" y="{y+49}" font-size="12" fill="{t["sub"]}">{escape(body)}</text></g>')
    defs = grad_def("ng", 44, 420) + (f'<linearGradient id="vg" x1="0" y1="0" x2="1" y2="1">'
                                      f'<stop offset="0" stop-color="#fa2d48"/><stop offset="1" stop-color="{GRAD[2]}"/></linearGradient>')
    return svg(W, H, "".join(b),
               "Side project, 100% vibe coded: Apple Music Release Tracker. Polls the iTunes API every 6 hours for "
               "53 artists and sends a push and an email on new releases. 4,808 releases logged, no pip dependencies.",
               defs=defs)


# ---------------------------------------------------------------- toolkit
def toolkit(t):
    cols = [("Query & code", [("SQL", "#0090f7"), ("Python", "#3776ab"), ("pandas", "#e70488"), ("matplotlib, seaborn", "#4c72b0")]),
            ("Databases", [("PostgreSQL", "#336791"), ("SQL Server", "#cc2927"), ("Azure SQL", "#0078d4"), ("MySQL", "#00758f")]),
            ("BI & visualization", [("Tableau", "#e97627"), ("Power BI", "#f2c811")]),
            ("Prep & modeling", [("Alteryx", "#0078c0"), ("Talend", "#ff6d70"), ("E/R Studio", "#94c941")])]
    W, H = 840, 310
    b = [card(t, W, H), eyebrow(t, 44, 56, "Toolkit", 0.05),
         txt(796, 56, "Built with, shipped with", 14, t["sub"], 500, delay=0.05, anchor="end")]
    cw, gap = (752 - 3 * 12) / 4, 12
    k = 0
    for i, (head, items) in enumerate(cols):
        x = 44 + i * (cw + gap)
        b.append(txt(x, 94, head, 13, t["sub"], 600, delay=0.1 + i * 0.05))
        for j, (name, colr) in enumerate(items):
            y = 110 + j * 46
            b.append(f'<g class="a" style="animation-delay:{0.2 + k*0.04:.2f}s"><rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="36" rx="18" fill="{t["chip"]}"/>'
                     f'<circle cx="{x+18:.1f}" cy="{y+18}" r="5" fill="{colr}"/>'
                     f'<text x="{x+32:.1f}" y="{y+23}" font-size="14" font-weight="500" fill="{t["text"]}">{escape(name)}</text></g>')
            k += 1
    return svg(W, H, "".join(b), "Toolkit. " + ". ".join(f"{h}: " + ", ".join(n for n, _ in it) for h, it in cols) + ".")


# ---------------------------------------------------------------- education
def education(t):
    W, H = 840, 236
    b = [card(t, W, H), eyebrow(t, 44, 56, "Education", 0.05),
         f'<line x1="44" x2="796" y1="92" y2="92" stroke="url(#ng)" stroke-width="2" stroke-dasharray="752" stroke-dashoffset="752" class="d" style="animation-delay:.15s"/>']
    rows = [("Sep 2022 – May 2024", "MS, Information Systems", "Northeastern University", "Boston, USA"),
            ("Jul 2016 – May 2020", "B.Tech, Information Technology", "SRM Institute of Science and Technology", "Chennai, India")]
    for i, (when, deg, school, place) in enumerate(rows):
        x = 44 + i * 396
        d = 0.35 + i * 0.25
        b.append(f'<g class="f" style="animation-delay:{d:.2f}s"><circle cx="{x+6}" cy="92" r="6" fill="{GRAD[i*2]}" stroke="{t["card"]}" stroke-width="3"/></g>')
        b.append(eyebrow(t, x, 130, when, d + 0.05))
        b.append(txt(x, 160, deg, 20, t["text"], 700, delay=d + 0.1, extra=' letter-spacing="-0.3"'))
        b.append(txt(x, 186, school, 15, t["text"], 500, delay=d + 0.15))
        b.append(txt(x, 208, place, 13, t["sub"], delay=d + 0.2))
    return svg(W, H, "".join(b),
               "Education: MS Information Systems, Northeastern University, 2022 to 2024. "
               "B.Tech Information Technology, SRM Institute of Science and Technology, 2016 to 2020.",
               defs=grad_def("ng", 44, 796))


def main():
    OUT.mkdir(exist_ok=True)
    for theme, t in THEMES.items():
        files = {"header": header(t), "about": terminal(t), "experience": experience(t),
                 "citibike": citibike(t), "imdb": imdb(t), "food": food(t), "tracker": tracker(t),
                 "toolkit": toolkit(t), "education": education(t)}
        for label, primary, slug in (("LinkedIn", True, "linkedin"), ("Portfolio", False, "portfolio"),
                                     ("Email", False, "email"), ("Live dashboard", True, "dashboard"),
                                     ("View repository", False, "repo")):
            files[f"btn-{slug}"] = button(t, label, primary)
        for name, content in files.items():
            (OUT / f"{name}-{theme}.svg").write_text(content)
    print("wrote", len(list(OUT.glob("*.svg"))), "files to", OUT)


if __name__ == "__main__":
    main()
