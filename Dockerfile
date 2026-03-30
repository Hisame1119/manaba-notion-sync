# ==========================================
# 課題同期 Dockerfile
# Playwright が動作する公式イメージを利用
# ==========================================

FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /app

# パッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

# コード群のコピー
COPY . .

# 標準出力のバッファリングを無効化（ログをリアルタイム出力するため）
ENV PYTHONUNBUFFERED=1

# コンテナ起動時に常駐スクリプトを実行
CMD ["python", "app_daemon.py"]
