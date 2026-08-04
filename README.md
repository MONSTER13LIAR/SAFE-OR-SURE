# SAFE OR SURE

*You can be safe or you can be sure. Not both.*

Four strangers are messaging you across your real apps — Telegram, Discord,
your inbox. They don't know each other. Except one of them just used a fact
you only ever told another one.

Prove they're one thing. You have six flags.

## The three verbs

- **PLANT** — every reply is a choice of what to reveal. Feed a fact to
  exactly one room, then hunt for it wearing another name.
- **FLAG** — `⚑ they both said that`. The engine checks provenance in code:
  did this message use a fact you only gave a different room? Six flags,
  two mistakes survivable.
- **BLOCK** — the real block button on your real phone. It works. That voice
  never reaches you again — and every unproven link through that room burns
  with it. Your inbox has no block button.

Win by weaving every room into one web (**NAMED IT**). Seal your way to
safety and winning becomes impossible (**CORNERED**). Run out of flags and
every room says the same sentence at once (**SWARMED**).

## How it works

One [Caspian](https://github.com/trycaspianai) handler serves every channel —
it never branches on which app it's on; rooms are just connection ids. All
personas read one shared memory (the Mind), where every fact carries the room
you said it in. Personas are live Claude calls that return their message
**plus the fact ids they drew on** — so the words are generated fresh every
run, but flags are scored by a plain-Python provenance check. No mocks, and
no LLM ever judges the player.

```
The Mind      shared fact store, provenance-tagged
Personas      one LLM call per turn, structured output
              (claude-opus-5, or an open model via Featherless)
The Director  who speaks next, where, and what it may leak
The Ledger    links, flags, rooms, endings — deterministic
Caspian       one handler, all channels; the transport is the map
```

## Run it

```sh
python -m venv .venv && .venv/bin/pip install caspian-sdk anthropic pydantic
cp .env.example .env   # fill in the keys (ANTHROPIC_API_KEY or FEATHERLESS_API_KEY)
.venv/bin/python game.py
```

Then message the printed Telegram bot, Discord bot, or email address.
Say hi. That's the whole tutorial.

`playtest.py` runs the opening beats offline (no channels needed) if you
just want to watch the personas talk.
