#!/usr/bin/env python3
"""
post-edit hook: validate-mcp-response.py

Runs after every agent file edit. Two responsibilities:
  1. Validate that the edited file has well-formed YAML frontmatter (if .md).
  2. Append a minimal PromptExecutionReceipt stub to stages/*/receipts/ for
     Stage 03 artifacts, as a placeholder until the full audit-logger skill
     is wired in.

Usage (called by .claude/settings.json postEdit hook):
  python .claude/hooks/validate-mcp-response.py --path <file_path>

Exit codes:
  0  OK
  1  Frontmatter parse error (warns, does not block)
"""

import sys
import os
import json
import hashlib
import datetime
import argparse

try:
    import yaml
except ImportError:
    # Soft fail: if PyYAML is not installed, skip frontmatter check.
    yaml = None


def parse_frontmatter(content: str) -> dict | None:
    """Extract and parse YAML frontmatter from a Markdown string."""
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1]) if yaml else None
    except Exception:
        return None


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def write_receipt_stub(file_path: str, frontmatter: dict) -> None:
    """Write a minimal receipt stub for Stage 03 output artifacts."""
    stage_dir = "stages/03-output/output/receipts"
    os.makedirs(stage_dir, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    receipt = {
        "receipt_id": f"stub-{ts}",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "hook": "post-edit",
        "edited_file": file_path,
        "file_hash_sha256": sha256_of_file(file_path),
        "frontmatter_snapshot": frontmatter,
        "note": "Stub receipt. Replace with full audit-logger skill output."
    }
    receipt_path = os.path.join(stage_dir, f"{ts}.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
    print(f"[post-edit] Receipt stub written: {receipt_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="Path to the edited file")
    args = parser.parse_args()

    file_path = args.path

    if not os.path.isfile(file_path):
        print(f"[post-edit] File not found: {file_path} (skipping)")
        sys.exit(0)

    # Only process Markdown files
    if not file_path.endswith(".md"):
        sys.exit(0)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Validate frontmatter
    fm = parse_frontmatter(content)
    if fm is None:
        if yaml is not None:
            print(f"[post-edit] WARNING: No valid YAML frontmatter in {file_path}")
        # Warn only; do not block (onError: warn in settings.json)
        sys.exit(0)

    required_fields = ["status", "stage"]
    missing = [k for k in required_fields if k not in fm]
    if missing:
        print(f"[post-edit] WARNING: Missing frontmatter fields in {file_path}: {missing}")
        sys.exit(1)

    print(f"[post-edit] Frontmatter OK: {file_path} (status={fm.get('status')}, stage={fm.get('stage')})")

    # 2. Write receipt stub only for Stage 03 output artifacts
    if "stages/03-output/output/" in file_path and not file_path.startswith("stages/03-output/output/receipts"):
        write_receipt_stub(file_path, fm)

    sys.exit(0)


if __name__ == "__main__":
    main()
