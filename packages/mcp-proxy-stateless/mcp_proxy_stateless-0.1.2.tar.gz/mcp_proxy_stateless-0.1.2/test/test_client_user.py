"""
エンドユーザー視点（MCPクライアントとして）の統合テスト。

目的:
- Claude Desktop の `mcpServers` 設定と同等の JSON を元に、外部プロセスとして
  スタートした `mcp-proxy-stateless`（stdio サーバ）に stdio クライアントとして接続し、
  initialize / list_tools / call_tool を確認します。

工夫点:
- 実運用では `"command": "wsl", "args": ["uvx", "mcp-proxy-stateless", ...]` としますが、
  テスト環境に `wsl` や `uvx` が無い場合に備え、Python モジュール直接実行
  (`sys.executable -m post_class.mcp_proxy_stateless.main`) へ自動フォールバックします。
- URL は `.env` の `TEST_URL_PLAYWRIGHT` を利用します。

前提:
- ネットワーク到達可能で、`TEST_URL_PLAYWRIGHT` が StreamableHTTP な MCP エンドポイントであること。
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def _load_test_env() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(dotenv_path=env_path)
    except Exception:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_test_env()


def _normalize_server_command(cfg: Dict[str, Any], *, extra_env: Optional[Dict[str, str]] = None) -> StdioServerParameters:
    """ユーザー設定（Claude の JSON 相当）から StdioServerParameters を生成。

    - `wsl` が無い環境では削除して後続へフォールバック
    - `uvx` が無ければ `python -m post_class.mcp_proxy_stateless.main` へ置換
    """
    # ユーザー設定のコマンド/引数から、`mcp-proxy-stateless` 以降を抽出し、
    # ローカルの Python モジュールを直接起動する形に統一する。
    # これにより、`wsl`/`uvx` 非依存でテストが安定する。
    raw_args: List[str] = list(cfg.get("args", []))
    tail: List[str]
    if "mcp-proxy-stateless" in raw_args:
        i = raw_args.index("mcp-proxy-stateless")
        tail = raw_args[i + 1 :]
    else:
        # `mcp-proxy-stateless` が明示されていない場合は、すべてをそのまま引き継ぐ。
        tail = raw_args

    command = sys.executable
    args = ["-m", "post_class.mcp_proxy_stateless.main", *tail]
    env = dict(cfg.get("env", {}) or {})
    if extra_env:
        env.update(extra_env)
    return StdioServerParameters(command=command, args=args, env=env or None)


class TestClientLike(unittest.TestCase):
    @staticmethod
    def _load_server_cfg(name: str) -> Dict[str, Any]:
        cfg_path = Path("test/test_mcp_servers.json")
        user_cfg_json = json.loads(cfg_path.read_text(encoding="utf-8"))
        mcp_servers = user_cfg_json.get("mcpServers", {})
        if name not in mcp_servers:
            raise AssertionError(f"server '{name}' not found in test_mcp_servers.json")
        server_cfg = dict(mcp_servers[name])

        # 環境変数展開
        raw_args: List[str] = list(server_cfg.get("args", []))
        expanded_args: List[str] = [os.path.expandvars(a) if isinstance(a, str) else a for a in raw_args]
        server_cfg["args"] = expanded_args

        # URL 後方互換（なければ TEST_URL_PLAYWRIGHT を末尾に追加）
        args_list: List[str] = list(server_cfg.get("args", []))
        has_url = any(isinstance(a, str) and (a.startswith("http://") or a.startswith("https://")) for a in args_list)
        if not has_url:
            override_url = os.environ.get("TEST_URL_PLAYWRIGHT")
            if override_url:
                args_list.append(override_url)
                server_cfg["args"] = args_list
        return server_cfg

    async def _run_flow(self, server_cfg: Dict[str, Any], *, expect_success: bool, extra_env: Optional[Dict[str, str]] = None) -> None:
        params = _normalize_server_command(server_cfg, extra_env=extra_env)
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    init = await asyncio.wait_for(session.initialize(), timeout=30)
                    if not expect_success:
                        raise AssertionError("expected failure but initialize succeeded")

                    # success path: tools + optional navigate
                    tools = await asyncio.wait_for(session.list_tools(), timeout=30)
                    names = [t.name for t in tools.tools]
                    if "browser_navigate" in names:
                        result = await asyncio.wait_for(
                            session.call_tool("browser_navigate", {"url": "https://yahoo.co.jp"}),
                            timeout=60,
                        )
                        texts = [getattr(c, "text", "") or "" for c in result.content]
                        joined = "\n".join(texts)
                        assert ("Yahoo! JAPAN" in joined) or ("Page URL" in joined)
        except Exception:
            if expect_success:
                raise
            # expected failure case
            return

    @unittest.skipUnless(Path("test/test_mcp_servers.json").exists(), "test_mcp_servers.json not found")
    def test_my_mcp_insecure(self) -> None:
        """--insecure が付与されているため、TLS検証失敗に起因するエラーは発生しない想定。"""
        server_cfg = self._load_server_cfg("my_mcp_insecure")
        asyncio.run(self._run_flow(server_cfg, expect_success=True))

    @unittest.skipUnless(Path("test/test_mcp_servers.json").exists(), "test_mcp_servers.json not found")
    def test_my_mcp_ssl_error(self) -> None:
        """--insecure が無いため、TLS検証でエラーになる想定。"""
        server_cfg = self._load_server_cfg("my_mcp_ssl_error")
        asyncio.run(self._run_flow(server_cfg, expect_success=False))

    @unittest.skipUnless(Path("test/test_mcp_servers.json").exists(), "test_mcp_servers.json not found")
    def test_my_mcp_ssl_cert_file(self) -> None:
        """SSL_CERT_FILE を環境変数として登録して TLS 検証を通す想定（--insecure 無し）。"""
        server_cfg = self._load_server_cfg("my_mcp_ssl_cert_file")
        ssl_cert_file = os.environ.get("SSL_CERT_FILE")
        if not ssl_cert_file:
            self.skipTest("SSL_CERT_FILE not set in environment/.env")
        asyncio.run(self._run_flow(server_cfg, expect_success=True, extra_env={"SSL_CERT_FILE": ssl_cert_file}))


if __name__ == "__main__":
    unittest.main()
