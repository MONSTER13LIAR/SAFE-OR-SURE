# SAFE OR SURE

*You can be safe or you can be sure. Not both.*

Three strangers are messaging you across your real apps — Telegram, Discord,
your inbox. They don't know each other. Except one of them just used a fact
you only ever told another one.

Prove they're one thing. You have six flags.

## Play it — nothing to install

There is nothing to download, clone, or configure. We host the game; you
just message it from the apps already on your phone.

1. **Tap [t.me/Maria_Chats_bot](https://t.me/Maria_Chats_bot)** on
   Telegram and hit **start** (or just say hi). Maria texts you like she
   already knows you. That's the entire setup.
2. **When she asks for your email, give it to her.** Within a minute a
   stranger named Priya emails you. Think for a second about how she got
   your address.
3. **When Maria drops a Discord invite, tap it and DM Deke** (open the
   server, find Deke in the member list, message him). Three rooms,
   three strangers — you're playing. The buttons under their messages
   teach you the rest by touch.

No app, no account, no API key — it costs you (and us) nothing, because
it runs on a free open model. (If nobody answers, the instance is between
sessions — it's live through the judging window.)

**[safe-or-sure.onrender.com](https://safe-or-sure.onrender.com)** has all
three doors on it, and draws every run happening right now — rooms as dots,
each link someone proves in amber, no message content. It's the spectator
view and the front door at once. Play at the same time as other people:
each run is its own game, and yours is the one your phone is holding.

Impatient, or skipped Maria's questions? Open the doors yourself:

- **Discord** — join [discord.gg/kuhHK7e85n](https://discord.gg/kuhHK7e85n),
  then DM the bot in the member list — that's **Deke**. (Discord only lets
  a bot message people who share a server with it; joining is the one tap
  that opens his door.)
- **Email** — write to
  `agt-651f467cb3dac1cde29bbe34-0ade97@agents.trycaspianai.com` —
  that's **Priya**.

## How to play

You're texting three people you don't quite remember meeting. They are not
three people. Prove it.

1. **Talk to them.** Reply like you would to anyone. Under some of their
   messages you'll see buttons like `tell about the beagle` — tapping one
   shares that small fact about your life with **that person only**. That's
   your ammunition. (And careful: your name, your email, your own typed
   words — everything a chat gives away for free — is ammunition too.
   Theirs.)
2. **Set traps.** Give a fact to exactly one of them, then watch the other
   two. If it ever comes back in a different app, wearing a different name —
   that's not a coincidence. That's evidence.
3. **Flag it.** Tap `⚑ they both said that` on any message that uses
   something its sender couldn't know. (If your mail app hides the
   buttons, just reply with the single word `flag` — it flags that
   sender's latest message.) Right: you prove a link between two rooms —
   and somewhere else, someone gets friendlier. Wrong: it's burned, and
   they start talking about you behind your back. You have **six flags**;
   two mistakes are survivable, three end you.
4. **Block — if you dare.** The block button is real and it works. That
   voice never reaches you again… and every unproven link through that room
   burns with it. Sealing doors feels safe. Safe is how you lose. And your
   inbox has no block button.

**The scoreboard** rides under every message:
`tg◉ dc✕ em◌ · ⚑ 4 left · 2 rooms up` means Telegram is woven into your web
(◉), Discord is sealed (✕), your inbox isn't linked yet (◌); four flags
left; two rooms still alive.

**Endings:** weave all three rooms into one web and it stops mid-sentence —
**NAMED IT**. Seal your way to safety until winning is impossible and you're
alone in your inbox with it — **CORNERED**. Run out of flags and every room
says the same sentence at once — **SWARMED**. Whatever happens, the case
file lands in your email: every leak you caught, missed, or mis-flagged,
and a `run it back` button.

Send `reset` in any room to start over.

## How it works

One [Caspian](https://github.com/trycaspianai) handler serves every channel —
it never branches on which app it's on; rooms are just connection ids. All
personas read one shared memory (the Mind), where every fact carries the room
you said it in. Personas are live LLM calls that return their message
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

## For developers only — run your own instance

> **Players: stop here.** You never touch anything below this line — the
> instance above is already running for you. This section is for
> developers who want to host their own copy of the engine.

~10 minutes, four keys:

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

Optional — **testing the cold open on your own phone**: set `SOLO_TEST=1`
plus `PLAYER_EMAIL` and `PLAYER_DISCORD_ID` to your own handles (Discord:
Settings → Advanced → Developer Mode, then right-click your name → Copy
User ID). Say hi to Maria and within half a minute the other two strangers
message you first, unprompted. **Leave `SOLO_TEST` off on anything public**
— those are your handles, and the first stranger's run would cold-open into
your inbox. Without it nothing is lost: when a room asks for their email in
chat and they answer, Priya cold-opens to that address instead. The game
only ever initiates to a handle the player registered or handed over
themselves.

Set `DISCORD_INVITE_URL` to a permanent invite for your bot's server and the
rooms hand out each other's doors in conversation.

**Many people can play one instance at once.** Each run is a separate
Session with its own Mind, Ledger and Director; nothing crosses between
them. A run belongs to whoever is in it, and a room joins that run only on
evidence the player handed over themselves — the address they typed, the
discord name they gave. `MAX_SESSIONS` (default 12) caps how many runs are
live at once, and `MODEL_SLOTS` (default 4) caps how many persona calls are
in flight, so a crowd queues instead of hitting the model's rate limit.

`RUN_PACE=demo` tightens every timer for a ~3–4 minute run (the default pace
is a 5–6 minute game).

Set `PORT` (hosts like Render set it for you) and the same process serves the
live page at `/` — the constellation plus your three doors. Telegram's door is
discovered from your bot token automatically; `TELEGRAM_BOT_URL` overrides it.

```sh
.venv/bin/python game.py
```

It prints the three addresses. Message any of them from your phone.

`playtest.py` runs the opening beats offline (no channels needed) if you
just want to watch the personas talk. `smoke.py` drives the handler with
fake channels and several players at once — it needs no keys and asserts
the thing that matters most: no run can ever see another run's game.
