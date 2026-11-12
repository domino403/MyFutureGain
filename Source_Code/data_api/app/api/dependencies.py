from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.repositories.historical_price_repository import (
    HistoricalPriceRepository,
)
from app.repositories.instrument_repository import InstrumentRepository
from app.services.market_data_service import MarketDataService


def get_market_data_service(
    db: Session = Depends(dependency=get_db),
) -> MarketDataService:
    return MarketDataService(
        instrument_repository=InstrumentRepository(db),
        historical_price_repository=HistoricalPriceRepository(db),
    )
