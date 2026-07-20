import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, UniqueConstraint

from app.database import Base


class User(Base):
    """A signed-in person. Profile only — session ownership is carried by the
    `owner_key` written into sessions.owner_token ("user:<id>"), so there is no
    user_id foreign key to keep in sync and account rows stay decoupled from the
    data they own."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String, nullable=False)  # "google"
    provider_subject = Column(String, nullable=False)  # stable id from the provider
    email = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # One account per (provider, subject); a returning user is matched, not
    # duplicated.
    __table_args__ = (UniqueConstraint("provider", "provider_subject", name="uq_user_provider_subject"),)
