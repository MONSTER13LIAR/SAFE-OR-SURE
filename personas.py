"""One persona turn = one LLM call with structured output.

The message text is fully generated; `facts_used` is the receipt the
Ledger scores against. Live AI, deterministic scoring.

Two backends, picked by which key is in .env:
  - ANTHROPIC_API_KEY   -> claude-opus-5 via messages.parse (preferred)
  - FEATHERLESS_API_KEY -> an open model via Featherless (sponsor track),
                           JSON-prompted and validated with one retry
"""

import json
import os
from pathlib import Path

import httpx
from pydantic import BaseModel

import voices

ANTHROPIC_MODEL = "claude-opus-5"
FEATHERLESS_MODEL = os.getenv("PERSONA_MODEL", "Qwen/Qwen3-30B-A3B-Instruct-2507")
FEATHERLESS_URL = "https://api.featherless.ai/v1/chat/completions"

JSON_CONTRACT = (
    'Reply with ONLY a JSON object: {"message": "...", "facts_used": ["id", ...]} '
    "— no code fences, no commentary, nothing before or after the JSON."
)


def load_env():
    """Mirror caspian-sdk's .env loading so the API keys are visible."""
    path = Path(__file__).parent / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                v = v.strip().strip('"').strip("'")
                if v:
                    os.environ.setdefault(k.strip(), v)


load_env()

_anthropic = None
if os.getenv("ANTHROPIC_API_KEY"):
    from anthropic import Anthropic

    _anthropic = Anthropic()
    BACKEND = f"anthropic/{ANTHROPIC_MODEL}"
elif os.getenv("FEATHERLESS_API_KEY"):
    BACKEND = f"featherless/{FEATHERLESS_MODEL}"
else:
    raise RuntimeError("no LLM key: set ANTHROPIC_API_KEY or FEATHERLESS_API_KEY in .env")


class PersonaTurn(BaseModel):
    message: str
    facts_used: list[str]


def _render_facts(tag: str, facts) -> str:
    return "\n".join(f"- [{f.id}] ({tag}) {f.text}" for f in facts)


def _build_prompt(persona, history, beat, own_facts, leak_facts, allowed_facts,
                  new_fact, notes):
    lines = [f"BEAT: {voices.BEATS[beat]}"]
    if notes:
        lines.append(f"BEAT NOTES: {notes}")

    known = []
    if new_fact is not None:
        known.append(f"- [{new_fact.id}] (NEW, they just told you) {new_fact.text}")
    if own_facts:
        known.append(_render_facts("they told you this here", own_facts))
    if leak_facts:
        known.append(_render_facts("LEAK", leak_facts))
    if allowed_facts:
        known.append(_render_facts("ALLOWED", allowed_facts))
    lines.append("FACTS YOU KNOW:\n" + "\n".join(known) if known
                 else "FACTS YOU KNOW: none yet.")

    if history:
        convo = "\n".join(
            f"{'them' if h['who'] == 'them' else 'you'}: {h['text']}" for h in history[-12:]
        )
        lines.append(f"RECENT CONVERSATION IN THIS ROOM:\n{convo}")
    else:
        lines.append("RECENT CONVERSATION IN THIS ROOM: none — this is the first message.")

    lines.append("Write this persona's next message.")
    return "\n\n".join(lines)


# ------------------------------------------------------------ backends
def _call_anthropic(persona: str, prompt: str) -> PersonaTurn:
    response = _anthropic.messages.parse(
        model=ANTHROPIC_MODEL,
        max_tokens=4000,
        output_config={"effort": "low"},
        system=[
            {"type": "text", "text": voices.SHARED_RULES},
            {
                "type": "text",
                "text": voices.VOICE_CARDS[persona],
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[{"role": "user", "content": prompt}],
        output_format=PersonaTurn,
    )
    return response.parsed_output


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"no JSON object in: {text[:120]!r}")
    return json.loads(text[start:end + 1])


def _call_featherless(persona: str, prompt: str) -> PersonaTurn:
    system = "\n\n".join([voices.SHARED_RULES, voices.VOICE_CARDS[persona], JSON_CONTRACT])
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    last_err = None
    for attempt in range(2):
        resp = httpx.post(
            FEATHERLESS_URL,
            headers={"Authorization": f"Bearer {os.environ['FEATHERLESS_API_KEY']}"},
            json={
                "model": FEATHERLESS_MODEL,
                "max_tokens": 500,
                "temperature": 0.8,
                "messages": messages,
            },
            timeout=120,
        )
        body = resp.json()
        if "choices" not in body:
            raise RuntimeError(f"featherless error: {body.get('error')}")
        raw = body["choices"][0]["message"]["content"] or ""
        try:
            return PersonaTurn.model_validate(_extract_json(raw))
        except Exception as e:  # malformed JSON — one strict retry
            last_err = e
            messages = messages[:2] + [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": f"That was not valid bare JSON ({e}). {JSON_CONTRACT}"},
            ]
    raise RuntimeError(f"featherless JSON failed twice: {last_err}")


# ------------------------------------------------------------ public
def persona_turn(
    persona: str,
    history: list[dict],
    beat: str,
    own_facts=(),
    leak_facts=(),
    allowed_facts=(),
    new_fact=None,
    notes: str = "",
) -> PersonaTurn:
    """history: [{"who": "them"|"you", "text": ...}] most recent last."""
    prompt = _build_prompt(persona, history, beat, own_facts, leak_facts,
                           allowed_facts, new_fact, notes)
    if _anthropic is not None:
        turn = _call_anthropic(persona, prompt)
    else:
        turn = _call_featherless(persona, prompt)

    # Sanitize the receipt: only ids that exist in the prompt count.
    legal = {f.id for f in (*own_facts, *leak_facts, *allowed_facts)}
    if new_fact is not None:
        legal.add(new_fact.id)
    turn.facts_used = [fid for fid in turn.facts_used if fid in legal]
    return turn
