"""Read-only Gmail ingestion: turns Gmail API messages into ``InboundEmail`` objects."""

import base64
from datetime import datetime
from email.utils import parseaddr, parsedate_to_datetime

from email_crm.models import InboundEmail


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")


def _extract_text(payload: dict) -> str:
    """Return the first text/plain body found in a (possibly multipart) payload."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return _decode(payload["body"]["data"])
    for part in payload.get("parts", []) or []:
        text = _extract_text(part)
        if text:
            return text
    return ""


def message_to_inbound(message: dict) -> InboundEmail:
    """Convert a Gmail API ``users.messages.get(format='full')`` response."""
    payload = message.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    name, address = parseaddr(headers.get("from", ""))
    try:
        received = parsedate_to_datetime(headers["date"]).replace(tzinfo=None)
    except (KeyError, TypeError, ValueError):
        received = datetime.now()
    body = _extract_text(payload) or message.get("snippet", "")
    return InboundEmail(
        message_id=message["id"],
        sender_name=name,
        sender_email=address,
        subject=headers.get("subject", "(no subject)"),
        body_text=body,
        received_at=received,
    )


def fetch_gmail_messages(service, query: str = "in:inbox", max_results: int = 20) -> list[InboundEmail]:
    """Fetch messages matching ``query``. Uses read-only API calls only."""
    listing = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    emails = []
    for ref in listing.get("messages", []):
        full = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
        emails.append(message_to_inbound(full))
    return emails
