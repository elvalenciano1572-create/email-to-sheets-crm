import base64

from email_crm.extractor import classify_inbound_email
from email_crm.gmail_source import fetch_gmail_messages, message_to_inbound
from email_crm.sheets_export import append_leads_to_sheet


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def _gmail_message(msg_id="m1", body="Need a quote for an automation project, budget $5k. Call +1 555-0199"):
    return {
        "id": msg_id,
        "snippet": "snippet",
        "payload": {
            "mimeType": "multipart/alternative",
            "headers": [
                {"name": "From", "value": "Sarah Lee <sarah@acme.com>"},
                {"name": "Subject", "value": "Project quote"},
                {"name": "Date", "value": "Mon, 20 Oct 2026 10:00:00 +0000"},
            ],
            "parts": [
                {"mimeType": "text/html", "body": {"data": _b64("<p>html</p>")}},
                {"mimeType": "text/plain", "body": {"data": _b64(body)}},
            ],
        },
    }


class FakeGmailService:
    def __init__(self, messages):
        self.store = {m["id"]: m for m in messages}
        self.calls = []

    def users(self):
        return self

    def messages(self):
        return self

    def list(self, **kwargs):
        self.calls.append(("list", kwargs))
        return _Exec({"messages": [{"id": i} for i in self.store]})

    def get(self, **kwargs):
        self.calls.append(("get", kwargs))
        return _Exec(self.store[kwargs["id"]])


class _Exec:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


def test_message_to_inbound_parses_headers_and_plain_body():
    email = message_to_inbound(_gmail_message())
    assert email.sender_name == "Sarah Lee"
    assert email.sender_email == "sarah@acme.com"
    assert email.subject == "Project quote"
    assert "budget $5k" in email.body_text


def test_fetch_is_read_only_and_feeds_the_classifier():
    service = FakeGmailService([_gmail_message("a"), _gmail_message("b")])
    emails = fetch_gmail_messages(service, "in:inbox", 5)
    assert [e.message_id for e in emails] == ["a", "b"]
    assert {name for name, _ in service.calls} == {"list", "get"}
    lead = classify_inbound_email(emails[0])
    assert lead.client_phone == "+1 555-0199"
    assert lead.estimated_budget == "$5k"


class FakeSheets:
    def __init__(self, existing_ids):
        self.column = [["Message ID"], *[[i] for i in existing_ids]] if existing_ids else []
        self.appended = None

    def spreadsheets(self):
        return self

    def values(self):
        return self

    def get(self, **kwargs):
        return _Exec({"values": self.column} if self.column else {})

    def append(self, **kwargs):
        self.appended = kwargs
        return _Exec({})


def test_sheet_append_writes_header_on_empty_tab_and_uses_raw():
    lead = classify_inbound_email(message_to_inbound(_gmail_message("x")))
    sheet = FakeSheets(existing_ids=[])
    assert append_leads_to_sheet(sheet, "sheet1", [lead]) == 1
    rows = sheet.appended["body"]["values"]
    assert rows[0][0] == "Message ID" and rows[1][0] == "x"
    assert sheet.appended["valueInputOption"] == "RAW"


def test_sheet_append_skips_duplicates():
    lead = classify_inbound_email(message_to_inbound(_gmail_message("dup")))
    sheet = FakeSheets(existing_ids=["dup"])
    assert append_leads_to_sheet(sheet, "sheet1", [lead]) == 0
    assert sheet.appended is None


def test_cli_reports_missing_token_cleanly(monkeypatch, capsys):
    from email_crm.cli import main

    monkeypatch.delenv('GOOGLE_TOKEN_FILE', raising=False)
    assert main(['--source', 'gmail']) == 2
    assert 'No token file given' in capsys.readouterr().err
