"""Mail account (IMAP mailbox) management, including credential encryption."""

from __future__ import annotations

import httpx
from importer.imap_client import MailboxConfig
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_secret, encrypt_secret
from app.models.enums import MailAccountAuthType
from app.models.mail_account import MailAccount
from app.repositories.mail_account_repository import MailAccountRepository
from app.schemas.mail_account import MailAccountCreate, MailAccountUpdate
from app.services.exceptions import NotFoundError
from app.services.oauth_microsoft import refresh_access_token


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

    def create_oauth_microsoft_account(
        self,
        *,
        user_id: int,
        email_address: str,
        refresh_token: str,
        folder: str,
        use_idle: bool,
        poll_interval_seconds: int,
    ) -> MailAccount:
        """Creates a mail account authenticated via Microsoft OAuth2 rather
        than a password - see ``app.services.oauth_microsoft``."""
        account = MailAccount(
            user_id=user_id,
            email_address=email_address,
            imap_host="outlook.office365.com",
            imap_port=993,
            imap_username=email_address,
            auth_type=MailAccountAuthType.OAUTH_MICROSOFT,
            encrypted_password=None,
            encrypted_oauth_refresh_token=encrypt_secret(refresh_token),
            use_ssl=True,
            folder=folder,
            use_idle=use_idle,
            poll_interval_seconds=poll_interval_seconds,
        )
        account = self.mail_accounts.add(account)
        self.mail_accounts.commit()
        return account

    def reconnect_oauth_microsoft_account(
        self, mail_account_id: int, user_id: int, refresh_token: str
    ) -> MailAccount:
        """Replaces the stored refresh token after the user re-completes
        Microsoft sign-in (e.g. because it was revoked or expired)."""
        account = self.get_account(mail_account_id, user_id)
        account.encrypted_oauth_refresh_token = encrypt_secret(refresh_token)
        self.mail_accounts.commit()
        self.db.refresh(account)
        return account

    def ensure_fresh_access_token(self, account: MailAccount, http_client: httpx.Client) -> str:
        """Redeems the stored Microsoft refresh token for a fresh access
        token, persisting the (possibly rotated) refresh token Microsoft
        returns. Raises :class:`ConnectionError` if sign-in was revoked and
        the mailbox needs reconnecting."""
        if account.encrypted_oauth_refresh_token is None:
            raise ConnectionError(f"Mail account {account.id} has no Microsoft sign-in on file")
        refresh_token = decrypt_secret(account.encrypted_oauth_refresh_token)
        try:
            result = refresh_access_token(http_client, refresh_token)
        except httpx.HTTPStatusError as exc:
            raise ConnectionError(
                "Microsoft sign-in has expired or was revoked; reconnect this mailbox."
            ) from exc
        account.encrypted_oauth_refresh_token = encrypt_secret(result.refresh_token)
        self.mail_accounts.commit()
        return result.access_token

    @staticmethod
    def build_mailbox_config(
        account: MailAccount, access_token: str | None = None
    ) -> MailboxConfig:
        """Build an importer-ready connection config. For a password
        account, decrypts the stored password; for an OAuth account, pass
        an already-refreshed ``access_token`` (see
        :meth:`ensure_fresh_access_token`)."""
        return MailboxConfig(
            host=account.imap_host,
            port=account.imap_port,
            username=account.imap_username,
            password=decrypt_secret(account.encrypted_password)
            if account.encrypted_password
            else None,
            access_token=access_token,
            use_ssl=account.use_ssl,
            folder=account.folder,
            use_idle=account.use_idle,
            poll_interval_seconds=account.poll_interval_seconds,
        )
