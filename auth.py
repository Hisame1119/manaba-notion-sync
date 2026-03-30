import json
import asyncio
import os
from pathlib import Path
from playwright.async_api import Page, BrowserContext

BASE_URL = os.environ.get("MANABA_URL", "https://example.manaba.jp/ct")
COOKIES_FILE = Path("logs/cookies.json")


async def save_cookies(context: BrowserContext) -> None:
    cookies = await context.cookies()
    COOKIES_FILE.write_text(json.dumps(cookies, ensure_ascii=False, indent=2))


async def load_cookies(context: BrowserContext) -> bool:
    if not COOKIES_FILE.exists():
        return False
    cookies = json.loads(COOKIES_FILE.read_text())
    await context.add_cookies(cookies)
    return True


async def _wait_for_manaba(page: Page, timeout_sec: int = 120) -> None:
    """
    MFA 完了後に manaba へ遷移するまでポーリングで待機する。
    途中で「サインインの状態を維持しますか？」(KMSI) が出た場合のみ「いいえ」を押す。
    MFA 画面のキャンセルボタンと混同しないよう、URL で KMSI ページを判定する。
    """
    print(f"MFA 認証を待機中（最大 {timeout_sec} 秒）...")
    await page.screenshot(path="debug_10_wait_start.png")
    for i in range(timeout_sec):
        await asyncio.sleep(1)

        if "manaba.jp" in page.url:
            return

        # KMSI ページは URL に "kmsi" を含む
        # ここでだけ #idBtn_Back（「いいえ」）を押す
        if "kmsi" in page.url.lower():
            try:
                await page.click("#idBtn_Back", timeout=3000)
                print("「サインインの状態を維持しますか？」→ いいえ を選択")
            except Exception:
                pass
        
        # 10秒ごとに状況を保存
        if i % 5 == 0:
            title = await page.title()
            print(f"待機中 URL: {page.url} / TITLE: {title}")
            await page.screenshot(path=f"debug_11_waiting_{i}.png")
            # 何かボタンが出ているかチェック
            html = await page.content()
            with open(f"debug_html_{i}.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            # もしidBtn_Backがあれば押してみる
            try:
                if await page.locator("#idBtn_Back").is_visible():
                    print("「いいえ」ボタンが見つかりました。クリックします...")
                    await page.click("#idBtn_Back", timeout=3000)
            except Exception:
                pass

    raise TimeoutError(f"{timeout_sec} 秒以内に manaba へ遷移しませんでした。")


async def _do_microsoft_login(page: Page, email: str, password: str) -> None:
    """Azure AD の Microsoft ログインフォームを操作する"""

    try:
        # メールアドレス入力
        await page.fill('input[name="loginfmt"]', email)
        await page.click('input[type="submit"]')
        await page.wait_for_load_state("networkidle")

        # パスワード入力
        await page.fill('input[name="passwd"]', password)
        await page.click('input[type="submit"]')
        await page.wait_for_load_state("networkidle")
    except Exception as e:
        print(f"ログイン入力中にエラー: {e}")
        raise e

    # MFA 自動入力処理 (TOTP)
    mfa_secret = os.environ.get("MANABA_MFA_SECRET")
    if mfa_secret:
        import pyotp
        totp = pyotp.TOTP(mfa_secret)
        code = totp.now()
        
        try:
            # ページ遷移や描画を少し待機
            await asyncio.sleep(2)
            
            # OTP入力欄が直接出ているか確認
            if await page.locator('input[name="otc"], #idTxtBx_SAOTCC_OTC').count() > 0:
                await page.fill('input[name="otc"], #idTxtBx_SAOTCC_OTC', code)
                await page.click('input[type="submit"]')
                print(f"MFA 自動入力完了: {code}")
            else:
                # 入力欄がない場合、「別の方法でサインインする」リンクがあれば押す
                if await page.locator('a[id="signInAnotherWay"]').count() > 0:
                    await page.click('a[id="signInAnotherWay"]')
                    await page.wait_for_load_state("networkidle")
                    
                    # 「確認コードを使用する」オプションをクリック
                    if await page.locator('div[data-value="PhoneAppOTP"]').count() > 0:
                        await page.click('div[data-value="PhoneAppOTP"]')
                        await page.wait_for_load_state("networkidle")
                        
                        await page.fill('input[name="otc"], #idTxtBx_SAOTCC_OTC', code)
                        await page.click('input[type="submit"]')
                        print(f"MFA 自動入力完了 (別メソッド選択経由): {code}")
                else:
                    print("MFAの入力欄も別オプション画面も見つかりませんでした。")
        except Exception as e:
            print(f"MFAの自動入力中にエラーまたはタイムアウト: {e}")

    # MFA 完了 → manaba 到達まで待機（KMSI ページのみ自動処理）
    await _wait_for_manaba(page)



async def ensure_logged_in(
    page: Page,
    context: BrowserContext,
    email: str,
    password: str,
) -> None:
    """
    保存済みクッキーでセッション復元を試み、
    期限切れ or 初回の場合はログインを実行してクッキーを保存する。

    MFA が必要な場合に備えて headless=False で起動することを推奨。
    """
    await load_cookies(context)

    await page.goto(f"{BASE_URL}/home")
    await page.wait_for_load_state("networkidle")

    # manaba のホームに到達できていればセッション有効
    if page.url.startswith(f"{BASE_URL}/home"):
        print("セッション有効: ログイン済みです")
        return

    print("ログインが必要です。Microsoft 認証を開始します...")
    await _do_microsoft_login(page, email, password)

    if not page.url.startswith(f"{BASE_URL}/"):
        raise RuntimeError(
            f"ログインに失敗しました。MFA の手動操作が必要な可能性があります。\n"
            f"現在の URL: {page.url}"
        )

    print("ログイン成功。クッキーを保存します。")
    await save_cookies(context)
