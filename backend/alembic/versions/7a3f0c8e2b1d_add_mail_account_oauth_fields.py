"""add mail account oauth fields

Revision ID: 7a3f0c8e2b1d
Revises: 0008b2eb8c6c
Create Date: 2026-07-15 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7a3f0c8e2b1d"
down_revision: Union[str, None] = "0008b2eb8c6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("mail_accounts") as batch_op:
        batch_op.add_column(
            sa.Column("auth_type", sa.String(length=20), nullable=False, server_default="password")
        )
        batch_op.add_column(
            sa.Column("encrypted_oauth_refresh_token", sa.String(length=2000), nullable=True)
        )
        batch_op.alter_column(
            "encrypted_password", existing_type=sa.String(length=1000), nullable=True
        )


def downgrade() -> None:
    with op.batch_alter_table("mail_accounts") as batch_op:
        batch_op.alter_column(
            "encrypted_password", existing_type=sa.String(length=1000), nullable=False
        )
        batch_op.drop_column("encrypted_oauth_refresh_token")
        batch_op.drop_column("auth_type")
