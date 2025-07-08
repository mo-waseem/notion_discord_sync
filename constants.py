import os

NOTION_URL = "https://api.notion.com"
DEFAULT_NOTION_HEADERS = {
    "Notion-Version": "2022-06-28",
    "Authorization": f'Bearer {os.getenv("NOTION_WEBHOOK_SECRET")}',
}
DISCORD_URL = "https://discord.com/api/v10"