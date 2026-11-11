import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class HistoricalPrice(Base):
    __tablename__ = "historical_prices"

    __table_args__ = (
        UniqueConstraint(
            "instrument_id",
            "price_date",
            "source",
            name="uq_historical_prices_instrument_date_source",
        ),
        CheckConstraint(
            "close_price > 0",
            name="valid_historical_price",
        ),
        CheckConstraint(
            "currency IN ('PLN', 'EUR', 'GBP', 'USD')",
            name="valid_historical_price_currency",
        ),
        Index(
            "ix_historical_prices_instrument_date",
            "instrument_id",
            "price_date",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("instruments.id", ondelete="RESTRICT"),
        nullable=False,
    )

    price_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    close_price: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    instrument: Mapped["Instrument"] = relationship(  # noqa
        back_populates="historical_prices",
    )
