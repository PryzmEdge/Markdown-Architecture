"""
StageContract validator.
Usage: python _config/stage-contract.py --stage <stage-name>
Exits 0 on pass, 1 on failure.
"""
import argparse
import sys
import os
import yaml
from pathlib import Path

REQUIRED_FRONTMATTER = ["status", "operator_approved", "risk_check_passed", "stage"]

STAGE_OUTPUT_REQUIREMENTS = {
    "00-intake": ["output/problem.md"],
    "01-research": ["output/brief.md", "output/sources.md", "output/contradictions.md"],
    "02-analysis": ["output/synthesis.md", "output/risk.md"],
    "03-output": [],  # dynamic slug — checked separately
}

def load_frontmatter(filepath: Path) -> dict:
    text = filepath.read_text()
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}

def validate_stage(stage: str) -> list:
    errors = []
    base = Path(f"stages/{stage}")

    if not base.exists():
        return [f"Stage directory not found: {base}"]

    # Check CONTEXT.md frontmatter
    context_path = base / "CONTEXT.md"
    if not context_path.exists():
        errors.append(f"Missing CONTEXT.md in {base}")
    else:
        fm = load_frontmatter(context_path)
        for field in REQUIRED_FRONTMATTER:
            if field not in fm:
                errors.append(f"CONTEXT.md missing frontmatter field: {field}")

    # Check required output files exist
    for rel_path in STAGE_OUTPUT_REQUIREMENTS.get(stage, []):
        output_file = base / rel_path
        if not output_file.exists():
            errors.append(f"Missing required output: {output_file}")
        else:
            fm = load_frontmatter(output_file)
            for field in REQUIRED_FRONTMATTER:
                if field not in fm:
                    errors.append(f"{output_file} missing frontmatter field: {field}")

    # Check operator_approved on output files
    output_dir = base / "output"
    if output_dir.exists():
        for md_file in output_dir.glob("*.md"):
            fm = load_frontmatter(md_file)
            if fm.get("operator_approved") is not True:
                errors.append(f"{md_file}: operator_approved is not true")

    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    args = parser.parse_args()

    errors = validate_stage(args.stage)

    if errors:
        print(f"FAIL — {len(errors)} error(s) in stage '{args.stage}':")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print(f"PASS — stage '{args.stage}' contract valid.")
        sys.exit(0)

if __name__ == "__main__":
    main()
