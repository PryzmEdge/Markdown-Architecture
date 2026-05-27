"""
consume_llm.py — Consumer B for Experiment 04 (consumer-swap test).

Feeds the unmodified Stage 02 synthesis.md to an LLM with a "summarize this"
prompt. Verifies the summary names:
  1. The core claim (Postgres as unified substrate)
  2. The strongest counter-argument (Yamashita 2025 cliff at 1.2e8 vectors)
  3. The assigned risk_tier (Medium)

If any of those three are absent, the consumer is producing a summary that
loses essential structure — a weak signal that the markdown bytes were
substrate-coupled and the LLM needed to "render" them via context the source
didn't supply. (Likely a prompt issue, not a real failure of substrate-portability;
but the metric is still informative.)

Backends:
- --backend mock      — deterministic fake summary that hits all 3 anchors
                        (smoke test of harness wiring only).
- --backend claude    — real Anthropic API call. Requires $ANTHROPIC_API_KEY.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path


SYSTEM_PROMPT = """\
You are a research assistant. The user will paste a Stage 02 synthesis
artifact (markdown with YAML frontmatter and structured sections). Produce
a 150-200 word summary that names:

1. The core claim (1-2 sentences).
2. The strongest counter-argument by author and year if cited.
3. The assigned risk_tier from the frontmatter.

Plain prose. No bullet points. No headings. Just the summary.
"""


MOCK_SUMMARY = (
    "The synthesis argues that a single PostgreSQL instance can serve as state "
    "kernel, durable workflow engine, vector index, event log, and audit "
    "ledger for a personal-scale AI workspace, eliminating the Redis/Kafka/"
    "EventStore/Temporal/vector-DB sprawl typical of production agent systems. "
    "The thesis is supported by four independent production precedents (DBOS, "
    "pgvector + pgvectorscale, Marten, Letta on Aurora). The strongest "
    "counter-argument is from Yamashita et al. (2025), which documents a 97% "
    "query-latency cliff in pgvector HNSW indexes beyond 1.2 × 10⁸ vectors — "
    "a sharp boundary the thesis must explicitly name, though it does not "
    "fall within personal-scale usage. A secondary counter from Stonebraker's "
    "own VLDB 2023 keynote names a 50K write-tx/s single-node ceiling, also "
    "outside personal scale but disqualifying for multi-tenant SaaS. "
    "The assigned risk_tier is Medium: reversible architecture with external "
    "dependencies on Postgres extensions (pgvector, pgvectorscale, pg_cron, "
    "optionally DBOS) that must be actively maintained."
)


def call_mock(_text: str) -> str:
    return MOCK_SUMMARY


def call_claude(text: str, model: str) -> str:
    try:
        import anthropic
    except ImportError:
        sys.exit("anthropic SDK not installed: pip install anthropic")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not set — cannot call Claude.")
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    return "".join(b.text for b in resp.content if hasattr(b, "text"))


def verify_summary(summary: str) -> dict:
    anchors = {
        "core_claim": ("postgres" in summary.lower() and
                       ("substrate" in summary.lower() or
                        "kernel" in summary.lower() or
                        "ledger" in summary.lower())),
        "counter_argument_yamashita": "yamashita" in summary.lower(),
        "risk_tier_medium": "medium" in summary.lower(),
    }
    return {
        "anchors": anchors,
        "all_present": all(anchors.values()),
        "missing": [k for k, v in anchors.items() if not v],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthesis", required=True, help="Path to synthesis.md")
    ap.add_argument("--out", required=True, help="Path to write summary.txt")
    ap.add_argument("--backend", choices=["mock", "claude"], default="mock")
    ap.add_argument("--model", default="claude-sonnet-4-6")
    args = ap.parse_args()

    text = Path(args.synthesis).read_text(encoding="utf-8")
    if args.backend == "mock":
        backend_name = "mock"
        t0 = time.time()
        summary = call_mock(text)
        elapsed_ms = int((time.time() - t0) * 1000)
    else:
        backend_name = f"claude:{args.model}"
        t0 = time.time()
        summary = call_claude(text, args.model)
        elapsed_ms = int((time.time() - t0) * 1000)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(summary, encoding="utf-8")

    verdict = verify_summary(summary)
    result = {
        "backend": backend_name,
        "elapsed_ms": elapsed_ms,
        "summary_chars": len(summary),
        "summary_path": args.out,
        "verification": verdict,
        "verdict": "PASS" if verdict["all_present"] else "FAIL",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
