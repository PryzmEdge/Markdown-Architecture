"""
ingester.py — Markdown artifact reader

Reads a Markdown file, parses YAML frontmatter, and returns a structured dict.
Used by the DBOS workflow as the first pipeline step.
"""

import hashlib
from pathlib import Path
from typing import Any

import yaml


class IngesterError(Exception):
    pass


def ingest(artifact_path: str) -> dict[str, Any]:
    """
    Read a Markdown artifact and return:
    {
      "path":        str,
      "hash_sha256": str,
      "frontmatter": dict,
      "body":        str,
    }
    Raises IngesterError if the file is missing or frontmatter is malformed.
    """
    path = Path(artifact_path)
    if not path.exists():
        raise IngesterError(f"Artifact not found: {artifact_path}")

    raw = path.read_text(encoding="utf-8")
    file_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    frontmatter, body = _parse_frontmatter(raw, artifact_path)

    return {
        "path":        artifact_path,
        "hash_sha256": file_hash,
        "frontmatter": frontmatter,
        "body":        body,
    }


def _parse_frontmatter(content: str, path: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise IngesterError(f"Malformed frontmatter in {path}: no closing '---'")

    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        raise IngesterError(f"YAML parse error in {path}: {e}")

    return fm, parts[2].strip()


def assert_approved(artifact: dict) -> None:
    """
    Raise IngesterError if the artifact is not operator-approved.
    Mirrors gate_00 logic from stage-contract.py.
    """
    fm = artifact["frontmatter"]
    if fm.get("operator_approved") is not True:
        raise IngesterError(
            f"{artifact['path']}: operator_approved is not true — gate blocked"
        )
    if fm.get("status") != "approved":
        raise IngesterError(
            f"{artifact['path']}: status is '{fm.get('status')}', expected 'approved'"
        )
