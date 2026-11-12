import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_market_data_service
from app.schemas.instrument import InstrumentCreate, InstrumentRead
from app.services.market_data_service import (
    InstrumentAlreadyExistsError,
    InstrumentNotFoundError,
    InvalidMarketDataError,
    MarketDataService,
)


router = APIRouter(prefix="/instruments", tags=["Instruments"])


@router.post(
    "",
    response_model=InstrumentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_instrument(
    payload: InstrumentCreate,
    service: Annotated[MarketDataService, Depends(get_market_data_service)],
):
    try:
        return service.create_instrument(**payload.model_dump())
    except InstrumentAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InvalidMarketDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{instrument_id}", response_model=InstrumentRead)
def get_instrument(
    instrument_id: uuid.UUID,
    service: Annotated[MarketDataService, Depends(get_market_data_service)],
):
    try:
        return service.get_instrument(instrument_id)
    except InstrumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
