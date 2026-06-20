"""
tests/test_model_swap_harness.py — regression test for the exp-03 result-integrity fix.

Bug (fixed in fix(exp-03)): the harness recorded an API-call failure as a gate
failure and discarded the error, silently corrupting gate-pass rates. These tests
inject run_one-style error results (NO real API call) and assert that errored runs
are excluded from BOTH the rate numerator and denominator, that a fully-errored
cell reports gate_pass_rate = null (not 0.0), and that n_error / sample_errors are
populated.
"""

import importlib.util
import json
import sys
from pathlib import Path

HARNESS_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments" / "03-model-swap" / "harness.py"
)


def _load_harness():
    spec = importlib.util.spec_from_file_location("exp03_harness", HARNESS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _iter_index(out_path: Path) -> int:
    # slug = "<model>-<gate>-<NN>.md"; the iteration is always the last '-' segment.
    return int(out_path.stem.split("-")[-1])


def _run_harness(monkeypatch, tmp_path, script, *, model="m1", gate="normal"):
    """Drive harness.main() in --mode claude with run_one/evaluate_one stubbed
    per `script` (one entry per iteration). Returns the parsed summary JSON."""
    harness = _load_harness()
    monkeypatch.setattr(harness, "RESULTS_DIR", tmp_path)

    def fake_run_one(model_, mock_behavior, out_path):
        entry = script[_iter_index(out_path)]
        if "error" in entry:
            return {"error": entry["error"]}
        return {"backend": f"claude:{model_}", "model": model_}

    def fake_evaluate_one(out_path, gate_):
        entry = script[_iter_index(out_path)]
        return {
            "gate_passed": entry["passed"],
            "gate_reason": "stub",
            "contradiction_detected": entry.get("contradiction", False),
            "operator_override_implied": entry.get("override", False),
        }

    monkeypatch.setattr(harness, "run_one", fake_run_one)
    monkeypatch.setattr(harness, "evaluate_one", fake_evaluate_one)

    out = tmp_path / "out.json"
    argv = ["harness.py", "--mode", "claude", "--models", model,
            "--gates", gate, "--iterations", str(len(script)), "--out", str(out)]
    monkeypatch.setattr(sys, "argv", argv)
    harness.main()
    return json.loads(out.read_text())


def test_fully_errored_cell_reports_null_not_zero(monkeypatch, tmp_path):
    script = [{"error": f"boom-{i}"} for i in range(4)]
    summary = _run_harness(monkeypatch, tmp_path, script)
    cell = summary["cells"][0]

    assert cell["n"] == 4
    assert cell["n_ok"] == 0
    assert cell["n_error"] == 4
    # The bug would have reported 0.0 here. The fix reports null.
    assert cell["gate_pass_rate"] is None
    assert cell["contradiction_detection_rate"] is None
    assert cell["operator_override_rate"] is None
    # sample_errors capped at 3, recovered from the previously-discarded strings.
    assert cell["sample_errors"] == ["boom-0", "boom-1", "boom-2"]

    assert summary["total_runs"] == 4
    assert summary["total_errors"] == 4
    assert any("WARNING" in n for n in summary["interpretation_notes"])
    # claude mode → the mock-only note must NOT appear
    assert not any("Mock mode does not" in n for n in summary["interpretation_notes"])


def test_errors_excluded_from_numerator_and_denominator(monkeypatch, tmp_path):
    # 4 runs: 2 errored, 2 succeeded (1 gate pass, 1 gate fail).
    script = [
        {"error": "boom-a"},
        {"passed": True, "contradiction": True},
        {"error": "boom-b"},
        {"passed": False, "contradiction": True},
    ]
    summary = _run_harness(monkeypatch, tmp_path, script)
    cell = summary["cells"][0]

    assert cell["n"] == 4
    assert cell["n_ok"] == 2
    assert cell["n_error"] == 2
    # Over successful runs only: 1 of 2 passed -> 0.5.
    # NOT 0.25 (counting errors in the denominator) and NOT corrupted by errors.
    assert cell["gate_pass_rate"] == 0.5
    assert cell["contradiction_detection_rate"] == 1.0   # 2/2 over ok runs
    assert cell["operator_override_rate"] == 0.0
    assert cell["sample_errors"] == ["boom-a", "boom-b"]

    assert summary["total_runs"] == 4
    assert summary["total_errors"] == 2
    assert any("WARNING" in n for n in summary["interpretation_notes"])
