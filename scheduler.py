"""
スクレイプ → Notion 同期を一括実行するエントリポイント。
Windows Task Scheduler や手動実行で使用する。
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from auth import ensure_logged_in
from scraper import get_unsubmitted_assignments
from notion_sync import sync_all

load_dotenv()

EMAIL    = os.environ["MANABA_EMAIL"]
PASSWORD = os.environ["MANABA_PASSWORD"]

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


def _log(message: str) -> None:
    """コンソールとログファイルの両方に出力する"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m')}.log"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


async def run() -> None:
    _log("=== 実行開始 ===")

    # ── STEP 1: スクレイピング ───────────────────────────────────
    _log("manaba に接続中...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page    = await context.new_page()

        try:
            await ensure_logged_in(page, context, EMAIL, PASSWORD)
            assignments = await get_unsubmitted_assignments(page)
        finally:
            await browser.close()

    _log(f"未提出課題: {len(assignments)} 件を取得")

    if not assignments:
        _log("同期対象なし。終了します。")
        return

    # ── STEP 2: Notion 同期 ──────────────────────────────────────
    _log("Notion へ同期中...")
    sync_all(assignments)

    _log("=== 実行完了 ===")


if __name__ == "__main__":
    asyncio.run(run())
