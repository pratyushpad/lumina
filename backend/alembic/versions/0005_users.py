"""Users (Google sign-in)

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-20

A profile table for signed-in people. Ownership is not stored here: a session
owned by an account carries owner_key "user:<id>" in sessions.owner_token (the
same column anonymous browsers use), so there is no foreign key to maintain and
existing sessions/messages are untouched. Signing in "claims" a browser's
anonymous sessions by rewriting that token to the account's owner_key.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_subject", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("avatar_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_user_provider_subject"),
    )


def downgrade() -> None:
    op.drop_table("users")
