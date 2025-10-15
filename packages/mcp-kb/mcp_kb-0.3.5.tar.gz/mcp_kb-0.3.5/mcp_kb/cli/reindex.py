"""CLI command to reindex the knowledge base into configured ingestors.

This command does not expose an MCP tool. Instead, it builds the configured
ingestors and calls their ``reindex`` method when available, allowing operators
to trigger a full rebuild of external indexes (e.g., Chroma) from the current
filesystem state.
"""

from __future__ import annotations

import argparse
import logging
from typing import Iterable, List

from mcp_kb.cli.args import add_chroma_arguments, build_chroma_listener
from mcp_kb.cli.runtime_config import (
    apply_cli_runtime_configuration,
    load_runtime_configuration,
    persist_runtime_configuration,
)
from mcp_kb.config import DATA_FOLDER_NAME, resolve_knowledge_base_root
from mcp_kb.knowledge.events import KnowledgeBaseReindexListener
from mcp_kb.knowledge.store import KnowledgeBase
from mcp_kb.security.path_validation import PathRules


logger = logging.getLogger(__name__)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the reindex command."""

    parser = argparse.ArgumentParser(
        description="Reindex the knowledge base into configured backends",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--root",
        dest="root",
        default=argparse.SUPPRESS,
        help="Optional path to the knowledge base root (defaults to environment configuration)",
    )
    add_chroma_arguments(parser)
    return parser


def run_reindex(arguments: Iterable[str] | None = None) -> int:
    """Execute a reindex run across all registered ingestors.

    The function constructs a :class:`~mcp_kb.knowledge.store.KnowledgeBase`
    using the same root resolution logic as the server, builds any enabled
    ingestion listeners from CLI options, and invokes ``reindex`` on those that
    implement the optional protocol. Configuration precedence mirrors the main
    server: command-line arguments override environment variables, which in
    turn override the last persisted configuration snapshot. The resolved
    mapping is written back to disk so the next invocation inherits the same
    defaults.

    Parameters
    ----------
    arguments:
        Optional iterable of command-line arguments, primarily used by tests.

    Returns
    -------
    int
        The total number of documents processed across all reindex-capable
        listeners.
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
    kb = KnowledgeBase(rules)

    listeners: List[KnowledgeBaseReindexListener] = []
    try:
        chroma = build_chroma_listener(options, root_path)
    except Exception as exc:  # pragma: no cover - configuration errors
        logger.exception(exc)
        raise SystemExit(f"Failed to configure Chroma ingestion: {exc}") from exc
    if chroma is not None and isinstance(chroma, KnowledgeBaseReindexListener):
        listeners.append(chroma)

    total = 0
    for listener in listeners:
        logger.info("Reindexing via %s", listener.__class__.__name__)
        count = listener.reindex(kb)
        logger.info("Reindexed %d documents via %s", count, listener.__class__.__name__)
        total += count

    persist_runtime_configuration(root_path, resolved_config)

    return total


def main() -> None:
    """CLI hook that executes :func:`run_reindex` and prints a summary."""

    total = run_reindex()
    print(f"Reindexed {total} documents")


if __name__ == "__main__":
    main()
