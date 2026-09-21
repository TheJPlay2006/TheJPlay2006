#!/usr/bin/env python3
"""Generates assets/stats.svg and assets/languages.svg from the GitHub GraphQL API.

Usage: GITHUB_TOKEN=... python3 scripts/generate_cards.py [login]
"""
import base64, datetime, html, json, math, os, pathlib, sys, urllib.request

LOGIN = sys.argv[1] if len(sys.argv) > 1 else "TheJPlay2006"
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets"
CYAN, PURPLE, BG, PANEL, TEXT, MUTED = "#36BCF7", "#9D4EDD", "#0D1117", "#161B22", "#E6EDF3", "#8B949E"
MONO = "'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', monospace"
SANS = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
GRAD = (f'<linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CYAN}"/>'
        f'<stop offset="1" stop-color="{PURPLE}"/></linearGradient>')
esc = html.escape


def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "User-Agent": "profile-cards"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    return data["data"]


def fetch():
    u = gql("""query($l:String!){ user(login:$l){ name createdAt followers{totalCount}
      pullRequests{totalCount} issues{totalCount}
      repositoriesContributedTo(first:1, contributionTypes:[COMMIT,ISSUE,PULL_REQUEST,REPOSITORY]){totalCount}
      contributionsCollection{ contributionYears }
      repositories(ownerAffiliations:OWNER, privacy:PUBLIC, isFork:false, first:100){ totalCount nodes{ stargazerCount
        languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name color } } } } } } }""",
        l=LOGIN)["user"]
    commits = 0
    for y in u["contributionsCollection"]["contributionYears"]:
        c = gql("""query($l:String!,$f:DateTime!,$t:DateTime!){ user(login:$l){
          contributionsCollection(from:$f,to:$t){ totalCommitContributions restrictedContributionsCount } } }""",
                l=LOGIN, f=f"{y}-01-01T00:00:00Z", t=f"{y}-12-31T23:59:59Z")["user"]["contributionsCollection"]
        commits += c["totalCommitContributions"] + c["restrictedContributionsCount"]
    repos = u["repositories"]["nodes"]
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]
            d = langs.setdefault(n["name"], {"size": 0, "color": n["color"] or "#8B949E"})
            d["size"] += e["size"]
    return {
        "commits": commits, "prs": u["pullRequests"]["totalCount"], "issues": u["issues"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos), "repos": u["repositories"]["totalCount"],
        "followers": u["followers"]["totalCount"],
        "contrib": u["repositoriesContributedTo"]["totalCount"], "langs": langs,
    }


def shell(w, h, title, ico, inner, uid):
    """Dashboard card: gradient border, dot grid, drifting aurora glows and a light sweep."""
    stamp = datetime.date.today().isoformat()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{GRAD}'
            f'<clipPath id="{uid}clip"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="18"/></clipPath>'
            f'<pattern id="{uid}dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="#30363D"/></pattern>'
            f'<radialGradient id="{uid}a"><stop offset="0" stop-color="{CYAN}" stop-opacity="0.30"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="{uid}b"><stop offset="0" stop-color="{PURPLE}" stop-opacity="0.32"/><stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></radialGradient>'
            f'<linearGradient id="{uid}s" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.09"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="18" fill="{PANEL}"/>'
            f'<g clip-path="url(#{uid}clip)"><rect width="{w}" height="{h}" fill="url(#{uid}dots)" opacity="0.55"/>'
            f'<circle cy="{h*0.2:.0f}" r="{h*0.9:.0f}" fill="url(#{uid}a)"><animate attributeName="cx" values="{w*0.1:.0f};{w*0.45:.0f};{w*0.1:.0f}" dur="14s" repeatCount="indefinite"/></circle>'
            f'<circle cy="{h*0.9:.0f}" r="{h*0.9:.0f}" fill="url(#{uid}b)"><animate attributeName="cx" values="{w*0.95:.0f};{w*0.55:.0f};{w*0.95:.0f}" dur="16s" repeatCount="indefinite"/></circle>'
            f'<rect y="0" width="160" height="{h}" fill="url(#{uid}s)" transform="skewX(-20)"><animate attributeName="x" values="-260;{w+120};{w+120}" keyTimes="0;0.4;1" dur="9s" repeatCount="indefinite"/></rect></g>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="18" fill="none" stroke="url(#g)" stroke-width="1.5"/>'
            f'<text x="28" y="44" font-size="20">{ico}</text>'
            f'<text x="58" y="44" font-family="{SANS}" font-size="20" font-weight="700" fill="url(#g)">{esc(title)}</text>'
            f'{inner}<text x="{w-18}" y="{h-12}" text-anchor="end" font-family="{SANS}" font-size="10" fill="#484F58">updated {stamp}</text></svg>')


def odometer(uid, x, y, text, color, delay, size=30, adv=17.5, lh=36):
    """Number whose digits roll up like an odometer, looping every 10 s."""
    out, cx = [], x
    for i, ch in enumerate(text):
        if not ch.isdigit():
            out.append(f'<text x="{cx+4:.1f}" y="{y}" text-anchor="middle" font-family="{MONO}" font-size="{size}" font-weight="700" fill="{color}">{ch}</text>')
            cx += 9
            continue
        d, cid = int(ch), f"{uid}o{i}"
        col = "".join(f'<text x="{cx+adv/2:.1f}" y="{y + k*lh}" text-anchor="middle" font-family="{MONO}" font-size="{size}" font-weight="700" fill="{color}">{k % 10}</text>' for k in range(20))
        target = -(10 + d) * lh
        t0 = 0.05 + delay + i * 0.06
        out.append(f'<clipPath id="{cid}"><rect x="{cx-2:.1f}" y="{y-size+2}" width="{adv+4}" height="{lh-4}"/></clipPath>'
                   f'<g clip-path="url(#{cid})"><g>{col}'
                   f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 {target};0 {target}" keyTimes="0;{t0/10:.3f};{(t0+1.7)/10:.3f};1" '
                   f'calcMode="spline" keySplines="0 0 1 1;0.15 0.8 0.2 1;0 0 1 1" dur="10s" repeatCount="indefinite"/></g></g>')
        cx += adv
    return "".join(out)


def stats_svg(s):
    tiles = [("📝", "Total commits", s["commits"], CYAN), ("🔀", "Pull requests", s["prs"], PURPLE),
             ("⚠️", "Issues", s["issues"], "#F0883E"), ("⭐", "Stars earned", s["stars"], "#E3B341"),
             ("📦", "Public repos", s["repos"], "#3FB950"), ("🤝", "Contributed to", s["contrib"], "#F778BA"),
             ("👥", "Followers", s["followers"], CYAN), ("🌐", "Languages", len(s["langs"]), PURPLE)]
    W, H, TW, TH, GX, X0, Y0 = 820, 290, 184, 92, 14, 28, 68
    b = []
    for i, (ico, label, val, col) in enumerate(tiles):
        x, y = X0 + (i % 4) * (TW + GX), Y0 + (i // 4) * (TH + 14)
        d = 0.12 * i
        b.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.6s" begin="{d:.2f}s" fill="freeze"/>'
                 f'<animateTransform attributeName="transform" type="translate" from="0 16" to="0 0" dur="0.6s" begin="{d:.2f}s" fill="freeze"/>'
                 f'<rect x="{x}" y="{y}" width="{TW}" height="{TH}" rx="14" fill="{BG}" fill-opacity="0.72" stroke="{col}" stroke-opacity="0.4">'
                 f'<animate attributeName="stroke-opacity" values="0.25;0.85;0.25" dur="4.5s" begin="{d:.2f}s" repeatCount="indefinite"/></rect>'
                 f'<rect x="{x}" y="{y+16}" width="4" height="{TH-32}" rx="2" fill="{col}"/>'
                 f'<text x="{x+20}" y="{y+30}" font-size="16">{ico}</text>'
                 f'<text x="{x+46}" y="{y+30}" font-family="{SANS}" font-size="13" fill="{MUTED}">{label}</text>'
                 f'{odometer(f"t{i}", x+20, y+72, f"{val:,}", col, d)}</g>')
    return shell(W, H, f"{LOGIN}'s GitHub Stats", "📊", "".join(b), "st")


def langs_svg(s):
    tot = sum(v["size"] for v in s["langs"].values()) or 1
    top = sorted(s["langs"].items(), key=lambda kv: -kv[1]["size"])[:6]
    W, H, cx, cy, r, sw = 820, 290, 170, 165, 70, 24
    C = 2 * math.pi * r
    arcs, cum, D = [], 0.0, 10.0
    for i, (name, v) in enumerate(top):
        frac = v["size"] / tot
        L = max(frac * C - 3, 1)
        a = (0.5 + i * 0.35) / D
        bt = min(a + 1.1 / D, 0.98)
        arcs.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{v["color"]}" stroke-width="{sw}" stroke-dasharray="0 {C:.1f}" stroke-dashoffset="{-cum:.1f}" transform="rotate(-90 {cx} {cy})">'
                    f'<animate attributeName="stroke-dasharray" values="0 {C:.1f};0 {C:.1f};{L:.1f} {C-L:.1f};{L:.1f} {C-L:.1f}" keyTimes="0;{a:.3f};{bt:.3f};1" dur="{D:.0f}s" repeatCount="indefinite"/></circle>')
        cum += frac * C
    lead = top[0]
    center = (f'<circle cx="{cx}" cy="{cy}" r="{r-sw/2-6}" fill="{BG}" fill-opacity="0.6"/>'
              f'<text x="{cx}" y="{cy+4}" text-anchor="middle" font-family="{SANS}" font-size="28" font-weight="700" fill="{TEXT}">{100*lead[1]["size"]/tot:.0f}%</text>'
              f'<text x="{cx}" y="{cy+24}" text-anchor="middle" font-family="{SANS}" font-size="13" fill="{lead[1]["color"]}">{esc(lead[0])}</text>'
              f'<circle cx="{cx}" cy="{cy}" r="{r+sw/2+8}" fill="none" stroke="url(#g)" stroke-width="1" stroke-dasharray="3 7" opacity="0.6">'
              f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="40s" repeatCount="indefinite"/></circle>')
    rows = []
    bx, bw = 470, 250
    for i, (name, v) in enumerate(top):
        y = 92 + i * 30
        w = max(bw * v["size"] / tot / (top[0][1]["size"] / tot), 4)     # scaled against the leader so small ones stay readable
        a = (0.5 + i * 0.3) / D
        rows.append(f'<g><circle cx="342" cy="{y-5}" r="5" fill="{v["color"]}"/>'
                    f'<text x="356" y="{y}" font-family="{SANS}" font-size="14" fill="{TEXT}">{esc(name)}</text>'
                    f'<rect x="{bx}" y="{y-11}" width="{bw}" height="10" rx="5" fill="{BG}" fill-opacity="0.8"/>'
                    f'<rect x="{bx}" y="{y-11}" width="0" height="10" rx="5" fill="{v["color"]}">'
                    f'<animate attributeName="width" values="0;0;{w:.1f};{w:.1f}" keyTimes="0;{a:.3f};{a+1.3/D:.3f};1" calcMode="spline" keySplines="0 0 1 1;0.2 0.8 0.2 1;0 0 1 1" dur="{D:.0f}s" repeatCount="indefinite"/></rect>'
                    f'<text x="{W-30}" y="{y}" text-anchor="end" font-family="{SANS}" font-size="14" font-weight="700" fill="{MUTED}">{100*v["size"]/tot:.1f}%</text></g>')
    foot = f'<text x="342" y="{92+6*30+2}" font-family="{SANS}" font-size="12.5" fill="{MUTED}">{len(s["langs"])} languages across {s["repos"]} public repos</text>'
    return shell(W, H, "Top Languages", "🧬", "".join(arcs) + center + "".join(rows) + foot, "lg")


def avatar_b64():
    req = urllib.request.Request(f"https://github.com/{LOGIN}.png?size=220", headers={"User-Agent": "profile-cards"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return base64.b64encode(r.read()).decode(), r.headers.get_content_type()


def hexpts(cx, cy, R):
    return " ".join(f"{cx + R*math.cos(math.radians(-90+60*k)):.1f},{cy + R*math.sin(math.radians(-90+60*k)):.1f}" for k in range(6))


def hero_svg(s):
    img, mime = avatar_b64()
    W, H, cx, cy, R = 820, 200, 112, 100, 60
    stats = [(f"{s['followers']:,}", "followers"), (f"{s['stars']:,}", "stars"),
             (f"{s['repos']:,}", "public repos"), (f"{s['commits']:,}", "commits")]
    st = []
    for i, (val, label) in enumerate(stats):
        x = 232 + i * 142
        if i:
            st.append(f'<rect x="{x-18}" y="136" width="1" height="38" fill="#30363D"/>')
        st.append(f'<text x="{x}" y="160" font-family="{SANS}" font-size="26" font-weight="700" fill="{CYAN}">{val}</text>'
                  f'<text x="{x}" y="178" font-family="{SANS}" font-size="12" fill="{MUTED}">{label}</text>')
    per = 6 * R
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{GRAD}'
            f'<radialGradient id="glow"><stop offset="0" stop-color="{CYAN}" stop-opacity="0.22"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>'
            f'<clipPath id="av"><polygon points="{hexpts(cx, cy, R-3)}"/></clipPath></defs>'
            f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="{PANEL}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="100" fill="url(#glow)"/>'
            f'<image href="data:{mime};base64,{img}" x="{cx-R}" y="{cy-R}" width="{2*R}" height="{2*R}" preserveAspectRatio="xMidYMid slice" clip-path="url(#av)"/>'
            f'<polygon points="{hexpts(cx, cy, R)}" fill="none" stroke="#30363D" stroke-width="3"/>'
            f'<polygon points="{hexpts(cx, cy, R)}" fill="none" stroke="{CYAN}" stroke-width="7" stroke-linecap="round" stroke-dasharray="70 {per-70:.0f}" opacity="0.28"><animate attributeName="stroke-dashoffset" from="{per:.0f}" to="0" dur="4.5s" repeatCount="indefinite"/></polygon>'
            f'<polygon points="{hexpts(cx, cy, R)}" fill="none" stroke="{CYAN}" stroke-width="3" stroke-linecap="round" stroke-dasharray="70 {per-70:.0f}"><animate attributeName="stroke-dashoffset" from="{per:.0f}" to="0" dur="4.5s" repeatCount="indefinite"/></polygon>'
            f'<polygon points="{hexpts(cx, cy, R)}" fill="none" stroke="{PURPLE}" stroke-width="3" stroke-linecap="round" stroke-dasharray="70 {per-70:.0f}"><animate attributeName="stroke-dashoffset" from="{per/2+per:.0f}" to="{per/2:.0f}" dur="4.5s" repeatCount="indefinite"/></polygon>'
            f'<text x="232" y="62" font-family="{SANS}" font-size="27" font-weight="700" fill="url(#g)">Junior Full-Stack Developer</text>'
            f'<text x="232" y="92" font-family="{SANS}" font-size="15" fill="{TEXT}">🎓 IT Engineering Student · Universidad Técnica Nacional</text>'
            f'<circle cx="238" cy="116" r="5" fill="#3FB950"><animate attributeName="r" values="5;7;5" dur="2s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite"/></circle>'
            f'<text x="252" y="121" font-family="{SANS}" font-size="15" fill="#3FB950">Open to opportunities</text>'
            f'<text x="440" y="121" font-family="{SANS}" font-size="15" fill="{TEXT}">📍 Costa Rica</text>'
            f'{"".join(st)}</svg>')


if __name__ == "__main__":
    s = fetch()
    OUT.mkdir(exist_ok=True)
    (OUT / "stats.svg").write_text(stats_svg(s))
    (OUT / "languages.svg").write_text(langs_svg(s))
    (OUT / "hero.svg").write_text(hero_svg(s))
    print({k: v for k, v in s.items() if k != "langs"}, list(s["langs"])[:6])
