from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LeadPriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SPAM = "SPAM_OR_IRRELEVANT"


class LeadCategory(str, Enum):
    NEW_PROJECT = "New Project Inquiry"
    SUPPORT = "Support / Technical Help"
    BILLING = "Billing / Invoices"
    PARTNERSHIP = "Partnership Proposal"
    GENERAL = "General Inquiry"


class InboundEmail(BaseModel):
    message_id: str
    sender_name: str
    sender_email: str
    subject: str
    body_text: str
    received_at: datetime = Field(default_factory=datetime.now)


class ParsedLead(BaseModel):
    message_id: str
    client_name: str
    client_email: str
    client_phone: str | None = None
    category: LeadCategory
    priority: LeadPriority
    estimated_budget: str | None = None
    summary: str
    extracted_at: datetime = Field(default_factory=datetime.now)
    action_item: str
