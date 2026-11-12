import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.instrument import Instrument


class InstrumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, instrument_id: uuid.UUID) -> Instrument | None:
        return self.db.get(Instrument, instrument_id)

    def get_by_symbol_and_exchange(
        self,
        symbol: str,
        exchange: str,
    ) -> Instrument | None:
        statement = select(Instrument).where(
            Instrument.symbol == symbol,
            Instrument.exchange == exchange,
        )

        return self.db.scalar(statement)

    def get_all(self) -> list[Instrument]:
        statement = select(Instrument).order_by(Instrument.symbol)

        return list(self.db.scalars(statement).all())

    def create(
        self,
        *,
        symbol: str,
        name: str,
        exchange: str,
        quote_currency: str,
    ) -> Instrument:
        instrument = Instrument(
            symbol=symbol,
            name=name,
            exchange=exchange,
            quote_currency=quote_currency,
        )

        self.db.add(instrument)
        self.db.flush()

        return instrument
