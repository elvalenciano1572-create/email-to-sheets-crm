from email_crm.cli import main
from email_crm.export import export_leads_to_csv, lead_to_row
from email_crm.extractor import classify_inbound_email, extract_budget, extract_phone
from email_crm.inbox import get_sample_inbox
from email_crm.models import InboundEmail, LeadCategory, LeadPriority


def test_phone_and_budget_extraction():
    sample_text = "Hello, my phone is +1 (555) 234-5678 and our budget is $5,000 EUR."
    phone = extract_phone(sample_text)
    budget = extract_budget(sample_text)
    assert phone is not None
    assert "555" in phone
    assert budget is not None


def test_classify_inbound_emails():
    inbox = get_sample_inbox()
    assert len(inbox) == 3

    # First is a project inquiry
    lead1 = classify_inbound_email(inbox[0])
    assert lead1.category == LeadCategory.NEW_PROJECT
    assert lead1.client_name == "Sarah Jenkins"
    assert lead1.estimated_budget == "$3,500"

    # Second is urgent support
    lead2 = classify_inbound_email(inbox[1])
    assert lead2.category == LeadCategory.SUPPORT
    assert lead2.priority == LeadPriority.HIGH

    # Third is spam
    lead3 = classify_inbound_email(inbox[2])
    assert lead3.priority == LeadPriority.SPAM


def test_csv_export(tmp_path):
    target_csv = tmp_path / "test_leads.csv"
    inbox = get_sample_inbox()
    leads = [classify_inbound_email(m) for m in inbox]

    count = export_leads_to_csv(leads, target_csv)
    assert count == 3
    assert target_csv.exists()

    content = target_csv.read_text(encoding="utf-8")
    assert "Sarah Jenkins" in content
    assert "Message ID" in content

    # Test appending without re-writing headers
    count_append = export_leads_to_csv(leads[:1], target_csv)
    assert count_append == 1
    lines = target_csv.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 5  # Header + 3 + 1


def test_lead_to_row_mapping():
    email = InboundEmail(
        message_id="id-1",
        sender_name="John Doe",
        sender_email="john@doe.com",
        subject="Support question",
        body_text="Need help fixing a bug",
    )
    lead = classify_inbound_email(email)
    row = lead_to_row(lead)
    assert row[0] == "id-1"
    assert row[2] == "John Doe"
    assert row[3] == "john@doe.com"


def test_cli_execution(tmp_path, capsys):
    output_file = tmp_path / "cli_leads.csv"
    exit_code = main(["--output", str(output_file)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "EMAIL-TO-SHEETS CRM" in captured.out
    assert "Successfully synchronized" in captured.out
    assert output_file.exists()
