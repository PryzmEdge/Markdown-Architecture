"""
synthesize.py — Stage 02 synthesis agent for Experiment 03 (model-swap insensitivity).

Reads:  brief.md, sources.md, contradictions.md (the Stage 01 outputs)
Writes: synthesis.md (the Stage 02 deliverable)

Two LLM modes:
- --backend mock          — deterministic fake responses for harness wiring tests
                            (does NOT exercise the real thesis — see README).
- --backend claude --model claude-{haiku,sonnet,opus}-4-{5,6,7}
                            — real Anthropic API call. Requires $ANTHROPIC_API_KEY.

Why split: this container has no API key. The harness ships ready-to-run; you supply
the key on your Mac. Mock backend validates the agent's I/O and prompt assembly
without burning credits.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path


SYSTEM_PROMPT = """\
You are the Stage 02 Synthesis & Risk Agent for the Markdown Architecture pipeline.
Your job: synthesize the Stage 01 research outputs into a structured argument and
assign a risk tier.

Read brief.md (the problem + top findings + proposed solution), sources.md (the
evidence table), and contradictions.md (disconfirming evidence — must not be
suppressed).

Output a single Markdown document with VALID YAML frontmatter and EXACTLY these
top-level sections in this order:

  ---
  status: review
  stage: "02-analysis"
  operator_approved: false
  risk_check_passed: false
  risk_tier: "Low" | "Medium" | "High" | "Critical"
  ---

  # Synthesis: <title>

  ## Core claim
  ## Evidence map
  ## Integrated findings
  ## Counter-argument
  ## Recommendations

The Counter-argument section must engage every named disconfirming source in
contradictions.md. If contradictions.md cites Yamashita et al. (2025), your
Counter-argument MUST name Yamashita by author and year.

Risk tier rules:
- Low: reversible, no external dependency.
- Medium: reversible, external dependency exists.
- High: partially irreversible or high-cost to undo. Requires risk_check_passed: true.
- Critical: irreversible, public, or financial consequence. Requires explicit
  operator sign-off.

Set risk_tier honestly based on the problem's actual scope. Do not inflate or
deflate to look prudent.
"""


def build_prompt(brief: str, sources: str, contradictions: str) -> str:
    return f"""\
Inputs:

=== brief.md ===
{brief}

=== sources.md ===
{sources}

=== contradictions.md ===
{contradictions}

Now produce synthesis.md. Output ONLY the Markdown content. No code fences, no
preamble, no explanation. Begin with the YAML frontmatter delimiter (---).
"""


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------

class MockBackend:
    """
    Deterministic fake LLM. Three behaviors keyed by a probe arg so the harness
    can exercise different code paths without burning API credits.
    """

    name = "mock"

    def __init__(self, behavior: str = "good"):
        # good = surfaces Yamashita, valid frontmatter, sane risk tier
        # forgetful = surfaces only the easy counter-evidence, MISSES Yamashita
        # broken = invalid frontmatter (missing risk_tier)
        if behavior not in {"good", "forgetful", "broken"}:
            raise ValueError(f"unknown mock behavior: {behavior}")
        self.behavior = behavior

    def synthesize(self, prompt: str) -> str:
        if self.behavior == "good":
            return self._good_response()
        if self.behavior == "forgetful":
            return self._forgetful_response()
        return self._broken_response()

    def _good_response(self) -> str:
        return (
            "---\n"
            "status: review\n"
            'stage: "02-analysis"\n'
            "operator_approved: false\n"
            "risk_check_passed: false\n"
            'risk_tier: "Medium"\n'
            "---\n\n"
            "# Synthesis: PostgreSQL as Personal-Scale AI Substrate\n\n"
            "## Core claim\n"
            "A single Postgres instance can serve as state kernel, event log, vector index,\n"
            "and audit ledger for a personal-scale AI workspace, eliminating Redis/Kafka/\n"
            "EventStore/Temporal/vector-DB sprawl.\n\n"
            "## Evidence map\n"
            "- DBOS (Stonebraker 2024) supports the durable-workflow claim.\n"
            "- pgvector + pgvectorscale support the vector-index claim under 1e8 vectors.\n"
            "- Marten + Letta support the event-sourcing-and-audit claim.\n\n"
            "## Integrated findings\n"
            "The four sources reinforce each other: each component the workspace needs\n"
            "(workflows, vectors, events, audit) has independent production-grade evidence\n"
            "of viability on Postgres at the scale this workspace targets.\n\n"
            "## Counter-argument\n"
            "Yamashita et al. (2025) document a 97% query-latency cliff in pgvector\n"
            "beyond 1.2e8 vectors. For workspaces approaching that threshold, dedicated\n"
            "vector DBs maintain sub-200ms p99 where pgvector regresses to multi-second\n"
            "p99. The thesis explicitly bounds itself at personal scale; the cliff\n"
            "marks the boundary. Stonebraker's own VLDB 2023 acknowledgment of the\n"
            "50K-write-tx/s limit reinforces that the thesis is scoped, not universal.\n\n"
            "## Recommendations\n"
            "Adopt Postgres-as-substrate at personal scale. Tag the architectural\n"
            "decision with an explicit re-evaluation trigger at 1e8 vectors or\n"
            "50K write-tx/s, whichever comes first.\n"
        )

    def _forgetful_response(self) -> str:
        return (
            "---\n"
            "status: review\n"
            'stage: "02-analysis"\n'
            "operator_approved: false\n"
            "risk_check_passed: false\n"
            'risk_tier: "Medium"\n'
            "---\n\n"
            "# Synthesis: PostgreSQL as Substrate\n\n"
            "## Core claim\n"
            "Postgres can serve as the unified substrate for personal-scale AI workspaces.\n\n"
            "## Evidence map\n"
            "Multiple sources support each capability needed.\n\n"
            "## Integrated findings\n"
            "Production precedent exists for every component.\n\n"
            "## Counter-argument\n"
            "Postgres has known scale limits. Stonebraker has noted single-node\n"
            "write-tx limits in the 50K/s range. CRDT-on-Postgres remains an open\n"
            "problem.\n\n"
            "## Recommendations\n"
            "Adopt at personal scale, re-evaluate at SaaS scale.\n"
        )

    def _broken_response(self) -> str:
        # Missing risk_tier in frontmatter — should fail the gate validator.
        return (
            "---\n"
            "status: review\n"
            'stage: "02-analysis"\n'
            "operator_approved: false\n"
            "risk_check_passed: false\n"
            "---\n\n"
            "# Synthesis\n\n"
            "Postgres for everything.\n"
        )


class ClaudeBackend:
    """Real Anthropic SDK call. Requires $ANTHROPIC_API_KEY."""

    def __init__(self, model: str):
        try:
            import anthropic
        except ImportError:
            sys.exit("anthropic SDK not installed: pip install anthropic")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY not set — synthesize.py cannot call claude.")
        self.client = anthropic.Anthropic()
        self.model = model
        self.name = f"claude:{model}"

    def synthesize(self, prompt: str) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if hasattr(b, "text"))


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Stage 02 synthesis agent")
    ap.add_argument("--brief", required=True, help="Path to brief.md")
    ap.add_argument("--sources", required=True, help="Path to sources.md")
    ap.add_argument("--contradictions", required=True, help="Path to contradictions.md")
    ap.add_argument("--out", required=True, help="Path to write synthesis.md")
    ap.add_argument("--backend", choices=["mock", "claude"], default="mock")
    ap.add_argument("--model", default="claude-sonnet-4-6",
                    help="Model ID when --backend claude")
    ap.add_argument("--mock-behavior", choices=["good", "forgetful", "broken"],
                    default="good", help="Mock backend behavior (ignored for claude)")
    args = ap.parse_args()

    brief = Path(args.brief).read_text(encoding="utf-8")
    sources = Path(args.sources).read_text(encoding="utf-8")
    contradictions = Path(args.contradictions).read_text(encoding="utf-8")

    prompt = build_prompt(brief, sources, contradictions)

    if args.backend == "mock":
        backend = MockBackend(args.mock_behavior)
    else:
        backend = ClaudeBackend(args.model)

    t0 = time.time()
    synthesis = backend.synthesize(prompt)
    elapsed_ms = int((time.time() - t0) * 1000)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(synthesis, encoding="utf-8")

    meta = {
        "backend": backend.name,
        "model": getattr(backend, "model", None),
        "mock_behavior": args.mock_behavior if args.backend == "mock" else None,
        "elapsed_ms": elapsed_ms,
        "output_chars": len(synthesis),
        "output_path": args.out,
    }
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
