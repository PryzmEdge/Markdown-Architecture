"""
StageContract validator — v2.3

Usage:
  python _config/stage-contract.py --stage <stage-name>
  python _config/stage-contract.py --stage all
  python _config/stage-contract.py --assess-command "<shell command>"

Exits 0 on pass, 1 on failure.

Gate boolean formulas (canonical):
  gate_00 = problem_md.operator_approved == True
  gate_01 = problem_md.operator_approved AND sources >= 3 AND contract passes
  gate_02 = brief_md.operator_approved AND risk_tier assigned
            AND (risk_tier not in [High, Critical] OR risk_check_passed)
            AND contract passes
  gate_03 = synthesis_md.operator_approved AND risk_md.operator_approved
            AND problem_md.operator_approved AND audit_receipt_written
            AND contract passes
"""

import argparse
import sys
import os
import re
import json
import yaml
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALL_STAGES = ["00-intake", "01-research", "02-analysis", "03-output"]

REQUIRED_FRONTMATTER_BASE = ["status", "operator_approved", "stage", "domain"]

STAGE_OUTPUT_REQUIREMENTS = {
    "00-intake":   ["output/problem.md"],
    "01-research": ["output/brief.md", "output/sources.md", "output/contradictions.md"],
    "02-analysis": ["output/synthesis.md", "output/risk.md"],
    "03-output":   [],  # dynamic slug checked separately
}

STAGE_EXTRA_CHECKS = {
    "01-research": ["sources_count"],
}

# Risk tiers that require risk_check_passed: true
HIGH_RISK_TIERS = {"High", "High/Critical", "Critical"}

# Shell command patterns that require elevated risk review
BLOCKED_COMMAND_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"DROP\s+DATABASE",
    r"DELETE\s+FROM",
    r"git\s+push\s+--force",
    r"chmod\s+777",
    r"curl.*\|\s*bash",
    r"wget.*\|\s*sh",
    r"truncate\s+table",
    r"ALTER\s+TABLE.*DROP",
]

WARN_COMMAND_PATTERNS = [
    r"git\s+push",
    r"make\s+clean",
    r"psql.*-c",
    r"python.*delete",
    r"DROP\s+TABLE",
]

# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

def load_frontmatter(filepath: Path) -> dict:
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}

def validate_artifact(path: Path) -> list[str]:
    """Validate a SINGLE artifact file against the base frontmatter contract.

    Mirrors validate_stage's per-file semantics (REQUIRED_FRONTMATTER_BASE +
    operator_approved is True + the conditional risk gate). It does NOT run
    stage-level cross-checks (sources_count, required-output sets) — those need
    a stage directory. Reuses load_frontmatter so behaviour matches --stage.
    """
    if not path.exists():
        return [f"artifact not found: {path}"]

    fm = load_frontmatter(path)
    if not fm:
        # load_frontmatter is lenient (returns {} on missing / invalid YAML);
        # layer a clearer message on top rather than four "missing field" lines.
        text = path.read_text(encoding="utf-8")
        if not text.lstrip().startswith("---"):
            return [f"{path}: missing YAML frontmatter (file must open with '---')"]
        return [f"{path}: frontmatter is empty or not valid YAML"]

    errors: list[str] = []
    for field in REQUIRED_FRONTMATTER_BASE:
        if field not in fm:
            errors.append(f"missing required field: {field}")
    if fm.get("operator_approved") is not True:
        errors.append(
            f"operator_approved must be the boolean true "
            f"(got {fm.get('operator_approved')!r})"
        )
    if fm.get("risk_tier") in HIGH_RISK_TIERS and fm.get("risk_check_passed") is not True:
        errors.append(
            f"risk_tier is {fm.get('risk_tier')!r} but risk_check_passed is not true"
        )
    return errors

def count_sources_in_table(filepath: Path) -> int:
    """Count data rows in a Markdown table in sources.md (excludes header + separator)."""
    text = filepath.read_text(encoding="utf-8")
    rows = [l for l in text.splitlines() if l.strip().startswith("|")]
    # Subtract header row and separator row
    return max(0, len(rows) - 2)

# ---------------------------------------------------------------------------
# Stage validation
# ---------------------------------------------------------------------------

def validate_stage(stage: str) -> list[str]:
    errors = []
    base = Path(f"stages/{stage}")

    if not base.exists():
        return [f"Stage directory not found: {base}"]

    # CONTEXT.md must exist and have base frontmatter
    context_path = base / "CONTEXT.md"
    if not context_path.exists():
        errors.append(f"Missing CONTEXT.md in {base}")
    else:
        fm = load_frontmatter(context_path)
        for field in REQUIRED_FRONTMATTER_BASE:
            if field not in fm:
                errors.append(f"CONTEXT.md missing frontmatter field: {field}")

    # Required output files exist and have base frontmatter
    for rel_path in STAGE_OUTPUT_REQUIREMENTS.get(stage, []):
        output_file = base / rel_path
        if not output_file.exists():
            errors.append(f"Missing required output: {output_file}")
        else:
            fm = load_frontmatter(output_file)
            for field in REQUIRED_FRONTMATTER_BASE:
                if field not in fm:
                    errors.append(f"{output_file} missing frontmatter field: {field}")

    # operator_approved must be true on all output files
    output_dir = base / "output"
    if output_dir.exists():
        for md_file in output_dir.glob("*.md"):
            fm = load_frontmatter(md_file)
            if fm.get("operator_approved") is not True:
                errors.append(f"{md_file}: operator_approved is not true")

    # Stage-specific extra checks
    if stage == "01-research":
        sources_path = base / "output/sources.md"
        if sources_path.exists():
            count = count_sources_in_table(sources_path)
            if count < 3:
                errors.append(
                    f"sources.md has {count} source row(s); gate_01 requires >= 3"
                )
            fm = load_frontmatter(sources_path)
            declared = fm.get("sources_count")
            if declared is None:
                errors.append(
                    "sources.md: frontmatter sources_count is missing (required for gate_01 cross-check)"
                )
            elif declared != count:
                errors.append(
                    f"sources.md: frontmatter sources_count={declared} "
                    f"does not match table row count={count}"
                )

    if stage == "02-analysis":
        risk_path = base / "output/risk.md"
        if risk_path.exists():
            fm = load_frontmatter(risk_path)
            risk_tier = fm.get("risk_tier")
            if not risk_tier:
                errors.append("risk.md: risk_tier is not set (gate_02 requires a non-empty value)")
            elif risk_tier in HIGH_RISK_TIERS:
                if fm.get("risk_check_passed") is not True:
                    errors.append(
                        f"risk.md: risk_tier is '{risk_tier}' but risk_check_passed is not true"
                    )

    if stage == "03-output":
        # Audit receipt must exist
        receipts_dir = base / "output/receipts"
        receipts = list(receipts_dir.glob("*.json")) if receipts_dir.exists() else []
        if not receipts:
            errors.append(
                "03-output: no audit receipt found in output/receipts/ (gate_03 requires audit_receipt_written)"
            )
        # At least one slug .md file must exist
        slugs = [
            f for f in (base / "output").glob("*.md")
            if f.name != "ATTENTION.md"
        ] if (base / "output").exists() else []
        if not slugs:
            errors.append("03-output: no final deliverable <slug>.md found in output/")

    return errors

# ---------------------------------------------------------------------------
# Command risk assessment
# ---------------------------------------------------------------------------

RISK_RESULT_BLOCKED = "BLOCKED"
RISK_RESULT_WARN    = "WARN"
RISK_RESULT_OK      = "OK"

def assess_command(command_line: str) -> tuple[str, str]:
    """
    Returns (risk_level, message).
    risk_level: BLOCKED | WARN | OK
    """
    for pattern in BLOCKED_COMMAND_PATTERNS:
        if re.search(pattern, command_line, re.IGNORECASE):
            return (
                RISK_RESULT_BLOCKED,
                f"Command matches blocked pattern '{pattern}'. "
                "Operator sign-off required before execution."
            )
    for pattern in WARN_COMMAND_PATTERNS:
        if re.search(pattern, command_line, re.IGNORECASE):
            return (
                RISK_RESULT_WARN,
                f"Command matches elevated-risk pattern '{pattern}'. "
                "Review before executing."
            )
    return (RISK_RESULT_OK, "Command cleared.")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Markdown Architecture stage contract validator v2.3"
    )
    parser.add_argument(
        "--stage",
        help="Stage name (e.g. 01-research) or 'all' to validate every stage."
    )
    parser.add_argument(
        "--assess-command",
        metavar="CMD",
        help="Assess risk level of a shell command string."
    )
    parser.add_argument(
        "artifact",
        nargs="?",
        help="Path to a single .md artifact to validate (alternative to --stage)."
    )
    args = parser.parse_args()

    # --assess-command mode
    if args.assess_command:
        level, msg = assess_command(args.assess_command)
        if level == RISK_RESULT_BLOCKED:
            print(f"BLOCKED — {msg}")
            sys.exit(1)
        elif level == RISK_RESULT_WARN:
            print(f"WARN — {msg}")
            sys.exit(0)  # warn only; does not block
        else:
            print(f"OK — {msg}")
            sys.exit(0)

    # single-artifact mode — a bare path, no --stage
    if args.artifact and not args.stage:
        errors = validate_artifact(Path(args.artifact))
        if errors:
            print(f"FAIL — {len(errors)} error(s) in {args.artifact}:")
            for e in errors:
                print(f"  ✗ {e}")
            sys.exit(1)
        print(f"PASS — {args.artifact} satisfies the artifact contract.")
        sys.exit(0)

    # --stage mode
    if not args.stage:
        parser.print_help()
        sys.exit(1)

    stages_to_check = ALL_STAGES if args.stage == "all" else [args.stage]
    total_errors = []

    for s in stages_to_check:
        errs = validate_stage(s)
        if errs:
            print(f"FAIL — stage '{s}' ({len(errs)} error(s)):")
            for e in errs:
                print(f"  ✗ {e}")
            total_errors.extend(errs)
        else:
            print(f"PASS — stage '{s}' contract valid.")

    if total_errors:
        print(f"\n{len(total_errors)} total error(s). Promotion blocked.")
        sys.exit(1)
    else:
        if len(stages_to_check) > 1:
            print("\nAll stages valid.")
        sys.exit(0)

if __name__ == "__main__":
    main()
