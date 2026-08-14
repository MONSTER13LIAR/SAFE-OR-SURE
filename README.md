# SAFE OR SURE

*You can be safe or you can be sure. Not both.*

Three strangers are messaging you across your real apps — Telegram, Discord,
your inbox. They don't know each other. Except one of them just used a fact
you only ever told another one.

**The whole game in five lines:**

> Three people message you on three different apps.
> They are one thing.
> Tell them things — each fact goes to one of them only.
> When one knows something you told somebody else, tap `⚑`.
> Catch it, and it comes back better at hiding.

Ten levels. Level 1 gives you six flags, no clock at all, and a leak so obvious
it's almost a favour. By level 5 it buries the slip mid-sentence and stops
forgiving your mistakes. By level 8 you have two flags and two and a half
minutes, and most of what sounds like a leak is bait.

**Level 10 cannot be won.** On the last rung it doesn't slip — not once —
and the only thing left to do is last. Getting there is the score.

## Play it — nothing to install

There is nothing to download, clone, or configure. We host the game; you
just message it from the apps already on your phone.

1. **Say hi to Maria on Telegram** —
   [t.me/Maria_Chats_bot](https://t.me/Maria_Chats_bot), hit **start**.
   The rules and your level-1 card arrive in two messages, then she texts
   you like she already knows you. That's the entire setup.
2. **Open a second door — that's the whole of level 1.** One room on its
   own can't leak anything, so nothing is catchable until a second
   stranger is talking to you. Maria hands you the door in the first
   minute: tap her Discord invite, DM **Deke**, and say the three-character
   word she gave you so he knows it's you. Within about ten seconds of
   that, he knows something you only ever told her. That's the game.
3. **Level 2 wants all three.** When she asks for your email, give it to
   her — within a minute **Priya** emails you. Think for a second about
   how she got your address.
4. **Play.** Tap `tell about the beagle`-style buttons to feed a fact to
   one person, then watch the other two for it. `⚑ they both said that`
   appears under their messages as soon as two rooms are open.

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
   something its sender couldn't know. (The button shows up once two rooms
   are open — before that no message can be a link. **Email has no buttons
   at all** — mail clients strip them — so in your inbox you reply with the
   word `flag`, or with a fact's name like `beagle` to tell Priya about it.
   Every email from her spells out the moves you have.) Right: you prove a
   link between two rooms — and somewhere else, someone gets friendlier.
   Wrong: it's burned, they start talking about you behind your back, and
   from level 2 it costs you seconds as well. Your flag budget shrinks as
   you climb — six on level 1, two by level 8 — and the free first mistake
   is gone from level 5.
4. **Block — if you dare.** The block button is real and it works. That
   voice never reaches you again… and every unproven link through that room
   burns with it. Sealing doors feels safe. Safe is how you lose. And your
   inbox has no block button.

**The scoreboard** rides under every message:
`L4 · tg◉ dc✕ em◌ · ⚑3 · 1 link · 2:14` means level 4; Telegram is woven
into your web (◉), Discord is sealed (✕), your inbox isn't linked yet (◌);
three flags left; one more link finishes the level; two minutes fourteen
on the clock.

**Ten levels.** Naming it doesn't end the run — it promotes you. Fewer
flags, less time, and a leak that goes from *almost a quote* to *a detail
from around the fact, never the fact*. From level 3 it starts talking
about things out of its own life that sound exactly like something you
told somebody — most of what looks like a leak on level 8 is bait. From
level 5 the free first mistake is gone.

| | flags | to prove | clock | it leaks by |
|---|---|---|---|---|
| **1** | 6 | 1 link | none | saying it almost word for word |
| **3** | 5 | 2 links | 4:30 | paraphrasing |
| **5** | 4 | 2 links | 3:30 | burying it mid-sentence |
| **8** | 2 | 2 links | 2:30 | using a detail from *around* it |
| **10** | 2 | 2 links | 1:50 | **it doesn't** |

**Endings.** Prove the level's links and it stops mid-sentence, all of
them at once — **NAMED IT**, and it comes back. Seal your way to safety
until winning is impossible — **CORNERED**. Run out of flags — **SWARMED**.
Run out of clock — **OUTRUN**. Outlast level 10, which never slips —
**TEN**, the highest thing anybody gets. Whatever happens, the case file
lands in your email: how far you climbed, every leak you caught, missed or
mis-flagged, and a `run it back` button.

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
The Ledger    links, flags, the level clock, endings — deterministic
The Ladder    ten rows of numbers; the only place difficulty lives
Caspian       one handler, all channels; the transport is the map
```

**How the difficulty is actually implemented** (`levels.py`): every level
is one frozen row — flag budget, links required, seconds, leak delay, leak
density, decoy odds, what a mistake costs, and one sentence of stage
direction that is handed straight to the persona (*"bury it in the middle
of a sentence about something else"*). The Director and the Ledger hold no
numbers of their own; they ask the level. So the thing that gets better at
hiding is a table you can read, and the leak is still a real LLM call that
returns a real receipt.

**Decoys are provably fair.** When a level fakes a leak, the persona is
told about a fact *the player has never given anyone* and asked to talk
about its own version of it. The fact's id is never shown to the model, so
it cannot appear in `facts_used`, so the Ledger scores a flag on it as
noise by construction — not by judgement. Level 10 is the same mechanism
turned all the way up: it spends the whole level knowing everything you
gave away on the way up, and never once leaves a receipt for any of it.
That is why it cannot be won.

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
Session with its own Mind, Ledger, Director and ladder position; nothing
crosses between them. A run belongs to whoever is in it, and a room joins
that run only on evidence the player handed over themselves — the address
they typed, the discord name they gave, or the run's three-character code,
which every handed-over door carries (*"say K7F to him or he wont know its
you"*). Matching is exact: a stranger called `samantha` never lands in the
run of a player who said `sam`. A room binds to one thread, once, so a
player who also posts in a public channel never drags their private game
into it. `MAX_SESSIONS` (default 12) caps how many runs are live at once,
and `MODEL_SLOTS` (default 4) caps how many persona calls are in flight,
so a crowd queues instead of hitting the model's rate limit.

`RUN_PACE=demo` tightens every timer for a ~3–4 minute run (the default pace
is a 5–6 minute game).

Set `PORT` (hosts like Render set it for you) and the same process serves the
live page at `/` — the constellation plus your three doors. Telegram's door is
discovered from your bot token automatically; `TELEGRAM_BOT_URL` overrides it.

```sh
.venv/bin/python game.py
```

It prints the three addresses. Message any of them from your phone.

`playtest.py` walks the ladder offline with real persona calls and no
channels — the same leak on levels 1, 5 and 9, a decoy, and level 10 — so
you can read whether the difficulty curve actually reads as one.

`smoke.py` drives the real handler with fake channels and a stubbed
persona engine, no keys and no network. **118 checks**, and they cover the
two promises this thing makes: several strangers play one instance and
never touch each other's run, and the ladder cannot be climbed except by
playing it — no free links from wrong flags, no re-tapping a spent offer,
no dodging a losing level with `reset`, and a level 10 that provably never
hands out a receipt.

```sh
.venv/bin/python smoke.py     # 118/118, ~50s, no keys needed
```
