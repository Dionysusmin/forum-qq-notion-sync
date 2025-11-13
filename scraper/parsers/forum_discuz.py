from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

BASE = "https://chunman4.com/"


def parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    items = []
    # Discuz 列表页帖子标题一般使用 a.xst
    for a in soup.select("a.xst"):
        title = a.get_text(strip=True)
        link = urljoin(BASE, a.get("href"))
        # 作者通常位于同一行的 .by 或 cite 元素内
        row = a.find_parent("tr") or a
        author = ""
        cand = None
        if row:
            cand = row.select_one(".by cite, cite, .xi2")
        if cand:
            author = cand.get_text(strip=True)
        items.append({
            "title": title,
            "url": link,
            "author": author,
            "published_at": datetime.utcnow().isoformat(),
            "digest": "",
            "platform": "论坛",
        })
    return items
