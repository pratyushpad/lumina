import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, default="New Session")
    # Opaque per-browser token. NULL means no owner: either a pre-ownership row
    # or the shared demo, neither of which is reachable by token match.
    owner_token = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    documents = relationship(
        "Document", back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )
    messages = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )
