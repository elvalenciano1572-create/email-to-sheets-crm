from email_crm.models import InboundEmail


def get_sample_inbox() -> list[InboundEmail]:
    """Deterministic sample inbox for demonstrations, offline testing and CI."""
    return [
        InboundEmail(
            message_id="msg-101",
            sender_name="Sarah Jenkins",
            sender_email="sarah.j@acme-corp.com",
            subject="Looking for Python API integration for our CRM system",
            body_text=(
                "Hello, We need an experienced Python developer to integrate our internal database "
                "with the Stripe and HubSpot APIs. Our estimated budget is around $3,500. "
                "You can reach me at +1 555-0199. Thanks!"
            ),
        ),
        InboundEmail(
            message_id="msg-102",
            sender_name="David Miller",
            sender_email="dmiller@fintech-ventures.io",
            subject="URGENT: Trading system feed latency issue",
            body_text=(
                "Hi Ruben, We are experiencing higher latency on our data ingest script. "
                "This is an emergency as markets open tomorrow. Please call my mobile at +44 20 7946 0912."
            ),
        ),
        InboundEmail(
            message_id="msg-103",
            sender_name="Spam Bot",
            sender_email="win@crypto-fortune-rewards.xyz",
            subject="Claim your $50,000 crypto profit bonus now",
            body_text=(
                "Dear friend, Click this link to withdraw your free casino and crypto rewards immediately."
            ),
        ),
    ]
