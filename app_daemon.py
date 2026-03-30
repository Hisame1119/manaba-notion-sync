import asyncio
import os
from datetime import datetime
from scheduler import run

# カンマ区切りでタイムテーブルを取得（例: "08:00,12:00,18:00"）
# 設定がない場合のデフォルトは朝・昼・夕方・夜の4回
env_timetables = os.environ.get("SCRAPING_TIMETABLES", "08:00,12:00,17:00,22:00")
TIMETABLES = [t.strip() for t in env_timetables.split(",") if t.strip()]

def _log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Dockerログ上でリアルタイム出力させるためにflush=Trueを設定
    print(f"[{timestamp}] [Daemon] {message}", flush=True)

async def main():
    _log(f"Docker用 DevOps Scraping Daemon 起動")
    _log(f"設定されたタイムテーブル: {', '.join(TIMETABLES)}")
    
    last_run_time = None
    is_initial_run = True  # 起動直後の初回実行フラグ
    
    while True:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        # 1. 予定時刻になった場合
        # 2. 起動直後の初回実行の場合
        is_scheduled_time = (current_time_str in TIMETABLES and last_run_time != current_time_str)
        
        if is_scheduled_time or is_initial_run:
            if is_initial_run:
                _log("起動直後のため、即座に実行を開始します。")
            else:
                _log(f"予定時刻 ({current_time_str}) になりました。スクレイピングを開始します。")
            
            try:
                # scheduler.py の同期処理を呼び出す
                await run()
            except Exception as e:
                _log(f"予期せぬエラーが発生しました: {e}")
            finally:
                last_run_time = current_time_str
                is_initial_run = False  # 初回実行完了
                _log("完了しました。次の予定時刻まで待機します...")
        
        # 10秒に1回現在時刻を確認する（毎分チェックで漏れがないように）
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
