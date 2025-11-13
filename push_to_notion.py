import os, requests, json

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}
API_URL = "https://api.notion.com/v1/pages"

def make_page(item: dict) -> dict:
    return {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "标题": {"title": [{"text": {"content": item["title"][:200]}}]},
            "来源链接": {"url": item["url"]},
            "平台": {"select": {"name": item["platform"]}},
            "发布时间": {"date": {"start": item["published_at"]}},
            "作者": {"rich_text": [{"text": {"content": item.get("author", "")}}]},
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": item.get("digest", "")}}
                    ]
                },
            }
        ],
    }

def push_items(items: list[dict]):
    print(f"[INFO] ready_to_push={len(items)}")
    for it in items:
        try:
            print("[PUSH]", it.get("title"), it.get("url"))
            payload = make_page(it)
            r = requests.post(API_URL, headers=HEADERS, data=json.dumps(payload), timeout=25)
            if r.status_code >= 400:
                # 打印更多上下文，方便在 Actions 日志定位问题
                print("[ERROR]", r.status_code, r.text[:500])
            r.raise_for_status()
            print("[OK]", it.get("title"))
        except Exception as e:
            print("[EXCEPTION]", it.get("title"), "->", repr(e))
