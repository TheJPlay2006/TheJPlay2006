#!/usr/bin/env python3
"""Generates assets/stats.svg and assets/languages.svg from the GitHub GraphQL API.

Usage: GITHUB_TOKEN=... python3 scripts/generate_cards.py [login]
"""
import base64, datetime, html, json, os, pathlib, sys, urllib.request

LOGIN = sys.argv[1] if len(sys.argv) > 1 else "TheJPlay2006"
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets"
CYAN, PURPLE, BG, PANEL, TEXT, MUTED = "#36BCF7", "#9D4EDD", "#0D1117", "#161B22", "#E6EDF3", "#8B949E"
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


def card(w, h, title, body):
    stamp = datetime.date.today().isoformat()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{GRAD}</defs>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="{PANEL}" stroke="url(#g)" stroke-width="1.5"/>'
            f'<text x="26" y="40" font-family="{SANS}" font-size="20" font-weight="700" fill="url(#g)">{esc(title)}</text>'
            f'{body}<text x="{w-16}" y="{h-12}" text-anchor="end" font-family="{SANS}" font-size="10" fill="#484F58">updated {stamp}</text></svg>')


def stats_svg(s):
    rows = [("📝", "Total commits", s["commits"]), ("🔀", "Pull requests", s["prs"]), ("⚠️", "Issues", s["issues"]),
            ("⭐", "Stars earned", s["stars"]), ("📦", "Public repos", s["repos"]), ("🤝", "Contributed to", s["contrib"]),
            ("👥", "Followers", s["followers"])]
    b = []
    for i, (ico, label, val) in enumerate(rows):
        y = 74 + i * 27
        b.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{0.15*i:.2f}s" fill="freeze"/>'
                 f'<animateTransform attributeName="transform" type="translate" from="-12 0" to="0 0" dur="0.5s" begin="{0.15*i:.2f}s" fill="freeze"/>'
                 f'<text x="26" y="{y}" font-size="15">{ico}</text>'
                 f'<text x="56" y="{y}" font-family="{SANS}" font-size="15" fill="{TEXT}">{label}</text>'
                 f'<text x="374" y="{y}" text-anchor="end" font-family="{SANS}" font-size="15" font-weight="700" fill="{CYAN}">{val:,}</text></g>')
    return card(400, 280, f"{LOGIN}'s GitHub Stats", "".join(b))


def langs_svg(s):
    tot = sum(v["size"] for v in s["langs"].values()) or 1
    top = sorted(s["langs"].items(), key=lambda kv: -kv[1]["size"])[:8]
    x, bar = 26, []
    bx, bw = 26, 348
    b = [f'<clipPath id="bar"><rect x="{bx}" y="56" width="{bw}" height="10" rx="5"/></clipPath><g clip-path="url(#bar)">']
    for name, v in top:
        w = bw * v["size"] / tot
        b.append(f'<rect x="{x:.1f}" y="56" width="0" height="10" fill="{v["color"]}"><animate attributeName="width" from="0" to="{w:.1f}" dur="1s" fill="freeze"/></rect>')
        x += w
    b.append('</g>')
    for i, (name, v) in enumerate(top):
        col, row = i % 2, i // 2
        px, py = 26 + col * 176, 108 + row * 38
        b.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{0.2+0.12*i:.2f}s" fill="freeze"/>'
                 f'<circle cx="{px+5}" cy="{py-5}" r="5" fill="{v["color"]}"/>'
                 f'<text x="{px+18}" y="{py}" font-family="{SANS}" font-size="14" fill="{TEXT}">{esc(name)}</text>'
                 f'<text x="{px+150}" y="{py}" text-anchor="end" font-family="{SANS}" font-size="14" font-weight="700" fill="{MUTED}">{100*v["size"]/tot:.1f}%</text></g>')
    b.append(f'<text x="26" y="244" font-family="{SANS}" font-size="13" fill="{MUTED}">{len(s["langs"])} languages across {s["repos"]} public repos</text>')
    return card(400, 280, "Top Languages", "".join(b))


def avatar_b64():
    req = urllib.request.Request(f"https://github.com/{LOGIN}.png?size=220", headers={"User-Agent": "profile-cards"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return base64.b64encode(r.read()).decode(), r.headers.get_content_type()


def hero_svg(s):
    img, mime = avatar_b64()
    W, H, cx, cy = 820, 200, 112, 100
    stats = [(f"{s['followers']:,}", "followers"), (f"{s['stars']:,}", "stars"),
             (f"{s['repos']:,}", "public repos"), (f"{s['commits']:,}", "commits")]
    st = []
    for i, (val, label) in enumerate(stats):
        x = 232 + i * 142
        if i:
            st.append(f'<rect x="{x-18}" y="136" width="1" height="38" fill="#30363D"/>')
        st.append(f'<text x="{x}" y="160" font-family="{SANS}" font-size="26" font-weight="700" fill="{CYAN}">{val}</text>'
                  f'<text x="{x}" y="178" font-family="{SANS}" font-size="12" fill="{MUTED}">{label}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{GRAD}'
            f'<radialGradient id="glow"><stop offset="0" stop-color="{CYAN}" stop-opacity="0.28"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>'
            f'<clipPath id="av"><circle cx="{cx}" cy="{cy}" r="58"/></clipPath></defs>'
            f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="{PANEL}" stroke="url(#g)" stroke-width="1.5"/>'
            f'<circle cx="{cx}" cy="{cy}" r="96" fill="url(#glow)"/>'
            f'<image href="data:{mime};base64,{img}" x="{cx-58}" y="{cy-58}" width="116" height="116" clip-path="url(#av)"/>'
            f'<circle cx="{cx}" cy="{cy}" r="58" fill="none" stroke="{BG}" stroke-width="3"/>'
            f'<circle cx="{cx}" cy="{cy}" r="68" fill="none" stroke="url(#g)" stroke-width="3" stroke-linecap="round" stroke-dasharray="70 30">'
            f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="14s" repeatCount="indefinite"/></circle>'
            f'<text x="232" y="62" font-family="{SANS}" font-size="27" font-weight="700" fill="url(#g)">IT Engineering Student</text>'
            f'<text x="232" y="92" font-family="{SANS}" font-size="15" fill="{TEXT}">🎓 Universidad Técnica Nacional  ·  📍 Costa Rica</text>'
            f'<circle cx="238" cy="116" r="5" fill="#3FB950"><animate attributeName="r" values="5;7;5" dur="2s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite"/></circle>'
            f'<text x="252" y="121" font-family="{SANS}" font-size="15" fill="#3FB950">Open to opportunities</text>'
            f'{"".join(st)}</svg>')


def rest(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={
        "Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "User-Agent": "profile-cards",
        "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def describe(e):
    """Turn a public event into (emoji, text) or None when it is not worth showing."""
    t, p, repo = e["type"], e["payload"], e["repo"]["name"].split("/")[-1]
    if t == "PushEvent":
        n = p.get("size") or len(p.get("commits", [])) or 1
        return "📝", f"Pushed {n} commit{'s' if n != 1 else ''} to {repo}"
    if t == "PullRequestEvent":
        pr = p["pull_request"]
        act = "Merged" if pr.get("merged") else p["action"].capitalize()
        return "🔀", f"{act} PR #{pr['number']} in {repo}"
    if t == "IssuesEvent":
        return "⚠️", f"{p['action'].capitalize()} issue #{p['issue']['number']} in {repo}"
    if t == "IssueCommentEvent":
        return "💬", f"Commented on #{p['issue']['number']} in {repo}"
    if t == "CreateEvent" and p.get("ref_type") == "repository":
        return "🚀", f"Created repository {repo}"
    if t == "WatchEvent":
        return "⭐", f"Starred {e['repo']['name']}"
    if t == "ForkEvent":
        return "🍴", f"Forked {e['repo']['name']}"
    if t == "ReleaseEvent":
        return "🏷️", f"Released {p['release']['tag_name']} in {repo}"
    return None


def activity_svg(events, limit=6, max_chars=52):
    rows, seen = [], set()
    for e in events:
        d = describe(e)
        if not d:
            continue
        day = e["created_at"][:10]
        key = (day, d[1])
        if key in seen:                       # collapse repeated identical events on the same day
            continue
        seen.add(key)
        rows.append((d[0], d[1] if len(d[1]) <= max_chars else d[1][:max_chars - 1] + "…",
                     datetime.date.fromisoformat(day).strftime("%b %d")))
        if len(rows) == limit:
            break
    h = 70 + 38 * max(len(rows), 1) + 24
    b = []
    for i, (ico, text, day) in enumerate(rows):
        y = 84 + i * 38
        b.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{0.18*i:.2f}s" fill="freeze"/>'
                 f'<animateTransform attributeName="transform" type="translate" from="-14 0" to="0 0" dur="0.5s" begin="{0.18*i:.2f}s" fill="freeze"/>'
                 f'<rect x="20" y="{y-22}" width="760" height="30" rx="8" fill="{BG}" opacity="0.55"/>'
                 f'<text x="34" y="{y}" font-size="16">{ico}</text>'
                 f'<text x="66" y="{y}" font-family="{SANS}" font-size="15" fill="{TEXT}" xml:space="preserve">{esc(text)}</text>'
                 f'<text x="766" y="{y}" text-anchor="end" font-family="{SANS}" font-size="13" fill="{MUTED}">{day}</text></g>')
    if not rows:
        b.append(f'<text x="400" y="100" text-anchor="middle" font-family="{SANS}" font-size="15" fill="{MUTED}">No recent public activity</text>')
    return card(800, h, "Recent Activity", "".join(b))


if __name__ == "__main__":
    s = fetch()
    events = rest(f"/users/{LOGIN}/events/public?per_page=100")
    (OUT / "activity.svg").write_text(activity_svg(events))
    (OUT / "hero.svg").write_text(hero_svg(s))
    OUT.mkdir(exist_ok=True)
    (OUT / "stats.svg").write_text(stats_svg(s))
    (OUT / "languages.svg").write_text(langs_svg(s))
    print({k: v for k, v in s.items() if k != "langs"}, list(s["langs"])[:6])
