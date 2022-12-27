import models
import uvicorn
import yfinance 
from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import Stock

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

class StockRequest(BaseModel):
    symbol: str

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@app.get("/")
def dashboard(request: Request, price = None, forward_pe = None, dividend_yield = None, ma50 = None, ma200 = None, db: Session = Depends(get_db)):
    # Displays the stock screener dashboard
    stocks = db.query(Stock)
    if forward_pe:
        stocks = stocks.filter(Stock.forward_pe < forward_pe)

    if dividend_yield:
        stocks = stocks.filter(Stock.dividend_yield > dividend_yield)

    if ma50:
        stocks = stocks.filter(Stock.price > Stock.ma50)

    if ma200:
        stocks = stocks.filter(Stock.price > Stock.ma200)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stocks": stocks,
        "price": price,
        "dividend_yield": dividend_yield,
        "forward_pe": forward_pe,
        "ma200": ma200,
        "ma50": ma50
    })

def fetch_stock_data(id: int):
    db = SessionLocal()
    stock = db.query(Stock).filter(Stock.id == id).first()
    # Gets real time stock data for the stock
    yahoo_data = yfinance.Ticker(stock.symbol)
    stock.ma200 = yahoo_data.info["twoHundredDayAverage"]
    stock.ma50 = yahoo_data.info["fiftyDayAverage"]
    stock.price = yahoo_data.info["previousClose"]
    stock.forward_pe = yahoo_data.info["forwardPE"]
    stock.forward_eps = yahoo_data.info["forwardEps"]
    if yahoo_data.info["dividendYield"] != None:
        stock.dividend_yield = yahoo_data.info["dividendYield"] * 100
    # Add new stock record to session and commit it
    db.add(stock)
    db.commit()

@app.post("/stock")
# Executes a background task and populates a database using Yahoo Finance data
async def create_stock(stock_request: StockRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Creates a stock that's stored in the database
    stock = Stock()
    stock.symbol = stock_request.symbol.upper()
    # Uses database session to add object to session and commit it to database
    db.add(stock)
    db.commit()
    background_tasks.add_task(fetch_stock_data, stock.id)
    return {
        "code": "success",
        "message": "stock created"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")