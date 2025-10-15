"""
統合テスト（実サーバ接続）。

前提:
- `.env` に `TEST_URL_PLAYWRIGHT` を設定してください。
  例) TEST_URL_PLAYWRIGHT=https://asktechno-browsermcp-stg.ask-techno.wdc.dev.cirrus.ibm.com/mcp

テスト内容:
- initialize 成功の確認（サーバ情報が返る）
- list_tools に `browser_navigate` が含まれること
- call_tool で `browser_navigate` を使い、https://yahoo.co.jp への遷移結果に
  タイトルや URL が含まれること（レスポンスのテキストを簡易検証）

注意:
- 環境に httpx がない場合、または TEST_URL_PLAYWRIGHT が未設定の場合はスキップします。
- 実サーバの実装/ネットワーク事情により SSE のクローズ時に一部警告ログが出ることがありますが、
  テスト結果には影響しません。
"""

import os
import asyncio
import unittest
from pathlib import Path


def _load_test_env() -> None:
    """.env を読み込む（python-dotenv があれば使用、なければ簡易パーサ）。"""
    env_path = Path(".env")
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(dotenv_path=env_path)
    except Exception:
        # 最小限のパーサ: KEY=VALUE のみを処理。コメント/空行は無視。
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_test_env()

try:
    import httpx  # noqa: F401
    HAS_HTTPX = True
except Exception:
    HAS_HTTPX = False

TEST_URL = os.environ.get("TEST_URL_PLAYWRIGHT")

from post_class.mcp_proxy_stateless.main import StatelessStreamableHTTPClient  # noqa: E402


@unittest.skipUnless(HAS_HTTPX and TEST_URL, "integration prerequisites not met")
class TestIntegration(unittest.TestCase):
    def setUp(self) -> None:
        # .env から読み込んだ URL をテスト対象として利用
        self.url = TEST_URL  # type: ignore[assignment]

    def test_initialize(self) -> None:
        async def run() -> None:
            client = StatelessStreamableHTTPClient(self.url, headers={}, insecure=True)
            res = await asyncio.wait_for(client.initialize(), timeout=20)
            # サーバ名（例: Playwright）が空でないこと
            self.assertTrue(getattr(res.serverInfo, "name", ""))

        asyncio.run(run())

    def test_list_tools(self) -> None:
        async def run() -> None:
            client = StatelessStreamableHTTPClient(self.url, headers={}, insecure=True)
            tools = await asyncio.wait_for(client.list_tools(), timeout=30)
            names = [t.name for t in tools.tools]
            # ブラウザ遷移ツールが含まれていること
            self.assertIn("browser_navigate", names)

        asyncio.run(run())

    def test_call_tool_navigate_yahoo(self) -> None:
        async def run() -> None:
            client = StatelessStreamableHTTPClient(self.url, headers={}, insecure=True)
            result = await asyncio.wait_for(
                client.call_tool("browser_navigate", {"url": "https://yahoo.co.jp"}),
                timeout=60,
            )
            # レスポンスの text を結合して、結果を簡易検証
            texts = []
            for c in result.content:
                text = getattr(c, "text", None)
                if text:
                    texts.append(text)
            joined = "\n".join(texts)
            # ページが描画されたことを示す文字列（タイトル or Page URL）が含まれているか
            self.assertTrue("Yahoo! JAPAN" in joined or "Page URL" in joined)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
