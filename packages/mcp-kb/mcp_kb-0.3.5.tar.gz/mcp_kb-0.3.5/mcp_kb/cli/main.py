"""Command line interface for running the MCP knowledge base server."""

from __future__ import annotations

import argparse
import asyncio
import logging
from typing import Iterable, List

from mcp_kb.config import DATA_FOLDER_NAME, resolve_knowledge_base_root
from mcp_kb.cli.args import add_chroma_arguments, build_chroma_listener
from mcp_kb.cli.runtime_config import (
    apply_cli_runtime_configuration,
    load_runtime_configuration,
    persist_runtime_configuration,
)
try:
    from mcp_kb.ingest.chroma import ChromaIngestor
    W_CHROMA = True
except ImportError:
    if TYPE_CHECKING:
        ChromaIngestor = None
    W_CHROMA = False
from mcp_kb.knowledge.bootstrap import install_default_documentation
from mcp_kb.security.path_validation import PathRules
from mcp_kb.server.app import create_fastmcp_app
from mcp.server.fastmcp import FastMCP
from mcp_kb.ui import start_ui_server

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser used by ``main``."""

    parser = argparse.ArgumentParser(
        description="Run the MCP knowledge base server", allow_abbrev=False
    )
    parser.add_argument(
        "--root",
        dest="root",
        default=argparse.SUPPRESS,
        help="Optional path to the knowledge base root (defaults to environment configuration)",
    )
    parser.add_argument(
        "--transport",
        dest="transports",
        action="append",
        choices=["stdio", "sse", "http"],
        default=argparse.SUPPRESS,
        help="Transport protocol to enable (repeatable). Defaults to stdio only.",
    )
    parser.add_argument(
        "--host",
        dest="host",
        default=argparse.SUPPRESS,
        help="Host interface for HTTP/SSE transports (default 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        dest="port",
        type=int,
        default=argparse.SUPPRESS,
        help="Port for HTTP/SSE transports (default 8000).",
    )
    parser.add_argument(
        "--ui-port",
        dest="ui_port",
        type=int,
        default=argparse.SUPPRESS,
        help=(
            "Starting port for the human UI (default 8765). If occupied, the UI "
            "server increments the port by 1 until a free one is found."
        ),
    )
    parser.add_argument(
        "--no-ui",
        dest="no_ui",
        action="store_true",
        help=(
            "Disable the human UI entirely, even when HTTP/SSE transports are active."
        ),
    )

    if W_CHROMA:
        add_chroma_arguments(parser)
    return parser


async def _run_transports(server: FastMCP, transports: List[str]) -> None:
    """Run all selected transport protocols concurrently."""

    coroutines = []
    for name in transports:
        if name == "stdio":
            coroutines.append(server.run_stdio_async())
        elif name == "sse":
            coroutines.append(server.run_sse_async())
        elif name == "http":
            coroutines.append(server.run_streamable_http_async())
        else:  # pragma: no cover - argparse restricts values
            raise ValueError(f"Unsupported transport: {name}")

    await asyncio.gather(*coroutines)


def run_server(arguments: Iterable[str] | None = None) -> None:
    """Entry point used by both CLI invocations and unit tests.

    Besides orchestrating the server lifecycle, the function resolves
    configuration values by layering command-line arguments over environment
    variables and any persisted defaults stored in the knowledge base data
    directory. The resolved mapping is written back to disk so that future runs
    inherit the same defaults unless explicitly overridden.
    """

    parser = _build_argument_parser()
    options = parser.parse_args(arguments)
    root_path = resolve_knowledge_base_root(getattr(options, "root", None))

    persisted_config = load_runtime_configuration(root_path)
    resolved_config = apply_cli_runtime_configuration(
        options,
        root=root_path,
        persisted=persisted_config,
    )
    rules = PathRules(root=root_path, protected_folders=(DATA_FOLDER_NAME,))
    install_default_documentation(root_path)
    listeners: List[ChromaIngestor] = []
    try:
        listener = build_chroma_listener(options, root_path)
    except Exception as exc:  # pragma: no cover - configuration errors
        logger.exception(exc)
        raise SystemExit(f"Failed to configure Chroma ingestion: {exc}") from exc
    if listener is not None:
        listeners.append(listener)
        logger.info(
            "Chroma ingestion enabled (client=%s, collection=%s)",
            options.chroma_client,
            options.chroma_collection,
        )
    server = create_fastmcp_app(
        rules,
        host=options.host,
        port=options.port,
        listeners=listeners,
    )
    transports = options.transports or ["stdio"]
    options.transports = transports
    resolved_config["transports"] = transports
    logger.info(
        f"Running server on {options.host}:{options.port} with transports {transports}"
    )
    logger.info(f"Data root is {root_path}")
    
    # Start the human-accessible UI when an HTTP-capable transport is active.
    if not options.no_ui and any(t in ("http", "sse") for t in transports):
        kb = getattr(server, "kb", None)
        if kb is not None:
            ui = start_ui_server(
                kb,
                host=options.host or "127.0.0.1",
                port=options.ui_port,
            )
            logger.info("UI available at http://%s:%d", ui.host, ui.port)

    persist_runtime_configuration(root_path, resolved_config)

    asyncio.run(_run_transports(server, transports))


def main() -> None:
    """CLI hook that executes :func:`run_server`."""

    run_server()


if __name__ == "__main__":
    main()
