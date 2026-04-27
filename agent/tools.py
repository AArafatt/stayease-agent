"""Tool definitions for the StayEase booking agent.

Each tool wraps a database query and is invoked by the LLM when
the conversation requires structured data retrieval or mutation.
"""

from datetime import date

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import async_session
from db.models import Booking, Listing


# ---------------------------------------------------------------------------
# Pydantic input schemas
# ---------------------------------------------------------------------------


class SearchInput(BaseModel):
    """Parameters for searching available properties."""

    location: str = Field(description="City or area name, e.g. 'Cox's Bazar'")
    check_in: date = Field(description="Check-in date (YYYY-MM-DD)")
    check_out: date = Field(description="Check-out date (YYYY-MM-DD)")
    num_guests: int = Field(ge=1, description="Number of guests")


class ListingDetailsInput(BaseModel):
    """Parameters for fetching a single listing's details."""

    listing_id: int = Field(description="Unique listing identifier")


class CreateBookingInput(BaseModel):
    """Parameters for creating a new booking."""

    listing_id: int = Field(description="Listing to book")
    guest_name: str = Field(description="Full name of the guest")
    guest_email: str = Field(description="Guest email for confirmation")
    check_in: date = Field(description="Check-in date (YYYY-MM-DD)")
    check_out: date = Field(description="Check-out date (YYYY-MM-DD)")
    num_guests: int = Field(ge=1, description="Number of guests")
    conversation_id: str = Field(description="Conversation this booking belongs to")


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


@tool("search_available_properties", args_schema=SearchInput)
async def search_available_properties(
    location: str,
    check_in: date,
    check_out: date,
    num_guests: int,
) -> list[dict]:
    """Search for available properties matching the guest's criteria.

    Returns a list of matching listings with key details and pricing.
    """
    async with async_session() as session:
        # Find listings in the requested location that can host enough guests
        # and are not already booked for the requested dates.
        booked_ids_subq = (
            select(Booking.listing_id)
            .where(
                and_(
                    Booking.status == "confirmed",
                    Booking.check_in < check_out,
                    Booking.check_out > check_in,
                )
            )
            .scalar_subquery()
        )

        query = (
            select(Listing)
            .where(
                and_(
                    Listing.location.ilike(f"%{location}%"),
                    Listing.max_guests >= num_guests,
                    Listing.is_available.is_(True),
                    Listing.id.not_in(booked_ids_subq),
                )
            )
            .order_by(Listing.rating.desc())
            .limit(5)
        )

        result = await session.execute(query)
        listings = result.scalars().all()

        nights = (check_out - check_in).days
        return [
            {
                "listing_id": l.id,
                "title": l.title,
                "location": l.location,
                "price_per_night": float(l.price_per_night),
                "total_price": float(l.price_per_night * nights),
                "max_guests": l.max_guests,
                "bedrooms": l.bedrooms,
                "rating": float(l.rating),
                "total_reviews": l.total_reviews,
            }
            for l in listings
        ]


@tool("get_listing_details", args_schema=ListingDetailsInput)
async def get_listing_details(listing_id: int) -> dict:
    """Retrieve full details for a specific property listing."""
    async with async_session() as session:
        result = await session.execute(
            select(Listing).where(Listing.id == listing_id)
        )
        listing = result.scalar_one_or_none()

        if listing is None:
            return {"error": f"Listing {listing_id} not found."}

        return {
            "listing_id": listing.id,
            "title": listing.title,
            "description": listing.description,
            "location": listing.location,
            "address": listing.address,
            "price_per_night": float(listing.price_per_night),
            "max_guests": listing.max_guests,
            "bedrooms": listing.bedrooms,
            "bathrooms": listing.bathrooms,
            "amenities": listing.amenities,
            "images": listing.images,
            "rating": float(listing.rating),
            "total_reviews": listing.total_reviews,
            "host_name": listing.host_name,
        }


@tool("create_booking", args_schema=CreateBookingInput)
async def create_booking(
    listing_id: int,
    guest_name: str,
    guest_email: str,
    check_in: date,
    check_out: date,
    num_guests: int,
    conversation_id: str,
) -> dict:
    """Create a confirmed booking for the given listing and guest."""
    async with async_session() as session:
        # Verify listing exists and can accommodate guests
        listing = await session.get(Listing, listing_id)
        if listing is None:
            return {"error": f"Listing {listing_id} not found."}
        if num_guests > listing.max_guests:
            return {"error": f"This property hosts up to {listing.max_guests} guests."}

        nights = (check_out - check_in).days
        if nights <= 0:
            return {"error": "Check-out must be after check-in."}

        total_price = listing.price_per_night * nights

        booking = Booking(
            listing_id=listing_id,
            conversation_id=conversation_id,
            guest_name=guest_name,
            guest_email=guest_email,
            check_in=check_in,
            check_out=check_out,
            num_guests=num_guests,
            total_price=total_price,
            status="confirmed",
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)

        return {
            "booking_id": booking.id,
            "listing_title": listing.title,
            "check_in": str(booking.check_in),
            "check_out": str(booking.check_out),
            "num_guests": booking.num_guests,
            "total_price": float(booking.total_price),
            "status": booking.status,
        }
