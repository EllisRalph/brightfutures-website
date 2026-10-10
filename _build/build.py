"""
Static site builder for Bright Futures Recruitment.

    py _build/build.py

Reads page bodies from _build/pages/, blog posts from _build/posts/,
vacancies from content/jobs/*.json and testimonials from
content/testimonials/*.json (both edited by the client in the CMS at /admin/),
wraps them in the shared header and footer below, and writes the finished site
to dist/. Netlify runs this on every deploy and every CMS save.
"""
import html
import json
import os
import re
import shutil
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_build"
CONTENT = ROOT / "content"
OUT = ROOT / "dist"
ASSET_V = "7"  # bump after CSS/JS edits so browsers fetch fresh copies

SITE = {
    "name": "Bright Futures Recruitment",
    "url": "https://brightfuturesrecruitment.com",
    "phone": "01268 205620",
    "tel": "+441268205620",
    "email": "info@brightfuturesrecruitment.co.uk",
    "facebook": "https://www.facebook.com/people/Bright-Futures-Recruitment/61584992966066/",
    "locality": "Hockley",
    "region": "Essex",
}
JOBPOSTING_SCHEMA = True  # Google for Jobs data on vacancies that have a 'posted' date
# Preview builds (e.g. the netlify.app demo before go-live): `NOINDEX=1 py _build/build.py`
# keeps search engines out. Leave unset for the real site.
NOINDEX = os.environ.get("NOINDEX") == "1"

e = html.escape

# ---------------------------------------------------------------- icons
ICONS = {
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "pound": '<path d="M18 7c0-5.333-8-5.333-8 0"/><path d="M10 7v14M6 21h12M6 13h10"/>',
    "briefcase": '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    "arrow": '<path d="M5 12h14M12 5l7 7-7 7"/>',
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>',
    "facebook": '<path d="M14 8.5V6.8c0-.8.5-1.3 1.3-1.3H17V2.2h-2.6C11.6 2.2 10 4 10 6.6v1.9H7.5v3.4H10V22h4V11.9h2.7l.5-3.4H14z" fill="currentColor" stroke="none"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="M18 6 6 18M6 6l12 12"/>',
    "chev": '<path d="m6 9 6 6 6-6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "star": '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="currentColor" stroke="none"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "school": '<path d="M14 22v-4a2 2 0 1 0-4 0v4"/><path d="m18 10 4 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-8l4-2M18 5v17M4 6l8-4 8 4M6 5v17"/><circle cx="12" cy="9" r="2"/>',
    "heart": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
    "book": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    "quote": '<path d="M3 21c3 0 7-1 7-8V5c0-1.25-.76-2.02-2-2H4c-1.25 0-2 .75-2 1.97V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .01-1 1.03V20c0 1 0 1 1 1zM15 21c3 0 7-1 7-8V5c0-1.25-.76-2.02-2-2h-4c-1.25 0-2 .75-2 1.97V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>',
    "external": '<path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    "puzzle": '<path d="M19.44 7.85c-.05.32.06.65.29.88l1.57 1.57c.47.47.7 1.09.7 1.7s-.23 1.24-.7 1.71l-1.61 1.61a.98.98 0 0 1-.84.28c-.47-.07-.8-.48-.97-.93a2.5 2.5 0 1 0-3.21 3.21c.45.17.86.5.93.97a.98.98 0 0 1-.28.84l-1.61 1.61a2.4 2.4 0 0 1-1.7.7 2.4 2.4 0 0 1-1.71-.7l-1.57-1.57a1.03 1.03 0 0 0-.88-.29c-.49.07-.84.5-1.02.97a2.5 2.5 0 1 1-3.24-3.24c.46-.18.9-.53.97-1.02a1.03 1.03 0 0 0-.29-.88l-1.57-1.57A2.4 2.4 0 0 1 2 12c0-.62.24-1.23.7-1.7L4.23 8.77c.24-.24.58-.35.92-.3.51.08.88.53 1.07 1.01a2.5 2.5 0 1 0 3.26-3.26c-.48-.2-.93-.56-1.01-1.07-.05-.34.06-.68.3-.92L10.3 2.7A2.4 2.4 0 0 1 12 2c.62 0 1.23.24 1.7.7l1.57 1.57c.23.23.56.34.88.29.49-.07.84-.5 1.02-.97a2.5 2.5 0 1 1 3.24 3.24c-.46.18-.9.53-.97 1.02Z"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>',
    "home": '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/>',
    "chat": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    "cap": '<path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>',
    "pencil": '<path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>',
    "wrench": '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
    "smile": '<circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01"/>',
    "clipboard": '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2M9 12h6M9 16h4"/>',
    "handshake": '<path d="m11 17 2 2a1 1 0 1 0 3-3"/><path d="m14 14 2.5 2.5a1 1 0 1 0 3-3l-3.88-3.88a3 3 0 0 0-4.24 0l-.88.88a1 1 0 1 1-3-3l2.81-2.81a5.79 5.79 0 0 1 7.06-.87l.47.28a2 2 0 0 0 1.42.25L21 4"/><path d="m21 3 1 11h-2M3 3 2 14l6.5 6.5a1 1 0 1 0 3-3M3 4h8"/>',
    "zap": '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "chart": '<path d="M3 3v18h18M18 17V9M13 17V5M8 17v-3"/>',
    "wallet": '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
    "id": '<rect x="2" y="5" width="20" height="14" rx="2"/><circle cx="8" cy="12" r="2.5"/><path d="M14 10h4M14 14h4"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "running": '<circle cx="13" cy="4" r="2"/><path d="m4 22 4-7 3 2 1-5 3 3h4M8 11l2-4 5 1"/>',
}


def icon(name, cls=""):
    extra = f" {cls}" if cls else ""
    return f'<svg class="ic ic-{name}{extra}" aria-hidden="true"><use href="#i-{name}"/></svg>'


SPRITE = '<svg width="0" height="0" style="position:absolute" aria-hidden="true">' + "".join(
    f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items()) + "</svg>"

CAT_META = {
    "primary": ("pencil", "school"),
    "secondary": ("cap", "school"),
    "send": ("puzzle", "specialist"),
    "semh": ("heart", "specialist"),
    "cover-supervisors": ("clipboard", "school"),
    "teaching-assistants": ("users", "school"),
    "lsa": ("smile", "school"),
    "residential": ("home", "care"),
    "therapy": ("chat", "specialist"),
    "other-school-roles": ("wrench", "school"),
}

# ---------------------------------------------------------------- data
TODAY = date.today().isoformat()
CATS = json.loads((SRC / "data/categories.json").read_text(encoding="utf-8"))
CAT_BY_ID = {c["id"]: c for c in CATS}


def load_jobs():
    jobs = []
    for f in sorted((CONTENT / "jobs").glob("*.json")):
        j = json.loads(f.read_text(encoding="utf-8"))
        j["slug"] = f.stem
        for k in ("title", "location", "hours", "start", "pay", "summary", "posted", "closing", "body", "area", "type"):
            j[k] = str(j.get(k) or "").strip()
        j["posted"] = (j["posted"] or "")[:10]
        j["closing"] = (j["closing"] or "")[:10]
        if j["category"] not in CAT_BY_ID:
            print(f"  ! {f.name}: unknown category {j['category']!r}, skipped")
            continue
        if not j.get("live", True):
            continue
        if j["closing"] and j["closing"] < TODAY:
            print(f"  - {f.name}: closing date {j['closing']} has passed, hidden")
            continue
        if not j["area"]:
            j["area"] = "Essex"
        if not j["type"]:
            j["type"] = "Permanent"
        jobs.append(j)
    # newest first; jobs without a posted date go after dated ones
    jobs.sort(key=lambda j: j["title"])
    jobs.sort(key=lambda j: j["posted"] or "0000", reverse=True)
    return jobs


JOBS = load_jobs()
COUNTS = {c["id"]: sum(1 for j in JOBS if j["category"] == c["id"]) for c in CATS}
LATEST = ([j for j in JOBS if j.get("featured")] + [j for j in JOBS if not j.get("featured")])[:6]

TESTIMONIALS = []
for f in sorted((CONTENT / "testimonials").glob("*.json")):
    t = json.loads(f.read_text(encoding="utf-8"))
    if t.get("show", True) and (t.get("quote") or "").strip():
        t["date"] = (t.get("date") or "")[:10]
        TESTIMONIALS.append(t)
TESTIMONIALS.sort(key=lambda t: t["date"], reverse=True)


# ---------------------------------------------------------------- markdown (subset written by the CMS editor)
def md_inline(text):
    keep = []

    def stash(m):
        keep.append(m.group(1))
        return f"\x00{len(keep) - 1}\x00"
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!>|~])", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: (
        f'<a href="{html.escape(m.group(2))}"' + (' target="_blank" rel="noopener"' if m.group(2).startswith("http") else "") + f">{m.group(1)}</a>"), text)
    text = re.sub(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1", r"<strong>\2</strong>", text)
    text = re.sub(r"(?<![\w*])(\*|_)(?=\S)(.+?)(?<=\S)\1(?![\w*])", r"<em>\2</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: html.escape(keep[int(m.group(1))], quote=False), text)


def md_to_html(md):
    out, para, items, list_tag = [], [], [], None

    def flush_para():
        if para:
            joined = ""
            for i, line in enumerate(para):
                hard = line.endswith("\\") or line.endswith("  ")
                line = line.rstrip("\\").rstrip()
                joined += md_inline(line) + ("<br>" if hard and i < len(para) - 1 else " ")
            out.append(f"<p>{joined.strip()}</p>")
            para.clear()

    def flush_list():
        nonlocal list_tag
        if items:
            out.append(f"<{list_tag}>" + "".join(f"<li>{md_inline(x)}</li>" for x in items) + f"</{list_tag}>")
            items.clear()
        list_tag = None

    for raw in (md or "").replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        m_h = re.match(r"^(#{1,6})\s+(.*)$", line)
        m_ul = re.match(r"^\s*[-*+]\s+(.*)$", line)
        m_ol = re.match(r"^\s*\d+[.)]\s+(.*)$", line)
        if not line.strip():
            flush_para()
            continue
        if m_h:
            flush_para(); flush_list()
            level = min(max(len(m_h.group(1)), 2), 4)  # page already has the h1
            out.append(f"<h{level}>{md_inline(m_h.group(2).strip().strip('#').strip())}</h{level}>")
        elif m_ul or m_ol:
            flush_para()
            tag = "ul" if m_ul else "ol"
            if list_tag and list_tag != tag:
                flush_list()
            list_tag = tag
            items.append((m_ul or m_ol).group(1).strip())
        else:
            if items and raw.startswith((" ", "\t")):
                items[-1] += " " + line.strip()
                continue
            flush_list()
            para.append(line.strip())
    flush_para(); flush_list()
    return "\n".join(out)


def front_matter(text):
    m = re.match(r"\s*<!--(.*?)-->\s*", text, re.S)
    meta = {}
    if m:
        for line in m.group(1).strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        text = text[m.end():]
    return meta, text


POSTS = []
for f in sorted((SRC / "posts").glob("*.html")):
    meta, body = front_matter(f.read_text(encoding="utf-8"))
    meta["body"] = body
    meta["slug"] = f.stem
    POSTS.append(meta)
POSTS.sort(key=lambda p: p["date"], reverse=True)


def nice_date(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day} {d.strftime('%B %Y')}"


# ---------------------------------------------------------------- partials
def head(title, desc, path, image="/assets/img/photos/hero-reading.jpg", extra=""):
    full_title = title if "Bright Futures" in title else f"{title} | Bright Futures Recruitment"
    url = SITE["url"] + path
    return f"""<!doctype html>
<html lang="en-GB" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#024550">{'<meta name="robots" content="noindex, nofollow">' if NOINDEX else ''}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Bright Futures Recruitment">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE['url']}{image}">
<meta property="og:locale" content="en_GB">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/img/brand/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/img/brand/favicon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:ital,wght@0,400;0,700;1,400&display=swap">
<link rel="stylesheet" href="/assets/css/site.css?v={ASSET_V}">
<script>document.documentElement.classList.remove('no-js');if(/(invite|recovery|confirmation|email_change)_token=/.test(location.hash))location.replace('/admin/'+location.hash)</script>
{extra}</head>
"""


NAV = [
    ("jobs", "Find a job", "/jobs.html"),
    ("candidates", "Candidates", "/candidates.html"),
    ("schools", "Schools", "/schools.html"),
    ("about", "About", "/about.html"),
    ("testimonials", "Testimonials", "/testimonials.html"),
    ("resources", "Resources", "/resources.html"),
    ("contact", "Contact", "/contact.html"),
]
RESOURCE_LINKS = [
    ("Teacher pay scales", "/resources.html#pay-scales", "pound"),
    ("DBS Update Service", "/resources.html#dbs", "shield"),
    ("Teaching assistant courses", "/resources.html#ta-courses", "cap"),
    ("Free teaching resources", "/resources.html#free-resources", "book"),
    ("FAQs", "/faq.html", "chat"),
    ("Blog", "/blog.html", "file"),
]


def header(active):
    def cur(key):
        return ' aria-current="page"' if key == active else ""

    job_menu = "".join(
        f'<li><a href="/jobs.html?cat={c["id"]}">{icon(CAT_META[c["id"]][0])}{e(c["label"])}<span class="count">{COUNTS[c["id"]]}</span></a></li>'
        for c in CATS)
    res_menu = "".join(f'<li><a href="{u}">{icon(i)}{e(t)}</a></li>' for t, u, i in RESOURCE_LINKS)
    items = []
    for key, label, url in NAV:
        if key == "jobs":
            items.append(f'<li class="{"is-current" if active == "jobs" else ""}"><a class="nav-link" href="{url}"{cur(key)}>{label}{icon("chev")}</a>'
                         f'<ul class="menu menu-wide">{job_menu}<li class="menu-all"><a href="/jobs.html">View all {len(JOBS)} vacancies {icon("arrow")}</a>'
                         f'<a href="/send-recruitment.html">{icon("puzzle")}SEND and SEMH recruitment</a></li></ul></li>')
        elif key == "resources":
            items.append(f'<li class="{"is-current" if active == "resources" else ""}"><a class="nav-link" href="{url}"{cur(key)}>{label}{icon("chev")}</a>'
                         f'<ul class="menu">{res_menu}</ul></li>')
        else:
            items.append(f'<li><a class="nav-link" href="{url}"{cur(key)}>{label}</a></li>')

    drawer_jobs = "".join(f'<a href="/jobs.html?cat={c["id"]}">{e(c["label"])}</a>' for c in CATS)
    drawer_res = "".join(f'<a href="{u}">{e(t)}</a>' for t, u, _ in RESOURCE_LINKS)
    return f"""<body>
{SPRITE}
<a class="skip-link" href="#main">Skip to content</a>
<div class="topbar">
  <div class="wrap">
    <span class="topbar-note">{icon("sun")} Education recruitment across Essex, London and the UK</span>
    <div class="topbar-links">
      <span class="topbar-note">{icon("clock")} Mon to Fri, 9am to 5pm</span>
      <a href="tel:{SITE['tel']}">{icon("phone")} {SITE['phone']}</a>
      <a class="tb-email" href="mailto:{SITE['email']}">{icon("mail")} {SITE['email']}</a>
      <a class="tb-fb" href="{SITE['facebook']}" target="_blank" rel="noopener" aria-label="Bright Futures Recruitment on Facebook">{icon("facebook")}</a>
    </div>
  </div>
</div>
<header class="site-header" id="top">
  <div class="wrap">
    <a class="brand" href="/" aria-label="Bright Futures Recruitment home"><img src="/assets/img/brand/logo-520.png" width="417" height="520" alt="Bright Futures Recruitment"></a>
    <nav class="nav" aria-label="Main"><ul>{''.join(items)}</ul></nav>
    <div class="header-actions">
      <a class="header-phone" href="tel:{SITE['tel']}"><span class="ic-wrap">{icon("phone")}</span><span class="num"><small>Call the team</small>{SITE['phone']}</span></a>
      <a class="btn btn-sun btn-sm" href="/register.html">Submit your CV</a>
      <button class="nav-toggle" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="drawer">{icon("menu")}</button>
    </div>
  </div>
</header>
<div class="drawer" id="drawer" aria-hidden="true">
  <div class="drawer-top">
    <img src="/assets/img/brand/logo-light-520.png" width="417" height="520" alt="Bright Futures Recruitment">
    <button class="drawer-close" type="button" aria-label="Close menu">{icon("close")}</button>
  </div>
  <nav aria-label="Mobile">
    <a href="/">Home</a>
    <details><summary>Find a job {icon("chev")}</summary><div><a href="/jobs.html"><b>All vacancies ({len(JOBS)})</b></a><a href="/send-recruitment.html"><b>SEND and SEMH</b></a>{drawer_jobs}</div></details>
    <a href="/candidates.html">Candidates</a>
    <a href="/schools.html">Schools</a>
    <a href="/about.html">About us</a>
    <a href="/testimonials.html">Testimonials</a>
    <details><summary>Resources {icon("chev")}</summary><div>{drawer_res}</div></details>
    <a href="/contact.html">Contact</a>
  </nav>
  <div class="drawer-foot">
    <a class="btn btn-sun" href="/register.html">Submit your CV {icon("arrow", "ic-arrow")}</a>
    <a href="tel:{SITE['tel']}">{icon("phone")} {SITE['phone']}</a>
    <a href="mailto:{SITE['email']}">{icon("mail")} {SITE['email']}</a>
  </div>
</div>
<main id="main">
"""


def footer(flush=False):
    year = date.today().year
    cat_links = "".join(f'<li><a href="/jobs.html?cat={c["id"]}">{e(c["label"])}</a></li>' for c in CATS[:6])
    return f"""</main>
<footer class="site-footer{' flush' if flush else ''}">
  <div class="wrap">
    <div class="foot-main">
      <div class="foot-brand">
        <img src="/assets/img/brand/logo-light-520.png" width="417" height="520" alt="Bright Futures Recruitment" loading="lazy">
        <p>Placing people, shaping futures. Specialist education recruitment for schools, specialist settings and children's homes, with safeguarding at the heart of everything we do.</p>
      </div>
      <div>
        <h4>Jobs</h4>
        <ul><li><a href="/jobs.html">All vacancies</a></li><li><a href="/send-recruitment.html">SEND recruitment</a></li>{cat_links}</ul>
      </div>
      <div>
        <h4>Work with us</h4>
        <ul>
          <li><a href="/candidates.html">For candidates</a></li>
          <li><a href="/register.html">Submit your CV</a></li>
          <li><a href="/schools.html">For schools</a></li>
          <li><a href="/schools.html#enquiry">Request staff</a></li>
          <li><a href="/about.html">About us</a></li>
          <li><a href="/testimonials.html">Testimonials</a></li>
        </ul>
      </div>
      <div>
        <h4>Resources</h4>
        <ul>
          <li><a href="/resources.html#pay-scales">Teacher pay scales</a></li>
          <li><a href="/resources.html#dbs">DBS Update Service</a></li>
          <li><a href="/resources.html#ta-courses">TA courses</a></li>
          <li><a href="/resources.html#free-resources">Free resources</a></li>
          <li><a href="/faq.html">FAQs</a></li>
          <li><a href="/blog.html">Blog</a></li>
        </ul>
      </div>
      <div class="foot-contact-col">
        <h4>Get in touch</h4>
        <ul class="foot-contact">
          <li>{icon("phone")}<a href="tel:{SITE['tel']}">{SITE['phone']}</a></li>
          <li>{icon("mail")}<a href="mailto:{SITE['email']}">{SITE['email']}</a></li>
          <li>{icon("clock")}<span>Monday to Friday, 9am to 5pm</span></li>
          <li>{icon("pin")}<span>{SITE['locality']}, {SITE['region']}</span></li>
        </ul>
        <div class="foot-social">
          <a href="{SITE['facebook']}" target="_blank" rel="noopener" aria-label="Bright Futures Recruitment on Facebook">{icon("facebook")}</a>
          <a href="mailto:{SITE['email']}" aria-label="Email Bright Futures Recruitment">{icon("mail")}</a>
          <a href="tel:{SITE['tel']}" aria-label="Call Bright Futures Recruitment">{icon("phone")}</a>
        </div>
      </div>
    </div>
    <div class="foot-bottom">
      <span>&copy; {year} Bright Futures Recruitment. All rights reserved.</span>
      <div class="foot-legal">
        <a href="/privacy.html">Privacy policy</a>
        <a href="/contact.html">Contact</a>
        <span class="credit">Site by <b>Sightwise</b></span>
      </div>
    </div>
  </div>
</footer>
<script src="/assets/js/main.js?v={ASSET_V}" defer></script>
</body>
</html>
"""


ORG_LD = {
    "@context": "https://schema.org",
    "@type": "EmploymentAgency",
    "name": SITE["name"],
    "url": SITE["url"],
    "logo": SITE["url"] + "/assets/img/brand/logo.png",
    "image": SITE["url"] + "/assets/img/photos/hero-reading.jpg",
    "telephone": SITE["tel"],
    "email": SITE["email"],
    "address": {"@type": "PostalAddress", "addressLocality": SITE["locality"], "addressRegion": SITE["region"], "addressCountry": "GB"},
    "areaServed": ["Essex", "London", "Kent", "Hertfordshire", "Suffolk", "United Kingdom"],
    "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "opens": "09:00", "closes": "17:00"}],
    "sameAs": [SITE["facebook"]],
}


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>\n"


# ---------------------------------------------------------------- components
def job_card(j, reveal=""):
    cat = CAT_BY_ID[j["category"]]
    group = CAT_META[j["category"]][1]
    meta = [f'<li>{icon("pin")}{e(j["location"])}</li>']
    if j.get("hours"):
        meta.append(f'<li>{icon("clock")}{e(j["hours"])}</li>')
    if j.get("pay"):
        meta.append(f'<li>{icon("pound")}{e(j["pay"])}</li>')
    elif j.get("start"):
        meta.append(f'<li>{icon("calendar")}Start: {e(j["start"])}</li>')
    text = " ".join([j["title"], j["location"], cat["label"], j["summary"], j["type"]]).lower()
    return f"""<article class="job-card{reveal}" data-cat="{j['category']}" data-area="{e(j['area'])}" data-type="{e(j['type'])}" data-closing="{j['closing']}" data-text="{e(text)}">
  <div class="job-tags"><span class="tag-cat" data-group="{group}">{e(cat['label'])}</span><span class="tag-type">{e(j['type'])}</span></div>
  <h3><a href="/jobs/{j['slug']}.html">{e(j['title'])}</a></h3>
  <ul class="job-meta">{''.join(meta)}</ul>
  <p>{e(j['summary'])}</p>
  <div class="card-foot"><span class="link-arrow">View role {icon("arrow")}</span></div>
</article>"""


def cat_tiles():
    out = []
    for i, c in enumerate(CATS):
        ic, group = CAT_META[c["id"]]
        n = COUNTS[c["id"]]
        out.append(f"""<a class="cat-tile reveal reveal-d{i % 4}" data-group="{group}" href="/jobs.html?cat={c['id']}">
  <span class="cat-ic">{icon(ic)}</span><h3>{e(c['label'])}</h3><p>{e(c['blurb'])}</p>
  <span class="count">{n} live role{'s' if n != 1 else ''}</span></a>""")
    return "\n".join(out)


def post_card(p):
    return f"""<article class="post-card reveal">
  <img src="{p['image'].replace('.jpg', '-sm.jpg')}" alt="" loading="lazy" width="900" height="563">
  <div class="post-body"><time datetime="{p['date']}">{nice_date(p['date'])}</time>
  <h3><a href="/blog/{p['slug']}.html">{e(p['title'])}</a></h3><p>{e(p['description'])}</p></div>
</article>"""


def month_year(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%B %Y")
    except ValueError:
        return ""


def review_card(t, i=0):
    when = month_year(t["date"])
    src = t.get("source") or ""
    meta = ", ".join(x for x in [t.get("who") or "", (f"via {src}" if src and src not in ("Other", "In person") else ""), when] if x)
    return f"""<figure class="review reveal reveal-d{i % 3 + 1}"><span class="q">{icon("quote")}</span>
  <div class="stars" aria-label="Five stars">{icon("star") * 5}</div>
  <blockquote style="margin-top:14px">“{e(t['quote'].strip())}”</blockquote>
  <figcaption><span class="avatar">{e(t['name'].strip()[:1])}</span><span><b>{e(t['name'])}</b><br>{e(meta)}</span></figcaption></figure>"""


def reviews_block(limit=2):
    cards = "".join(review_card(t, i) for i, t in enumerate(TESTIMONIALS[:limit]))
    return f"""<div class="reviews">
  <div class="review-score reveal">
    <p class="eyebrow">What people say</p>
    <div class="big">100%</div>
    <p>of people who have reviewed us on Facebook recommend Bright Futures Recruitment.</p>
    <div class="btn-row"><a class="btn btn-sun btn-sm" href="/testimonials.html">Read all testimonials {icon("arrow", "ic-arrow")}</a>
    <a class="btn btn-outline-light btn-sm" href="{SITE['facebook']}" target="_blank" rel="noopener">{icon("facebook")} Facebook</a></div>
  </div>
  <div class="review-list">{cards}</div>
</div>"""


def section_html(blocks):
    out = []
    for b in blocks:
        if isinstance(b, list):
            out.append("<ul>" + "".join(f"<li>{e(x)}</li>" for x in b) + "</ul>")
        elif b.startswith("#"):
            out.append(f"<h3>{e(b[1:].strip())}</h3>")
        else:
            out.append(f"<p>{e(b)}</p>")
    return "\n".join(out)


def options(values, all_label):
    return f'<option value="">{all_label}</option>' + "".join(f'<option value="{e(v)}">{e(v)}</option>' for v in values)


def replace_tokens(body):
    areas = sorted({j["area"] for j in JOBS}, key=lambda a: (a != "Essex", a))
    types = ["Permanent", "Temp to perm", "Long term", "Fixed term", "Term time only", "Supply", "Day to day"]
    types = [t for t in types if any(j["type"] == t for j in JOBS)]
    chips = f'<button class="chip" type="button" data-cat="" aria-pressed="true">All roles<span class="n">{len(JOBS)}</span></button>' + "".join(
        f'<button class="chip" type="button" data-cat="{c["id"]}" aria-pressed="false">{e(c["label"])}<span class="n">{COUNTS[c["id"]]}</span></button>'
        for c in CATS if COUNTS[c["id"]])
    tokens = {
        "{{JOB_COUNT}}": str(len(JOBS)),
        "{{LATEST_JOBS}}": "\n".join(job_card(j, f" reveal reveal-d{i % 3}") for i, j in enumerate(LATEST)),
        "{{SEND_JOBS}}": "\n".join(job_card(j) for j in JOBS if j["category"] in ("send", "semh")),
        "{{SEND_COUNT}}": str(sum(1 for j in JOBS if j["category"] in ("send", "semh"))),
        "{{TESTIMONIAL_CARDS}}": "\n".join(review_card(t, i) for i, t in enumerate(TESTIMONIALS)),
        "{{CAT_TILES}}": cat_tiles(),
        "{{JOB_BOARD}}": "\n".join(job_card(j) for j in JOBS),
        "{{CAT_CHIPS}}": chips,
        "{{AREA_OPTIONS}}": options(areas, "All areas"),
        "{{TYPE_OPTIONS}}": options(types, "All contract types"),
        "{{CAT_OPTIONS}}": "".join(f'<option value="{c["id"]}">{e(c["label"])}</option>' for c in CATS),
        "{{CAT_SELECT}}": "".join(f'<option>{e(c["label"])}</option>' for c in CATS),
        "{{POST_CARDS}}": "\n".join(post_card(p) for p in POSTS),
        "{{POST_CARDS_3}}": "\n".join(post_card(p) for p in POSTS[:3]),
        "{{REVIEWS}}": reviews_block(),
        "{{PHONE}}": SITE["phone"],
        "{{TEL}}": SITE["tel"],
        "{{EMAIL}}": SITE["email"],
        "{{FACEBOOK}}": SITE["facebook"],
    }
    for k, v in tokens.items():
        body = body.replace(k, v)
    # {{icon:name}} shortcodes
    body = re.sub(r"\{\{icon:([a-z]+)\}\}", lambda m: icon(m.group(1)), body)
    body = re.sub(r"\{\{arrow\}\}", icon("arrow", "ic-arrow"), body)
    return body


# ---------------------------------------------------------------- job pages
def employment_types(j):
    t = ["PART_TIME" if "part" in (j.get("hours") or "").lower() else "FULL_TIME"]
    if j["type"] in ("Temp to perm", "Long term", "Fixed term", "Supply"):
        t.append("TEMPORARY")
    return t


def job_page(j):
    cat = CAT_BY_ID[j["category"]]
    facts = [f'<li>{icon("pin")}{e(j["location"])}</li>', f'<li>{icon("briefcase")}{e(j["type"])}</li>']
    if j.get("hours"):
        facts.append(f'<li>{icon("clock")}{e(j["hours"])}</li>')
    if j.get("start"):
        facts.append(f'<li>{icon("calendar")}Start: {e(j["start"])}</li>')
    if j.get("pay"):
        facts.append(f'<li>{icon("pound")}{e(j["pay"])}</li>')
    if j.get("closing"):
        facts.append(f'<li>{icon("clock")}Closing date: {nice_date(j["closing"])}</li>')
    body_html = md_to_html(j["body"])
    sections = f'<section>{body_html}</section>'
    group = CAT_META[j["category"]][1]
    related = [x for x in JOBS if x["category"] == j["category"] and x["slug"] != j["slug"]]
    related += [x for x in JOBS if x["category"] != j["category"] and CAT_META[x["category"]][1] == group]
    related = related[:3]
    job_label = f'{j["title"]} ({j["location"]})'
    extra = ""
    if JOBPOSTING_SCHEMA and j.get("posted"):
        locality = j["location"].split(",")[0].replace("Near ", "")
        posting = {
            "@context": "https://schema.org", "@type": "JobPosting",
            "title": j["title"], "description": body_html or e(j["summary"]), "datePosted": j["posted"],
            "employmentType": employment_types(j),
            "hiringOrganization": {"@type": "Organization", "name": SITE["name"], "sameAs": SITE["url"], "logo": SITE["url"] + "/assets/img/brand/logo.png"},
            "jobLocation": {"@type": "Place", "address": {"@type": "PostalAddress", "addressLocality": locality, "addressRegion": j["area"], "addressCountry": "GB"}},
            "directApply": True,
            "identifier": {"@type": "PropertyValue", "name": SITE["name"], "value": j["slug"]},
        }
        if j.get("closing"):
            posting["validThrough"] = j["closing"] + "T23:59:00+00:00"
        extra = ld(posting)
    crumbs = ld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE["url"] + "/"},
        {"@type": "ListItem", "position": 2, "name": "Jobs", "item": SITE["url"] + "/jobs.html"},
        {"@type": "ListItem", "position": 3, "name": j["title"], "item": f'{SITE["url"]}/jobs/{j["slug"]}.html'}]})
    desc = f'{j["title"]} in {j["location"]}. {j["summary"]} Apply with Bright Futures Recruitment.'
    body = f"""<section class="job-hero">
  <div class="wrap">
    <ol class="crumbs"><li><a href="/">Home</a></li><li><a href="/jobs.html">Jobs</a></li><li><a href="/jobs.html?cat={cat['id']}">{e(cat['label'])}</a></li><li>{e(j['title'])}</li></ol>
    <div class="job-tags" style="margin-bottom:14px"><span class="tag-cat" data-group="{group}">{e(cat['label'])}</span></div>
    <h1>{e(j['title'])}</h1>
    <p class="lead">{e(j['summary'])}</p>
    <ul class="job-facts">{''.join(facts)}</ul>
    <div class="btn-row job-hero-cta"><a class="btn btn-sun" href="#apply">Apply for this role {icon("arrow", "ic-arrow")}</a><a class="btn btn-ghost" href="tel:{SITE['tel']}">{icon("phone")} {SITE['phone']}</a></div>
    <div class="closed-note" data-closing="{j['closing']}" hidden>{icon("clock")}<span>This vacancy has now closed. Take a look at our <a href="/jobs.html">live vacancies</a> or <a href="/register.html">send us your CV</a>.</span></div>
  </div>
</section>
<section class="section bg-white" style="padding-top:clamp(40px,5vw,72px)">
  <div class="wrap job-layout">
    <div class="job-content">
{sections}
      <div class="safeguard-note">{icon("shield")}<p style="margin:0">Bright Futures Recruitment is committed to safeguarding and promoting the welfare of children and young people. All roles are subject to an enhanced DBS check, references and our full compliance checks, in line with Keeping Children Safe in Education.</p></div>
      <p style="margin-top:28px"><a class="link-arrow" href="/jobs.html">{icon("arrow")} Back to all vacancies</a></p>
    </div>
    <aside class="job-side" id="apply">
      <div class="apply-card">
        <h2>Apply for this role</h2>
        <p>Send us your details and CV and one of our consultants will be in touch to talk it through.</p>
        {apply_form(job_label)}
      </div>
      <div class="side-card">
        <h3>Questions about this role?</h3>
        <p style="font-size:.95rem">Talk to the team before you apply. We're happy to tell you more about the school and the role.</p>
        <a href="tel:{SITE['tel']}">{icon("phone")} {SITE['phone']}</a>
        <a href="mailto:{SITE['email']}?subject={e('Enquiry: ' + job_label)}">{icon("mail")} Email the team</a>
      </div>
    </aside>
  </div>
</section>
<div class="apply-bar" aria-hidden="true"><a class="btn btn-sun" href="#apply" tabindex="-1">Apply for this role {icon("arrow", "ic-arrow")}</a><a class="apply-bar-call" href="tel:{SITE['tel']}" tabindex="-1" aria-label="Call {SITE['phone']}">{icon("phone")}</a></div>
<section class="section related">
  <div class="wrap">
    <div class="sec-head-row"><div class="sec-head"><p class="eyebrow">You might also like</p><h2>Similar roles</h2></div><a class="btn btn-ghost" href="/jobs.html">All vacancies {icon("arrow", "ic-arrow")}</a></div>
    <div class="job-grid">{''.join(job_card(x) for x in related)}</div>
  </div>
</section>"""
    return head(f'{j["title"]}, {j["location"]}', desc, f'/jobs/{j["slug"]}.html', extra=extra + crumbs) + header("jobs") + body + footer()


def apply_form(job_label):
    return f"""<form class="form" name="job-application" method="POST" action="/thank-you.html" data-netlify="true" netlify-honeypot="bot-field" enctype="multipart/form-data">
  <input type="hidden" name="form-name" value="job-application">
  <input type="hidden" name="job" value="{e(job_label)}">
  <p class="hidden-field"><label>Leave this empty <input name="bot-field"></label></p>
  <div class="field"><label for="a-name">Full name</label><input id="a-name" name="name" autocomplete="name" required></div>
  <div class="field"><label for="a-email">Email</label><input id="a-email" type="email" name="email" autocomplete="email" required></div>
  <div class="field"><label for="a-phone">Phone</label><input id="a-phone" type="tel" name="phone" autocomplete="tel" required></div>
  <label class="file-drop"><input type="file" name="cv" accept=".pdf,.doc,.docx,.odt,.rtf" required><span class="ic-wrap">{icon("upload")}</span><span><b data-file-label>Upload your CV</b><span>PDF or Word, up to 8MB</span></span></label>
  <div class="field"><label for="a-msg">Anything else? <span class="opt">(optional)</span></label><textarea id="a-msg" name="message" rows="3" style="min-height:90px"></textarea></div>
  <label class="consent"><input type="checkbox" name="consent" value="yes" required><span>I agree to Bright Futures Recruitment storing my details to help me find work, as set out in the <a href="/privacy.html">privacy policy</a>.</span></label>
  <button class="btn btn-teal" type="submit">Send application {icon("arrow", "ic-arrow")}</button>
</form>"""


# ---------------------------------------------------------------- post pages
def post_page(p):
    others = [x for x in POSTS if x["slug"] != p["slug"]][:2]
    body = f"""<section class="page-hero">
  <div class="wrap wrap-narrow">
    <ol class="crumbs"><li><a href="/">Home</a></li><li><a href="/blog.html">Blog</a></li><li>{e(p['title'])}</li></ol>
    <p class="post-meta"><time datetime="{p['date']}">{nice_date(p['date'])}</time><span>{e(p.get('category', 'News'))}</span></p>
    <h1>{e(p['title'])}</h1>
    <p class="lead">{e(p['description'])}</p>
  </div>
  <div class="wrap post-hero"><img src="{p['image']}" alt="{e(p.get('alt', ''))}" width="2000" height="857"></div>
</section>
<section class="section bg-white" style="padding-top:clamp(40px,5vw,72px)">
  <div class="wrap wrap-narrow"><article class="prose">{replace_tokens(p['body'])}</article></div>
</section>
<section class="section">
  <div class="wrap">
    <div class="sec-head-row"><div class="sec-head"><p class="eyebrow">Keep reading</p><h2>More from the blog</h2></div><a class="btn btn-ghost" href="/blog.html">All posts {icon("arrow", "ic-arrow")}</a></div>
    <div class="post-grid">{''.join(post_card(x) for x in others)}</div>
  </div>
</section>"""
    art = ld({"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"], "datePublished": p["date"],
              "image": SITE["url"] + p["image"], "author": {"@type": "Organization", "name": SITE["name"]},
              "publisher": {"@type": "Organization", "name": SITE["name"], "logo": {"@type": "ImageObject", "url": SITE["url"] + "/assets/img/brand/logo.png"}}})
    return head(p["title"], p["description"], f"/blog/{p['slug']}.html", image=p["image"], extra=art) + header("resources") + body + footer()


# ---------------------------------------------------------------- build
STATIC = ["assets", "admin", "_headers", "_redirects", "robots.txt"]


def build():
    # start from an empty dist/ so deleted vacancies disappear too (empty it rather than
    # delete it, so a preview server running inside it doesn't block the build on Windows)
    OUT.mkdir(exist_ok=True)
    for child in OUT.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for name in STATIC:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, OUT / name)
        elif src.exists():
            shutil.copy2(src, OUT / name)

    # CMS: /admin/ is the client's vacancies-only view; /admin/full/ (Sightwise safety login)
    # adds testimonials. Same vacancy fields in both, because full = base config + extras.
    admin_out = OUT / "admin"
    if (admin_out / "config.yml").exists() and (ROOT / "admin" / "_full-extra.yml").exists():
        (admin_out / "full").mkdir(exist_ok=True)
        base_cfg = (admin_out / "config.yml").read_text(encoding="utf-8").rstrip() + "\n\n"
        extra_cfg = (ROOT / "admin" / "_full-extra.yml").read_text(encoding="utf-8")
        (admin_out / "full" / "config.yml").write_text(base_cfg + extra_cfg, encoding="utf-8")
        full_html = (admin_out / "index.html").read_text(encoding="utf-8").replace(
            "<title>Manage vacancies |", "<title>Sightwise admin |")
        (admin_out / "full" / "index.html").write_text(full_html, encoding="utf-8")
        (admin_out / "_full-extra.yml").unlink(missing_ok=True)

    written = []
    for f in sorted((SRC / "pages").glob("*.html")):
        meta, body = front_matter(f.read_text(encoding="utf-8"))
        out_name = meta.get("out", f.stem + ".html")
        path = "/" if out_name == "index.html" else "/" + out_name
        extra = ld(ORG_LD) if meta.get("org") == "yes" else ""
        if meta.get("faq"):
            extra += faq_ld(body)
        page = head(meta["title"], meta["description"], path, image=meta.get("image", "/assets/img/photos/hero-reading.jpg"), extra=extra) \
            + header(meta.get("nav", "")) + replace_tokens(body) + footer(flush=meta.get("flush") == "yes")
        (OUT / out_name).write_text(page, encoding="utf-8")
        written.append(path)
    (OUT / "jobs").mkdir()
    for j in JOBS:
        (OUT / "jobs" / f"{j['slug']}.html").write_text(job_page(j), encoding="utf-8")
        written.append(f"/jobs/{j['slug']}.html")
    (OUT / "blog").mkdir()
    for p in POSTS:
        (OUT / "blog" / f"{p['slug']}.html").write_text(post_page(p), encoding="utf-8")
        written.append(f"/blog/{p['slug']}.html")
    skip = {"/404.html", "/thank-you.html"}
    urls = "".join(f"<url><loc>{SITE['url']}{u}</loc><lastmod>{TODAY}</lastmod></url>" for u in written if u not in skip)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    if NOINDEX:
        (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
        print("  NOINDEX build: search engines blocked (preview only)")
    print(f"Built {len(written)} pages into dist/ ({len(JOBS)} live jobs, {len(TESTIMONIALS)} testimonials, {len(POSTS)} posts)")


def faq_ld(body):
    """FAQPage structured data from <details><summary>Q</summary><div class="answer">A</div></details> blocks."""
    qa = []
    for q, a in re.findall(r"<summary>(.*?)<span class=\"plus\">.*?</summary>\s*<div class=\"answer\">(.*?)</div>\s*</details>", body, re.S):
        clean = lambda s: re.sub(r"\s+([,.;:!?)])", r"\1", re.sub(r"\s+", " ", re.sub(r"<[^>]+>|\{\{[^}]+\}\}", " ", s))).strip()
        qa.append({"@type": "Question", "name": clean(q), "acceptedAnswer": {"@type": "Answer", "text": clean(replace_tokens(a))}})
    if not qa:
        return ""
    return ld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": qa})


if __name__ == "__main__":
    build()
