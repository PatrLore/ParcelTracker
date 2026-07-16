"""Fetches new mail for a :class:`MailAccount`, parses it with the pluggable
merchant parsers in ``importer.parsers``, and persists the result.

This is the only place backend code depends on ``importer`` - it converts
the library's pure ``RawEmail``/``ParsedOrder`` data into database rows,
keeping ``importer`` itself free of any database or FastAPI dependency.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

import httpx
from importer.emails import RawEmail
from importer.imap_client import ImapMailbox, MailboxConfig
from importer.parsers import ParsedOrder, detect
from notification import NotificationDispatcher, NotificationMessage
from sqlalchemy.orm import Session

from app.models.carrier import Carrier
from app.models.email import Email
from app.models.enums import MailAccountAuthType, OrderStatus, ShipmentStatus
from app.models.mail_account import MailAccount
from app.models.order import Order
from app.models.shipment import Shipment
from app.repositories.carrier_repository import CarrierRepository
from app.repositories.email_repository import EmailRepository
from app.repositories.mail_account_repository import MailAccountRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.shipment_repository import ShipmentRepository
from app.schemas.mail_account import MailAccountSyncResult
from app.services.mail_account_service import MailAccountService

#: Upper bound on how many emails a single sync() call will fetch. Without
#: this, a mailbox with a large backlog (e.g. a first-time sync against
#: Gmail's "All Mail" folder, which has no per-folder UID history to resume
#: from) would try to FETCH its entire history in one blocking IMAP call -
#: see importer.imap_client.ImapMailbox.fetch_since. Oldest-first ordering
#: means repeated syncs make steady progress through a large backlog instead
#: of re-fetching the same batch.
MAX_EMAILS_PER_SYNC = 200


class Mailbox(Protocol):
    """The subset of :class:`importer.imap_client.ImapMailbox` this service needs."""

    def session(self): ...  # noqa: D102

    def fetch_since(self, since_uid: int, limit: int | None = None) -> list[RawEmail]: ...  # noqa: D102


MailboxFactory = Callable[[MailboxConfig], Mailbox]


class EmailIngestionService:
    """Orchestrates one mailbox sync: fetch -> parse -> persist."""

    def __init__(
        self,
        db: Session,
        mailbox_factory: MailboxFactory = ImapMailbox,
        dispatcher: NotificationDispatcher | None = None,
        http_client_factory: Callable[[], httpx.Client] = lambda: httpx.Client(timeout=10.0),
    ) -> None:
        self.db = db
        self._mailbox_factory = mailbox_factory
        self._dispatcher = dispatcher
        self._http_client_factory = http_client_factory
        self.mail_accounts = MailAccountRepository(db)
        self.emails = EmailRepository(db)
        self.orders = OrderRepository(db)
        self.shipments = ShipmentRepository(db)
        self.carriers = CarrierRepository(db)

    def sync_account(self, account: MailAccount) -> MailAccountSyncResult:
        access_token = None
        if account.auth_type in (
            MailAccountAuthType.OAUTH_MICROSOFT,
            MailAccountAuthType.OAUTH_GOOGLE,
        ):
            with self._http_client_factory() as client:
                access_token = MailAccountService(self.db).ensure_fresh_access_token(
                    account, client
                )
        config = MailAccountService.build_mailbox_config(account, access_token=access_token)
        mailbox = self._mailbox_factory(config)

        with mailbox.session():
            raw_emails = mailbox.fetch_since(account.last_seen_uid, limit=MAX_EMAILS_PER_SYNC)

        matched_orders = 0
        created_shipments = 0

        for raw_email in raw_emails:
            if self.emails.get_by_message_id(raw_email.message_id) is not None:
                continue

            parsed = detect(raw_email)
            order = self._persist_parsed_order(parsed, account.user_id) if parsed else None
            if order is not None:
                matched_orders += 1
                created_shipments += self._persist_shipments(order, parsed)

            self.emails.add(
                Email(
                    order_id=order.id if order else None,
                    message_id=raw_email.message_id,
                    subject=raw_email.subject,
                    sender=raw_email.sender,
                    received_at=raw_email.received_at,
                    raw_content=raw_email.text_body,
                    attachments=raw_email.attachments,
                )
            )

            account.last_seen_uid = max(account.last_seen_uid, raw_email.uid)

        account.last_synced_at = datetime.now(UTC)
        self.mail_accounts.commit()

        return MailAccountSyncResult(
            fetched_emails=len(raw_emails),
            matched_orders=matched_orders,
            created_shipments=created_shipments,
            truncated=len(raw_emails) == MAX_EMAILS_PER_SYNC,
        )

    def _persist_parsed_order(self, parsed: ParsedOrder, user_id: int) -> Order | None:
        order = None
        if parsed.order_number:
            order = self.orders.get_by_merchant_and_number(
                user_id, parsed.merchant, parsed.order_number
            )

        if order is None:
            order = self.orders.add(
                Order(
                    user_id=user_id,
                    merchant=parsed.merchant,
                    order_number=parsed.order_number,
                    order_date=parsed.order_date,
                    invoice_amount=_parse_amount(parsed.invoice_amount),
                    currency=parsed.currency or "EUR",
                    status=OrderStatus.CONFIRMED,
                )
            )
            if self._dispatcher is not None:
                self._dispatcher.dispatch(
                    NotificationMessage(
                        event="new_confirmation",
                        title=f"New order from {parsed.merchant}",
                        body=f"A shipping confirmation from {parsed.merchant} was detected.",
                        metadata={
                            "merchant": parsed.merchant,
                            "order_number": parsed.order_number or "",
                        },
                    )
                )

        if parsed.tracking_numbers and order.status == OrderStatus.CONFIRMED:
            order.status = OrderStatus.SHIPPED

        return order

    def _persist_shipments(self, order: Order, parsed: ParsedOrder) -> int:
        created = 0
        for tracking_number in parsed.tracking_numbers:
            if self.shipments.get_by_order_and_tracking_number(order.id, tracking_number):
                continue

            carrier = self._get_or_create_carrier(parsed.carrier_hint)
            self.shipments.add(
                Shipment(
                    order_id=order.id,
                    carrier_id=carrier.id if carrier else None,
                    tracking_number=tracking_number,
                    tracking_status=ShipmentStatus.LABEL_CREATED,
                )
            )
            created += 1
        return created

    def _get_or_create_carrier(self, carrier_name: str | None) -> Carrier | None:
        if not carrier_name:
            return None
        carrier = self.carriers.get_by_name(carrier_name)
        if carrier is None:
            carrier = self.carriers.add(Carrier(name=carrier_name))
        return carrier


def _parse_amount(amount: str | None) -> float | None:
    if amount is None:
        return None
    normalized = amount.replace(".", "").replace(",", ".") if "," in amount else amount
    try:
        return float(normalized)
    except ValueError:
        return None
