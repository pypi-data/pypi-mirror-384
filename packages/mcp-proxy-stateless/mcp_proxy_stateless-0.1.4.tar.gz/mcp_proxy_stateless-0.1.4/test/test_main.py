"""
単体テスト（ユニットテスト）

このファイルでは、以下の観点を重点的に確認します。

- ヘッダー前処理: ユーザーが指定した `mcp-session-id` を常に破棄できているか
- TLS 検証切替: `--insecure` 指定の有無で httpx の検証挙動が切り替わるか

注意点:
- CI/開発環境に `mcp` SDK がインストールされていなくてもテストを実行できるよう、
  ここでは `mcp` をスタブ（最小限のダミー実装）で差し込んでいます。
- ネットワークには接続せず、httpx の内部状態のみを確認します。
"""

import ssl
import unittest
import asyncio
import sys
import types

# `mcp` SDK が未インストールでも import 可能にするための簡易スタブ。
# ここでは型や実行経路が必要最小限に満たされれば良いので、
# 実処理は呼ばれないよう RuntimeError を上げるダミーを用意しています。
mcp = types.ModuleType("mcp")
mcp.server = types.ModuleType("mcp.server")
mcp.types = types.ModuleType("mcp.types")
mcp.client = types.ModuleType("mcp.client")
mcp.client.session = types.ModuleType("mcp.client.session")

class _DummyClientSession:  # pragma: no cover - not executed
    def __init__(self, *_, **__):
        pass

mcp.client.session.ClientSession = _DummyClientSession

mcp.client.streamable_http = types.ModuleType("mcp.client.streamable_http")
async def _dummy_streamablehttp_client(*_, **__):  # pragma: no cover - not executed
    raise RuntimeError("not used in unit tests")

mcp.client.streamable_http.streamablehttp_client = _dummy_streamablehttp_client
mcp.server.stdio = types.ModuleType("mcp.server.stdio")
async def _dummy_stdio_server():  # pragma: no cover - not executed
    raise RuntimeError("not used in unit tests")

mcp.server.stdio.stdio_server = _dummy_stdio_server

sys.modules.setdefault("mcp", mcp)
sys.modules.setdefault("mcp.server", mcp.server)
sys.modules.setdefault("mcp.types", mcp.types)
sys.modules.setdefault("mcp.client", mcp.client)
sys.modules.setdefault("mcp.client.session", mcp.client.session)
sys.modules.setdefault("mcp.client.streamable_http", mcp.client.streamable_http)
sys.modules.setdefault("mcp.server.stdio", mcp.server.stdio)

try:
    import httpx  # noqa: F401
    HAS_HTTPX = True
except Exception:  # pragma: no cover - environment dependent
    HAS_HTTPX = False

from post_class.mcp_proxy_stateless.main import (
    StatelessStreamableHTTPClient,  # 被テスト対象: httpx クライアントファクトリ等
    _parse_headers,  # 被テスト対象: ヘッダー前処理（mcp-session-id 破棄）
)


class TestMain(unittest.TestCase):
    def test_parse_headers_drops_mcp_session_id(self) -> None:
        """ユーザー指定ヘッダーから mcp-session-id を確実に除去できること。"""
        pairs = [("Authorization", "token"), ("mcp-session-id", "abc"), ("X-Test", "1")]
        out = _parse_headers(pairs)
        self.assertIn("Authorization", out)
        self.assertEqual(out["Authorization"], "token")
        self.assertIn("X-Test", out)
        self.assertEqual(out["X-Test"], "1")
        # mcp-session-id must be removed
        self.assertNotIn("mcp-session-id", {k.lower() for k in out.keys()})

    @unittest.skipUnless(HAS_HTTPX, "httpx not installed")
    def test_httpx_client_factory_insecure_true_sets_no_verify(self) -> None:
        """--insecure 指定時は証明書検証とホスト名検証が無効化されること。"""
        async def run() -> None:
            client = StatelessStreamableHTTPClient("https://example.invalid", insecure=True)
            async_client = client._httpx_client_factory()  # type: ignore[attr-defined]
            try:
                pool = async_client._transport._pool  # type: ignore[attr-defined]
                ctx = pool._ssl_context  # type: ignore[attr-defined]
                self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)
                self.assertFalse(ctx.check_hostname)
            finally:
                await async_client.aclose()

        asyncio.run(run())

    @unittest.skipUnless(HAS_HTTPX, "httpx not installed")
    def test_httpx_client_factory_insecure_false_keeps_verify(self) -> None:
        """--insecure 未指定時は証明書/ホスト名検証が有効のままであること。"""
        async def run() -> None:
            client = StatelessStreamableHTTPClient("https://example.invalid", insecure=False)
            async_client = client._httpx_client_factory()  # type: ignore[attr-defined]
            try:
                pool = async_client._transport._pool  # type: ignore[attr-defined]
                ctx = pool._ssl_context  # type: ignore[attr-defined]
                self.assertNotEqual(ctx.verify_mode, ssl.CERT_NONE)
                self.assertTrue(ctx.check_hostname)
            finally:
                await async_client.aclose()

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
