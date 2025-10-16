import asyncio
import datetime
from abc import ABC, abstractmethod
from decimal import Decimal
from enum import Enum
from typing import List, Optional

import numpy
from async_lru import alru_cache
from pydantic import ConfigDict

from sirius.common import DataClass, Currency
from sirius.exceptions import SiriusException
from sirius.http_requests import ServerSideException


def calculate_annualized_return(starting: Decimal, ending: Decimal, number_of_days: int) -> Decimal:
    daily_return = (ending / starting)
    annualization_factor = Decimal("365") / Decimal(number_of_days)
    annualized_return = daily_return ** annualization_factor - Decimal("1")
    return annualized_return


class MarketDataException(SiriusException):
    pass


class Exchange(Enum):
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"


class Asset(DataClass):
    name: str
    currency: Currency


class Stock(Asset, ABC):
    ticker: str

    @classmethod
    async def _get_local_object(cls, other: "Stock") -> "Stock":
        if isinstance(other, cls):
            return other
        else:
            stock: Stock | None = await cls._find(other.ticker)
            if not stock:
                raise MarketDataException(f"Could not find stock with ticker: {other.ticker}")

            return stock

    @staticmethod
    @abstractmethod
    async def _find(ticker: str) -> Optional["Stock"]:
        ...

    @staticmethod
    async def find(ticker: str) -> Optional["Stock"]:
        from sirius.market_data.database import CachedStock
        return await CachedStock._find(ticker)

    @staticmethod
    async def get(ticker: str) -> "Stock":
        stock: Stock = await Stock.find(ticker)
        if not stock:
            raise MarketDataException(f"Could not find stock with ticker: {ticker}")

        return stock


class Option(Asset, ABC):
    underlying_stock: Stock
    strike_price: Decimal
    expiry_date: datetime.date
    type: str

    @staticmethod
    @abstractmethod
    async def _find_all_options(ticker: str, number_of_days_to_expiry: int) -> List["Option"]:
        ...

    @staticmethod
    async def find_all_options(ticker: str, number_of_days_to_expiry: int) -> List["Option"]:
        from sirius.market_data.database import CachedOption
        return await CachedOption._find_all_options(ticker, number_of_days_to_expiry)


class StockMarketData(DataClass, ABC):
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    timestamp: datetime.datetime
    stock: Stock

    @staticmethod
    @abstractmethod
    async def _get(abstract_stock: Stock, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> List["StockMarketData"]:
        ...

    @staticmethod
    async def get(stock: Stock, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime | None = None) -> List["StockMarketData"]:
        from sirius.market_data.database import CachedStockMarketData
        to_timestamp = datetime.datetime.now() if not to_timestamp else to_timestamp
        return await CachedStockMarketData._get(stock, from_timestamp, to_timestamp)


class StockPerformance(DataClass):
    position_open: StockMarketData
    position_close: StockMarketData
    absolute_return: Decimal
    annualized_return: Decimal
    model_config = ConfigDict(frozen=True)

    @staticmethod
    def _construct(position_open: StockMarketData, position_close: StockMarketData) -> "StockPerformance":
        absolute_return: Decimal = (position_close.close - position_open.close) / position_open.close
        number_of_days = Decimal((position_close.timestamp.date() - position_open.timestamp.date()).days)
        annualized_return = calculate_annualized_return(position_open.close, position_close.close, int(number_of_days))

        return StockPerformance(
            position_open=position_open,
            position_close=position_close,
            absolute_return=absolute_return,
            annualized_return=annualized_return
        )

    @staticmethod
    @alru_cache(maxsize=50, ttl=600)  # 5 min cache
    async def get(ticker: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime, buffer: datetime.timedelta | None = None) -> Optional["StockPerformance"]:
        buffer = datetime.timedelta(days=1) if not buffer else buffer
        stock: Stock = await Stock.get(ticker)
        market_data_list: List[StockMarketData] = await StockMarketData.get(stock, from_timestamp, to_timestamp)

        if not market_data_list:
            return None

        position_open: StockMarketData = min(market_data_list, key=lambda m: m.timestamp)
        position_close: StockMarketData = max(market_data_list, key=lambda m: m.timestamp)

        if (position_open.timestamp - from_timestamp) > buffer or (to_timestamp - position_close.timestamp) > buffer:
            return None

        return StockPerformance._construct(position_open, position_close)


class StockPerformanceAnalysis(DataClass):
    stock_performance_list: List[StockPerformance]
    standard_deviation_absolute_return: Decimal
    standard_deviation_annualized_return: Decimal
    mean_absolute_return: Decimal
    mean_annualized_return: Decimal
    median_absolute_return: Decimal
    median_annualized_return: Decimal
    min_absolute_return: Decimal
    min_annualized_return: Decimal
    max_absolute_return: Decimal
    max_annualized_return: Decimal

    @staticmethod
    @alru_cache(maxsize=50, ttl=600)  # 5 min cache
    async def get(ticker: str, number_of_days_invested: int, number_of_days_to_analyse: int, analysis_end_timestamp: datetime.datetime | None = None) -> "StockPerformanceAnalysis":
        analysis_end_timestamp = datetime.datetime.now() if not analysis_end_timestamp else analysis_end_timestamp
        analysis_dates_list: List[datetime.datetime] = [analysis_end_timestamp - datetime.timedelta(days=day + number_of_days_invested) for day in range(number_of_days_to_analyse)]
        raw_stock_performance_list: List[Optional[StockPerformance]] = await asyncio.gather(*[StockPerformance.get(ticker, date, date + datetime.timedelta(days=number_of_days_invested)) for date in analysis_dates_list])
        stock_performance_list: List[StockPerformance] = [result for result in raw_stock_performance_list if result is not None]

        if not stock_performance_list:
            raise ServerSideException("Did not retrieve any Market Data")

        absolute_return_list: List[Decimal] = [stock_performance.absolute_return for stock_performance in stock_performance_list]
        annualized_return_list: List[Decimal] = [stock_performance.annualized_return for stock_performance in stock_performance_list]
        standard_deviation_absolute_return: Decimal = Decimal(str(numpy.std(absolute_return_list)))  # type: ignore[arg-type]
        standard_deviation_annualized_return: Decimal = Decimal(str(numpy.std(annualized_return_list)))  # type: ignore[arg-type]
        mean_absolute_return: Decimal = Decimal(str(numpy.mean(absolute_return_list)))  # type: ignore[arg-type]
        mean_annualized_return: Decimal = Decimal(str(numpy.mean(annualized_return_list)))  # type: ignore[arg-type]
        median_absolute_return: Decimal = Decimal(str(numpy.median(absolute_return_list)))  # type: ignore[arg-type]
        median_annualized_return: Decimal = Decimal(str(numpy.median(annualized_return_list)))  # type: ignore[arg-type]
        min_absolute_return: Decimal = Decimal(str(numpy.min(absolute_return_list)))  # type: ignore[arg-type]
        min_annualized_return: Decimal = Decimal(str(numpy.min(annualized_return_list)))  # type: ignore[arg-type]
        max_absolute_return: Decimal = Decimal(str(numpy.max(absolute_return_list)))  # type: ignore[arg-type]
        max_annualized_return: Decimal = Decimal(str(numpy.max(annualized_return_list)))  # type: ignore[arg-type]

        return StockPerformanceAnalysis(
            stock_performance_list=stock_performance_list,
            standard_deviation_absolute_return=standard_deviation_absolute_return,
            standard_deviation_annualized_return=standard_deviation_annualized_return,
            mean_absolute_return=mean_absolute_return,
            mean_annualized_return=mean_annualized_return,
            median_absolute_return=median_absolute_return,
            median_annualized_return=median_annualized_return,
            min_absolute_return=min_absolute_return,
            min_annualized_return=min_annualized_return,
            max_absolute_return=max_absolute_return,
            max_annualized_return=max_annualized_return
        )
