#!/usr/bin/env python3
"""Build the Cartier Creative blog.

Posts live in blog/_src/posts/*.md. Each file starts with a front matter block:

    ---
    title: The math on one missed call
    slug: missed-call-math
    date: 2026-11-24
    tag: Numbers
    summary: One or two sentences for the blog index and search results.
    ---

The body is a small Markdown subset: ## and ### headings, paragraphs,
- bullet lists, 1. numbered lists, > quotes, **bold**, *italic*, [links](url).
A line containing only `:::cta` places the booking call to action there.
Without one, the call to action goes at the end of the post.

Run from anywhere:  python3 blog/_src/build.py
It writes blog/<slug>/index.html, blog/index.html and blog/feed.xml.
Underscore folders are not published by GitHub Pages, so this folder stays private.
No third-party packages needed.
"""
import html
import re
import sys
from datetime import date
from pathlib import Path

SRC = Path(__file__).resolve().parent
BLOG = SRC.parent
POSTS = SRC / "posts"
SITE = "https://cartiercreativeco.com"
BOOKING = "https://api.leadconnectorhq.com/widget/booking/nKwdftctGGdOVALb2mp9"

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">')
ICON = ("<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%2309090a'/%3E%3Ctext x='16' y='21.5' text-anchor='middle' font-family='Georgia,serif' font-size='13' fill='%23d4b06a'%3ECCA%3C/text%3E%3C/svg%3E\">")

NAV_T = """<header class="nav">
  <div class="wrap">
    <a class="brand" href="{R}" aria-label="Cartier Creative home"><span class="mk">CCA</span><span class="nm">Cartier Creative</span></a>
    <nav class="links" aria-label="Main">
      <a class="l" href="{R}">Home</a>
      <a class="l on" href="{R}blog/">Field Notes</a>
      <a class="btn ghost" href="tel:+17194280390">Talk to a human</a>
      <a class="btn" href="{R}#audit">Free audit</a>
    </nav>
  </div>
</header>"""

FOOTER_T = """<footer>
  <div class="wrap">
    <p>Cartier Creative. Smarter communication for owner-run service businesses.<br>15485 Vollmer Rd, Colorado Springs, CO 80908 &middot; <a href="tel:+17194280390">(719) 428-0390</a></p>
    <nav aria-label="Footer"><a href="{R}">Home</a><a href="{R}blog/">Field Notes</a><a href="{R}blog/feed.xml">RSS</a><a href="{R}snow/">Snow crews</a><a href="{R}privacy/">Privacy</a><a href="{R}terms/">Terms</a></nav>
  </div>
</footer>"""

def NAV(R): return NAV_T.replace("{R}", R)
def FOOTER(R): return FOOTER_T.replace("{R}", R)

CTA = f"""<aside class="cta-box">
  <p class="mono kicker">Free audit</p>
  <p class="cta-h">Want to know what your phone is costing you?</p>
  <p>We look at your calls, your Google profile and your follow-up. Thirty minutes. You keep the notes either way.</p>
  <a class="btn goldbtn" href="{BOOKING}" target="_blank" rel="noopener">Book the free audit</a>
</aside>"""


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        sys.exit(f"{path.name}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    for key in ("title", "slug", "date", "summary"):
        if not meta.get(key):
            sys.exit(f"{path.name}: front matter needs '{key}'")
    meta.setdefault("tag", "Field note")
    meta["draft"] = meta.get("draft", "").lower() == "true"
    meta["body"] = m.group(2)
    meta["d"] = date.fromisoformat(meta["date"])
    return meta


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: f'<a href="{m.group(2)}"' + (' target="_blank" rel="noopener"' if m.group(2).startswith("http") else "") + f">{m.group(1)}</a>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", s)
    return s


def md(body):
    out, para, lst, quote = [], [], None, []

    def flush():
        nonlocal para, lst, quote
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para = []
        if lst:
            tag, items = lst
            out.append(f"<{tag}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{tag}>")
            lst = None
        if quote:
            out.append(f"<blockquote><p>{inline(' '.join(quote))}</p></blockquote>")
            quote = []

    for raw in body.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        if line.strip() == ":::cta":
            flush(); out.append(CTA); continue
        h = re.match(r"(#{2,3})\s+(.*)", line)
        if h:
            flush()
            lvl = len(h.group(1))
            out.append(f"<h{lvl}>{inline(h.group(2))}</h{lvl}>")
            continue
        b = re.match(r"\s*[-*]\s+(.*)", line)
        n = re.match(r"\s*\d+[.)]\s+(.*)", line)
        if b or n:
            tag = "ul" if b else "ol"
            if para or quote:
                flush()
            if lst and lst[0] != tag:
                flush()
            if not lst:
                lst = (tag, [])
            lst[1].append((b or n).group(1))
            continue
        q = re.match(r">\s?(.*)", line)
        if q:
            if para or lst:
                flush()
            quote.append(q.group(1))
            continue
        if lst:  # continuation of a list item
            lst[1][-1] += " " + line.strip()
            continue
        para.append(line.strip())
    flush()
    return "\n".join(out)


def nice(d):
    return d.strftime("%B %-d, %Y")


def read_minutes(body):
    return max(2, round(len(re.findall(r"\w+", body)) / 230))


def head(title, desc, url, R, og_type="website"):
    t, dsc = html.escape(title), html.escape(desc)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{dsc}">
<meta name="theme-color" content="#09090a">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{dsc}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="{og_type}">
<link rel="alternate" type="application/rss+xml" title="Cartier Creative Field Notes" href="{R}blog/feed.xml">
{ICON}
{FONTS}
<link rel="stylesheet" href="{R}blog/blog.css">
</head>"""


def post_page(p, newer, older):
    url = f"{SITE}/blog/{p['slug']}/"
    ld = ('{"@context":"https://schema.org","@type":"BlogPosting",'
          f'"headline":{html.escape(repr_json(p["title"]), quote=False)},'
          f'"datePublished":"{p["date"]}",'
          '"author":{"@type":"Person","name":"Carter Birky"},'
          '"publisher":{"@type":"Organization","name":"Cartier Creative"},'
          f'"mainEntityOfPage":"{url}"}}')
    pager = []
    if older:
        pager.append(f'<a class="pg" href="../{older["slug"]}/"><span class="mono">Older</span>{html.escape(older["title"])}</a>')
    if newer:
        pager.append(f'<a class="pg nx" href="../{newer["slug"]}/"><span class="mono">Newer</span>{html.escape(newer["title"])}</a>')
    return f"""{head(p['title'] + ' | Cartier Creative', p['summary'], url, '../../', 'article')}
<body>
<script type="application/ld+json">{ld}</script>
{NAV('../../')}
<main class="post">
  <div class="wrap narrow">
    <a class="back mono" href="../">&larr; All field notes</a>
    <p class="meta mono"><span class="tag">{html.escape(p['tag'])}</span><time datetime="{p['date']}">{nice(p['d'])}</time><span>{read_minutes(p['body'])} min read</span></p>
    <h1 class="balance">{inline(p['title'])}</h1>
    <p class="dek pretty">{inline(p['summary'])}</p>
    <p class="by">By Carter Birky, Cartier Creative</p>
    <article class="prose">
{md(p['body'])}
    </article>
    {'' if ':::cta' in p['body'] else CTA}
    <nav class="pager" aria-label="More posts">{''.join(pager)}</nav>
  </div>
</main>
{FOOTER('../../')}
</body>
</html>
"""


def repr_json(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def index_page(posts):
    cards = []
    for i, p in enumerate(posts):
        cls = "card lead" if i == 0 else "card"
        cards.append(f"""      <a class="{cls}" href="{p['slug']}/">
        <p class="meta mono"><span class="tag">{html.escape(p['tag'])}</span><time datetime="{p['date']}">{nice(p['d'])}</time></p>
        <h2 class="balance">{inline(p['title'])}</h2>
        <p class="pretty">{inline(p['summary'])}</p>
        <span class="more mono">Read &rarr;</span>
      </a>""")
    return f"""{head('Field Notes | Cartier Creative', 'Weekly notes for owner-run trades: plumbing, HVAC, roofing, electrical, landscaping and handyman. The numbers, the news, and what is working.', SITE + '/blog/', '../')}
<body>
{NAV('../')}
<main class="index">
  <div class="wrap">
    <p class="mono kicker">Field Notes &middot; every Monday</p>
    <h1 class="balance">Notes for the people <em>doing the work.</em></h1>
    <p class="sub pretty">One short read a week for owner-run trades. The numbers behind the phone, the news that hits your job sites, and what is working for shops like yours.</p>
    <div class="grid">
{chr(10).join(cards)}
    </div>
  </div>
</main>
{FOOTER('../')}
</body>
</html>
"""


def feed(posts):
    items = []
    for p in posts[:20]:
        url = f"{SITE}/blog/{p['slug']}/"
        pub = p["d"].strftime("%a, %d %b %Y 13:00:00 +0000")
        items.append(f"""  <item>
    <title>{html.escape(p['title'])}</title>
    <link>{url}</link>
    <guid>{url}</guid>
    <pubDate>{pub}</pubDate>
    <description>{html.escape(p['summary'])}</description>
  </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Cartier Creative Field Notes</title>
  <link>{SITE}/blog/</link>
  <description>Weekly notes for owner-run service businesses.</description>
{chr(10).join(items)}
</channel>
</rss>
"""


def main():
    posts = [parse(f) for f in sorted(POSTS.glob("*.md"))]
    live = sorted((p for p in posts if not p["draft"] and p["d"] <= date.today()),
                  key=lambda p: (p["d"], p["slug"]), reverse=True)
    for i, p in enumerate(live):
        newer = live[i - 1] if i > 0 else None
        older = live[i + 1] if i + 1 < len(live) else None
        d = BLOG / p["slug"]
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(post_page(p, newer, older), encoding="utf-8")
    (BLOG / "index.html").write_text(index_page(live), encoding="utf-8")
    (BLOG / "feed.xml").write_text(feed(live), encoding="utf-8")
    skipped = [p["slug"] for p in posts if p not in live]
    print(f"Built {len(live)} posts." + (f" Held back (draft or future date): {', '.join(skipped)}" if skipped else ""))


if __name__ == "__main__":
    main()
