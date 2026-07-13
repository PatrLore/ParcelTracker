"""IMAP mailbox client: fetch-since-UID polling and IDLE push notifications.

Wraps the ``imapclient`` library so the rest of the importer never touches
IMAP protocol details directly. Works uniformly across Gmail, Outlook/
Exchange, GMX, WEB.DE, Yahoo, and any other IMAP4rev1 server.
"""

from __future__ import annotations

import email
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from email.message import Message
from email.utils import parseaddr

from imapclient import IMAPClient

from importer.emails import RawEmail

DEFAULT_IDLE_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class MailboxConfig:
    """Connection details for a single IMAP mailbox."""

    host: str
    username: str
    password: str
    port: int = 993
    use_ssl: bool = True
    folder: str = "INBOX"
    use_idle: bool = False
    poll_interval_seconds: int = 300


def _decode_header_value(message: Message, header: str) -> str:
    value = message.get(header, "")
    return str(email.header.make_header(email.header.decode_header(value)))


def _extract_bodies(message: Message) -> tuple[str, str, list[str]]:
    text_body = ""
    html_body = ""
    attachments: list[str] = []

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition") or "")
            filename = part.get_filename()

            if filename and "attachment" in disposition:
                attachments.append(filename)
                continue

            if content_type == "text/plain" and not text_body:
                text_body = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8", errors="replace"
                )
            elif content_type == "text/html" and not html_body:
                html_body = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8", errors="replace"
                )
    else:
        payload = message.get_payload(decode=True) or b""
        decoded = payload.decode(message.get_content_charset() or "utf-8", errors="replace")
        if message.get_content_type() == "text/html":
            html_body = decoded
        else:
            text_body = decoded

    return text_body, html_body, attachments


def parse_raw_message(uid: int, raw_bytes: bytes) -> RawEmail:
    message = email.message_from_bytes(raw_bytes)
    text_body, html_body, attachments = _extract_bodies(message)

    date_header = message.get("Date")
    try:
        received_at = email.utils.parsedate_to_datetime(date_header) if date_header else None
    except (TypeError, ValueError):
        received_at = None
    if received_at is None:
        received_at = datetime.now(UTC)

    return RawEmail(
        uid=uid,
        message_id=message.get("Message-ID", f"<generated-{uid}@parcel-server>").strip(),
        subject=_decode_header_value(message, "Subject"),
        sender=parseaddr(message.get("From", ""))[1],
        received_at=received_at,
        text_body=text_body,
        html_body=html_body,
        attachments=attachments,
    )


class ImapMailbox:
    """A connected IMAP mailbox, ready to fetch or watch for new messages."""

    def __init__(self, config: MailboxConfig) -> None:
        self.config = config
        self._client: IMAPClient | None = None

    def connect(self) -> None:
        self._client = IMAPClient(self.config.host, port=self.config.port, ssl=self.config.use_ssl)
        self._client.login(self.config.username, self.config.password)
        self._client.select_folder(self.config.folder)

    def disconnect(self) -> None:
        if self._client is not None:
            self._client.logout()
            self._client = None

    @property
    def client(self) -> IMAPClient:
        if self._client is None:
            raise RuntimeError("ImapMailbox is not connected; call connect() first")
        return self._client

    def fetch_since(self, since_uid: int) -> list[RawEmail]:
        """Fetch every message with a UID greater than ``since_uid``."""
        uids = [uid for uid in self.client.search(["UID", f"{since_uid + 1}:*"]) if uid > since_uid]
        if not uids:
            return []

        response = self.client.fetch(uids, ["RFC822"])
        return [parse_raw_message(uid, data[b"RFC822"]) for uid, data in sorted(response.items())]

    def idle_check(
        self, on_new_mail: Callable[[], None], timeout: int = DEFAULT_IDLE_TIMEOUT_SECONDS
    ) -> None:
        """Block in IMAP IDLE for up to ``timeout`` seconds, calling
        ``on_new_mail`` once if new messages arrived while idling."""
        self.client.idle()
        try:
            responses = self.client.idle_check(timeout=timeout)
        finally:
            self.client.idle_done()
        if any(response[1] in (b"EXISTS", b"RECENT") for response in responses):
            on_new_mail()

    @contextmanager
    def session(self) -> Iterator[ImapMailbox]:
        self.connect()
        try:
            yield self
        finally:
            self.disconnect()
