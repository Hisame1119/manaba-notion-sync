"""
Notion 同期の動作確認用テストスクリプト。
ダミーの Assignment を1件作成して Notion に登録する。
動作確認後は Notion 上で手動削除してください。
"""

from dotenv import load_dotenv
from scraper import Assignment
from notion_sync import sync_all

load_dotenv()

test_assignment = Assignment(
    type        = "レポート",
    title       = "【テスト】動作確認用エントリ",
    title_url   = "https://example.manaba.jp/ct/test_entry_do_not_submit",
    course      = "テスト科目",
    course_url  = "",
    start_date  = "2026-03-03 00:00",
    end_date    = "2026-03-31 23:59",
    description = "これは動作確認用のテストエントリです。確認後に削除してください。",
    status      = "受付中",
)

print("テストエントリを Notion に同期します...")
sync_all([test_assignment])
