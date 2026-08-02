"""The spine: two channels, ONE shared handler, real messages.

Idea-agnostic. Every candidate needs exactly this underneath it.
Run:  .venv/bin/python spine.py
"""

import os

from caspian_sdk import CommClient

client = CommClient()  # reads CASPIAN_API_KEY / CASPIAN_BASE_URL from .env

# --- channels -------------------------------------------------------------
# Idempotent: re-running returns the same inbox, never a duplicate.
email = client.connect_email(username=os.getenv("AGENT_NAME", "kernel"))
print(f"email    {email['address']}")

# Discord. Prefer OUR OWN bot: a player can block *this* identity cleanly,
# which the shared install-bot does not give us. Falls back to one-click.
# NOTE: install_discord() mints a NEW pending connection on every call — only
# call it when we don't already have one, or pending rows pile up.
if bot_token := os.getenv("DISCORD_BOT_TOKEN"):
    dc = client.connect_discord(bot_token=bot_token)
    print(f"discord  {dc.get('id')} (own bot)")
elif conn_id := os.getenv("DISCORD_CONNECTION_ID"):
    dc = client.get_connection(conn_id)
    print(f"discord  {conn_id} status={dc.get('status')}")
else:
    dc = client.install_discord(display_name="Kernel")
    print(f"discord  OPEN ONCE -> {dc.get('authorize_url')}")
    print(f"         then: echo DISCORD_CONNECTION_ID={dc.get('id')} >> .env")

# Telegram, once you have a token from @BotFather:
if token := os.getenv("TELEGRAM_BOT_TOKEN"):
    tg = client.connect_telegram(bot_token=token)
    print(f"telegram {tg.get('id')}")


# --- the one handler ------------------------------------------------------
# Never branches on message.channel. It cannot tell where it is, by design.
@client.on_message
def handle(message):
    sender = message.sender or {}
    who = sender.get("address") or sender.get("username") or sender.get("id") or "?"
    print(f"<- [{message.connection_id}] {who}: {message.text!r}")
    message.reply(f"heard you. (this handler does not know which app you're on)")


print("\nlistening — ctrl-c to stop\n")
client.listen()
