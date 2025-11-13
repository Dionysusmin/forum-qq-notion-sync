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


# -------------------------------------------------------
# 🔥 添加超级 debug 版 fetch
# -------------------------------------------------------
def fetch(url: str) -> str | None:
    headers = {"User-Agent": UA}
    if COOKIE:
        headers["Cookie"] = COOKIE

    print(f"\n[FETCH] requesting: {url}")
    print(f"[FETCH] Cookie present: {bool(COOKIE)}")

    for i in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=20)

            print(f"[FETCH] Attempt {i+1} status:", r.status_code)
            print("[FETCH] Header Server:", r.headers.get("Server"))
            print("[FETCH] Snippet:", r.text[:300].replace("\n", " ")[:300])

            if r.status_code == 200:
                return r.text
        except Exception as e:
            print(f"[FETCH] Exception: {repr(e)}")

        time.sleep(2 ** i)

    print("[FETCH] FAILED")
    return None


# -------------------------------------------------------
# 🔥 主流程（加强 debug）
# -------------------------------------------------------
def main():
    conn = ensure_db()

    # Load sources
    with open("scraper/sources.yaml", "r", encoding="utf-8") as f:
        sources = yaml.safe_load(f) or []

    print(f"\n[INFO] Loaded sources: {len(sources)}")
    for s in sources:
        print("[INFO] source:", s)

    to_push = []

    for src in sources:
        url = src.get("url")
        parser_name = src.get("parser")

        if not url or not parser_name:
            print("[WARN] source missing url/parser:", src)
            continue

        # Fetch
        html = fetch(url)
        if not html:
            print("[WARN] fetch_failed", url)
            continue

        # Import parser
        try:
            mod = import_module(f"scraper.parsers.{parser_name}")
            print(f"[PARSER] Loaded: {parser_name}")
        except Exception as e:
            print("[ERROR] import_parser_failed", parser_name, repr(e))
            continue

        # Parse
        try:
            items = mod.parse(html)
            print(f"[PARSER] Parsed items: {len(items)}")
        except Exception as e:
            print("[ERROR] parse_failed:", repr(e))
            continue

        # Dedup
        for it in items:
            fpx = fp(it)
            if not already(conn, fpx):
                to_push.append(it)
                mark(conn, fpx)

        time.sleep(random.uniform(1, 2))

print(f"\n[INFO] Loaded sources: {len(sources)}")
for s in sources:
    print("[INFO] source:", s)


