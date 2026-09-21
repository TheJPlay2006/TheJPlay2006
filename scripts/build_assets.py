#!/usr/bin/env python3
"""Builds the static animated SVGs in assets/ (pure SVG/SMIL, no external services)."""
import base64, html, pathlib, urllib.request

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)
CYAN, PURPLE, BG, PANEL, TEXT, MUTED = "#36BCF7", "#9D4EDD", "#0D1117", "#161B22", "#E6EDF3", "#8B949E"
SANS = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
MONO = "'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', monospace"
GRAD = (f'<linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CYAN}"/>'
        f'<stop offset="1" stop-color="{PURPLE}"/></linearGradient>')
esc = html.escape


def save(name, svg):
    (OUT / name).write_text(svg)
    print(f"{name:20s} {len(svg)/1024:.1f} KB")


# ---------------------------------------------------------------- divider
def divider():
    save("divider.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="14" viewBox="0 0 800 14">
<defs>
<linearGradient id="f" x1="0" y1="0" x2="1" y2="0" spreadMethod="reflect" gradientUnits="objectBoundingBox">
<stop offset="0" stop-color="{CYAN}"/><stop offset="0.5" stop-color="{PURPLE}"/><stop offset="1" stop-color="{CYAN}"/>
<animate attributeName="x1" values="0;1;0" dur="6s" repeatCount="indefinite"/>
<animate attributeName="x2" values="1;2;1" dur="6s" repeatCount="indefinite"/>
</linearGradient>
<radialGradient id="dot"><stop offset="0" stop-color="#fff"/><stop offset="0.4" stop-color="{CYAN}" stop-opacity="0.8"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
</defs>
<rect x="20" y="6" width="760" height="2" rx="1" fill="url(#f)" opacity="0.85"/>
<circle r="7" cy="7" fill="url(#dot)"><animate attributeName="cx" values="20;780;20" dur="5s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/></circle>
</svg>''')


# ---------------------------------------------------------------- terminal
def terminal():
    # (kind, text)  kind: cmd | out | ok
    script = [
        ("cmd", "whoami"), ("out", "Jairo Herrera Romero"),
        ("cmd", "cat about.txt"), ("out", "IT Engineering student @ UTN, Costa Rica"),
        ("cmd", "ls skills/"), ("out", "web-dev/  databases/  ai/  infrastructure/"),
        ("cmd", "echo $GOAL"), ("ok", "Grow professionally and earn my place in a tech company"),
        ("cmd", "git commit -m \"learning every day\""), ("ok", "[main] 1 more step forward"),
    ]
    CW, LH, X0, Y0 = 8.45, 26, 34, 92           # char width, line height
    TYPE, PAUSE_OUT, PAUSE_NEXT, HOLD = 0.055, 0.35, 0.45, 4.0
    t, sched = 0.4, []
    for kind, text in script:
        if kind == "cmd":
            sched.append((kind, text, t, len(text) * TYPE)); t += len(text) * TYPE + PAUSE_OUT
        else:
            sched.append((kind, text, t, 0)); t += PAUSE_NEXT
    D = t + HOLD
    H = Y0 + LH * len(script) + 26
    W = 820
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
             f'<defs>{GRAD}</defs>',
             f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" fill="{BG}" stroke="url(#g)" stroke-width="1.5"/>',
             f'<path d="M1 13a12 12 0 0 1 12-12h{W-26}a12 12 0 0 1 12 12v30H1z" fill="{PANEL}"/>',
             '<circle cx="24" cy="22" r="6" fill="#FF5F56"/><circle cx="46" cy="22" r="6" fill="#FFBD2E"/><circle cx="68" cy="22" r="6" fill="#27C93F"/>',
             f'<text x="{W/2}" y="27" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">jairo@utn: ~/profile</text>']
    for i, (kind, text, start, dur) in enumerate(sched):
        y = Y0 + i * LH
        kt = start / D
        if kind == "cmd":
            n = len(text)
            # keyTimes: 0 -> hidden until start, then one step per char, hold to end
            kts = [0.0, round(kt, 5)] + [round((start + k * TYPE) / D, 5) for k in range(1, n + 1)]
            vs = [0, 0] + [round(k * CW, 1) for k in range(1, n + 1)]
            # discrete animation needs len(values)==len(keyTimes)
            cid = f"c{i}"
            parts.append(f'<clipPath id="{cid}"><rect x="{X0+18}" y="{y-16}" width="0" height="22">'
                         f'<animate attributeName="width" values="{";".join(map(str, vs))}" keyTimes="{";".join(map(str, kts))}" '
                         f'calcMode="discrete" dur="{D:.2f}s" repeatCount="indefinite"/></rect></clipPath>')
            parts.append(f'<text x="{X0}" y="{y}" font-family="{MONO}" font-size="14" fill="{CYAN}" opacity="0">$'
                         f'<animate attributeName="opacity" values="0;1;1" keyTimes="0;{kt:.5f};1" calcMode="discrete" dur="{D:.2f}s" repeatCount="indefinite"/></text>')
            parts.append(f'<text x="{X0+18}" y="{y}" font-family="{MONO}" font-size="14" fill="{TEXT}" clip-path="url(#{cid})" xml:space="preserve">{esc(text)}</text>')
        else:
            col = "#3FB950" if kind == "ok" else MUTED
            parts.append(f'<text x="{X0+18}" y="{y}" font-family="{MONO}" font-size="14" fill="{col}" opacity="0" xml:space="preserve">{esc(text)}'
                         f'<animate attributeName="opacity" values="0;1;1" keyTimes="0;{kt:.5f};1" calcMode="discrete" dur="{D:.2f}s" repeatCount="indefinite"/></text>')
    # blinking cursor block at the end
    cy = Y0 + len(script) * LH
    parts.append(f'<text x="{X0}" y="{cy}" font-family="{MONO}" font-size="14" fill="{CYAN}">$</text>'
                 f'<rect x="{X0+18}" y="{cy-13}" width="8" height="17" fill="{CYAN}"><animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect>')
    parts.append('</svg>')
    save("terminal.svg", "\n".join(parts))


# ---------------------------------------------------------------- marquee
ROWS = [
    ["java", "python", "js", "php", "cs", "go", "cpp", "html", "css", "react", "bootstrap"],
    ["django", "laravel", "dotnet", "spring", "mysql", "sqlite", "postgres", "git", "github", "vscode", "docker", "figma", "postman", "wordpress", "linux", "nginx"],
]


def fetch_icon(slug):
    url = f"https://skillicons.dev/icons?i={slug}&theme=dark"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (profile-readme-builder)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return base64.b64encode(r.read()).decode()


def marquee():
    icons = {s: fetch_icon(s) for row in ROWS for s in row}
    S, GAP, W = 52, 22, 900
    defs = [GRAD, f'<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.08" stop-color="#fff"/>'
            f'<stop offset="0.92" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>',
            f'<mask id="m"><rect width="{W}" height="200" fill="url(#fade)"/></mask>']
    for s, b in icons.items():
        defs.append(f'<image id="i-{s}" width="{S}" height="{S}" href="data:image/svg+xml;base64,{b}"/>')
    body, y = [], 12
    for r, row in enumerate(ROWS):
        step = S + GAP
        set_w = step * len(row)
        reps = -(-W // set_w) + 1            # enough copies so the loop is seamless
        items = "".join(f'<use href="#i-{row[k % len(row)]}" x="{k*step}" y="0"/>' for k in range(reps * len(row) * 1 + len(row)))
        # duplicate the row set so translating by -set_w loops seamlessly
        frm, to = (0, -set_w) if r % 2 == 0 else (-set_w, 0)
        dur = 26 + r * 6
        body.append(f'<g transform="translate(0 {y})"><g><animateTransform attributeName="transform" type="translate" from="{frm} 0" to="{to} 0" dur="{dur}s" repeatCount="indefinite"/>{items}</g></g>')
        y += S + 18
    H = y - 6
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{"".join(defs)}</defs>'
           f'<g mask="url(#m)">{"".join(body)}</g></svg>')
    save("marquee.svg", svg)


# ---------------------------------------------------------------- focus cards
def focus():
    cards = [("🌐", "Frontend Development", ["Clean, useful and easy-to-use", "interfaces, layouts and web experiences."]),
             ("🤖", "Artificial Intelligence", ["How powerful AI can be for creating", "tools and solving real problems."]),
             ("🗄️", "Databases", ["Fundamentals, SQL skills,", "relationships and data modeling."]),
             ("🛠️", "Support & Infrastructure", ["Technical support, systems, tools and", "the infrastructure behind solutions."])]
    W, CWD, CH, G = 880, 420, 128, 20
    H = CH * 2 + G + 12
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{GRAD}</defs>']
    for i, (ico, title, lines) in enumerate(cards):
        x, y = 10 + (i % 2) * (CWD + G), 6 + (i // 2) * (CH + G)
        d = i * 0.6
        p.append(f'<g transform="translate({x} {y})">'
                 f'<rect width="{CWD}" height="{CH}" rx="14" fill="{PANEL}" stroke="url(#g)" stroke-width="1.5">'
                 f'<animate attributeName="stroke-opacity" values="0.35;1;0.35" dur="4s" begin="{d}s" repeatCount="indefinite"/></rect>'
                 f'<rect width="5" height="{CH}" rx="2.5" fill="url(#g)"/>'
                 f'<text x="36" y="52" font-size="30">{ico}<animateTransform attributeName="transform" type="translate" values="0 0;0 -4;0 0" dur="3s" begin="{d}s" repeatCount="indefinite"/></text>'
                 f'<text x="84" y="46" font-family="{SANS}" font-size="20" font-weight="700" fill="{TEXT}">{esc(title)}</text>'
                 f'<text x="84" y="76" font-family="{SANS}" font-size="14" fill="{MUTED}">{esc(lines[0])}</text>'
                 f'<text x="84" y="98" font-family="{SANS}" font-size="14" fill="{MUTED}">{esc(lines[1])}</text></g>')
    p.append('</svg>')
    save("focus.svg", "\n".join(p))


# ---------------------------------------------------------------- growing (loading bars)
def growing():
    items = [("🌐", "Improving my web development skills"), ("🗄️", "Strengthening database fundamentals"),
             ("🛠️", "Practicing with real software projects"), ("🤖", "Learning AI tools and development workflows"),
             ("🧩", "Building better programming logic"), ("📁", "Improving my professional portfolio"),
             ("🌱", "Growing with consistency and perseverance")]
    W, RH = 760, 46
    H = RH * len(items) + 24
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<defs>{GRAD}<linearGradient id="sh" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>']
    for i, (ico, text) in enumerate(items):
        y = 14 + i * RH
        d = i * 0.35
        bx, bw = 470, 250
        p.append(f'<g transform="translate(0 {y})">'
                 f'<text x="24" y="22" font-size="20">{ico}</text>'
                 f'<text x="60" y="22" font-family="{SANS}" font-size="16" fill="{TEXT}">{esc(text)}</text>'
                 f'<clipPath id="b{i}"><rect x="{bx}" y="7" width="{bw}" height="12" rx="6"/></clipPath>'
                 f'<rect x="{bx}" y="7" width="{bw}" height="12" rx="6" fill="{PANEL}" stroke="#30363D"/>'
                 f'<g clip-path="url(#b{i})"><rect x="{bx}" y="7" width="0" height="12" fill="url(#g)">'
                 f'<animate attributeName="width" values="0;{bw*0.55:.0f};{bw*0.55:.0f};0" keyTimes="0;0.35;0.9;1" dur="6s" begin="{d}s" repeatCount="indefinite"/></rect>'
                 f'<rect x="{bx-60}" y="7" width="60" height="12" fill="url(#sh)"><animate attributeName="x" values="{bx-60};{bx+bw}" dur="2.2s" begin="{d}s" repeatCount="indefinite"/></rect></g></g>')
    p.append('</svg>')
    save("growing.svg", "\n".join(p))




# ---------------------------------------------------------------- pills / buttons
def pill_shell(w, h, inner, fill=PANEL, stroke="url(#g)", uid="p"):
    """Rounded pill with animated shimmer sweeping across it."""
    r = h / 2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{GRAD}'
            f'<linearGradient id="sh" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<clipPath id="c"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{r-1}"/></clipPath></defs>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{r-1}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            f'<g clip-path="url(#c)"><rect x="-40" y="0" width="40" height="{h}" fill="url(#sh)"><animate attributeName="x" values="-40;{w+40};{w+40}" keyTimes="0;0.5;1" dur="5s" repeatCount="indefinite"/></rect></g>'
            f'{inner}</svg>')


def icon_path(slug):
    import re
    req = urllib.request.Request(f"https://cdn.jsdelivr.net/npm/simple-icons@11.14.0/icons/{slug}.svg", headers={"User-Agent": "Mozilla/5.0"})
    return re.search(r' d="([^"]+)"', urllib.request.urlopen(req, timeout=30).read().decode()).group(1)


def contact_buttons():
    items = [("linkedin", "LinkedIn", "jairoshr", "#0A66C2"), ("gmail", "Gmail", "jh599350@gmail.com", "#EA4335"),
             ("github", "GitHub", "TheJPlay2006", "#30363D")]
    for slug, name, handle, col in items:
        d = icon_path(slug)
        w, h = int(max(len(name) * 8.5, len(handle) * 7.4) + 100), 52
        inner = (f'<g transform="translate(22 14) scale(1)"><path transform="scale(1)" d="{d}" fill="#fff"/></g>'
                 f'<text x="58" y="23" font-family="{SANS}" font-size="12" fill="#fff" opacity="0.8">{name}</text>'
                 f'<text x="58" y="41" font-family="{SANS}" font-size="14" font-weight="700" fill="#fff">{esc(handle)}</text>')
        save(f"contact-{slug}.svg", pill_shell(w, h, inner, fill=col, stroke="#ffffff33"))





# ---------------------------------------------------------------- CV sections
import textwrap


def wrap(text, px, size):
    return textwrap.wrap(text, width=max(10, int(px / (size * 0.53))))


def chips(x, y, items, maxx, col=CYAN, delay=0.0):
    """Row(s) of small rounded chips starting at (x, y); returns (svg, next_y)."""
    out, cx, cy = [], x, y
    for it in items:
        w = int(len(it) * 6.8 + 24)
        if cx + w > maxx:
            cx, cy = x, cy + 32
        out.append(f'<g transform="translate({cx} {cy})"><rect width="{w}" height="24" rx="12" fill="{col}" fill-opacity="0.12" stroke="{col}" stroke-opacity="0.55"/>'
                   f'<text x="{w/2}" y="16" text-anchor="middle" font-family="{SANS}" font-size="12" fill="{TEXT}">{esc(it)}</text></g>')
        cx += w + 8
    return "".join(out), cy + 24


def experience():
    jobs = [
        ("Junior Full-Stack Developer", "ForeSight Solutions, SRL", "Oct 2025 – Present",
         ["Development and maintenance of web solutions, business sites, interfaces and features for clients.",
          "Work with servers, databases, automations and bots, plus technical support and incident resolution.",
          "Technical documentation and adapting digital platforms to business needs and IT best practices."],
         ["HTML", "CSS", "JavaScript", "PHP", "WordPress", "SQL", "Git/GitHub", "Linux", "Automation"]),
        ("Web Designer / Website Developer", "Independent / Freelance", "Jan 2025 – Present",
         ["Design and build modern, fast, responsive websites for companies, brands and entrepreneurs.",
          "Corporate sites, landing pages, digital catalogs and informational pages focused on visual clarity and user experience."],
         ["HTML", "CSS", "JavaScript", "WordPress", "UI", "Responsive design", "GitHub"]),
    ]
    W, X, CW = 840, 78, 740
    body, y = [], 12
    dots = []
    for i, (role, company, period, bullets, stack) in enumerate(jobs):
        lines = [l for b in bullets for l in (["• " + wrap(b, CW - 60, 13)[0]] + ["   " + w for w in wrap(b, CW - 60, 13)[1:]])]
        # rebuild wrapped bullets keeping first-line bullet mark
        lines = []
        for b in bullets:
            ws = wrap(b, CW - 60, 13)
            lines += [("•  " if k == 0 else "    ") + w for k, w in enumerate(ws)]
        cy0 = y
        ty = cy0 + 84 + 20 * len(lines)
        chip_svg, end = chips(X + 26, ty + 4, stack, X + CW - 20)
        h = end - cy0 + 24
        pw = int(len(period) * 7.4 + 28)
        d = i * 0.7
        body.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.7s" begin="{d}s" fill="freeze"/>'
                    f'<animateTransform attributeName="transform" type="translate" from="0 14" to="0 0" dur="0.7s" begin="{d}s" fill="freeze"/>'
                    f'<rect x="{X}" y="{cy0}" width="{CW}" height="{h}" rx="16" fill="{PANEL}" stroke="url(#g)" stroke-width="1.5"/>'
                    f'<text x="{X+26}" y="{cy0+38}" font-family="{SANS}" font-size="20" font-weight="700" fill="{TEXT}">{esc(role)}</text>'
                    f'<text x="{X+26}" y="{cy0+62}" font-family="{SANS}" font-size="14.5" font-weight="600" fill="{CYAN}">{esc(company)}</text>'
                    f'<g transform="translate({X+CW-26-pw} {cy0+18})"><rect width="{pw}" height="28" rx="14" fill="{PURPLE}" fill-opacity="0.16" stroke="{PURPLE}" stroke-opacity="0.8"/>'
                    f'<text x="{pw/2}" y="19" text-anchor="middle" font-family="{SANS}" font-size="13" fill="{TEXT}">{period}</text></g>'
                    + "".join(f'<text x="{X+26}" y="{cy0+92+k*20}" font-family="{SANS}" font-size="13" fill="{MUTED}" xml:space="preserve">{esc(l)}</text>' for k, l in enumerate(lines))
                    + chip_svg + '</g>')
        dots.append((cy0 + 34, d))
        y = cy0 + h + 20
    H = y - 4
    line = (f'<line x1="36" y1="20" x2="36" y2="{H-10}" stroke="{CYAN}" stroke-opacity="0.8" stroke-width="3" stroke-linecap="round" stroke-dasharray="{H}" stroke-dashoffset="{H}">'
            f'<animate attributeName="stroke-dashoffset" from="{H}" to="0" dur="1.6s" fill="freeze"/></line>')
    dot_svg = "".join(f'<circle cx="36" cy="{dy}" r="8" fill="{BG}" stroke="url(#g)" stroke-width="3"><animate attributeName="r" values="8;10;8" dur="2.6s" begin="{d}s" repeatCount="indefinite"/></circle>'
                      f'<line x1="46" y1="{dy}" x2="{X}" y2="{dy}" stroke="{PURPLE}" stroke-width="2" opacity="0.7"/>' for dy, d in dots)
    save("experience.svg", f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{GRAD}</defs>{line}{dot_svg}{"".join(body)}</svg>')


def project_card(fname, icon, title, tag, desc, stack, link=None):
    W, CW = 820, 820
    lines = wrap(desc, W - 110, 14)
    ty = 92 + 21 * len(lines)
    chip_svg, end = chips(34, ty + 2, stack, W - 30, col=PURPLE) if stack else ("", ty)
    if link:
        end = max(end, ty + 24)
        chip_svg += f'<text x="34" y="{ty+16}" font-family="{MONO}" font-size="14" fill="{CYAN}">↗ {esc(link)}</text>'
    H = end + 26
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{GRAD}</defs>'
           f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="{PANEL}" stroke="url(#g)" stroke-width="1.5"><animate attributeName="stroke-opacity" values="0.4;1;0.4" dur="5s" repeatCount="indefinite"/></rect>'
           f'<rect x="1" y="18" width="5" height="{H-36}" rx="2.5" fill="url(#g)"/>'
           f'<text x="34" y="46" font-size="26">{icon}</text>'
           f'<text x="76" y="44" font-family="{SANS}" font-size="20" font-weight="700" fill="{TEXT}">{esc(title)}</text>'
           f'<text x="76" y="64" font-family="{SANS}" font-size="13" fill="{CYAN}">{esc(tag)}</text>'
           + "".join(f'<text x="34" y="{92+k*21}" font-family="{SANS}" font-size="14" fill="{MUTED}">{esc(l)}</text>' for k, l in enumerate(lines))
           + chip_svg + '</svg>')
    save(fname, svg)


def projects():
    project_card("project-erp.svg", "🍫", "Two Little Monkeys ERP & POS", "Offline-first business system · chocolate shop & tour operator",
                 "POS, inventory, cash register, customers, suppliers, users, reports and backups, with synchronization through a REST API between a local SQLite database and a central PostgreSQL.",
                 ["C#", ".NET 8", "Avalonia UI", "MVVM", "ASP.NET Core", "REST API", "SQLite", "PostgreSQL", "QuestPDF", "Linux/Nginx"])
    project_card("project-restaurant.svg", "🔥", "Restaurante Parrillero", "Informational website · local restaurant",
                 "Responsive website that presents the restaurant clearly and improves its digital presence, with a functional experience that adapts to mobile devices.",
                 ["HTML", "CSS", "JavaScript", "Responsive design", "GitHub"])
    project_card("project-tiendahi.svg", "🛍️", "Tienda Hi", "Featured web project · real client",
                 "Modern, responsive and functional website designed and developed for a real business.",
                 [], link="tiendahi.com")


def credentials():
    certs = [("🌐", "CCNA: Enterprise Networking, Security, and Automation", "Cisco"),
             ("🐙", "GitHub Foundations", "Verified badge"),
             ("☁️", "AB-900T00: Microsoft 365 and AI Administration", "2026"),
             ("🐍", "Analysis and Automation with Python", "2026")]
    W, CWD, CH, G = 880, 420, 96, 20
    H = CH * 2 + G + 12
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{GRAD}</defs>']
    for i, (ico, name, issuer) in enumerate(certs):
        x, y = 10 + (i % 2) * (CWD + G), 6 + (i // 2) * (CH + G)
        ls = wrap(name, CWD - 96, 15)
        d = i * 0.5
        p.append(f'<g transform="translate({x} {y})"><rect width="{CWD}" height="{CH}" rx="14" fill="{PANEL}" stroke="url(#g)" stroke-width="1.5">'
                 f'<animate attributeName="stroke-opacity" values="0.35;1;0.35" dur="4.4s" begin="{d}s" repeatCount="indefinite"/></rect>'
                 f'<text x="26" y="{CH/2+11}" font-size="30">{ico}</text>'
                 + "".join(f'<text x="80" y="{36+k*20}" font-family="{SANS}" font-size="15" font-weight="700" fill="{TEXT}">{esc(l)}</text>' for k, l in enumerate(ls))
                 + f'<text x="80" y="{36+len(ls)*20+2}" font-family="{SANS}" font-size="13" fill="{CYAN}">{esc(issuer)}</text></g>')
    p.append('</svg>')
    save("certs.svg", "\n".join(p))

    # education / languages / strengths
    W, H = 900, 200
    cols = [10, 280, 550]
    cws = [250, 250, 340]
    cw = 250
    def box(x, title, ico):
        w = cws[cols.index(x)]
        return (f'<rect x="{x}" y="6" width="{w}" height="{H-12}" rx="14" fill="{PANEL}" stroke="url(#g)" stroke-width="1.5"/>'
                f'<text x="{x+22}" y="38" font-size="16">{ico}</text>'
                f'<text x="{x+50}" y="38" font-family="{SANS}" font-size="16" font-weight="700" fill="url(#g)">{title}</text>')
    edu = box(cols[0], "Education", "🎓")
    for k, l in enumerate(wrap("Information Technology Engineering", cw - 44, 15)):
        edu += f'<text x="{cols[0]+22}" y="{68+k*20}" font-family="{SANS}" font-size="15" font-weight="700" fill="{TEXT}">{esc(l)}</text>'
    edu += (f'<text x="{cols[0]+22}" y="112" font-family="{SANS}" font-size="13.5" fill="{TEXT}">Universidad Técnica Nacional</text>'
            f'<text x="{cols[0]+22}" y="132" font-family="{SANS}" font-size="13.5" fill="{TEXT}">(UTN)</text>'
            f'<text x="{cols[0]+22}" y="162" font-family="{SANS}" font-size="12.5" fill="{MUTED}">Jan 2024 – Present · In progress</text>')
    lang = box(cols[1], "Languages", "🗣️")
    for k, (n, lv, col) in enumerate([("Spanish", "Native", "#3FB950"), ("English", "A2 · Basic", CYAN)]):
        y = 78 + k * 50
        w = int(len(lv) * 7.4 + 30)
        lang += (f'<text x="{cols[1]+22}" y="{y}" font-family="{SANS}" font-size="16" font-weight="600" fill="{TEXT}">{n}</text>'
                 f'<g transform="translate({cols[1]+cw-22-w} {y-20})"><rect width="{w}" height="28" rx="14" fill="{col}" fill-opacity="0.14" stroke="{col}" stroke-opacity="0.7"/>'
                 f'<text x="{w/2}" y="19" text-anchor="middle" font-family="{SANS}" font-size="13" fill="{TEXT}">{lv}</text></g>')
    stg = box(cols[2], "Strengths", "💪")
    c_svg, _ = chips(cols[2] + 22, 56, ["Continuous learning", "Problem solving", "Adaptability", "Technical communication", "Client orientation"], cols[2] + cws[2] - 14)
    save("profile.svg", f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{GRAD}</defs>{edu}{lang}{stg}{c_svg}</svg>')


if __name__ == "__main__":
    divider(); terminal(); focus(); growing(); marquee(); contact_buttons(); experience(); projects(); credentials()
