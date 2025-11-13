from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

BASE = "<https://chunman4.com/>"

CANDIDATE_SELECTORS = [
    "a.xst",
    "a.s.xst",
    ".threadlist a[href*='thread-']",
    "a[href*='thread-']",
]

def parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    links = []
    for sel in CANDIDATE_SELECTORS:
        links = soup.select(sel)
        if links:
            break
    items = []
    for a in links:
        href = a.get("href") or ""
        title = a.get_text(strip=True)
        if not href or not title:
            continue
        link = urljoin(BASE, href)
        row = a.find_parent("tr") or a.find_parent("li") or a
        author = ""
        digest = ""
        cand_auth = row.select_one(".by cite, cite, .xi2, .author") if row else None
        if cand_auth:
            author = cand_auth.get_text(strip=True)
        cand_dig = row.select_one(".abstract, .summary, .excerpt")
        if cand_dig:
            digest = cand_dig.get_text(strip=True)[:200]
        items.append({
            "title": title,
            "url": link,
            "author": author,
            "published_at": datetime.utcnow().isoformat(),
            "digest": digest,
            "platform": "论坛",
        })
    return items
