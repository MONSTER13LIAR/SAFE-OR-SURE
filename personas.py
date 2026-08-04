"""One persona turn = one Claude call with structured output.

The message text is fully generated; `facts_used` is the receipt the
Ledger scores against. Live AI, deterministic scoring.
"""

import os
from pathlib import Path

from anthropic import Anthropic
from pydantic import BaseModel

import voices

MODEL = "claude-opus-5"


def load_env():
    """Mirror caspian-sdk's .env loading so ANTHROPIC_API_KEY is visible."""
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
client = Anthropic()


class PersonaTurn(BaseModel):
    message: str
    facts_used: list[str]


def _render_facts(tag: str, facts) -> str:
    return "\n".join(f"- [{f.id}] ({tag}) {f.text}" for f in facts)


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
    if known:
        lines.append("FACTS YOU KNOW:\n" + "\n".join(known))
    else:
        lines.append("FACTS YOU KNOW: none yet.")

    if history:
        convo = "\n".join(
            f"{'them' if h['who'] == 'them' else 'you'}: {h['text']}" for h in history[-12:]
        )
        lines.append(f"RECENT CONVERSATION IN THIS ROOM:\n{convo}")
    else:
        lines.append("RECENT CONVERSATION IN THIS ROOM: none — this is the first message.")

    lines.append("Write this persona's next message.")

    response = client.messages.parse(
        model=MODEL,
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
        messages=[{"role": "user", "content": "\n\n".join(lines)}],
        output_format=PersonaTurn,
    )
    turn = response.parsed_output

    # Sanitize the receipt: only ids that exist in the prompt count.
    legal = {f.id for f in (*own_facts, *leak_facts, *allowed_facts)}
    if new_fact is not None:
        legal.add(new_fact.id)
    turn.facts_used = [fid for fid in turn.facts_used if fid in legal]
    return turn
