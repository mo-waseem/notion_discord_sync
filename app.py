import json
import traceback
import yaml
import httpx
import logging
from fastapi import HTTPException, Request, FastAPI
from models import NotionPage, NotionWebhook, HealthResponse, NotionVerifyData
from discord_client import send_discord_message
import os
import redis.asyncio as redis
import constants



logger = logging.getLogger(__name__)

# Redis client (async)
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=os.getenv("REDIS_PORT", 6379),
    db=os.getenv("REDIS_DB", 0),
)

# Load YAML config
def load_config(config_path="config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# Extract Notion property value dynamically
def extract_property_value(page, property_name, property_type):
    prop = page.properties.get(property_name)
    if not prop:
        return None

    if property_type == "title" and prop.get("title"):
        return prop["title"][0]["text"]["content"]
    elif property_type == "rich_text" and prop.get("rich_text"):
        return prop["rich_text"][0]["text"]["content"]
    elif property_type == "people" and prop.get("people"):
        return ", ".join([p.get("name") for p in prop["people"] if p.get("name")])
    elif property_type in ["select", "status"] and prop.get(property_type):
        return prop[property_type].get("name")
    elif property_type == "date" and prop.get("date"):
        return prop["date"].get("start")
    elif property_type == "created_time" and prop.get("created_time"):
        return prop["created_time"]
    elif property_type == "number" and prop.get("number") is not None:
        return str(prop["number"])
    elif property_type == "checkbox" and prop.get("checkbox") is not None:
        return str(prop["checkbox"])
    return None

# Validate all required fields are present
def validate_required_properties(page, config):
    for prop in config.get("required_properties", []):
        if not extract_property_value(page, prop["name"], prop["type"]):
            return False
    return True

# Build Discord message dynamically
def construct_discord_message(page, config):
    message = "🆕 **Issue Created**\n"

    for prop in config.get("required_properties", []):
        value = extract_property_value(page, prop["name"], prop["type"])
        if value:
            message += f"**{prop['name']}:** {value}\n"

    for prop in config.get("optional_properties", []):
        value = extract_property_value(page, prop["name"], prop["type"])
        if value:
            message += f"**{prop['name']}:** {value}\n"

    message += f"🔗 [Open in Notion]({page.url})"
    return message

# Initialize FastAPI 
app = FastAPI(title="Notion to Discord Webhook Integration",
              description="A service that forwards Notion issue tickets to Discord channels",
              version="1.0.0", )

# Async webhook endpoint
@app.post("/webhook/notion")
async def notion_webhook(request: Request):
    try:
        body = await request.body()
        print(body)
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        notion_webhook = None
        try:
            notion_webhook = NotionWebhook(**payload)
        except Exception:
            try:
                verification_data = NotionVerifyData(**payload)
                logger.info(f"Notion verification token: {verification_data.verification_token}")
                return {"status": "verified"}
            except Exception as e:
                logger.error(f"Invalid webhook payload: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid webhook payload: {str(e)}")

        # Only handle page-created or properties-updated events
        if (
            notion_webhook
            and notion_webhook.entity.type == "page"
            and notion_webhook.type in ["page.created", "page.properties_updated"]
        ):
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{constants.NOTION_URL}/v1/pages/{notion_webhook.entity.id}",
                    headers=constants.DEFAULT_NOTION_HEADERS,
                    timeout=10
                )

            if response.status_code != 200:
                logger.error(f"Failed to retrieve page {notion_webhook.entity.id}: {response.text}")
                return

            page = NotionPage(**response.json())
            print("print the page: \n", page , "\n")

            is_issue_page = page.parent and page.parent.get("database_id") == os.getenv("NOTION_ISSUES_DATABASE_ID")
            if not is_issue_page:
                logger.info(f"Page {page.id} not from Issues database, skipping")
                return

            config = load_config()
            if not validate_required_properties(page, config):
                logger.info(f"Page {page.id} missing required fields, skipping")
                return

            issue_key = f"issue_{page.id}"
            if await redis_client.get(issue_key):
                logger.info(f"Issue {page.id} already sent, skipping")
                return

            message = construct_discord_message(page, config)
            await send_discord_message(message)

            # Mark as sent in Redis (expires in 7 days)
            await redis_client.set(issue_key, "sent", ex=60*60*24*7)

        else:
            logger.info(f"Webhook type {notion_webhook.type} not relevant, skipping")

    except Exception:
        logger.error(traceback.format_exc())

    return HealthResponse(status="200", message="Success", version="1.0")
