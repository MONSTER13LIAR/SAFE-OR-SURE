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
              (free by default: Qwen3-30B via Featherless, ~3-4s/turn;
               claude-opus-5 takes over automatically if a key is set)
The Director  who speaks next, where, and what it may leak
The Ledger    links, flags, rooms, endings — deterministic
Caspian       one handler, all channels; the transport is the map
```

## Play it (zero setup)

If an instance is running — ours is, through judging — there is nothing to
install and no account to make. Message the Telegram bot, the Discord bot,
or the email address it prints, and say hi. That's the whole tutorial.

The game is **free to run**: it plays on an open model (Qwen3-30B via
Featherless, ~3–4s a turn). No paid API anywhere — not for the judges, not
for the developer, not for the many players a free game realistically gets.

## Host it yourself (~10 minutes, four keys)

```sh
python -m venv .venv && .venv/bin/pip install caspian-sdk
cp .env.example .env
```

Then fill `.env`:

1. `CASPIAN_API_KEY` — sign up at [trycaspianai.com](https://trycaspianai.com)
   and run `caspian init` (it writes the key for you).
2. `TELEGRAM_BOT_TOKEN` — message `@BotFather` on Telegram, `/newbot`,
   paste the token. This bot is Maria.
3. `DISCORD_BOT_TOKEN` — [discord.com/developers](https://discord.com/developers/applications)
   → New Application → Bot → token. Invite the bot to any server you're in —
   Discord only lets it DM people it shares a server with. This bot is Deke.
4. `FEATHERLESS_API_KEY` — any [featherless.ai](https://featherless.ai) key.
   (Or set `ANTHROPIC_API_KEY` instead and the personas run on claude-opus-5.)

Optional but worth it — **the cold open**: set `PLAYER_EMAIL` and
`PLAYER_DISCORD_ID` to your own handles (Discord: Settings → Advanced →
Developer Mode, then right-click your name → Copy User ID). Say hi to Maria
and within half a minute the other two strangers message you first,
unprompted. The game only ever initiates to those pre-registered handles of
yours; leave them empty and every room waits for you instead.

`RUN_PACE=demo` tightens every timer for a ~3–4 minute run (the default pace
is a 5–6 minute game).

```sh
.venv/bin/python game.py
```

It prints the three addresses. Message any of them from your phone.

`playtest.py` runs the opening beats offline (no channels needed) if you
just want to watch the personas talk.
