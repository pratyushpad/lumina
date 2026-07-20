"""Per-browser session ownership

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-20

Sessions were global and unauthenticated: any visitor could list, read, rename,
or delete any other visitor's sessions, including the seeded demo. This adds an
opaque per-browser token so a session is only visible to the browser that
created it. The shared demo session stays readable by everyone (it is matched by
id, not by token) but is not mutable.

Existing rows keep owner_token NULL. That is deliberate: those sessions were
created before ownership existed, so there is no honest way to attribute them to
a browser, and guessing would hand one visitor another visitor's data. NULL is
treated as "no owner" and is invisible to every caller. To purge them once you
are satisfied nothing of yours is in there:

    DELETE FROM sessions WHERE owner_token IS NULL AND id <> 'demo';

Documents, messages, chunks, and traces all cascade from sessions, so that one
statement is a complete cleanup. It is left as a manual step rather than run
here because a migration should not silently destroy user data.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("owner_token", sa.String(), nullable=True))
    op.create_index("ix_sessions_owner_token", "sessions", ["owner_token"])

    # Messages carry the owner too, so the shared demo session can show each
    # visitor only their own conversation without splitting it into per-visitor
    # sessions (which would re-ingest the corpus for every visitor).
    op.add_column("messages", sa.Column("owner_token", sa.String(), nullable=True))
    op.create_index(
        "ix_messages_session_owner", "messages", ["session_id", "owner_token"]
    )


def downgrade() -> None:
    op.drop_index("ix_messages_session_owner", table_name="messages")
    op.drop_column("messages", "owner_token")
    op.drop_index("ix_sessions_owner_token", table_name="sessions")
    op.drop_column("sessions", "owner_token")
