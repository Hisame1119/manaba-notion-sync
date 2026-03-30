import os
from dotenv import load_dotenv

# dotenv を読み込みつつ、データベースIDとデータソースIDをデモ用に上書きする
load_dotenv()
db_id = os.environ.get("DEMO_NOTION_DATABASE_ID")
ds_id = os.environ.get("DEMO_NOTION_DATASOURCE_ID")

if not db_id or not ds_id:
    print("エラー: DEMO_NOTION_DATABASE_ID または DEMO_NOTION_DATASOURCE_ID が .env に設定されていません。")
    exit(1)

os.environ["NOTION_DATABASE_ID"] = db_id
os.environ["NOTION_DATASOURCE_ID"] = ds_id

# 上書き後にモジュールをインポートする（モジュールレベルで環境変数を読むため）
from scraper import Assignment
from notion_sync import sync_all

demo_data = [
    # ソフトウェア工学
    Assignment(type="レポート", title="第1回 ソフトウェア開発プロセスについてのレポート", title_url="https://example.manaba.jp/ct/d1", course="ソフトウェア工学", course_url="", start_date="2026-04-01 09:00", end_date="2026-04-07 23:59", description="アジャイルとウォーターフォールの比較", status="受付中"),
    Assignment(type="小テスト", title="アジャイル開発 小テスト", title_url="https://example.manaba.jp/ct/d2", course="ソフトウェア工学", course_url="", start_date="2026-04-05 09:00", end_date="2026-04-06 23:59", description="確認テスト", status="未完了"),

    # データベース基礎
    Assignment(type="課題", title="ER図の作成課題", title_url="https://example.manaba.jp/ct/d3", course="データベース基礎", course_url="", start_date="2026-04-02 10:00", end_date="2026-04-09 17:00", description="指定された要件からER図を作成", status="受付中"),
    Assignment(type="レポート", title="正規化についての考察", title_url="https://example.manaba.jp/ct/d4", course="データベース基礎", course_url="", start_date="2026-04-10 09:00", end_date="2026-04-17 23:59", description="第3正規形までの手順", status="受付前"),

    # 情報工学演習
    Assignment(type="プロジェクト", title="中間プロダクトの提出", title_url="https://example.manaba.jp/ct/d5", course="情報工学演習", course_url="", start_date="2026-03-31 09:00", end_date="2026-04-15 12:00", description="ソースコード一式をZIPで提出", status="受付中"),
    Assignment(type="小テスト", title="Gitの基本操作テスト", title_url="https://example.manaba.jp/ct/d6", course="情報工学演習", course_url="", start_date="2026-04-01 09:00", end_date="2026-04-03 23:59", description="変更のコミットからPushまで", status="受付中"),
    Assignment(type="アンケート", title="チーム開発振り返りアンケート", title_url="https://example.manaba.jp/ct/d7", course="情報工学演習", course_url="", start_date="2026-04-15 12:00", end_date="2026-04-20 23:59", description="KPT法による振り返り", status="受付前"),

    # アルゴリズム論
    Assignment(type="課題", title="ソートアルゴリズムの実装", title_url="https://example.manaba.jp/ct/d8", course="アルゴリズム論", course_url="", start_date="2026-04-05 09:00", end_date="2026-04-12 23:59", description="クイックソートとマージソートの実装", status="受付中"),
    Assignment(type="レポート", title="計算量の比較レポート", title_url="https://example.manaba.jp/ct/d9", course="アルゴリズム論", course_url="", start_date="2026-04-12 09:00", end_date="2026-04-19 23:59", description="O(n log n)の証明", status="受付前"),

    # 情報セキュリティ
    Assignment(type="小テスト", title="暗号化方式の基礎", title_url="https://example.manaba.jp/ct/d10", course="情報セキュリティ", course_url="", start_date="2026-04-02 09:00", end_date="2026-04-04 23:59", description="共通鍵と公開鍵の違い", status="受付中"),
    Assignment(type="課題", title="脆弱性診断レポート", title_url="https://example.manaba.jp/ct/d11", course="情報セキュリティ", course_url="", start_date="2026-04-10 09:00", end_date="2026-04-24 23:59", description="提供されたWebアプリのSQLiを特定する", status="受付前"),

    # ネットワーク工学
    Assignment(type="レポート", title="OSI参照モデルの各層の役割", title_url="https://example.manaba.jp/ct/d12", course="ネットワーク工学", course_url="", start_date="2026-04-08 09:00", end_date="2026-04-15 23:59", description="第1層から第7層まで", status="受付中"),
    Assignment(type="小テスト", title="TCP/IP 小テスト", title_url="https://example.manaba.jp/ct/d13", course="ネットワーク工学", course_url="", start_date="2026-04-01 09:00", end_date="2026-04-08 23:59", description="ハンドシェイクプロトコルについて", status="受付中"),

    # 教養ゼミナール
    Assignment(type="アンケート", title="第1回 興味のある研究テーマ調査", title_url="https://example.manaba.jp/ct/d14", course="教養ゼミナール", course_url="", start_date="2026-04-01 09:00", end_date="2026-04-05 23:59", description="卒論に向けたアンケート", status="受付中"),
    Assignment(type="レポート", title="先行研究の要約", title_url="https://example.manaba.jp/ct/d15", course="教養ゼミナール", course_url="", start_date="2026-04-05 09:00", end_date="2026-04-20 23:59", description="論文3本の要約", status="受付中"),

    # 期限切れ（過去日付）のサンプル
    Assignment(type="レポート", title="第1回 演習レポート（締切済み）", title_url="https://example.manaba.jp/ct/d16", course="情報工学演習", course_url="", start_date="2026-03-01 09:00", end_date="2026-03-15 23:59", description="提出期限を過ぎた未提出課題", status="未完了"),
    Assignment(type="小テスト", title="アルゴリズム基礎確認テスト", title_url="https://example.manaba.jp/ct/d17", course="アルゴリズム論", course_url="", start_date="2026-03-10 09:00", end_date="2026-03-25 23:59", description="期限が切れて受付終了となったもの", status="受付終了"),
]

print("15件のデモデータを Notino に同期します...")
sync_all(demo_data)
print("同期が完了しました。")
