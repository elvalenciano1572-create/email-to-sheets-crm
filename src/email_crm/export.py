import csv
from pathlib import Path

from email_crm.models import ParsedLead

HEADERS = [
    "Message ID",
    "Extracted At",
    "Client Name",
    "Client Email",
    "Phone",
    "Category",
    "Priority",
    "Estimated Budget",
    "Subject / Summary",
    "Action Item",
]


def lead_to_row(lead: ParsedLead) -> list[str]:
    return [
        lead.message_id,
        lead.extracted_at.strftime("%Y-%m-%d %H:%M"),
        lead.client_name,
        lead.client_email,
        lead.client_phone or "-",
        lead.category.value,
        lead.priority.value,
        lead.estimated_budget or "Not specified",
        lead.summary,
        lead.action_item,
    ]


def export_leads_to_csv(leads: list[ParsedLead], target_file: Path) -> int:
    """Exports parsed leads cleanly to CSV format."""
    write_header = not target_file.exists() or target_file.stat().st_size == 0

    with open(target_file, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(HEADERS)
        for lead in leads:
            writer.writerow(lead_to_row(lead))

    return len(leads)
