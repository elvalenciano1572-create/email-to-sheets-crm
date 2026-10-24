"""Append parsed leads to a Google Sheet, skipping message IDs that are already present."""

from email_crm.export import HEADERS, lead_to_row
from email_crm.models import ParsedLead


def append_leads_to_sheet(service, spreadsheet_id: str, leads: list[ParsedLead], tab: str = "Leads") -> int:
    """Append new leads and return how many rows were written.

    Writes the header row if the tab is empty. Values are sent as ``RAW`` so email content
    can never be interpreted as a spreadsheet formula.
    """
    values = service.spreadsheets().values()
    existing = values.get(spreadsheetId=spreadsheet_id, range=f"{tab}!A:A").execute().get("values", [])
    known_ids = {row[0] for row in existing if row}

    rows = []
    if not existing:
        rows.append(HEADERS)
    new_leads = [lead for lead in leads if lead.message_id not in known_ids]
    rows.extend(lead_to_row(lead) for lead in new_leads)

    if not new_leads:
        return 0

    values.append(
        spreadsheetId=spreadsheet_id,
        range=f"{tab}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()
    return len(new_leads)
