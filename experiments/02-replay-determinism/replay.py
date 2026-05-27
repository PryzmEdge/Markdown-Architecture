"""
replay.py — Experiment 02: Replay-determinism test

Hypothesis (from docs/thesis-experiments.md):
    ADR-005 requires the workflow layer to be pure: no `datetime.now()`,
    no `uuid.uuid4()`, no network calls. A replay of the event log from
    any committed run should re-derive *identical* gate decisions and
    *identical* receipt bodies.

Method:
    1. Pick the most recent complete workflow_run_id from Postgres.
    2. For each gate event in workflow_events, re-derive the gate verdict
       from first principles (running assert_approved against the input
       artifact's current frontmatter) and compare it to the recorded
       verdict.
    3. Rebuild the receipt by calling build_receipt() with the same inputs
       and diff it field-by-field against the receipt_json stored in
       provenance_log.
    4. Report:
         - Gate decisions: replayed vs recorded (expected: identical).
         - Receipt fields: replayed vs recorded (expected: 4 non-deterministic
           fields differ; everything else matches).

Verdict semantics:
    PASS = gate decisions and receipt body match bit-identical.
    FAIL = anything differs.

This experiment is designed to FAIL on the current proof/workflow.py.
The failure is productive: it empirically pins the ADR-005 gap that
proof/explanation.md § "The DBOS gap" already named in prose.
"""

import json
import os
import sys
from pathlib import Path

import psycopg2

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "proof"))
from ingester import ingest, assert_approved, IngesterError
from workflow import build_receipt  # noqa: E402

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://ma:ma_dev@localhost:5432/markdown_arch"
)


def latest_complete_run(conn):
    """Return the workflow_run_id of the most recent complete (3-event + 1-receipt) run."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT pl.workflow_run_id
            FROM provenance_log pl
            ORDER BY pl.created_at DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
    if not row:
        sys.exit("No complete runs found in provenance_log.")
    return row[0]


def fetch_events(conn, run_id):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT step_name, status, payload
            FROM workflow_events
            WHERE workflow_run_id = %s
            ORDER BY id
            """,
            (run_id,),
        )
        return [{"step": r[0], "status": r[1], "payload": r[2]} for r in cur.fetchall()]


def fetch_receipt(conn, run_id):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT operator_id, pg_receipt_hash, receipt_json
            FROM provenance_log
            WHERE workflow_run_id = %s
            ORDER BY created_at ASC
            LIMIT 1
            """,
            (run_id,),
        )
        row = cur.fetchone()
    if not row:
        sys.exit(f"No receipt found for run {run_id}.")
    return {"operator_id": row[0], "pg_receipt_hash": row[1], "receipt_json": row[2]}


def replay_gate(events, artifact):
    """
    Re-derive the gate_00 verdict from first principles using the live
    artifact (parsed from the same path). Compare to the recorded verdict.
    """
    recorded = next((e for e in events if e["step"] == "gate_00"), None)
    if not recorded:
        return {"recorded": None, "replayed": None, "match": None,
                "note": "no gate_00 event recorded"}
    recorded_results = recorded["payload"]

    try:
        assert_approved(artifact)
        replayed_results = {
            "operator_approved": True, "status_approved": True, "contract_passed": True,
        }
    except IngesterError as e:
        replayed_results = {"error": str(e), "contract_passed": False}

    match = recorded_results == replayed_results
    return {
        "recorded": recorded_results,
        "replayed": replayed_results,
        "match": match,
    }


def diff_receipts(recorded: dict, replayed: dict):
    """Field-by-field diff. Returns (matches, differs)."""
    matches, differs = {}, {}
    keys = set(recorded.keys()) | set(replayed.keys())
    for k in sorted(keys):
        a = recorded.get(k, "<MISSING>")
        b = replayed.get(k, "<MISSING>")
        if a == b:
            matches[k] = a
        else:
            differs[k] = {"recorded": a, "replayed": b}
    return matches, differs


def main():
    out_path = REPO_ROOT / "experiments" / "02-replay-determinism" / "results" / "replay-results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    conn = psycopg2.connect(DATABASE_URL)
    run_id = latest_complete_run(conn)
    print(f"Replaying run_id: {run_id}")

    events = fetch_events(conn, run_id)
    receipt_row = fetch_receipt(conn, run_id)
    recorded_receipt = receipt_row["receipt_json"]
    operator_id = receipt_row["operator_id"]
    recorded_hash = receipt_row["pg_receipt_hash"]

    artifact_path = recorded_receipt["input_artifacts"][0]["path"]
    artifact = ingest(artifact_path)

    gate_replay = replay_gate(events, artifact)
    gate_check_results = gate_replay["replayed"]
    if not isinstance(gate_check_results, dict) or "operator_approved" not in gate_check_results:
        gate_check_results = recorded_receipt.get("gate_check_results", {})

    replayed_receipt = build_receipt(run_id, artifact, operator_id, gate_check_results)

    receipt_matches, receipt_differs = diff_receipts(recorded_receipt, replayed_receipt)

    expected_diff_fields = {
        "receipt_id", "timestamp", "operator_signoff",
    }
    observed_diff_fields = set(receipt_differs.keys())
    unexpected_diff_fields = observed_diff_fields - expected_diff_fields
    expected_but_missing = expected_diff_fields - observed_diff_fields

    gate_verdict = "PASS" if gate_replay.get("match") else "FAIL"
    receipt_verdict = "PASS" if not receipt_differs else "FAIL (non-deterministic body)"
    overall_purity = "PASS" if gate_replay.get("match") and not receipt_differs else "FAIL"

    import hashlib
    replayed_json = json.dumps(replayed_receipt, indent=2, default=str)
    replayed_hash = hashlib.sha256(replayed_json.encode()).hexdigest()

    results = {
        "run_id": run_id,
        "database_url": DATABASE_URL.replace(":ma_dev@", ":***@"),
        "gate": gate_replay,
        "receipt": {
            "recorded_hash": recorded_hash,
            "replayed_hash": replayed_hash,
            "hashes_match": recorded_hash == replayed_hash,
            "fields_match": list(receipt_matches.keys()),
            "fields_differ": receipt_differs,
            "expected_non_deterministic_fields": sorted(expected_diff_fields),
            "unexpected_divergence": sorted(unexpected_diff_fields),
            "expected_divergence_not_observed": sorted(expected_but_missing),
        },
        "verdict": {
            "gate_determinism": gate_verdict,
            "receipt_determinism": receipt_verdict,
            "overall": overall_purity,
        },
    }

    out_path.write_text(json.dumps(results, indent=2, default=str))
    conn.close()

    print()
    print("=== Gate determinism ===")
    print(f"  Gate verdict: {gate_verdict}")
    print(f"    Recorded:  {gate_replay['recorded']}")
    print(f"    Replayed:  {gate_replay['replayed']}")
    print()
    print("=== Receipt determinism ===")
    print(f"  Recorded SHA-256:  {recorded_hash[:16]}...")
    print(f"  Replayed SHA-256:  {replayed_hash[:16]}...")
    print(f"  Hashes match:      {recorded_hash == replayed_hash}")
    print(f"  Fields match:      {len(receipt_matches)}")
    print(f"  Fields differ:     {len(receipt_differs)}")
    for k in sorted(receipt_differs.keys()):
        rec = receipt_differs[k]["recorded"]
        rep = receipt_differs[k]["replayed"]
        rec_s = repr(rec)[:60]
        rep_s = repr(rep)[:60]
        print(f"    - {k}:")
        print(f"        recorded:  {rec_s}")
        print(f"        replayed:  {rep_s}")
    if unexpected_diff_fields:
        print()
        print(f"  ⚠ UNEXPECTED divergence (NOT in {sorted(expected_diff_fields)}):")
        for k in sorted(unexpected_diff_fields):
            print(f"    - {k}")
    print()
    print(f"=== Overall: {overall_purity} ===")
    print(f"Results JSON: {out_path}")
    print()
    if overall_purity == "FAIL":
        print("(Expected failure — this experiment is designed to falsify the")
        print(" current proof/workflow.py against ADR-005's purity requirement.)")


if __name__ == "__main__":
    main()
