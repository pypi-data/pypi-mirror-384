from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
import sys
from typing import Any, Dict, Iterable, Tuple


# The MCP Python SDK provides both client and server primitives
from mcp import server as mcp_server
from mcp import types as mcp_types
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.server.stdio import stdio_server


def _parse_headers(pairs: Iterable[Tuple[str, str]]) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for k, v in pairs:
        # Drop mcp-session-id from user-provided headers to enforce stateless behavior
        if k.lower() == "mcp-session-id":
            continue
        headers[k] = v
    return headers


class StatelessStreamableHTTPClient:
    """A thin wrapper that opens a fresh StreamableHTTP session per call.

    Notes
    - Each method call below performs its own connection lifecycle:
      connect -> initialize -> perform the action -> close.
    - This avoids carrying over any session state or mcp-session-id between calls.
    """

    def __init__(
        self,
        url: str,
        headers: Dict[str, Any] | None = None,
        *,
        insecure: bool = False,
        ssl_cert_file: str | None = None,
        timeout: int | float = 120,
    ) -> None:
        self._url = url
        self._headers = dict(headers or {})
        self._insecure = insecure
        self._ssl_cert_file = ssl_cert_file
        self._timeout = float(timeout)

    def _httpx_client_factory(
        self,
        *,
        headers: Dict[str, str] | None = None,
        timeout: Any | None = None,
        auth: Any | None = None,
    ) -> Any:
        # Local import to avoid hard dependency at module import time
        import httpx  # type: ignore
        kwargs: Dict[str, Any] = {
            "follow_redirects": True,
        }
        if timeout is None:
            # Use overall timeout for individual HTTP operations
            kwargs["timeout"] = httpx.Timeout(self._timeout)
        else:
            kwargs["timeout"] = timeout
        if headers is not None:
            kwargs["headers"] = headers
        if auth is not None:
            kwargs["auth"] = auth
        if self._insecure:
            kwargs["verify"] = False
        elif self._ssl_cert_file:
            # Use the provided CA bundle only for this client.
            kwargs["verify"] = self._ssl_cert_file
        return httpx.AsyncClient(**kwargs)

    async def _with_session(self) -> Tuple[ClientSession, Any, Any]:  # type: ignore[override]
        ctx = streamablehttp_client(
            url=self._url,
            headers=self._headers,
            httpx_client_factory=lambda **kw: self._httpx_client_factory(**kw),
        )
        read = write = None
        session: ClientSession | None = None
        streams_cm = ctx  # alias for clarity
        streams = await streams_cm.__aenter__()
        try:
            if isinstance(streams, tuple) and len(streams) >= 2:
                read, write = streams[0], streams[1]
            else:  # pragma: no cover - defensive
                raise RuntimeError("Invalid streams from streamablehttp_client")

            session_cm = ClientSession(read, write)
            session = await session_cm.__aenter__()
            return session, streams_cm, session_cm
        except Exception:
            # Best-effort cleanup on failure
            with contextlib.suppress(Exception):
                if session is not None:
                    await session_cm.__aexit__(*sys.exc_info())  # type: ignore[arg-type]
            with contextlib.suppress(Exception):
                await streams_cm.__aexit__(*sys.exc_info())  # type: ignore[arg-type]
            raise

    async def initialize(self) -> mcp_types.InitializeResult:
        session, streams_cm, session_cm = await self._with_session()
        try:
            async with asyncio.timeout(self._timeout):
                init = await session.initialize()
                return init
        finally:
            await session_cm.__aexit__(None, None, None)
            await streams_cm.__aexit__(None, None, None)

    # Prompts
    async def list_prompts(self) -> mcp_types.ListPromptsResult:
        session, streams_cm, session_cm = await self._with_session()
        try:
            async with asyncio.timeout(self._timeout):
                await session.initialize()
                return await session.list_prompts()
        finally:
            await session_cm.__aexit__(None, None, None)
            await streams_cm.__aexit__(None, None, None)

    async def get_prompt(self, name: str, arguments: Dict[str, Any] | None = None) -> mcp_types.GetPromptResult:
        session, streams_cm, session_cm = await self._with_session()
        try:
            async with asyncio.timeout(self._timeout):
                await session.initialize()
                return await session.get_prompt(name, arguments)
        finally:
            await session_cm.__aexit__(None, None, None)
            await streams_cm.__aexit__(None, None, None)

    # Resources
    async def list_resources(self) -> mcp_types.ListResourcesResult:
        session, streams_cm, session_cm = await self._with_session()
        try:
            async with asyncio.timeout(self._timeout):
                await session.initialize()
                return await session.list_resources()
        finally:
            await session_cm.__aexit__(None, None, None)
            await streams_cm.__aexit__(None, None, None)

    async def list_resource_templates(self) -> mcp_types.ListResourceTemplatesResult:
        session, streams_cm, session_cm = await self._with_session()
        try:
            async with asyncio.timeout(self._timeout):
                await session.initialize()
                return await session.list_resource_templates()
        finally:
            await session_cm.__aexit__(None, None, None)
            await streams_cm.__aexit__(None, None, None)

    async def read_resource(self, uri: str) -> mcp_types.ReadResourceResult:
        session, streams_cm, session_cm = await self._with_session()
        try:
            async with asyncio.timeout(self._timeout):
                await session.initialize()
                return await session.read_resource(uri)
        finally:
            await session_cm.__aexit__(None, None, None)
            await streams_cm.__aexit__(None, None, None)

    # Tools
    async def list_tools(self) -> mcp_types.ListToolsResult:
        session, streams_cm, session_cm = await self._with_session()
        try:
            async with asyncio.timeout(self._timeout):
                await session.initialize()
                return await session.list_tools()
        finally:
            await session_cm.__aexit__(None, None, None)
            await streams_cm.__aexit__(None, None, None)

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> mcp_types.CallToolResult:
        session, streams_cm, session_cm = await self._with_session()
        try:
            async with asyncio.timeout(self._timeout):
                await session.initialize()
                return await session.call_tool(name, arguments)
        finally:
            await session_cm.__aexit__(None, None, None)
            await streams_cm.__aexit__(None, None, None)

    # Logging
    async def set_logging_level(self, level: mcp_types.LoggingLevel) -> None:
        session, streams_cm, session_cm = await self._with_session()
        try:
            async with asyncio.timeout(self._timeout):
                await session.initialize()
                await session.set_logging_level(level)
        finally:
            await session_cm.__aexit__(None, None, None)
            await streams_cm.__aexit__(None, None, None)

    # Subscriptions
    async def subscribe_resource(self, uri: str) -> None:
        session, streams_cm, session_cm = await self._with_session()
        try:
            async with asyncio.timeout(self._timeout):
                await session.initialize()
                await session.subscribe_resource(uri)
        finally:
            await session_cm.__aexit__(None, None, None)
            await streams_cm.__aexit__(None, None, None)

    async def unsubscribe_resource(self, uri: str) -> None:
        session, streams_cm, session_cm = await self._with_session()
        try:
            async with asyncio.timeout(self._timeout):
                await session.initialize()
                await session.unsubscribe_resource(uri)
        finally:
            await session_cm.__aexit__(None, None, None)
            await streams_cm.__aexit__(None, None, None)

    # Client notifications
    async def send_progress_notification(self, token: str, progress: int | None, total: int | None) -> None:  # noqa: D401
        session, streams_cm, session_cm = await self._with_session()
        try:
            async with asyncio.timeout(self._timeout):
                await session.initialize()
                await session.send_progress_notification(token, progress, total)
        finally:
            await session_cm.__aexit__(None, None, None)
            await streams_cm.__aexit__(None, None, None)

    # Completion APIs
    async def complete(self, ref: str, argument: Dict[str, Any] | None = None) -> mcp_types.CompleteResult:
        session, streams_cm, session_cm = await self._with_session()
        try:
            async with asyncio.timeout(self._timeout):
                await session.initialize()
                return await session.complete(ref, argument or {})
        finally:
            await session_cm.__aexit__(None, None, None)
            await streams_cm.__aexit__(None, None, None)


async def _create_proxy_server(remote_app: Any) -> mcp_server.Server[object]:
    """Create a proxy MCP server that forwards to the remote client.

    This mirrors the behavior of mcp-proxy, but uses the provided remote client
    (our stateless wrapper) for each request.
    """
    init = await remote_app.initialize()
    capabilities = init.capabilities

    app: mcp_server.Server[object] = mcp_server.Server(name=init.serverInfo.name)

    if capabilities.prompts:
        async def _list_prompts(_: Any) -> mcp_types.ServerResult:  # noqa: ANN401
            result = await remote_app.list_prompts()
            return mcp_types.ServerResult(result)

        app.request_handlers[mcp_types.ListPromptsRequest] = _list_prompts

        async def _get_prompt(req: mcp_types.GetPromptRequest) -> mcp_types.ServerResult:
            result = await remote_app.get_prompt(req.params.name, req.params.arguments)
            return mcp_types.ServerResult(result)

        app.request_handlers[mcp_types.GetPromptRequest] = _get_prompt

    if capabilities.resources:
        async def _list_resources(_: Any) -> mcp_types.ServerResult:  # noqa: ANN401
            result = await remote_app.list_resources()
            return mcp_types.ServerResult(result)

        app.request_handlers[mcp_types.ListResourcesRequest] = _list_resources

        async def _list_resource_templates(_: Any) -> mcp_types.ServerResult:  # noqa: ANN401
            result = await remote_app.list_resource_templates()
            return mcp_types.ServerResult(result)

        app.request_handlers[mcp_types.ListResourceTemplatesRequest] = _list_resource_templates

        async def _read_resource(req: mcp_types.ReadResourceRequest) -> mcp_types.ServerResult:
            result = await remote_app.read_resource(req.params.uri)
            return mcp_types.ServerResult(result)

        app.request_handlers[mcp_types.ReadResourceRequest] = _read_resource

        async def _subscribe_resource(req: mcp_types.SubscribeRequest) -> mcp_types.ServerResult:
            await remote_app.subscribe_resource(req.params.uri)
            return mcp_types.ServerResult(mcp_types.EmptyResult())

        app.request_handlers[mcp_types.SubscribeRequest] = _subscribe_resource

        async def _unsubscribe_resource(req: mcp_types.UnsubscribeRequest) -> mcp_types.ServerResult:
            await remote_app.unsubscribe_resource(req.params.uri)
            return mcp_types.ServerResult(mcp_types.EmptyResult())

        app.request_handlers[mcp_types.UnsubscribeRequest] = _unsubscribe_resource

    if capabilities.logging:
        async def _set_logging_level(req: mcp_types.SetLevelRequest) -> mcp_types.ServerResult:
            await remote_app.set_logging_level(req.params.level)
            return mcp_types.ServerResult(mcp_types.EmptyResult())

        app.request_handlers[mcp_types.SetLevelRequest] = _set_logging_level

    if capabilities.tools:
        async def _list_tools(_: Any) -> mcp_types.ServerResult:  # noqa: ANN401
            tools = await remote_app.list_tools()
            return mcp_types.ServerResult(tools)

        app.request_handlers[mcp_types.ListToolsRequest] = _list_tools

        async def _call_tool(req: mcp_types.CallToolRequest) -> mcp_types.ServerResult:
            try:
                result = await remote_app.call_tool(
                    req.params.name,
                    (req.params.arguments or {}),
                )
                return mcp_types.ServerResult(result)
            except Exception as e:  # noqa: BLE001
                return mcp_types.ServerResult(
                    mcp_types.CallToolResult(
                        content=[mcp_types.TextContent(type="text", text=str(e))],
                        isError=True,
                    ),
                )

        app.request_handlers[mcp_types.CallToolRequest] = _call_tool

    async def _send_progress_notification(req: mcp_types.ProgressNotification) -> None:
        await remote_app.send_progress_notification(
            req.params.progressToken,
            req.params.progress,
            req.params.total,
        )

    app.notification_handlers[mcp_types.ProgressNotification] = _send_progress_notification

    async def _complete(req: mcp_types.CompleteRequest) -> mcp_types.ServerResult:
        result = await remote_app.complete(
            req.params.ref,
            req.params.argument.model_dump(),
        )
        return mcp_types.ServerResult(result)

    return app


async def _run(
    url: str,
    headers: Dict[str, str],
    *,
    insecure: bool,
    ssl_cert_file: str | None,
    timeout: int | float,
) -> None:
    remote = StatelessStreamableHTTPClient(
        url=url,
        headers=headers,
        insecure=insecure,
        ssl_cert_file=ssl_cert_file,
        timeout=timeout,
    )
    app = await _create_proxy_server(remote)
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "StreamableHTTP MCP proxy: stdio in, HTTP out. Stateless by clearing mcp-session-id."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument(
        "url",
        help=(
            "Target MCP StreamableHTTP endpoint. Example: https://example.com/mcp"
        ),
    )
    p.add_argument(
        "-H",
        "--headers",
        nargs=2,
        action="append",
        metavar=("KEY", "VALUE"),
        help="Extra request headers (can repeat). mcp-session-id is always stripped.",
        default=[],
    )
    p.add_argument(
        "--insecure",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Disable TLS certificate verification when connecting to the remote server.",
    )
    p.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("MCP_PROXY_TIMEOUT", "120")),
        help="Per-request overall timeout in seconds (default 120).",
    )
    p.add_argument(
        "--ssl-cert-file",
        dest="ssl_cert_file",
        type=str,
        default=os.getenv("SSL_CERT_FILE"),
        help=(
            "CA bundle path used only for the remote MCP HTTPS connection.\n"
            "If omitted, uses system/default trust. Falls back to env SSL_CERT_FILE if set."
        ),
    )
    p.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity. Default INFO.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level))
    headers = _parse_headers(args.headers)

    # Run the stdio<->HTTP proxy
    try:
        asyncio.run(
            _run(
                args.url,
                headers,
                insecure=args.insecure,
                ssl_cert_file=args.ssl_cert_file,
                timeout=args.timeout,
            ),
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
