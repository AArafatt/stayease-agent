"""SQLAlchemy models for the StayEase platform."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Listing(Base):
    """A short-term rental property listed on StayEase."""

    __tablename__ = "listings"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    title: str = Column(String(200), nullable=False)
    description: str = Column(Text, nullable=False)
    location: str = Column(String(100), nullable=False, index=True)
    address: str = Column(String(300), nullable=False)
    price_per_night: Decimal = Column(Numeric(10, 2), nullable=False)
    max_guests: int = Column(Integer, nullable=False)
    bedrooms: int = Column(Integer, nullable=False)
    bathrooms: int = Column(Integer, nullable=False)
    amenities: list = Column(JSONB, default=list)
    images: list = Column(JSONB, default=list)
    is_available: bool = Column(Boolean, default=True)
    rating: Decimal = Column(Numeric(2, 1), default=0.0)
    total_reviews: int = Column(Integer, default=0)
    host_name: str = Column(String(100), nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    bookings = relationship("Booking", back_populates="listing")

    def __repr__(self) -> str:
        return f"<Listing(id={self.id}, title='{self.title}', location='{self.location}')>"


class Booking(Base):
    """A reservation made by a guest for a listing."""

    __tablename__ = "bookings"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    listing_id: int = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    conversation_id: str = Column(
        String(36), ForeignKey("conversations.id"), nullable=False, index=True
    )
    guest_name: str = Column(String(100), nullable=False)
    guest_email: str = Column(String(200), nullable=False)
    guest_phone: str = Column(String(20), nullable=True)
    check_in: date = Column(Date, nullable=False)
    check_out: date = Column(Date, nullable=False)
    num_guests: int = Column(Integer, nullable=False)
    total_price: Decimal = Column(Numeric(10, 2), nullable=False)
    status: str = Column(String(20), default="confirmed")  # confirmed | cancelled | completed
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())

    listing = relationship("Listing", back_populates="bookings")
    conversation = relationship("Conversation", back_populates="bookings")

    def __repr__(self) -> str:
        return f"<Booking(id={self.id}, listing_id={self.listing_id}, status='{self.status}')>"


class Conversation(Base):
    """Tracks a chat session between a guest and the AI agent."""

    __tablename__ = "conversations"

    id: str = Column(String(36), primary_key=True)  # UUID
    guest_name: str = Column(String(100), nullable=True)
    messages: list = Column(JSONB, default=list)  # [{role, content, timestamp}]
    intent: str = Column(String(50), nullable=True)  # search | details | book | escalate
    context: dict = Column(JSONB, default=dict)  # extracted entities from conversation
    is_escalated: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    bookings = relationship("Booking", back_populates="conversation")

    def __repr__(self) -> str:
        return f"<Conversation(id='{self.id}', intent='{self.intent}')>"
