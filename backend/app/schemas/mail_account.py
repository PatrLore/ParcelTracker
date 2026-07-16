"""Mail account (IMAP mailbox) schemas. The password is write-only -
it never appears in any response schema, only the encrypted form is stored."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import MailAccountAuthType


class MailAccountBase(BaseModel):
    email_address: EmailStr
    imap_host: str
    imap_port: int = 993
    imap_username: str
    use_ssl: bool = True
    folder: str = "INBOX"
    use_idle: bool = False
    poll_interval_seconds: int = 300


class MailAccountCreate(MailAccountBase):
    password: str = Field(min_length=1)


class MailAccountUpdate(BaseModel):
    imap_host: str | None = None
    imap_port: int | None = None
    imap_username: str | None = None
    password: str | None = None
    use_ssl: bool | None = None
    folder: str | None = None
    use_idle: bool | None = None
    poll_interval_seconds: int | None = None
    is_active: bool | None = None


class MailAccountRead(MailAccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    auth_type: MailAccountAuthType
    is_active: bool
    last_seen_uid: int
    last_synced_at: datetime | None
    created_at: datetime


class MailAccountSyncResult(BaseModel):
    fetched_emails: int
    matched_orders: int
    created_shipments: int
    truncated: bool = False


class MicrosoftOAuthFlowStart(BaseModel):
    flow_id: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


class MicrosoftOAuthFlowStatus(BaseModel):
    status: str  # "pending" | "complete"


class MicrosoftOAuthFinalize(BaseModel):
    flow_id: str
    email_address: EmailStr
    folder: str = "INBOX"
    use_idle: bool = False
    poll_interval_seconds: int = 300


class MicrosoftOAuthReconnect(BaseModel):
    flow_id: str


class GoogleOAuthFlowStart(BaseModel):
    flow_id: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


class GoogleOAuthFlowStatus(BaseModel):
    status: str  # "pending" | "complete"


class GoogleOAuthFinalize(BaseModel):
    flow_id: str
    email_address: EmailStr
    folder: str = "INBOX"
    use_idle: bool = False
    poll_interval_seconds: int = 300


class GoogleOAuthReconnect(BaseModel):
    flow_id: str
