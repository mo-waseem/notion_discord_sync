import os
import logging
import traceback
import json
from fastapi import FastAPI, Request, HTTPException
import requests
from dotenv import load_dotenv
import redis.asyncio as redis
import constants
from models import NotionPage, NotionWebhook, HealthResponse, NotionVerifyData
from discord_client import send_discord_message

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Notion to Discord Webhook Integration",
    description="A service that forwards Notion issue tickets to Discord channels",
    version="1.0.0",
)

# Connect to Redis server running locally
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=os.getenv("REDIS_PORT", 6379),
    db=os.getenv("REDIS_DB", 0),
    password=os.getenv("REDIS_PASS", None),
    username=os.getenv("REDIS_USER", None)
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with basic service information"""
    return HealthResponse(
        status="healthy",
        message="Notion to Discord Webhook Integration Service",
        version="1.0.0",
    )


@app.post("/webhook/notion")
async def notion_webhook(request: Request):
    """
    Webhook endpoint to receive Notion updates for new issue tickets
    """
    try:
        # Get request body and headers
        body = await request.body()

        # Parse webhook payload
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload received")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        if payload.get("verification_token"):
            try:
                verification_data = NotionVerifyData(**payload)  # noqa
                logger.info(
                    f"Notion webhook subscription key: {verification_data.verification_token}"  # noqa
                )
                return HealthResponse(status="200", message="verification token received", version="1.0")
            except Exception as e:
                logger.error(f"Invalid webhook payload structure: {str(e)}")
                raise HTTPException(
                    status_code=400, detail=f"Invalid webhook payload: {str(e)}"
                )
       
        if not payload.get("id"):
            logger.info(f"Ignoring non-valid events{payload}")
            return HealthResponse(status="200", message="Ignored non-valid event", version="1.0")
        
        # Validate and parse Notion webhook data
        notion_webhook = None
        try:
            notion_webhook = NotionWebhook(**payload)
        except Exception as e:  # noqa
                logger.error(f"Invalid webhook payload structure: {str(e)}")
                raise HTTPException(
                    status_code=400, detail=f"Invalid webhook payload: {str(e)}"
                )

        if (
            notion_webhook
            and notion_webhook.entity.type == "page"
            and notion_webhook.type in ["page.created", "page.properties_updated"]
        ):
            # 1- We need only issues page updates
            # the updates are: create a new page or update it and we need to send that
            # only if all of assigned, priority and name are set.
            page_response = requests.get(
                f"{constants.NOTION_URL}/v1/pages/{notion_webhook.entity.id}",
                headers=constants.DEFAULT_NOTION_HEADERS,
            )
            if page_response.status_code != 200:
                logger.error(
                    f"Error in retreiving the page id: {notion_webhook.entity.id}, error:\n {page_response.content}"
                )
                return

            page_body = page_response.json()
            logger.info(page_body)
            page = NotionPage(**page_body)

            # 2- Send a discord message to the live-issues channel,
            # it will contains the following:
            # - Name
            # - Assignee
            # This will be if:
            # a- page is from Issues database
            # b- required attrs are filled
            # c- we don't send it before to the channel
            is_issue_page = page.parent and page.parent.get("database_id") == os.getenv(
                "NOTION_ISSUES_DATABASE_ID"
            )
            # print(f"is_issue_page: {is_issue_page}")
            required_properties = {"Assignee": False, "Name": False}
            for property_obj_name in page.properties:
                if property_obj_name in required_properties:
                    if property_obj_name == "Assignee":
                        people = page.properties[property_obj_name]["people"]
                        if people and people[0].get("name"):
                            required_properties[property_obj_name] = True
                    elif property_obj_name == "Name":
                        name_object = page.properties[property_obj_name]
                        if (
                            name_object
                            and name_object["title"]
                            and name_object["title"][0]
                            and name_object["title"][0]["text"]
                            and name_object["title"][0]["text"]["content"]
                        ):
                            required_properties[property_obj_name] = True

            # print(f"required_properties: {required_properties}")
            all_required_properties_filled = all(
                [
                    required_properties[property_name]
                    for property_name in required_properties
                ]
            )

            # await redis_client.delete(f"issue_{page.id}")
            issue_sent_before = await redis_client.get(f"issue_{page.id}")
            # print(f"issue_sent_before: {issue_sent_before}")
            if (
                is_issue_page
                and all_required_properties_filled
                and not issue_sent_before
            ):
                # print("discord send")
                msg = (
                    f"🆕 **Issue Created**\n"
                    f"**Name:** {page.properties['Name']['title'][0]['text']['content']}\n"
                    f"**Assigned to:** {page.properties['Assignee']['people'][0]['name']}\n"
                )
                if (
                    page.properties["Priority"]
                    and page.properties["Priority"]["select"]
                    and page.properties["Priority"]["select"]["name"]
                ):
                    priority = page.properties["Priority"]["select"]["name"]
                    msg += f"**Priority:** {priority}\n"

                msg += f"🔗 [Open in Notion]({page.url})"

                await send_discord_message(msg)

                # Mark as sent in Redis
                await redis_client.set(f"issue_{page.id}", "sent")

    except Exception:
        print(traceback.format_exc())

    return HealthResponse(status="200", message="Success", version="1.0")
