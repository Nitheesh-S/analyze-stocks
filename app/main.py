import datetime
import calendar
from typing import Union
from collections import OrderedDict

from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from . import models, schemas, constants, types, utils, controllers
from .database import SessionLocal, engine
from fyers_api import accessToken, fyersModel


app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def generate_fyers_auth_code():
    session = accessToken.SessionModel(
        client_id=constants.fyers_app_id,
        secret_key=constants.fyers_secret_id,
        redirect_uri=constants.fyers_redirect_url,
        response_type="code",
    )

    redirect_url = session.generate_authcode()
    return RedirectResponse(redirect_url)


@app.get("/fyers")
def authenticate_fyers(auth_code: str = "", db: Session = Depends(get_db)):
    if not auth_code:
        return "No auth code provided!"

    session = accessToken.SessionModel(
        client_id=constants.fyers_app_id,
        secret_key=constants.fyers_secret_id,
        redirect_uri=constants.fyers_redirect_url,
        response_type="code",
        grant_type="authorization_code",
    )
    session.set_token(auth_code)
    response = session.generate_token()

    access_token: str = response.get("access_token", "")
    if not access_token:
        return {"error": "No access token found!", "response": response}

    record = models.ThirdPartyToken(
        access_token=access_token,
        refresh_token=response.get("refresh_token", ""),
        website="fyers",
    )

    stmt = (
        insert(models.ThirdPartyToken)
        .values(
            access_token=record.access_token,
            refresh_token=record.refresh_token,
            website=record.website,
        )
        .on_conflict_do_update(
            index_elements=[models.ThirdPartyToken.website],
            set_={
                "access_token": record.access_token,
                "refresh_token": record.refresh_token,
            },
        )
    )

    db.execute(stmt)
    db.commit()
    return {"msg": "Set token successfully!"}


@app.get("/stocks/{stock_symbol}")
def get_stock(stock_symbol: str, start_year: int = 2001, db: Session = Depends(get_db)):
    symbol = (
        db.query(models.SymbolMaster)
        .filter_by(ticker=stock_symbol, exchange="NSE", is_active=True)
        .first()
    )

    if not symbol:
        return {"error": "No stock found!"}
    
    start_date = datetime.datetime(start_year, 1, 2)

    data = db.query(models.SymbolHistory).filter(
        models.SymbolHistory.symbol_master_id == symbol.id,
        models.SymbolHistory.timestamp >= start_date,
    ).all()

    result = OrderedDict()

    diff_thresholds = [50, 100, 150, 200, 250, 300]
    
    max_threshold = diff_thresholds[-1]

    result[f'{-max_threshold} and below'] = 0

    for diff in reversed(diff_thresholds):
        result[f'{-diff} to {-diff + 50}'] = 0

    for diff in diff_thresholds:
        result[f'{diff - 50} to {diff}'] = 0
    
    result[f'{max_threshold} and above'] = 0
    

    for row in data:
        # if open is 700 and close is 750 then change is 50
        change = row.close - row.open
        
        for diff in diff_thresholds:
            if change >= diff - 50 and change < diff:
                result[f'{diff - 50} to {diff}'] += 1
            elif change <= -diff + 50 and change > -diff:
                result[f'{-diff} to {-diff + 50}'] += 1            
            
        if change >= max_threshold:
            result[f'{max_threshold} and above'] += 1
        if change <= -max_threshold:
            result[f'{-max_threshold} and below'] += 1

    return result


@app.post("/stocks/{stock_symbol}")
def update_stock_data(start_year: int = 2001, stock_symbol: str = "NSE:NIFTY50-INDEX", db: Session = Depends(get_db)):
    fyers_record: models.ThirdPartyToken = (
        db.query(models.ThirdPartyToken).filter_by(website="fyers").first()
    )

    symbol = (
        db.query(models.SymbolMaster)
        .filter_by(ticker=stock_symbol, exchange="NSE", is_active=True)
        .first()
    )

    if not symbol:
        return {"error": "No stock found!"}

    if (
        not fyers_record
        or fyers_record.access_token is None
        or fyers_record.access_token == ""
    ):
        return {"error": "No access token found!"}

    fyers = fyersModel.FyersModel(
        client_id=constants.fyers_app_id, 
        token=fyers_record.access_token,
        log_path="./logs",
    )
    
    start_date = datetime.datetime(start_year, 1, 1)
    end_date = datetime.datetime.now()

    last_updated_date = controllers.get_last_updated_date(symbol.id, db)
    if last_updated_date:
        start_date = last_updated_date + datetime.timedelta(days=1)

    candle_list = []
    intervals = utils.split_date_range_into_intervals(start_date, end_date, 364)
    for range in intervals:
        data = {
            "symbol": stock_symbol,
            "resolution": "D",
            "date_format": "0",
            "range_from": calendar.timegm(range[0].timetuple()),
            "range_to": calendar.timegm(range[1].timetuple()),
            "cont_flag": "1",
        }

        response: types.FyersHistoryResponse = fyers.history(data=data)

        if not isinstance(response, dict):
            return {"error": "Invalid response from fyers!", "response": response}

        candle_list.extend(response.get("candles", []))

    history_data = [
        {
            "symbol_master_id": symbol.id,
            "timestamp": datetime.datetime.fromtimestamp(candle[0]),
            "open": candle[1],
            "high": candle[2],
            "low": candle[3],
            "close": candle[4],
            "volume": candle[5],
        }
        for candle in candle_list
    ]

    db.bulk_insert_mappings(models.SymbolHistory, history_data)
    db.commit()

    return {"msg": f"Successfully inserted candles! from {start_date} to {end_date}"}
