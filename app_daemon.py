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
    
    while True:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        # 設定された時刻に一致し、かつ同じ分内で重複実行しないかチェック
        if current_time_str in TIMETABLES and last_run_time != current_time_str:
            _log(f"予定時刻 ({current_time_str}) になりました。スクレイピングを開始します。")
            try:
                # scheduler.py の同期処理を呼び出す
                await run()
            except Exception as e:
                _log(f"予期せぬエラーが発生しました: {e}")
            finally:
                last_run_time = current_time_str
                _log("完了しました。次の予定時刻まで待機します...")
        
        # 10秒に1回現在時刻を確認する（毎分チェックで漏れがないように）
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
