"""Mail account (IMAP mailbox) endpoints. Scoped to the authenticated user."""

from __future__ import annotations

import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.mail_account import (
    MailAccountCreate,
    MailAccountRead,
    MailAccountSyncResult,
    MailAccountUpdate,
    MicrosoftOAuthFinalize,
    MicrosoftOAuthFlowStart,
    MicrosoftOAuthFlowStatus,
    MicrosoftOAuthReconnect,
)
from app.services.email_ingestion_service import EmailIngestionService
from app.services.exceptions import NotFoundError
from app.services.mail_account_service import MailAccountService
from app.services.oauth_microsoft import (
    DeviceFlowExpiredError,
    DeviceFlowFailedError,
    DeviceFlowNotFoundError,
    poll_device_flow,
    start_device_flow,
    take_completed_tokens,
)

router = APIRouter(
    prefix="/mail-accounts", tags=["mail-accounts"], dependencies=[Depends(get_current_user)]
)


def _require_microsoft_oauth_configured() -> None:
    settings = get_settings().microsoft_oauth
    if not settings.enabled or not settings.client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Microsoft sign-in isn't configured on this server - an administrator needs "
                "to set microsoft_oauth.client_id in config.yaml. See docs/mailboxes.md."
            ),
        )


@router.get("", response_model=list[MailAccountRead])
def list_mail_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MailAccountRead]:
    return MailAccountService(db).list_accounts(current_user.id)


@router.post("", response_model=MailAccountRead, status_code=status.HTTP_201_CREATED)
def create_mail_account(
    payload: MailAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MailAccountRead:
    return MailAccountService(db).create_account(payload, current_user.id)


@router.get("/{mail_account_id}", response_model=MailAccountRead)
def get_mail_account(
    mail_account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MailAccountRead:
    try:
        return MailAccountService(db).get_account(mail_account_id, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{mail_account_id}", response_model=MailAccountRead)
def update_mail_account(
    mail_account_id: int,
    payload: MailAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MailAccountRead:
    try:
        return MailAccountService(db).update_account(mail_account_id, payload, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{mail_account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mail_account(
    mail_account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        MailAccountService(db).delete_account(mail_account_id, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{mail_account_id}/sync", response_model=MailAccountSyncResult)
def sync_mail_account(
    mail_account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MailAccountSyncResult:
    try:
        account = MailAccountService(db).get_account(mail_account_id, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    try:
        return EmailIngestionService(db).sync_account(account)
    except ConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Could not reach mailbox: {exc}"
        ) from exc


@router.post("/oauth/microsoft/start", response_model=MicrosoftOAuthFlowStart)
def start_microsoft_oauth(
    current_user: User = Depends(get_current_user),
) -> MicrosoftOAuthFlowStart:
    """Starts a device-code sign-in (see ``app.services.oauth_microsoft``) -
    the user completes it in a browser, then the frontend polls ``/poll``."""
    _require_microsoft_oauth_configured()
    with httpx.Client(timeout=10.0) as client:
        flow = start_device_flow(client, current_user.id)
    return MicrosoftOAuthFlowStart(
        flow_id=flow.flow_id,
        user_code=flow.user_code,
        verification_uri=flow.verification_uri,
        expires_in=max(0, round(flow.expires_at - time.monotonic())),
        interval=flow.interval,
    )


@router.get("/oauth/microsoft/poll/{flow_id}", response_model=MicrosoftOAuthFlowStatus)
def poll_microsoft_oauth(
    flow_id: str,
    current_user: User = Depends(get_current_user),
) -> MicrosoftOAuthFlowStatus:
    _require_microsoft_oauth_configured()
    try:
        with httpx.Client(timeout=10.0) as client:
            complete = poll_device_flow(client, flow_id, current_user.id)
    except DeviceFlowNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unknown or expired sign-in flow"
        ) from exc
    except DeviceFlowExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="The sign-in code expired before it was used. Start again.",
        ) from exc
    except DeviceFlowFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Microsoft sign-in failed: {exc}"
        ) from exc
    return MicrosoftOAuthFlowStatus(status="complete" if complete else "pending")


@router.post(
    "/oauth/microsoft/finalize", response_model=MailAccountRead, status_code=status.HTTP_201_CREATED
)
def finalize_microsoft_oauth(
    payload: MicrosoftOAuthFinalize,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MailAccountRead:
    """Creates the mail account once the device-code sign-in has completed."""
    _require_microsoft_oauth_configured()
    try:
        tokens = take_completed_tokens(payload.flow_id, current_user.id)
    except DeviceFlowNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sign-in isn't complete yet, or has already been used",
        ) from exc
    return MailAccountService(db).create_oauth_microsoft_account(
        user_id=current_user.id,
        email_address=payload.email_address,
        refresh_token=tokens.refresh_token,
        folder=payload.folder,
        use_idle=payload.use_idle,
        poll_interval_seconds=payload.poll_interval_seconds,
    )


@router.post("/{mail_account_id}/oauth/microsoft/reconnect", response_model=MailAccountRead)
def reconnect_microsoft_oauth(
    mail_account_id: int,
    payload: MicrosoftOAuthReconnect,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MailAccountRead:
    """Replaces the stored refresh token for an existing Microsoft-linked
    mailbox after the user re-completes the ``start``/``poll`` sign-in."""
    _require_microsoft_oauth_configured()
    try:
        tokens = take_completed_tokens(payload.flow_id, current_user.id)
    except DeviceFlowNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sign-in isn't complete yet, or has already been used",
        ) from exc
    try:
        return MailAccountService(db).reconnect_oauth_microsoft_account(
            mail_account_id, current_user.id, tokens.refresh_token
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
