"""
ai_gateway.py — the single point every LLM call must pass through.

The thesis this file is here to prove: stage code never talks to the model
SDK directly. It calls one function, `call_llm`, which (a) picks a model by
TIER rather than by name, (b) makes the call, and (c) hands back both the text
and the raw usage numbers so a receipt can be written. Centralising the call
is what makes cost policy, tiering, and provenance enforceable later — none of
that is possible if every stage instantiates its own client.

SDK SIGNATURE — verified against the current Anthropic API reference (2026-06):
The call below uses the Messages API shape
    client.messages.create(model=..., max_tokens=..., messages=[...])
and reads usage from `response.usage.input_tokens` / `.output_tokens`. Both the
call shape and those usage field names are current. The model IDs in
MODEL_BY_TIER are the current canonical aliases (do NOT append date suffixes).
Note: Opus 4.8 / Sonnet 4.6 reject `temperature`/`top_p`/`top_k` and
`budget_tokens`; this gateway passes none of them, so it is compatible as-is.
If a stage later needs reasoning, add `thinking={"type": "adaptive"}` here —
that is the only on-mode for the current Opus tier.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# Tier -> concrete model id. Stage code asks for a TIER ("haiku"/"sonnet"/
# "opus"), never a model string. That indirection is the whole point: swapping
# the model behind a tier is a one-line config change, not a code-wide find.
MODEL_BY_TIER: dict[str, str] = {
    "haiku": "claude-haiku-4-5",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-8",
}

DEFAULT_TIER = "haiku"  # cheapest capable model unless a stage justifies more


@dataclass
class LLMResult:
    """Everything the receipt writer needs, in one plain object."""
    text: str
    model_id: str
    input_tokens: int
    output_tokens: int


def call_llm(
    prompt: str,
    *,
    stage_id: str,
    tier: str = DEFAULT_TIER,
    max_tokens: int = 1024,
) -> LLMResult:
    """Route one prompt through the gateway and return text + usage.

    `stage_id` is required (not optional) on purpose: an ungoverned call with
    no owning stage is exactly what the gateway exists to prevent. We don't use
    it for anything clever here — we just refuse to let a call be anonymous.
    """
    if not stage_id:
        raise ValueError("every gateway call must declare a stage_id")
    if tier not in MODEL_BY_TIER:
        raise ValueError(f"unknown tier {tier!r}; expected one of {list(MODEL_BY_TIER)}")

    model_id = MODEL_BY_TIER[tier]

    # Imported lazily so the contract validator and tests can import this module
    # WITHOUT the anthropic package installed or an API key present.
    import anthropic

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Export it before running a real call:\n"
            "    export ANTHROPIC_API_KEY=sk-ant-..."
        )

    _client = anthropic.Anthropic()
    response = _client.messages.create(
        model=model_id,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )

    # The SDK returns content as a list of typed blocks; for a plain text reply
    # the text lives on the first block. We concatenate defensively in case the
    # model returns more than one text block.
    text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )

    return LLMResult(
        text=text,
        model_id=model_id,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
