"""Unit tests for mail account management and credential encryption."""

from __future__ import annotations

import pytest

from app.schemas.mail_account import MailAccountCreate, MailAccountUpdate
from app.schemas.user import UserCreate
from app.services.exceptions import NotFoundError
from app.services.mail_account_service import MailAccountService
from app.services.user_service import UserService


@pytest.fixture()
def user(db_session):
    return UserService(db_session).create_user(
        UserCreate(email="mailbox-owner@example.com", password="password123")
    )


def _create_payload(**overrides) -> MailAccountCreate:
    fields = {
        "email_address": "owner@gmail.com",
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
        "imap_username": "owner@gmail.com",
        "password": "super-secret-app-password",
    }
    fields.update(overrides)
    return MailAccountCreate(**fields)


def test_create_account_encrypts_password_at_rest(db_session, user):
    account = MailAccountService(db_session).create_account(_create_payload(), user.id)

    assert account.encrypted_password != "super-secret-app-password"


def test_build_mailbox_config_decrypts_password(db_session, user):
    account = MailAccountService(db_session).create_account(_create_payload(), user.id)

    config = MailAccountService.build_mailbox_config(account)

    assert config.password == "super-secret-app-password"
    assert config.host == "imap.gmail.com"
    assert config.username == "owner@gmail.com"


def test_update_account_rotates_password(db_session, user):
    service = MailAccountService(db_session)
    account = service.create_account(_create_payload(), user.id)
    old_encrypted = account.encrypted_password

    updated = service.update_account(
        account.id, MailAccountUpdate(password="a-new-app-password"), user.id
    )

    assert updated.encrypted_password != old_encrypted
    assert MailAccountService.build_mailbox_config(updated).password == "a-new-app-password"


def test_account_scoped_to_owner(db_session, user):
    other = UserService(db_session).create_user(
        UserCreate(email="someone-else@example.com", password="password123")
    )
    service = MailAccountService(db_session)
    account = service.create_account(_create_payload(), user.id)

    with pytest.raises(NotFoundError):
        service.get_account(account.id, other.id)


def test_list_accounts_for_user(db_session, user):
    service = MailAccountService(db_session)
    service.create_account(_create_payload(), user.id)
    service.create_account(
        _create_payload(email_address="second@gmx.de", imap_host="imap.gmx.net"), user.id
    )

    assert len(service.list_accounts(user.id)) == 2


def test_delete_account(db_session, user):
    service = MailAccountService(db_session)
    account = service.create_account(_create_payload(), user.id)

    service.delete_account(account.id, user.id)

    with pytest.raises(NotFoundError):
        service.get_account(account.id, user.id)
