"""
harness.py — Experiment 01: Fault injection on proof/workflow.py

Hypothesis (from docs/thesis-experiments.md):
    After a kill at any timing, the database lands in exactly one of four
    states: {empty, ingest-committed, gate-committed, complete}. No
    half-committed events; no receipts without their corresponding event;
    no event rows outside the expected sequence.

Method:
    Spawn proof/workflow.py as a subprocess against the approved fixture,
    kill -9 it after a randomized 0.1-1.5 s delay, then classify the
    terminal database state for that run_id. Repeat N times. Tabulate.

Falsification: any run lands in a state outside the four expected ones.
"""

import argparse
import json
import os
import random
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

import psycopg2

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://ma:ma_dev@localhost:5432/markdown_arch"
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
APPROVED_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "approved.md"


def reset_tables(conn):
    """Drop+recreate the two tables so each harness invocation starts clean."""
    with conn.cursor() as cur:
        cur.execute("TRUNCATE workflow_events, provenance_log RESTART IDENTITY;")
    conn.commit()


def classify_run(conn, run_id: str) -> dict:
    """
    Return the terminal state for a single workflow_run_id:
      events:   ordered list of (step_name, status)
      receipts: count of provenance_log rows for this run_id
      class:    'empty' | 'ingest' | 'gate' | 'complete' | 'UNEXPECTED'
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT step_name, status FROM workflow_events
            WHERE workflow_run_id = %s ORDER BY id
            """,
            (run_id,),
        )
        events = [(r[0], r[1]) for r in cur.fetchall()]
        cur.execute(
            "SELECT count(*) FROM provenance_log WHERE workflow_run_id = %s",
            (run_id,),
        )
        receipt_count = cur.fetchone()[0]

    # Expected sequences:
    #   []                                                 -> empty
    #   [(ingest, passed)]                                 -> ingest
    #   [(ingest, passed), (gate_00, passed)]              -> gate
    #   [(ingest, passed), (gate_00, passed),
    #    (receipt, passed)] + receipt_count == 1           -> complete
    expected_complete = [
        ("ingest", "passed"),
        ("gate_00", "passed"),
        ("receipt", "passed"),
    ]
    expected_gate = expected_complete[:2]
    expected_ingest = expected_complete[:1]

    if not events and receipt_count == 0:
        cls = "empty"
    elif events == expected_ingest and receipt_count == 0:
        cls = "ingest"
    elif events == expected_gate and receipt_count == 0:
        cls = "gate"
    elif events == expected_complete and receipt_count == 1:
        cls = "complete"
    else:
        cls = "UNEXPECTED"

    return {"events": events, "receipts": receipt_count, "class": cls}


def find_run_ids_since(conn, since_id: int) -> list[str]:
    """Return distinct workflow_run_ids for events with id > since_id, in order."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT workflow_run_id, MIN(id) AS first_id
            FROM workflow_events
            WHERE id > %s
            GROUP BY workflow_run_id
            ORDER BY first_id
            """,
            (since_id,),
        )
        return [r[0] for r in cur.fetchall()]


def max_event_id(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(id), 0) FROM workflow_events;")
        return cur.fetchone()[0]


def run_one(delay: float, label: str) -> dict:
    """
    Spawn workflow.py, sleep `delay` seconds, SIGKILL it, wait for exit.
    Returns metadata about the run; classification happens after.
    """
    cmd = [
        sys.executable,
        str(REPO_ROOT / "proof" / "workflow.py"),
        "--problem",
        str(APPROVED_FIXTURE),
        "--operator",
        f"harness-{label}",
    ]
    env = os.environ.copy()
    env["DATABASE_URL"] = DATABASE_URL
    # Suppress workflow.py's chatty stdout to keep the harness output clean.
    proc = subprocess.Popen(
        cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        cwd=REPO_ROOT,
    )
    killed = False
    completed_naturally = False
    time.sleep(delay)
    if proc.poll() is None:
        proc.send_signal(signal.SIGKILL)
        killed = True
    proc.wait(timeout=10)
    if not killed:
        completed_naturally = True
    return {
        "label": label,
        "delay": delay,
        "killed": killed,
        "completed_naturally": completed_naturally,
        "exit_code": proc.returncode,
    }


def main():
    ap = argparse.ArgumentParser(
        description="Fault-injection harness for proof/workflow.py"
    )
    ap.add_argument("--iterations", "-n", type=int, default=100,
                    help="Number of fault-injection runs (default: 100)")
    ap.add_argument("--delay-min", type=float, default=0.1)
    ap.add_argument("--delay-max", type=float, default=1.5)
    ap.add_argument("--seed", type=int, default=42,
                    help="RNG seed for reproducible delay distribution")
    ap.add_argument("--results-path", default=str(
        Path(__file__).parent / "results" / "fault-injection-results.json"
    ))
    ap.add_argument("--reset", action="store_true",
                    help="TRUNCATE workflow_events + provenance_log first")
    args = ap.parse_args()

    if not APPROVED_FIXTURE.exists():
        sys.exit(f"missing fixture: {APPROVED_FIXTURE}")

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    if args.reset:
        reset_tables(conn)

    random.seed(args.seed)
    baseline_id = max_event_id(conn)
    runs = []
    print(f"Running {args.iterations} fault-injection iterations "
          f"(delay {args.delay_min}-{args.delay_max}s)...")
    for i in range(1, args.iterations + 1):
        delay = random.uniform(args.delay_min, args.delay_max)
        meta = run_one(delay, label=str(i))
        runs.append(meta)
        if i % 10 == 0 or i == args.iterations:
            print(f"  {i}/{args.iterations} done (last delay={delay:.3f}s)")

    # Refresh connection state and classify every run_id created since baseline.
    conn.rollback()
    run_ids = find_run_ids_since(conn, baseline_id)
    classifications = [classify_run(conn, rid) for rid in run_ids]

    distribution = {
        "empty": 0, "ingest": 0, "gate": 0, "complete": 0, "UNEXPECTED": 0,
    }
    for c in classifications:
        distribution[c["class"]] += 1

    # Iterations that wrote no DB row at all (killed during interpreter
    # startup before workflow.py opened a connection) are "empty" by
    # definition: no events, no receipts, nothing in any table.
    db_silent_iterations = args.iterations - len(classifications)
    distribution["empty"] += db_silent_iterations

    unexpected = [c for c in classifications if c["class"] == "UNEXPECTED"]

    results = {
        "iterations_requested": args.iterations,
        "runs_observed_in_db": len(classifications),
        "db_silent_iterations": db_silent_iterations,
        "delay_range": [args.delay_min, args.delay_max],
        "seed": args.seed,
        "database_url": DATABASE_URL.replace(":ma_dev@", ":***@"),
        "distribution": distribution,
        "unexpected_runs": unexpected,
        "verdict": "PASS" if not unexpected else "FAIL",
        "runs": [
            {**meta, **{f"db_{k}": v for k, v in cls.items()}}
            for meta, cls in zip(runs, classifications)
        ],
    }

    Path(args.results_path).parent.mkdir(parents=True, exist_ok=True)
    Path(args.results_path).write_text(json.dumps(results, indent=2, default=str))
    conn.close()

    print()
    print(f"=== Distribution over {args.iterations} iterations ===")
    print(f"    ({len(classifications)} touched the DB; "
          f"{db_silent_iterations} killed during interpreter startup → empty)")
    total = args.iterations
    for k in ("empty", "ingest", "gate", "complete", "UNEXPECTED"):
        bar_len = max(1, int(60 * distribution[k] / total)) if distribution[k] else 0
        bar = "#" * bar_len
        pct = 100.0 * distribution[k] / total if total else 0.0
        print(f"  {k:11s} {distribution[k]:4d}  ({pct:5.1f}%)  {bar}")
    print()
    print(f"Verdict: {results['verdict']}")
    if unexpected:
        print(f"  {len(unexpected)} UNEXPECTED run(s) — see results JSON.")
    print(f"Results JSON: {args.results_path}")


if __name__ == "__main__":
    main()
