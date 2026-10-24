import re

from email_crm.models import InboundEmail, LeadCategory, LeadPriority, ParsedLead


def extract_phone(text: str) -> str | None:
    match = re.search(
        r"(\+\d{1,3}[\s.-]?)?(\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}", text
    )
    if match:
        return match.group(0).strip()
    return None


def extract_budget(text: str) -> str | None:
    pattern = (
        r"(\$|€|£)\s?(\d+([,\.]\d+)?[kKmMbB]?)|"
        r"\b(\d+([,\.]\d+)?)\s?(eur|usd|euros|dollars)"
    )
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(0).strip()
    return None


def classify_inbound_email(email: InboundEmail) -> ParsedLead:
    """Extract lead details, intent, and priority from inbound email text."""
    content = f"{email.subject} {email.body_text}".lower()

    # Determine Category
    if any(k in content for k in ["quote", "project", "build", "develop", "hire", "automation", "api"]):
        category = LeadCategory.NEW_PROJECT
    elif any(k in content for k in ["bug", "issue", "error", "broken", "help", "support"]):
        category = LeadCategory.SUPPORT
    elif any(k in content for k in ["invoice", "payment", "bill", "receipt", "charge"]):
        category = LeadCategory.BILLING
    elif any(k in content for k in ["partner", "collaborate", "affiliate"]):
        category = LeadCategory.PARTNERSHIP
    else:
        category = LeadCategory.GENERAL

    # Determine Priority (Spam checks first)
    spam_markers = ["viagra", "casino", "lottery", "crypto profit", "dear friend", "bonus now"]
    if any(k in content for k in spam_markers):
        priority = LeadPriority.SPAM
    elif any(k in content for k in ["urgent", "asap", "emergency", "immediately", "high priority"]):
        priority = LeadPriority.HIGH
    elif category in {LeadCategory.NEW_PROJECT, LeadCategory.BILLING}:
        priority = LeadPriority.MEDIUM
    else:
        priority = LeadPriority.LOW

    budget = extract_budget(email.body_text)
    phone = extract_phone(email.body_text)

    # Clean client name from sender
    client_name = email.sender_name.strip() if email.sender_name else email.sender_email.split("@")[0]

    if category == LeadCategory.NEW_PROJECT:
        action = "Respond with discovery call link"
    else:
        action = "Review and route"

    return ParsedLead(
        message_id=email.message_id,
        client_name=client_name,
        client_email=email.sender_email,
        client_phone=phone,
        category=category,
        priority=priority,
        estimated_budget=budget,
        summary=email.subject,
        action_item=action,
    )
