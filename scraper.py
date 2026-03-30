import asyncio
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag
from playwright.async_api import Page

from auth import BASE_URL

# 詳細ページの th テキスト → フィールド名 のマッピング
_FIELD_MAP = {
    "課題に関する説明": "description",
    "受付開始日時":     "start_at",
    "受付終了日時":     "end_at",
    "状態":            "status",
}


@dataclass
class Assignment:
    type: str
    title: str
    title_url: str
    course: str
    course_url: str
    start_date: str       # 一覧ページから取得
    end_date: str         # 一覧ページから取得（空 → "期限なし"）
    description: str | None = None  # 詳細ページから取得（行ごと存在しない場合は None）
    status: str | None = None       # 詳細ページから取得


def _abs(href: str) -> str:
    """相対 URL を絶対 URL に変換する"""
    return f"{BASE_URL}/{href}" if href else ""


def _parse_row(row: Tag) -> "Assignment | None":
    """一覧の 1 行（tr.row0 / tr.row1）を Assignment に変換する"""
    tds = row.find_all("td", recursive=False)
    if len(tds) < 5:
        return None

    # タイプ（1列目）
    type_a = tds[0].find("a")
    assign_type = type_a.text.strip() if type_a else "不明"

    # タイトル（2列目）: <div class="myassignments-title"><a href="...">
    title_a = tds[1].select_one(".myassignments-title a")
    title = title_a.text.strip() if title_a else "不明"
    title_url = _abs(title_a.get("href", "")) if title_a else ""

    # コース（3列目）: <div class="mycourse-title"><a href="...">
    course_a = tds[2].select_one(".mycourse-title a")
    course = course_a.text.strip() if course_a else "不明"
    course_url = _abs(course_a.get("href", "")) if course_a else ""

    # 受付日時（4・5列目）: class="center td-period"
    period_tds = row.select("td.td-period")
    start_date = period_tds[0].text.strip() if len(period_tds) > 0 else ""
    end_date   = period_tds[1].text.strip() if len(period_tds) > 1 else ""

    return Assignment(
        type=assign_type,
        title=title,
        title_url=title_url,
        course=course,
        course_url=course_url,
        start_date=start_date,
        end_date=end_date if end_date else "期限なし",
    )


def _parse_detail(html: str) -> dict:
    """
    詳細ページの table.stdlist を解析する。
    行構造: th（ラベル）+ td（値）のペア形式。
    「課題に関する説明」行が存在しない場合は None のまま返す。
    """
    soup = BeautifulSoup(html, "html.parser")
    result: dict = {key: None for key in _FIELD_MAP.values()}

    table = soup.select_one("table.stdlist")
    if not table:
        return result

    for row in table.select("tr"):
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue

        label = th.get_text(strip=True)
        if label not in _FIELD_MAP:
            continue

        value: str | None = td.get_text(strip=True) or None
        if value in ("未設定", ""):
            value = None
        result[_FIELD_MAP[label]] = value

    return result


async def _fetch_detail(page: Page, url: str) -> dict:
    """詳細ページへ遷移して説明等を取得する"""
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    return _parse_detail(await page.content())


async def get_unsubmitted_assignments(page: Page) -> list[Assignment]:
    """
    1. home_library_query で未提出課題一覧を取得
    2. 各課題の詳細ページを順に巡回して description / status を補完
    """
    # ── STEP 1: 一覧取得 ────────────────────────────────────────
    await page.goto(f"{BASE_URL}/home_library_query")
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)

    soup = BeautifulSoup(await page.content(), "html.parser")
    table = soup.find("table", class_="stdlist")

    if not table:
        print("課題一覧テーブルが見つかりませんでした（課題ゼロ、またはログイン切れの可能性）。")
        return []

    assignments: list[Assignment] = []
    for row in table.select("tr.row0, tr.row1"):
        a = _parse_row(row)
        if a:
            assignments.append(a)

    # ── STEP 2: 各詳細ページを巡回 ──────────────────────────────
    total = len(assignments)
    for i, assignment in enumerate(assignments, 1):
        if not assignment.title_url:
            continue

        print(f"  [{i}/{total}] 詳細取得: {assignment.title}")
        detail = await _fetch_detail(page, assignment.title_url)
        assignment.description = detail["description"]
        assignment.status      = detail["status"]
        # 詳細ページの受付終了日時が取れた場合は一覧ページの値を上書き
        if detail.get("end_at"):
            assignment.end_date = detail["end_at"]
        await asyncio.sleep(1)  # サーバー負荷軽減

    # ── STEP 3: 期限なしの課題を除外 ────────────────────────────
    before = len(assignments)
    assignments = [a for a in assignments if a.end_date != "期限なし"]
    excluded = before - len(assignments)
    if excluded:
        print(f"  ※ 期限未設定の課題を {excluded} 件除外しました")

    return assignments
