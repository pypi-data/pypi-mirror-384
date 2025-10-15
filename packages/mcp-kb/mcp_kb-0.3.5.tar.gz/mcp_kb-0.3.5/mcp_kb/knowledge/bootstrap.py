"""Bootstrap helpers executed during server startup."""

from __future__ import annotations

import importlib.resources as resources
from pathlib import Path

from mcp_kb.config import DATA_FOLDER_NAME, DOC_FILENAME


def install_default_documentation(root: Path) -> Path:
    """Ensure the default documentation file exists under ``root``.

    The function creates the documentation directory if necessary and copies the
    packaged ``KNOWLEDBASE_DOC.md`` file into place. Existing documentation is
    preserved so that operators can customize the file without losing changes on
    subsequent startups.

    Parameters
    ----------
    root:
        Absolute path representing the knowledge base root directory.

    Returns
    -------
    Path
        Path to the documentation file inside the knowledge base tree.
    """

    docs_dir = root / DATA_FOLDER_NAME
    doc_path = docs_dir / DOC_FILENAME
    if doc_path.exists():
        return doc_path

    docs_dir.mkdir(parents=True, exist_ok=True)

    with (
        resources.files("mcp_kb.data")
        .joinpath("KNOWLEDBASE_DOC.md")
        .open("r", encoding="utf-8") as source
    ):
        doc_path.write_text(source.read(), encoding="utf-8")

    return doc_path
