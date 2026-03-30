import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from auth import ensure_logged_in
from scraper import get_unsubmitted_assignments, Assignment

load_dotenv()

# ── 設定 ────────────────────────────────────────────────
EMAIL    = os.environ["MANABA_EMAIL"]
PASSWORD = os.environ["MANABA_PASSWORD"]

# MFA が求められる場合や初回セットアップ時は False に変更する
HEADLESS = False
# ────────────────────────────────────────────────────────


def _display(assignments: list[Assignment]) -> None:
    if not assignments:
        print("\n未提出の課題はありません。")
        return

    print(f"\n未提出課題: {len(assignments)} 件\n")
    print(f"{'タイプ':<10} {'締切':<20} {'コース':<28} タイトル")
    print("─" * 90)
    for a in assignments:
        deadline = a.end_date if a.end_date != "期限なし" else "期限なし"
        print(f"┌ [{a.type}] {a.title}")
        print(f"│  コース : {a.course}")
        print(f"│  締切   : {deadline}")
        print(f"│  説明   : {a.description or '（説明なし）'}")
        print(f"└  URL    : {a.title_url}")
        print()


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await ensure_logged_in(page, context, EMAIL, PASSWORD)
            assignments = await get_unsubmitted_assignments(page)
        finally:
            await browser.close()

    _display(assignments)


if __name__ == "__main__":
    asyncio.run(main())
