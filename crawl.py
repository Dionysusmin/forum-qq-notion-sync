import os, time, sqlite3, hashlib, random, requests, yaml
from datetime import datetime
from importlib import import_module
from push_to_notion import push_items

DB_PATH = "scraper/storage.sqlite"
COOKIE = os.environ.get("COOKIES_OR_TOKEN", "")
UA = "Mozilla/5.0 (NotionBot)"

def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pushed (
            fingerprint TEXT PRIMARY KEY,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn

def fp(item: dict) -> str:
    base = f"{item.get('url','')}|{item.get('title','')}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def already(conn, f: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pushed WHERE fingerprint=?", (f,))
    return cur.fetchone() is not None

def mark(conn, f: str):
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO pushed (fingerprint, created_at) VALUES (?, ?)",
        (f, datetime.utcnow().isoformat()),
    )
    conn.commit()

def fetch(url: str) -> str | None:
    headers = {"User-Agent": UA}
    if COOKIE:
        headers["Cookie"] = COOKIE
    for i in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        time.sleep(2 ** i)
    return None

def main():
    conn = ensure_db()

    with open("scraper/sources.yaml", "r", encoding="utf-8") as f:
        sources = yaml.safe_load(f) or []

    to_push = []
    print(f"[INFO] sources={len(sources)}")

    for src in sources:
        url = src.get("url")
        parser_name = src.get("parser")
        if not url or not parser_name:
            continue

        html = fetch(url)
        if not html:
            print("[WARN] fetch_failed", url)
            continue

        try:
            mod = import_module(f"scraper.parsers.{parser_name}")
        except Exception as e:
            print("[ERROR] import_parser_failed", parser_name, repr(e))
            continue

        try:
            items = mod.parse(html)
        except Exception as e:
            print("[ERROR] parse_failed", url, repr(e))
            continue

        for it in items:
            fpx = fp(it)
            if not already(conn, fpx):
                to_push.append(it)
                mark(conn, fpx)

        time.sleep(random.uniform(1, 3))

    print(f"[INFO] items_to_push={len(to_push)}")
    if to_push:
        print("[SAMPLE]", to_push[0].get("title"), to_push[0].get("url"))
        push_items(to_push)
    else:
        print("[INFO] nothing_to_push")

if __name__ == "__main__":
    main()
