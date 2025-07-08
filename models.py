from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class Entity(BaseModel):
    id: str
    type: str
    
class NotionWebhook(BaseModel):
    """Model for Notion webhook payload"""
    id: str = Field(..., description="Webhook event ID")
    timestamp: str = Field(..., description="Timestamp when the event occurred")
    workspace_id: str = Field(..., description="Notion workspace ID")
    workspace_name: str = Field(..., description="Notion workspace name")
    subscription_id: str = Field(..., description="Webhook subscription ID")
    integration_id: str = Field(..., description="Integration ID")
    authors: List[Dict[str, Any]] = Field(..., description="List of authors who triggered the event")
    attempt_number: int = Field(..., description="Attempt number for webhook delivery")
    type: str = Field(..., description="Event type (e.g., 'comment.created', 'page.created')")
    entity: Entity = Field(..., description="The entity that triggered the event")
    data: Dict[str, Any] = Field(..., description="Additional event data")
    
    class Config:
        extra = "allow"

class NotionVerifyData(BaseModel):
    verification_token: str


class HealthResponse(BaseModel):
    """Model for health check response"""
    status: str = Field(..., description="Health status")
    message: str = Field(..., description="Health message")
    version: str = Field(..., description="Service version")


class User(BaseModel):
    object: str
    id: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    type: Optional[str] = None
    person: Optional[Dict] = None


class SelectOption(BaseModel):
    id: str
    name: str
    color: str


class TextContent(BaseModel):
    content: str
    link: Optional[str] = None


class Annotations(BaseModel):
    bold: bool
    italic: bool
    strikethrough: bool
    underline: bool
    code: bool
    color: str


class TitleText(BaseModel):
    type: str
    text: TextContent
    annotations: Annotations
    plain_text: str
    href: Optional[str] = None


class NotionPage(BaseModel):
    object: str
    id: str
    created_time: datetime
    last_edited_time: datetime
    created_by: User
    last_edited_by: User
    cover: Optional[Any] = None
    icon: Optional[Dict] = None
    parent: Dict[str, str]
    archived: bool
    in_trash: bool
    properties: Dict[str, Dict] = Field(description="Properties as a dictionary")
    url: str
    public_url: Optional[str] = None
    developer_survey: Optional[Any] = None
    request_id: str 