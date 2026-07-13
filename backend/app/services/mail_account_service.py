"""Mail account (IMAP mailbox) management, including credential encryption."""

from __future__ import annotations

from importer.imap_client import MailboxConfig
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_secret, encrypt_secret
from app.models.mail_account import MailAccount
from app.repositories.mail_account_repository import MailAccountRepository
from app.schemas.mail_account import MailAccountCreate, MailAccountUpdate
from app.services.exceptions import NotFoundError


class MailAccountService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.mail_accounts = MailAccountRepository(db)

    def list_accounts(self, user_id: int) -> list[MailAccount]:
        return self.mail_accounts.list_for_user(user_id)

    def get_account(self, mail_account_id: int, user_id: int) -> MailAccount:
        account = self.mail_accounts.get_for_user(mail_account_id, user_id)
        if account is None:
            raise NotFoundError(f"Mail account {mail_account_id} not found")
        return account

    def create_account(self, data: MailAccountCreate, user_id: int) -> MailAccount:
        fields = data.model_dump(exclude={"password"})
        account = MailAccount(
            **fields,
            user_id=user_id,
            encrypted_password=encrypt_secret(data.password),
        )
        account = self.mail_accounts.add(account)
        self.mail_accounts.commit()
        return account

    def update_account(
        self, mail_account_id: int, data: MailAccountUpdate, user_id: int
    ) -> MailAccount:
        account = self.get_account(mail_account_id, user_id)
        changes = data.model_dump(exclude_unset=True, exclude={"password"})
        for field, value in changes.items():
            setattr(account, field, value)
        if data.password is not None:
            account.encrypted_password = encrypt_secret(data.password)
        self.mail_accounts.commit()
        self.db.refresh(account)
        return account

    def delete_account(self, mail_account_id: int, user_id: int) -> None:
        account = self.get_account(mail_account_id, user_id)
        self.mail_accounts.delete(account)
        self.mail_accounts.commit()

    @staticmethod
    def build_mailbox_config(account: MailAccount) -> MailboxConfig:
        """Build an importer-ready connection config, decrypting the password."""
        return MailboxConfig(
            host=account.imap_host,
            port=account.imap_port,
            username=account.imap_username,
            password=decrypt_secret(account.encrypted_password),
            use_ssl=account.use_ssl,
            folder=account.folder,
            use_idle=account.use_idle,
            poll_interval_seconds=account.poll_interval_seconds,
        )
