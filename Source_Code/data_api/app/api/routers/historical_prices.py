import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_market_data_service
from app.schemas.historical_price import (
    HistoricalPriceBatchCreate,
    HistoricalPriceRead,
)
from app.services.market_data_service import (
    HistoricalPriceData,
    InstrumentNotFoundError,
    InvalidMarketDataError,
    MarketDataService,
)


router = APIRouter(tags=["Historical Prices"])


@router.post(
    "/instruments/{instrument_id}/prices",
    status_code=status.HTTP_204_NO_CONTENT,
)
def save_historical_prices(
    instrument_id: uuid.UUID,
    payload: HistoricalPriceBatchCreate,
    service: Annotated[MarketDataService, Depends(get_market_data_service)],
):
    prices = [
        HistoricalPriceData(
            price_date=item.price_date,
            close_price=item.close_price,
            currency=item.currency,
            source=item.source,
        )
        for item in payload.prices
    ]

    try:
        service.save_historical_prices(instrument_id, prices)
    except InstrumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidMarketDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get(
    "/instruments/{instrument_id}/prices",
    response_model=list[HistoricalPriceRead],
)
def get_historical_prices(
    instrument_id: uuid.UUID,
    start_date: Annotated[date, Query()],
    end_date: Annotated[date, Query()],
    service: Annotated[MarketDataService, Depends(get_market_data_service)],
):
    try:
        return service.get_historical_prices(
            instrument_id,
            start_date,
            end_date,
        )
    except InstrumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidMarketDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
