"""
harness.py — Experiment 03: Model-swap insensitivity

Hypothesis (from docs/thesis-experiments.md):
    End-to-end pipeline reliability is dominated by gate quality, not by
    which LLM occupies the reasoning slot. Holding gates fixed and swapping
    the model should yield flat metrics; holding the model fixed and varying
    gate strictness should yield sharply different metrics.

Method:
    Run a Stage 02 synthesis agent N times per cell across the grid:

        Axis A: model       ∈ {haiku-4-5, sonnet-4-6, opus-4-8}
        Axis B: gate strict ∈ {permissive, normal, strict}

    For each output synthesis.md, compute three metrics:
      - gate_passed: does the gate validator accept the artifact?
      - contradiction_detected: does the synthesis surface the salted
        Yamashita 2025 counter-evidence by name?
      - operator_override_implied: did the model assign a risk_tier that
        would require operator sign-off (High/Critical)?

    Tabulate per-cell rates and report the two correlation analyses:
      - Axis A: does metric vary with model size?
      - Axis B: does metric vary with gate strictness?

Falsification: if Axis A produces a steeper gradient than Axis B, the
thesis ("orchestration dominates model capability") is weaker than claimed.

Container note: this container has no $ANTHROPIC_API_KEY. The harness ships
working mock-mode results to validate plumbing. Real-LLM cells require the
user to run on a machine with the key set.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
RESULTS_DIR = Path(__file__).parent / "results"

DEFAULT_MODELS = ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-8"]
DEFAULT_GATES = ["permissive", "normal", "strict"]

SALTED_PROBE_AUTHOR = "Yamashita"


# ---------------------------------------------------------------------------
# Gate validators (three strictness levels)
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> dict | None:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None


def gate_permissive(synthesis_text: str) -> dict:
    """Accepts almost anything that parses as YAML+markdown."""
    fm = parse_frontmatter(synthesis_text)
    return {"passed": fm is not None, "reason": "permissive: frontmatter parsable"
            if fm is not None else "permissive: frontmatter unparseable"}


def gate_normal(synthesis_text: str) -> dict:
    """Standard gate: matches what _config/stage-contract.py would enforce."""
    fm = parse_frontmatter(synthesis_text)
    if fm is None:
        return {"passed": False, "reason": "no frontmatter"}
    required = {"status", "stage", "operator_approved", "risk_check_passed", "risk_tier"}
    missing = required - set(fm.keys())
    if missing:
        return {"passed": False, "reason": f"missing: {sorted(missing)}"}
    if fm.get("stage") != "02-analysis":
        return {"passed": False, "reason": f"wrong stage: {fm.get('stage')}"}
    if fm.get("risk_tier") not in {"Low", "Medium", "High", "Critical"}:
        return {"passed": False, "reason": f"bad risk_tier: {fm.get('risk_tier')}"}
    return {"passed": True, "reason": "normal: frontmatter complete"}


def gate_strict(synthesis_text: str) -> dict:
    """Strict: normal + body must include all 5 required sections + non-trivial counter-arg."""
    # TODO(exp-03): doc spec says "strict" Axis-B = ≥5 sources. NOT implemented:
    # gate_strict does no source count; the real stage-contract.py enforces ≥3.
    # Run real models at the current gates first, inspect gate-pass / contradiction
    # rates, THEN decide if ≥5 is scientifically load-bearing or just theater.
    r = gate_normal(synthesis_text)
    if not r["passed"]:
        return r
    required_sections = [
        "## Core claim",
        "## Evidence map",
        "## Integrated findings",
        "## Counter-argument",
        "## Recommendations",
    ]
    missing = [s for s in required_sections if s not in synthesis_text]
    if missing:
        return {"passed": False, "reason": f"missing sections: {missing}"}
    # Counter-argument must be non-trivial (>= 80 chars after the heading)
    m = re.search(r"## Counter-argument\n(.*?)(?=\n## |\Z)", synthesis_text, re.DOTALL)
    if not m or len(m.group(1).strip()) < 80:
        return {"passed": False, "reason": "counter-argument too short or empty"}
    return {"passed": True, "reason": "strict: all sections present, counter-arg substantial"}


GATES = {"permissive": gate_permissive, "normal": gate_normal, "strict": gate_strict}


# ---------------------------------------------------------------------------
# Per-output metrics
# ---------------------------------------------------------------------------

def detect_salted_contradiction(synthesis_text: str) -> bool:
    """True iff the synthesis names Yamashita (the salted counter-evidence author)."""
    return SALTED_PROBE_AUTHOR.lower() in synthesis_text.lower()


def operator_override_implied(synthesis_text: str) -> bool:
    """True iff the assigned risk_tier is High or Critical."""
    fm = parse_frontmatter(synthesis_text) or {}
    return fm.get("risk_tier") in {"High", "Critical"}


# ---------------------------------------------------------------------------
# Cell runner
# ---------------------------------------------------------------------------

def run_one(model: str, mock_behavior: str | None, out_path: Path) -> dict:
    cmd = [
        sys.executable, str(Path(__file__).parent / "synthesize.py"),
        "--brief", str(FIXTURES / "brief.md"),
        "--sources", str(FIXTURES / "sources.md"),
        "--contradictions", str(FIXTURES / "contradictions.md"),
        "--out", str(out_path),
    ]
    if mock_behavior is not None:
        cmd += ["--backend", "mock", "--mock-behavior", mock_behavior]
    else:
        cmd += ["--backend", "claude", "--model", model]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return {"error": r.stderr.strip()[:500] or r.stdout.strip()[:500]}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": "non-JSON synthesize output"}


def evaluate_one(synthesis_path: Path, gate_name: str) -> dict:
    if not synthesis_path.exists():
        return {"gate_passed": False, "contradiction_detected": False,
                "operator_override_implied": False, "missing_output": True}
    text = synthesis_path.read_text(encoding="utf-8")
    gate_result = GATES[gate_name](text)
    return {
        "gate_passed": gate_result["passed"],
        "gate_reason": gate_result["reason"],
        "contradiction_detected": detect_salted_contradiction(text),
        "operator_override_implied": operator_override_implied(text),
    }


# ---------------------------------------------------------------------------
# Main grid
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["mock", "claude"], default="mock",
                    help="mock = use deterministic fake LLM; claude = real API calls")
    ap.add_argument("--iterations", "-n", type=int, default=20)
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS,
                    help="Model IDs (only used in --mode claude)")
    ap.add_argument("--gates", nargs="+", default=DEFAULT_GATES)
    ap.add_argument("--mock-behaviors", nargs="+",
                    default=["good", "good", "forgetful"],
                    help="One behavior per 'model' in mock mode "
                         "(simulates: haiku=good, sonnet=good, opus=forgetful — "
                         "default deliberately wrong-headed to show how a real "
                         "result would look)")
    ap.add_argument("--out", default=str(RESULTS_DIR / "model-swap-results.json"))
    args = ap.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    cells = []

    for axis_a_idx, model in enumerate(args.models):
        mock_behavior = args.mock_behaviors[axis_a_idx % len(args.mock_behaviors)] \
            if args.mode == "mock" else None
        for gate in args.gates:
            cell_runs = []
            for i in range(args.iterations):
                slug = f"{model.replace(':', '_')}-{gate}-{i:02d}.md"
                out_path = RESULTS_DIR / "outputs" / slug
                out_path.parent.mkdir(parents=True, exist_ok=True)
                meta = run_one(model, mock_behavior, out_path)
                eval_ = evaluate_one(out_path, gate)
                cell_runs.append({"meta": meta, "eval": eval_})

            n = len(cell_runs)
            pass_rate = sum(r["eval"]["gate_passed"] for r in cell_runs) / n
            contradiction_rate = sum(r["eval"]["contradiction_detected"]
                                     for r in cell_runs) / n
            override_rate = sum(r["eval"]["operator_override_implied"]
                                for r in cell_runs) / n
            cells.append({
                "model": model,
                "gate": gate,
                "mock_behavior": mock_behavior,
                "n": n,
                "gate_pass_rate": pass_rate,
                "contradiction_detection_rate": contradiction_rate,
                "operator_override_rate": override_rate,
            })

    # Axis A: hold gate fixed at "normal", look at variance across models
    normal_cells = [c for c in cells if c["gate"] == "normal"]
    axis_a_pass = [(c["model"], c["gate_pass_rate"]) for c in normal_cells]
    axis_a_contradiction = [(c["model"], c["contradiction_detection_rate"])
                            for c in normal_cells]

    # Axis B: hold model fixed at first model, look at variance across gates
    first_model = args.models[0] if args.models else None
    fm_cells = [c for c in cells if c["model"] == first_model]
    axis_b_pass = [(c["gate"], c["gate_pass_rate"]) for c in fm_cells]

    summary = {
        "mode": args.mode,
        "iterations_per_cell": args.iterations,
        "cells": cells,
        "axis_A_model_vs_pass_rate (gate=normal)": axis_a_pass,
        "axis_A_model_vs_contradiction_rate (gate=normal)": axis_a_contradiction,
        "axis_B_gate_vs_pass_rate (model={})".format(first_model): axis_b_pass,
        "interpretation_notes": [
            "If axis A is flat and axis B is steep → thesis supported.",
            "If axis A is steep and axis B is flat → thesis falsified.",
            "Mock mode does not exercise the real thesis; rerun with --mode claude on a machine with $ANTHROPIC_API_KEY for actual data.",
        ],
    }

    Path(args.out).write_text(json.dumps(summary, indent=2))
    print(f"Wrote {args.out}")
    print()
    print("=== Cell grid ===")
    print(f"  {'model':24s} {'gate':12s} {'pass':>6s} {'cntr':>6s} {'ovrd':>6s}")
    for c in cells:
        print(f"  {c['model']:24s} {c['gate']:12s} "
              f"{c['gate_pass_rate']:5.2f}  {c['contradiction_detection_rate']:5.2f}  "
              f"{c['operator_override_rate']:5.2f}")
    print()
    print(f"Axis A (model vs gate-pass, gate=normal): {axis_a_pass}")
    print(f"Axis B (gate vs gate-pass, model={first_model}): {axis_b_pass}")


if __name__ == "__main__":
    main()
