import argparse
import sys
from pathlib import Path

from email_crm.export import export_leads_to_csv
from email_crm.extractor import classify_inbound_email
from email_crm.google_auth import GoogleAuthError
from email_crm.inbox import get_sample_inbox
from email_crm.models import LeadPriority


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Autonomous email inbox to spreadsheet CRM pipeline."
    )
    parser.add_argument(
        "--source",
        choices=["sample", "gmail"],
        default="sample",
        help="Where to read emails from: built-in sample inbox or Gmail API (read-only)",
    )
    parser.add_argument("--gmail-query", default="in:inbox", help="Gmail search query (default: in:inbox)")
    parser.add_argument("--max-emails", type=int, default=20, help="Max emails to fetch from Gmail")
    parser.add_argument(
        "--token-file",
        default=None,
        help="Google OAuth token JSON (or set GOOGLE_TOKEN_FILE). Never commit this file.",
    )
    parser.add_argument("--sheet-id", default=None, help="Append leads to this Google Sheet instead of CSV")
    parser.add_argument("--sheet-tab", default="Leads", help="Sheet tab name (default: Leads)")
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
    return parser


def _load_inbox(args):
    if args.source == "gmail":
        from email_crm.gmail_source import fetch_gmail_messages
        from email_crm.google_auth import build_service

        service = build_service("gmail", "v1", args.token_file)
        return fetch_gmail_messages(service, args.gmail_query, args.max_emails)
    return get_sample_inbox()


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    print("=" * 65)
    print("   EMAIL-TO-SHEETS CRM: INBOX INGESTION & PIPELINE ENGINE")
    print("=" * 65)

    try:
        inbox = _load_inbox(args)
    except GoogleAuthError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    print(f"[*] Fetched {len(inbox)} inbound email messages ({args.source}).")

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

    if args.sheet_id:
        from email_crm.google_auth import build_service
        from email_crm.sheets_export import append_leads_to_sheet

        sheets = build_service("sheets", "v4", args.token_file)
        written = append_leads_to_sheet(sheets, args.sheet_id, valid_leads, args.sheet_tab)
        skipped = len(valid_leads) - written
        print(
            f"\n[OK] Appended {written} new leads to Google Sheet {args.sheet_id} "
            f"({skipped} already present)."
        )
    else:
        target_path = Path(args.output)
        count = export_leads_to_csv(valid_leads, target_path)
        print(f"\n[OK] Successfully synchronized {count} leads to: {target_path.resolve()}")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
