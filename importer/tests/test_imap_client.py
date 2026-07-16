"""Tests for MIME parsing of a raw fetched message into a RawEmail, and for
ImapMailbox.connect()'s error handling (login/folder-select failures)."""

from __future__ import annotations

from email.message import EmailMessage

import pytest
from imapclient.exceptions import IMAPClientError
from importer import imap_client as imap_client_module
from importer.imap_client import ImapConnectionError, ImapMailbox, MailboxConfig, parse_raw_message


class FakeIMAPClient:
    """Stands in for imapclient.IMAPClient - only the methods ImapMailbox
    calls during connect() are implemented."""

    def __init__(self, host, port=None, ssl=True):
        self.login_error: Exception | None = None
        self.select_error: Exception | None = None
        self.folders: list[tuple] = []

    def login(self, username, password):
        if self.login_error:
            raise self.login_error

    def oauth2_login(self, username, access_token):
        if self.login_error:
            raise self.login_error

    def select_folder(self, folder):
        if self.select_error:
            raise self.select_error

    def list_folders(self):
        return self.folders


def _config(**overrides) -> MailboxConfig:
    fields = {"host": "imap.example.com", "username": "me@example.com", "password": "secret"}
    fields.update(overrides)
    return MailboxConfig(**fields)


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


def test_connect_succeeds_with_no_errors(monkeypatch):
    fake = FakeIMAPClient(None)
    monkeypatch.setattr(imap_client_module, "IMAPClient", lambda *a, **kw: fake)

    ImapMailbox(_config()).connect()  # should not raise


def test_connect_wraps_login_error(monkeypatch):
    fake = FakeIMAPClient(None)
    fake.login_error = IMAPClientError("bad credentials")
    monkeypatch.setattr(imap_client_module, "IMAPClient", lambda *a, **kw: fake)

    with pytest.raises(ImapConnectionError, match="IMAP login failed"):
        ImapMailbox(_config()).connect()


def test_connect_wraps_folder_not_found_and_lists_available_folders(monkeypatch):
    fake = FakeIMAPClient(None)
    fake.select_error = IMAPClientError("select failed")
    fake.folders = [(None, b"/", "INBOX"), (None, b"/", "[Gmail]/All Mail")]
    monkeypatch.setattr(imap_client_module, "IMAPClient", lambda *a, **kw: fake)

    with pytest.raises(ImapConnectionError) as exc_info:
        ImapMailbox(_config(folder="Nonexistent")).connect()

    message = str(exc_info.value)
    assert "Nonexistent" in message
    assert "INBOX" in message
    assert "[Gmail]/All Mail" in message


def test_connect_folder_error_survives_broken_list_folders(monkeypatch):
    """If listing folders itself fails, still report the original error
    (with an empty "Available folders:" list) rather than crashing."""

    class BrokenListFolders(FakeIMAPClient):
        def list_folders(self):
            raise IMAPClientError("LIST not permitted")

    fake = BrokenListFolders(None)
    fake.select_error = IMAPClientError("select failed")
    monkeypatch.setattr(imap_client_module, "IMAPClient", lambda *a, **kw: fake)

    with pytest.raises(ImapConnectionError, match="Nonexistent"):
        ImapMailbox(_config(folder="Nonexistent")).connect()
