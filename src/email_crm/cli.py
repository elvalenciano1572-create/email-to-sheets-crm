import argparse
import sys
from pathlib import Path

from email_crm.export import export_leads_to_csv
from email_crm.extractor import classify_inbound_email
from email_crm.inbox import get_sample_inbox
from email_crm.models import LeadPriority


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Autonomous email inbox to spreadsheet CRM pipeline."
    )
    parser.add_argument(
        "--output",
        "-o",
        default="leads_crm.csv",
        help="Target output CSV file path (default: leads_crm.csv)",
    )
    parser.add_argument(
        "--filter-spam",
        action="store_true",
        default=True,
        help="Exclude spam/irrelevant inquiries from CRM export",
    )
    args = parser.parse_args(argv)

    print("=" * 65)
    print("   EMAIL-TO-SHEETS CRM: INBOX INGESTION & PIPELINE ENGINE")
    print("=" * 65)

    inbox = get_sample_inbox()
    print(f"[*] Fetched {len(inbox)} inbound email messages.")

    parsed_leads = [classify_inbound_email(m) for m in inbox]

    if args.filter_spam:
        valid_leads = [
            lead for lead in parsed_leads if lead.priority != LeadPriority.SPAM
        ]
        filtered_count = len(parsed_leads) - len(valid_leads)
        print(f"[*] Filtered {filtered_count} spam/irrelevant emails.")
    else:
        valid_leads = parsed_leads

    print("\n[Parsed Leads Overview]:")
    for lead in valid_leads:
        print(f"  + [{lead.priority.value}] {lead.client_name} ({lead.client_email})")
        print(f"    Category: {lead.category.value} | Budget: {lead.estimated_budget or 'N/A'}")
        print(f"    Phone: {lead.client_phone or 'N/A'} | Action: {lead.action_item}")

    target_path = Path(args.output)
    count = export_leads_to_csv(valid_leads, target_path)
    print(f"\n[OK] Successfully synchronized {count} leads to: {target_path.resolve()}")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
