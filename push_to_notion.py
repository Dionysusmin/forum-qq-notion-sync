import os, requests, json

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

if not NOTION_TOKEN or not NOTION_DATABASE_ID:
    raise ValueError("缺少 NOTION_TOKEN 或 NOTION_DATABASE_ID 环境变量")

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
            "来源链接": {"url": item.get("url")},
            "平台": {"select": {"name": item.get("platform", "未知")}},
            "发布时间": {"date": {"start": item.get("published_at")}},
            "作者": {"rich_text": [{"text": {"content": item.get("author", "")}}]},
        }
    }


def push_items(items: list[dict]):
    for it in items:
        payload = make_page(it)
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=25)
        if not r.ok:
            print("❌ 创建失败:", r.status_code, r.text)
        else:
            print("✅ 创建成功:", r.json()["id"])
