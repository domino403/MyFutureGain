import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


SUPPORTED_CURRENCIES = ("PLN", "EUR", "GBP", "USD")


class Instrument(Base):
    __tablename__ = "instruments"

    __table_args__ = (
        UniqueConstraint(
            "exchange",
            "symbol",
            name="uq_instruments_exchange_symbol",
        ),
        CheckConstraint(
            "quote_currency IN ('PLN', 'EUR', 'GBP', 'USD')",
            name="valid_instrument_quote_currency",
        ),
        Index("ix_instruments_symbol", "symbol"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    symbol: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    exchange: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    quote_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    historical_prices: Mapped[list["HistoricalPrice"]] = relationship(  # noqa
        back_populates="instrument",
        passive_deletes=True,
    )
