import os

from discord import SyncWebhook

# Put your webhook URL here
DISCORD_LIVE_ISSUES_WEBHOOK_URL = os.getenv("DISCORD_LIVE_ISSUES_WEBHOOK_URL")

async def send_discord_message(content: str):
    # SyncWebhook is blocking, so run it in a thread
    import asyncio

    def send_sync():
        webhook = SyncWebhook.from_url(DISCORD_LIVE_ISSUES_WEBHOOK_URL)
        webhook.send(content)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_sync)
