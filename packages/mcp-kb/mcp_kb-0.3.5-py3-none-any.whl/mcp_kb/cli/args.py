"""Shared CLI argument wiring for knowledge base utilities.

This module centralizes the definition of common command-line options and
helpers so that multiple entry points (e.g., server and reindex commands) can
remain small and focused while sharing consistent behavior. The helpers are
careful to avoid embedding environment defaults directly into the argparse
objects so that downstream consumers can layer persisted runtime configuration
in between CLI flags and built-in defaults.
"""

from __future__ import annotations

import argparse
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional

try:
    from mcp_kb.ingest.chroma import SUPPORTED_CLIENTS, ChromaConfiguration, ChromaIngestor
    W_CHROMA = True
except ImportError:
    W_CHROMA = False

def parse_bool(value: str | bool | None) -> bool:
    """Return ``True`` when ``value`` represents an affirmative boolean string.

    The function accepts case-insensitive variants such as "true", "t",
    "yes", and "1". ``None`` yields ``False``.
    """

    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return value.lower() in {"1", "true", "t", "yes", "y"}


def add_chroma_arguments(parser: ArgumentParser) -> None:
    """Register Chroma ingestion arguments on ``parser``.

    The parser intentionally suppresses defaults for all options so that the
    calling code can merge CLI flags, environment variables, and persisted
    runtime configuration explicitly. This keeps precedence handling in a
    single location rather than scattering logic across the argument
    registrations themselves.
    """
    if not W_CHROMA:
        return None

    parser.add_argument(
        "--chroma-client",
        dest="chroma_client",
        choices=SUPPORTED_CLIENTS,
        default=argparse.SUPPRESS,
        help="Client implementation for mirroring data to ChromaDB (default: persistent).",
    )
    parser.add_argument(
        "--chroma-collection",
        dest="chroma_collection",
        default=argparse.SUPPRESS,
        help="Chroma collection name used to store documents.",
    )
    parser.add_argument(
        "--chroma-embedding",
        dest="chroma_embedding",
        default=argparse.SUPPRESS,
        help="Embedding function name registered with chromadb.utils.embedding_functions.",
    )
    parser.add_argument(
        "--chroma-data-dir",
        dest="chroma_data_dir",
        default=argparse.SUPPRESS,
        help="Storage directory for the persistent Chroma client.",
    )
    parser.add_argument(
        "--chroma-host",
        dest="chroma_host",
        default=argparse.SUPPRESS,
        help="Target host for HTTP or cloud Chroma clients.",
    )
    parser.add_argument(
        "--chroma-port",
        dest="chroma_port",
        type=int,
        default=argparse.SUPPRESS,
        help="Port for the HTTP Chroma client.",
    )
    parser.add_argument(
        "--chroma-ssl",
        dest="chroma_ssl",
        type=parse_bool,
        default=argparse.SUPPRESS,
        help="Toggle SSL for the HTTP Chroma client (default: true).",
    )
    parser.add_argument(
        "--chroma-tenant",
        dest="chroma_tenant",
        default=argparse.SUPPRESS,
        help="Tenant identifier for Chroma Cloud deployments.",
    )
    parser.add_argument(
        "--chroma-database",
        dest="chroma_database",
        default=argparse.SUPPRESS,
        help="Database name for Chroma Cloud deployments.",
    )
    parser.add_argument(
        "--chroma-api-key",
        dest="chroma_api_key",
        default=argparse.SUPPRESS,
        help="API key used to authenticate against Chroma Cloud.",
    )
    parser.add_argument(
        "--chroma-custom-auth",
        dest="chroma_custom_auth",
        default=argparse.SUPPRESS,
        help="Optional custom auth credentials for self-hosted HTTP deployments.",
    )
    parser.add_argument(
        "--chroma-id-prefix",
        dest="chroma_id_prefix",
        default=argparse.SUPPRESS,
        help="Prefix applied to document IDs stored in Chroma (default: kb::).",
    )
    parser.add_argument(
        "--chroma-sentence-transformer",
        dest="chroma_sentence_transformer",
        default=argparse.SUPPRESS,
        help="Sentence transformer model name.",
    )
    parser.add_argument(
        "--chroma-chunk-size",
        dest="chroma_chunk_size",
        type=int,
        default=argparse.SUPPRESS,
        help="Chunk size for the sentence transformer model.",
    )
    parser.add_argument(
        "--chroma-chunk-overlap",
        dest="chroma_chunk_overlap",
        type=int,
        default=argparse.SUPPRESS,
        help="Chunk overlap for the sentence transformer model.",
    )


def build_chroma_listener(options: Namespace, root: Path) -> Optional[ChromaIngestor]:
    """Construct a Chroma listener from parsed CLI options when enabled.

    Returns ``None`` when the configured client type is ``off``.
    """
    if not W_CHROMA:
        return None

    configuration = ChromaConfiguration.from_options(
        root=root,
        client_type=options.chroma_client,
        collection_name=options.chroma_collection,
        embedding=options.chroma_embedding,
        data_directory=options.chroma_data_dir,
        host=options.chroma_host,
        port=options.chroma_port,
        ssl=options.chroma_ssl,
        tenant=options.chroma_tenant,
        database=options.chroma_database,
        api_key=options.chroma_api_key,
        custom_auth_credentials=options.chroma_custom_auth,
        id_prefix=options.chroma_id_prefix,
        sentence_transformer=options.chroma_sentence_transformer,
        chunk_size=options.chroma_chunk_size,
        chunk_overlap=options.chroma_chunk_overlap,
    )
    if not configuration.enabled:
        return None
    return ChromaIngestor(configuration)
