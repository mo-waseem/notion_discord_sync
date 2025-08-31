import os
import logging
from discord import SyncWebhook
import asyncio
logger = logging.getLogger(__name__)

DISCORD_LIVE_ISSUES_WEBHOOK_URL = os.getenv("DISCORD_LIVE_ISSUES_WEBHOOK_URL")

async def send_discord_message(content: str):
    if not DISCORD_LIVE_ISSUES_WEBHOOK_URL:
        logger.warning("Discord webhook URL is not set. Message not sent.")
        return

    def send_sync():
        try:
            webhook = SyncWebhook.from_url(DISCORD_LIVE_ISSUES_WEBHOOK_URL)
            webhook.send(content)
            logger.info("Discord message sent successfully")
        except Exception as e:
            logger.error(f"Failed to send Discord message: {str(e)}")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_sync)
