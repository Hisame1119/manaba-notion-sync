import os
import httpx
from datetime import datetime
from dotenv import load_dotenv
from scraper import Assignment

load_dotenv()

_API_KEY = os.environ["NOTION_API_KEY"]
DB_ID    = os.environ["NOTION_DATABASE_ID"]   # データベースコンテナの ID
DS_ID    = os.environ["NOTION_DATASOURCE_ID"] # データソースの ID（クエリ・ページ作成に使用）

_BASE    = "https://api.notion.com/v1"
_HEADERS = {
    "Authorization": f"Bearer {_API_KEY}",
    "Notion-Version": "2025-09-03",
    "Content-Type": "application/json",
}

# ── 科目マッピング ────────────────────────────────────────────────
# manaba のコース名 → Notion の科目 Select 値
# 辞書にないコース名は manaba 名をそのまま Notion に追加する（自動新規作成）
COURSE_MAP: dict[str, str] = {
    # "manaba のコース名（完全一致）": "Notion の科目名",
    # 例: "2025年度プログラミング応用": "プログラミング応用 [A]",
}
# ────────────────────────────────────────────────────────────────


def _to_notion_date(date_str: str) -> dict | None:
    """
    "2025-03-01 09:00" や "2025-03-01 09:00:00" → {"start": "2025-03-01T09:00:00", "time_zone": "Asia/Tokyo"}
    空文字 / "期限なし" → None

    Notion の仕様:
    - time_zone 指定時は UTC オフセット (+09:00) を付けてはいけない
    - time_zone 指定時は時刻を必ず含める必要がある
    """
    if not date_str or date_str == "期限なし":
        return None
    
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return {
                "start":     dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "time_zone": "Asia/Tokyo",
            }
        except ValueError:
            pass
            
    return None


def _resolve_course(course_name: str) -> str:
    return COURSE_MAP.get(course_name, course_name)


def _find_existing_page(url: str) -> str | None:
    """
    場所フィールドの URL で既存ページを検索し page_id を返す。
    2025-09-03: /databases/{id}/query → /data_sources/{id}/query
    """
    res = httpx.post(
        f"{_BASE}/data_sources/{DS_ID}/query",
        headers=_HEADERS,
        json={
            "filter": {
                "property": "場所",
                "rich_text": {"equals": url},
            }
        },
    )
    res.raise_for_status()
    results = res.json().get("results", [])
    return results[0]["id"] if results else None


def _build_properties(a: Assignment, *, is_new: bool) -> dict:
    props: dict = {
        "タスク名": {"title":     [{"text": {"content": a.title}}]},
        "科目":     {"select":    {"name": _resolve_course(a.course)}},
        "タイプ":   {"select":    {"name": a.type}},
        "場所":     {"rich_text": [{"text": {"content": a.title_url, "link": {"url": a.title_url}}}]},
        "詳細":     {"rich_text": [{"text": {"content": a.description or ""}}]},
    }
    # 進捗は新規作成時のみ設定（更新時はユーザーの現在値を保持）
    if is_new:
        props["進捗"] = {"status": {"name": "未着手"}}
    if date := _to_notion_date(a.end_date):
        props["期限"] = {"date": date}
    return props


def upsert(a: Assignment) -> str:
    """
    場所フィールドの URL で重複チェック。
    - 既存あり → 更新（進捗は保持）
    - 既存なし → 新規作成（進捗 = 未着手）
    2025-09-03: parent.database_id → parent.data_source_id
    """
    page_id = _find_existing_page(a.title_url)

    if page_id:
        res = httpx.patch(
            f"{_BASE}/pages/{page_id}",
            headers=_HEADERS,
            json={"properties": _build_properties(a, is_new=False)},
        )
        res.raise_for_status()
        return "updated"
    else:
        res = httpx.post(
            f"{_BASE}/pages",
            headers=_HEADERS,
            json={
                "parent":     {"type": "data_source_id", "data_source_id": DS_ID},
                "properties": _build_properties(a, is_new=True),
            },
        )
        res.raise_for_status()
        return "created"


def sync_all(assignments: list[Assignment]) -> None:
    # 確実に期限が取得・パースできている課題のみを同期対象とする
    valid_assignments = [a for a in assignments if _to_notion_date(a.end_date) is not None]
    
    total   = len(valid_assignments)
    created = updated = 0

    for i, a in enumerate(valid_assignments, 1):
        result = upsert(a)
        if result == "created":
            created += 1
        else:
            updated += 1
        print(f"  [{i}/{total}] {result}: {a.title}")

    print(f"\n同期完了 — 新規: {created} 件, 更新: {updated} 件")

