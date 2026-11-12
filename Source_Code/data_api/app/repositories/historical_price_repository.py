import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.historical_price import HistoricalPrice


class HistoricalPriceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_instrument_and_date_range(
        self,
        instrument_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[HistoricalPrice]:
        statement = (
            select(HistoricalPrice)
            .where(
                HistoricalPrice.instrument_id == instrument_id,
                HistoricalPrice.price_date >= start_date,
                HistoricalPrice.price_date <= end_date,
            )
            .order_by(HistoricalPrice.price_date)
        )

        return list(self.db.scalars(statement).all())

    def get_latest(
        self,
        instrument_id: uuid.UUID,
    ) -> HistoricalPrice | None:
        statement = (
            select(HistoricalPrice)
            .where(HistoricalPrice.instrument_id == instrument_id)
            .order_by(HistoricalPrice.price_date.desc())
            .limit(1)
        )

        return self.db.scalar(statement)

    def upsert_many(
        self,
        prices: list[dict],
    ) -> None:
        if not prices:
            return

        statement = insert(HistoricalPrice).values(prices)

        statement = statement.on_conflict_do_update(
            constraint="uq_historical_prices_instrument_date_source",
            set_={
                "close_price": statement.excluded.close_price,
                "currency": statement.excluded.currency,
            },
        )

        self.db.execute(statement)
        self.db.flush()
