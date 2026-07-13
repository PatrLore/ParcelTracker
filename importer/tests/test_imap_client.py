"""Tests for MIME parsing of a raw fetched message into a RawEmail."""

from __future__ import annotations

from email.message import EmailMessage

from importer.imap_client import parse_raw_message


def test_parse_raw_message_extracts_fields():
    msg = EmailMessage()
    msg["From"] = "Shop <shop@example.com>"
    msg["Subject"] = "Your order shipped"
    msg["Date"] = "Wed, 01 Jul 2026 10:00:00 +0000"
    msg["Message-ID"] = "<abc123@example.com>"
    msg.set_content("Plain text body with tracking 1Z999AA10123456784")

    raw = parse_raw_message(42, bytes(msg))

    assert raw.uid == 42
    assert raw.sender == "shop@example.com"
    assert raw.subject == "Your order shipped"
    assert "1Z999AA10123456784" in raw.text_body
    assert raw.message_id == "<abc123@example.com>"
    assert raw.received_at.year == 2026


def test_parse_raw_message_collects_attachment_filenames():
    msg = EmailMessage()
    msg["From"] = "Shop <shop@example.com>"
    msg["Subject"] = "Your invoice"
    msg["Message-ID"] = "<with-attachment@example.com>"
    msg.set_content("See attached invoice.")
    msg.add_attachment(
        b"%PDF-1.4 fake", maintype="application", subtype="pdf", filename="invoice.pdf"
    )

    raw = parse_raw_message(7, bytes(msg))

    assert raw.attachments == ["invoice.pdf"]
    assert "See attached invoice." in raw.text_body


def test_parse_raw_message_falls_back_to_now_without_date_header():
    msg = EmailMessage()
    msg["From"] = "shop@example.com"
    msg["Subject"] = "No date header"
    msg["Message-ID"] = "<no-date@example.com>"
    msg.set_content("body")

    raw = parse_raw_message(1, bytes(msg))

    assert raw.received_at is not None
