import datetime
from typing import Optional, List, cast, Dict, Set

from async_lru import alru_cache
from beanie import DecimalAnnotation, Link

from sirius import common
from sirius.common import PersistedDataClass
from sirius.market_data import Stock, StockMarketData
from sirius.market_data.ibkr import IBKRStockMarketData, IBKRStock


class CachedStock(PersistedDataClass, Stock):  # type:ignore[misc]
    id: str  # type:ignore[assignment]

    @staticmethod
    @alru_cache(maxsize=50, ttl=86_400)  # 24 hour cache
    async def _find_from_data_provider(ticker: str) -> Optional["CachedStock"]:
        ibkr_stock: IBKRStock = cast(IBKRStock, await IBKRStock._find(ticker))
        return CachedStock(
            id=ibkr_stock.ticker,
            name=ibkr_stock.name,
            ticker=ibkr_stock.ticker,
            currency=ibkr_stock.currency
        )

    @staticmethod
    @alru_cache(maxsize=50, ttl=86_400)  # 24 hour cache
    async def _find(ticker: str) -> Optional["Stock"]:
        cached_stock: CachedStock | None = await CachedStock.get(ticker)
        if cached_stock:
            return cached_stock

        cached_stock = await CachedStock._find_from_data_provider(ticker)
        return await cached_stock.save()


class CachedStockMarketData(PersistedDataClass, StockMarketData):  # type:ignore[misc]
    id: str  # type:ignore[assignment]
    open: DecimalAnnotation
    high: DecimalAnnotation
    low: DecimalAnnotation
    close: DecimalAnnotation
    stock: Link[CachedStock]  # type:ignore[assignment]

    class Settings:
        use_cache = True

    @staticmethod
    @alru_cache(maxsize=50, ttl=43_200)  # 12 hour cache
    async def _get_from_data_provider(ticker: str, from_timestamp: datetime.datetime) -> List["CachedStockMarketData"]:
        abstract_stock: Stock = await Stock.get(ticker)
        stock: CachedStock = cast(CachedStock, await CachedStock._get_local_object(abstract_stock))
        latest_market_data_list: List[StockMarketData] = await IBKRStockMarketData._get(abstract_stock, from_timestamp, datetime.datetime.now())

        return [CachedStockMarketData(
            id=f"{market_data.stock.ticker} | {int(market_data.timestamp.timestamp())}",
            open=market_data.open,
            high=market_data.high,
            low=market_data.low,
            close=market_data.close,
            timestamp=market_data.timestamp,
            stock=stock)
            for market_data in latest_market_data_list]

    @staticmethod
    async def _update_cache(ticker: str, from_timestamp: datetime.datetime | None = None) -> List["CachedStockMarketData"]:
        from_timestamp = (datetime.datetime.now().replace(year=datetime.datetime.now().year - 10)) if not from_timestamp else from_timestamp  # 10 years
        current_data: Dict[str, CachedStockMarketData] = {data.id: data for data in await CachedStockMarketData._get_all(ticker, is_update_cache=False)}
        latest_data: Dict[str, CachedStockMarketData] = {data.id: data for data in await CachedStockMarketData._get_from_data_provider(ticker, from_timestamp)}
        new_data_ids: Set[str] = latest_data.keys() - current_data.keys()
        unique_data_to_update_list: List[CachedStockMarketData] = [latest_data[k] for k in new_data_ids]
        await CachedStockMarketData.insert_many(unique_data_to_update_list)

        return unique_data_to_update_list

    @staticmethod
    @alru_cache(maxsize=50, ttl=43_200)  # 12 hour cache
    async def _get_all(ticker: str, is_update_cache: bool = True) -> List["CachedStockMarketData"]:
        all_data_list: List[CachedStockMarketData] = await CachedStockMarketData.find(CachedStockMarketData.stock.id == ticker, fetch_links=False).to_list()  # type:ignore[attr-defined]
        latest_data: CachedStockMarketData | None = max(all_data_list, key=lambda d: d.timestamp) if all_data_list else None
        expected_latest_data_date: datetime.datetime = common.get_previous_business_day(datetime.datetime.now())

        if is_update_cache and (not all_data_list or (expected_latest_data_date - latest_data.timestamp).days > 1):
            all_data_list = all_data_list + await CachedStockMarketData._update_cache(ticker, latest_data.timestamp if latest_data else None)

        return all_data_list

    @staticmethod
    async def _get(abstract_stock: Stock, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> List["StockMarketData"]:
        from_timestamp = common.get_next_business_day_adjusted_date(from_timestamp)
        to_timestamp = common.get_previous_business_day_adjusted_date(to_timestamp)
        cached_data_list: List[CachedStockMarketData] = await CachedStockMarketData._get_all(abstract_stock.ticker)

        return [obj for obj in cached_data_list if from_timestamp <= obj.timestamp <= to_timestamp]
