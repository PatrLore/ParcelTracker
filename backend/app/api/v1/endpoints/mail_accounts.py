"""Mail account (IMAP mailbox) endpoints. Scoped to the authenticated user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.mail_account import (
    MailAccountCreate,
    MailAccountRead,
    MailAccountSyncResult,
    MailAccountUpdate,
)
from app.services.email_ingestion_service import EmailIngestionService
from app.services.exceptions import NotFoundError
from app.services.mail_account_service import MailAccountService

router = APIRouter(
    prefix="/mail-accounts", tags=["mail-accounts"], dependencies=[Depends(get_current_user)]
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
