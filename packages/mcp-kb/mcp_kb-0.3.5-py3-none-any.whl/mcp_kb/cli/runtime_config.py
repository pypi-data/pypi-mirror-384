"""Runtime configuration helpers for CLI defaults and persistence.

The MCP knowledge base CLI needs to juggle three independent sources of
configuration: command-line arguments, environment variables, and the last set
of options emitted by a previous run. Centralising that precedence logic in a
dedicated module keeps the main CLI entry points focused on orchestration while
making it simple to unit test the resolution rules.

The module exposes three primitives:

``load_runtime_configuration``
    Reads the serialized configuration dictionary stored in the knowledge base
    data directory (``.data`` by default). Missing or invalid files are treated
    as empty configuration snapshots.

``apply_cli_runtime_configuration``
    Normalises an ``argparse.Namespace`` to ensure every CLI option has a
    concrete value after considering CLI flags, environment variables, and the
    persisted snapshot. The function also returns the resolved mapping so that
    callers can persist exactly what was used during the current run.

``persist_runtime_configuration``
    Writes the resolved mapping back to the data directory so that subsequent
    runs inherit the same defaults unless explicitly overridden.

All helper functions include extensive docstrings so that readers understand
their role in the configuration pipeline without diving into the implementation
details.
"""

from __future__ import annotations

import json
import logging
import os
from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, MutableMapping, Sequence

from mcp_kb.cli.args import parse_bool
from mcp_kb.config import DATA_FOLDER_NAME


logger = logging.getLogger(__name__)


CONFIG_FILENAME = "cli-config.json"
"""str: File name used to persist resolved CLI defaults within ``.data``."""


def _configuration_path(root: Path) -> Path:
    """Return the absolute path to the persisted CLI configuration file.

    Parameters
    ----------
    root:
        Knowledge base root directory that owns the ``.data`` folder where
        configuration metadata is stored.
    """

    return root / DATA_FOLDER_NAME / CONFIG_FILENAME


def load_runtime_configuration(root: Path) -> dict[str, Any]:
    """Load the previously persisted CLI configuration snapshot.

    The function returns an empty dictionary when no configuration file exists
    or when the file cannot be decoded as JSON. Invalid files are logged at the
    DEBUG level so that operators can inspect issues while keeping the CLI
    output quiet by default.
    """

    config_path = _configuration_path(root)
    if not config_path.exists():
        return {}

    try:
        contents = config_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - filesystem edge cases
        logger.debug("Failed to read CLI configuration at %s: %s", config_path, exc)
        return {}

    try:
        payload = json.loads(contents)
    except json.JSONDecodeError as exc:
        logger.debug("Invalid CLI configuration JSON at %s: %s", config_path, exc)
        return {}

    if not isinstance(payload, dict):
        logger.debug(
            "Ignoring CLI configuration at %s because the payload is not a mapping",
            config_path,
        )
        return {}

    return payload


def persist_runtime_configuration(root: Path, configuration: Mapping[str, Any]) -> Path:
    """Persist ``configuration`` into the knowledge base data directory.

    Parameters
    ----------
    root:
        Knowledge base root directory that owns the ``.data`` folder.
    configuration:
        Final configuration mapping produced by
        :func:`apply_cli_runtime_configuration`.

    Returns
    -------
    Path
        The absolute path to the written configuration file.
    """

    config_path = _configuration_path(root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    # Sorting keys makes the file diff-friendly and easier to inspect manually.
    serialized = json.dumps(configuration, indent=2, sort_keys=True)
    config_path.write_text(serialized + "\n", encoding="utf-8")
    return config_path


def _identity(value: Any) -> Any:
    """Return ``value`` unchanged.

    The helper keeps ``OptionSpec`` declarations concise; it is intentionally
    defined at module scope so it can be referenced multiple times without
    allocating additional callables.
    """

    return value


def _normalize_optional_int(value: Any) -> int | None:
    """Convert ``value`` into an optional integer.

    ``None`` and empty strings remain ``None``. Numeric strings are coerced using
    :class:`int`, and floats are truncated. Any other type raises ``TypeError`` so
    that misconfigured persisted values become obvious during testing.
    """

    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return int(value)
    raise TypeError(f"Expected optional int-compatible value, received {type(value)!r}")


def _normalize_lower_str(value: Any) -> str | None:
    """Normalize ``value`` to a lowercase string when possible."""

    if value is None:
        return None
    if isinstance(value, str):
        return value.lower()
    return str(value).lower()


def _normalize_transports(value: Any) -> list[str] | None:
    """Ensure transport selections are serializable lists of strings."""

    if value is None:
        return None
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    raise TypeError(f"Unsupported transports value: {value!r}")


def _normalize_bool(value: Any) -> bool:
    """Convert ``value`` into a boolean using :func:`parse_bool` semantics."""

    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return parse_bool(value)
    return bool(value)


def _parse_optional_int(value: str) -> int | None:
    """Parse ``value`` from the environment into an optional integer."""

    stripped = value.strip()
    if not stripped:
        return None
    return int(stripped)


@dataclass(frozen=True)
class OptionSpec:
    """Specification describing how to resolve a single CLI option.

    Attributes
    ----------
    name:
        Attribute name on the :class:`argparse.Namespace` produced by the CLI
        parser.
    env_var:
        Optional environment variable that should be considered when the CLI
        did not provide a value. ``None`` skips environment lookup.
    default:
        Fallback value used when neither CLI flags, environment variables, nor
        persisted configuration provide a value. This can be a raw value or a
        zero-argument callable that produces the value on demand.
    env_parser:
        Optional callable that converts the raw environment string into the
        expected type before normalisation.
    normalizer:
        Callable that converts the CLI/environment/persisted value into the
        final, type-stable representation.
    """

    name: str
    env_var: str | None = None
    default: Any | Callable[[], Any] = None
    env_parser: Callable[[str], Any] | None = None
    normalizer: Callable[[Any], Any] = field(default=_identity)


def _evaluate_default(default: Any | Callable[[], Any]) -> Any:
    """Return the default value, invoking callables when necessary."""

    if callable(default):  # ``bool`` defaults are handled by ``normalizer``
        return default()
    return default


OPTION_SPECS: Sequence[OptionSpec] = (
    OptionSpec("host", default=None),
    OptionSpec("port", default=None, normalizer=_normalize_optional_int),
    OptionSpec("transports", default=None, normalizer=_normalize_transports),
    OptionSpec("ui_port", default=None, normalizer=_normalize_optional_int),
    OptionSpec(
        "chroma_client",
        env_var="MCP_KB_CHROMA_CLIENT",
        default="persistent",
        env_parser=lambda value: value.lower(),
        normalizer=_normalize_lower_str,
    ),
    OptionSpec(
        "chroma_collection",
        env_var="MCP_KB_CHROMA_COLLECTION",
        default="knowledge-base",
    ),
    OptionSpec(
        "chroma_embedding",
        env_var="MCP_KB_CHROMA_EMBEDDING",
        default="default",
    ),
    OptionSpec(
        "chroma_data_dir",
        env_var="MCP_KB_CHROMA_DATA_DIR",
        default=None,
    ),
    OptionSpec(
        "chroma_host",
        env_var="MCP_KB_CHROMA_HOST",
        default=None,
    ),
    OptionSpec(
        "chroma_port",
        env_var="MCP_KB_CHROMA_PORT",
        default=None,
        env_parser=_parse_optional_int,
        normalizer=_normalize_optional_int,
    ),
    OptionSpec(
        "chroma_ssl",
        env_var="MCP_KB_CHROMA_SSL",
        default=True,
        env_parser=parse_bool,
        normalizer=_normalize_bool,
    ),
    OptionSpec(
        "chroma_tenant",
        env_var="MCP_KB_CHROMA_TENANT",
        default=None,
    ),
    OptionSpec(
        "chroma_database",
        env_var="MCP_KB_CHROMA_DATABASE",
        default=None,
    ),
    OptionSpec(
        "chroma_api_key",
        env_var="MCP_KB_CHROMA_API_KEY",
        default=None,
    ),
    OptionSpec(
        "chroma_custom_auth",
        env_var="MCP_KB_CHROMA_CUSTOM_AUTH",
        default=None,
    ),
    OptionSpec(
        "chroma_id_prefix",
        env_var="MCP_KB_CHROMA_ID_PREFIX",
        default=None,
    ),
    OptionSpec(
        "chroma_sentence_transformer",
        env_var="MCP_KB_CHROMA_SENTENCE_TRANSFORMER",
        default=None,
    ),
    OptionSpec(
        "chroma_chunk_size",
        env_var="MCP_KB_CHROMA_CHUNK_SIZE",
        default=200,
    ),
    OptionSpec(
        "chroma_chunk_overlap",
        env_var="MCP_KB_CHROMA_CHUNK_OVERLAP",
        default=20,
    ),
)


def _resolve_option_value(
    namespace: Namespace,
    spec: OptionSpec,
    persisted: Mapping[str, Any],
    environ: Mapping[str, str],
) -> Any:
    """Resolve a single option using CLI, env, and persisted configuration."""

    if hasattr(namespace, spec.name):
        raw = getattr(namespace, spec.name)
        value = spec.normalizer(raw)
        setattr(namespace, spec.name, value)
        return value

    if spec.env_var:
        env_raw = environ.get(spec.env_var)
        if env_raw is not None:
            parsed = spec.env_parser(env_raw) if spec.env_parser else env_raw
            value = spec.normalizer(parsed)
            setattr(namespace, spec.name, value)
            return value

    if spec.name in persisted:
        stored = spec.normalizer(persisted[spec.name])
        setattr(namespace, spec.name, stored)
        return stored

    fallback = spec.normalizer(_evaluate_default(spec.default))
    setattr(namespace, spec.name, fallback)
    return fallback


def _resolve_no_ui(
    namespace: Namespace,
    persisted: Mapping[str, Any],
    environ: Mapping[str, str],
) -> bool:
    """Resolve the ``--no-ui`` flag with persisted fallback semantics."""

    if getattr(namespace, "no_ui", False):
        return True

    env_value = environ.get("MCP_KB_NO_UI")
    if env_value is not None:
        return parse_bool(env_value)

    stored = persisted.get("no_ui")
    if stored is None:
        return False
    if isinstance(stored, bool):
        return stored
    if isinstance(stored, str):
        return parse_bool(stored)
    return bool(stored)


def apply_cli_runtime_configuration(
    namespace: Namespace,
    *,
    root: Path,
    persisted: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Populate ``namespace`` with resolved CLI options and return the mapping.

    Parameters
    ----------
    namespace:
        Parsed CLI arguments as produced by a shared :mod:`argparse` parser.
    root:
        Knowledge base root path. The value is not used directly during
        resolution but is included to make the signature self-documenting and
        accommodate future enhancements that may require the path.
    persisted:
        Previously persisted configuration mapping. ``None`` is treated as an
        empty mapping.
    environ:
        Mapping interface used to look up environment variables. Defaults to
        :data:`os.environ` for production usage and can be overridden by tests
        to exercise precedence rules deterministically.
    """

    del root  # currently unused but retained for signature symmetry
    persisted = dict(persisted or {})
    environ = environ or os.environ

    resolved: MutableMapping[str, Any] = {}
    for spec in OPTION_SPECS:
        resolved_value = _resolve_option_value(namespace, spec, persisted, environ)
        resolved[spec.name] = resolved_value

    no_ui_value = _resolve_no_ui(namespace, persisted, environ)
    namespace.no_ui = no_ui_value
    resolved["no_ui"] = no_ui_value

    return dict(resolved)
