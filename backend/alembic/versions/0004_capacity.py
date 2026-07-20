"""Free-tier capacity: daily usage ledger + demo answer cache

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-20

Two tables that let the app answer "hundreds of demo prompts a day" honestly on
a free tier:

- usage_daily: running per-provider spend for each UTC day, so a provider that
  has burned its free quota is skipped instead of returning a 503.
- demo_answer_cache: stored answers to normalised demo questions, replayed at
  zero token cost (the demo corpus and its suggested questions are fixed).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usage_daily",
        sa.Column("day", sa.String(), primary_key=True),
        sa.Column("provider", sa.String(), primary_key=True),
        sa.Column("tokens_used", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("requests_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "demo_answer_cache",
        sa.Column("query_norm", sa.String(), primary_key=True),
        sa.Column("answer", sa.String(), nullable=False),
        sa.Column("citations", JSONB(), nullable=True),
        sa.Column("model_used", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("demo_answer_cache")
    op.drop_table("usage_daily")
