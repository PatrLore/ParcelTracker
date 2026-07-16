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
from imapclient.exceptions import IMAPClientError

from importer.emails import RawEmail

DEFAULT_IDLE_TIMEOUT_SECONDS = 30
#: Socket timeout for all non-IDLE IMAP operations (connect, login, search,
#: fetch, ...). Without this, imapclient's default (no timeout - blocking
#: forever) means a stalled connection or an unresponsive server hangs the
#: sync indefinitely with no feedback, instead of failing with a clear error.
DEFAULT_SOCKET_TIMEOUT_SECONDS = 60.0


class ImapConnectionError(ConnectionError):
    """Wraps an IMAP protocol error from login or folder selection (wrong
    password, unknown/unselectable folder, ...) as a :class:`ConnectionError`
    so it's covered by the same handling as a plain unreachable-host error
    (see ``app.api.v1.endpoints.mail_accounts.sync_mail_account``), instead
    of surfacing as an unhandled exception with no useful detail."""


@dataclass(frozen=True)
class MailboxConfig:
    """Connection details for a single IMAP mailbox.

    Exactly one of ``password`` (plain IMAP LOGIN) or ``access_token``
    (XOAUTH2 - required by providers like Outlook.com/Hotmail that no
    longer accept Basic Authentication) must be set.
    """

    host: str
    username: str
    port: int = 993
    use_ssl: bool = True
    folder: str = "INBOX"
    use_idle: bool = False
    poll_interval_seconds: int = 300
    password: str | None = None
    access_token: str | None = None


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
        self._client = IMAPClient(
            self.config.host,
            port=self.config.port,
            ssl=self.config.use_ssl,
            timeout=DEFAULT_SOCKET_TIMEOUT_SECONDS,
        )
        try:
            if self.config.access_token is not None:
                self._client.oauth2_login(self.config.username, self.config.access_token)
            else:
                self._client.login(self.config.username, self.config.password)
        except IMAPClientError as exc:
            raise ImapConnectionError(f"IMAP login failed: {exc}") from exc

        try:
            self._client.select_folder(self.config.folder)
        except IMAPClientError as exc:
            raise ImapConnectionError(
                f"Folder '{self.config.folder}' not found or not selectable. "
                f"Available folders: {', '.join(self._list_folder_names())}"
            ) from exc

    def _list_folder_names(self) -> list[str]:
        try:
            return sorted(name for _, _, name in self.client.list_folders())
        except IMAPClientError:
            return []

    def disconnect(self) -> None:
        if self._client is not None:
            self._client.logout()
            self._client = None

    @property
    def client(self) -> IMAPClient:
        if self._client is None:
            raise RuntimeError("ImapMailbox is not connected; call connect() first")
        return self._client

    def fetch_since(self, since_uid: int, limit: int | None = None) -> list[RawEmail]:
        """Fetch messages with a UID greater than ``since_uid``, oldest
        first. If ``limit`` is set, fetches at most that many in this call -
        see ``EmailIngestionService`` for why: a mailbox with a large
        backlog (e.g. a first-time sync against Gmail's "All Mail") could
        otherwise mean one FETCH pulling in everything the account has ever
        received, in a single call with no progress feedback."""
        uids = sorted(
            uid for uid in self.client.search(["UID", f"{since_uid + 1}:*"]) if uid > since_uid
        )
        if not uids:
            return []
        if limit is not None:
            uids = uids[:limit]

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
