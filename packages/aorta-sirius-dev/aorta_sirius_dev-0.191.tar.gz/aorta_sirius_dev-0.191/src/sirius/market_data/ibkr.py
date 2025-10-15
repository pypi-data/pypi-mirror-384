import asyncio
import datetime
import itertools
from decimal import Decimal
from typing import List, Dict, Any, cast, Set, Callable, Optional

from async_lru import alru_cache
from pydantic import ConfigDict

from sirius import common
from sirius.common import Currency
from sirius.exceptions import SiriusException
from sirius.http_requests import HTTPResponse, ServerSideException
from sirius.ibkr import session, base_url
from sirius.market_data import Stock, Option, StockMarketData, Exchange

OPTIONS_DATE_FORMAT: str = "%b%y"


class IBKRException(SiriusException):
    pass


class IBKRStock(Stock):
    contract_id: int
    model_config = ConfigDict(frozen=True)

    @staticmethod
    @alru_cache(maxsize=50, ttl=86_400)  # 24 hour cache
    async def _find(ticker: str) -> Optional[Stock]:
        response: HTTPResponse = await session.get(f"{base_url}iserver/secdef/search?symbol={ticker}&secType=STK")
        filtered_list: List[Dict[str, Any]] = list(filter(lambda d: d["description"] in Exchange, response.data))
        contract_id_list: List[int] = [int(data["conid"]) for data in filtered_list]

        if not contract_id_list:
            return None

        if len(contract_id_list) > 1:
            raise IBKRException(f"More than one stock found for the ticker: {ticker}")

        contract_id: int = contract_id_list[0]
        response = await session.get(f"{base_url}iserver/contract/{contract_id}/info")
        return IBKRStock(
            name=response.data["company_name"],
            currency=Currency(response.data["currency"]),
            ticker=response.data["symbol"],
            contract_id=contract_id
        )


class IBKROption(Option):
    contract_id: int

    @staticmethod
    async def __get_all_expiry_month_list(stock: IBKRStock, number_of_days_to_expiry: int | None = None) -> List[datetime.date]:
        number_of_days_to_expiry = 3 if not number_of_days_to_expiry else number_of_days_to_expiry
        response: HTTPResponse = await session.get(f"{base_url}iserver/secdef/search?symbol={stock.ticker}&secType=STK")
        data: Dict[str, Any] = next(filter(lambda c: int(c["conid"]) == stock.contract_id, response.data))
        option_data: Dict[str, Any] = next(filter(lambda o: o["secType"] == "OPT", data["sections"]))
        all_expiry_month_str_list: List[str] = option_data["months"].split(";")
        all_expiry_month_list: List[datetime.date] = [datetime.datetime.strptime(expiry_month, OPTIONS_DATE_FORMAT).date() for expiry_month in all_expiry_month_str_list]

        return [date for date in all_expiry_month_list if (date - datetime.datetime.now().date()).days <= number_of_days_to_expiry]

    @staticmethod
    async def __get_for_strike_and_expiry(stock: IBKRStock, expiry_month: datetime.date, strike_price: Decimal) -> List["IBKROption"]:
        expiry_month_str: str = expiry_month.strftime(OPTIONS_DATE_FORMAT).upper()
        response: HTTPResponse = await session.get(
            f"{base_url}iserver/secdef/info",
            query_params={
                "conid": stock.contract_id,
                "sectype": "OPT",
                "month": expiry_month_str,
                "strike": float(strike_price)}
        )

        return [IBKROption(
            contract_id=data["conid"],
            strike_price=strike_price,
            expiry_date=datetime.datetime.strptime(data["maturityDate"], '%Y%m%d').date(),
            type="CALL" if data["right"] == "C" else "PUT",
            underlying_stock=stock,
            name=f"{stock.name} | {common.get_decimal_str(strike_price)}",
            currency=stock.currency
        ) for data in response.data]

    @staticmethod
    @alru_cache(maxsize=50, ttl=43_200)  # 12 hour cache
    async def _get(abstract_stock: Stock, number_of_days_to_expiry: int) -> List[Option]:
        stock = cast(IBKRStock, await IBKRStock._get_local_object(abstract_stock))
        option_contract_list: List[Option] = []
        expiry_month_list: List[datetime.date] = await IBKROption.__get_all_expiry_month_list(stock, number_of_days_to_expiry)
        expiry_month_str_list: List[str] = [expiry_month.strftime(OPTIONS_DATE_FORMAT).upper() for expiry_month in expiry_month_list]

        responses: List[HTTPResponse] = await asyncio.gather(*[
            session.get(f"{base_url}iserver/secdef/strikes", query_params={"conid": stock.contract_id, "sectype": "OPT", "month": expiry_month_str})
            for expiry_month_str in expiry_month_str_list
        ])
        for expiry_month, response in zip(expiry_month_list, responses):
            all_strike_price_set: Set[Decimal] = set([Decimal(str(strike_price)) for strike_price in response.data.get("call", [])])
            all_strike_price_set.update([Decimal(str(strike_price)) for strike_price in response.data.get("put", [])])
            all_option_contract_list: List[IBKROption] = list(itertools.chain.from_iterable(await asyncio.gather(*[
                IBKROption.__get_for_strike_and_expiry(stock, expiry_month, strike_price)
                for strike_price in all_strike_price_set
            ])))

            option_contract_list.extend(
                [option
                 for option in all_option_contract_list
                 if (option.expiry_date - datetime.datetime.now().date()).days == number_of_days_to_expiry]
            )

        return option_contract_list


class IBKRStockMarketData(StockMarketData):
    @staticmethod
    async def __get_ohlc_data(contract_id: int, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> List[Dict[str, float]]:
        DATE_FORMAT: str = "%Y%m%d-%H:%M:%S"
        try:
            response = await session.get(
                f"{base_url}iserver/marketdata/history",
                query_params={
                    "conid": contract_id,
                    "period": "999d",
                    "bar": "1d",
                    "startTime": (to_timestamp + datetime.timedelta(days=1)).strftime(DATE_FORMAT),  # IBKR sends data 1 day earlier, no idea why.
                    "direction": "-1"
                }
            )
        except ServerSideException as e:
            raise ServerSideException("Did not retrieve any historical market data due to: " + str(e))

        data = response.data.get("data", [])
        earliest_data_timestamp = min([datetime.datetime.fromtimestamp(d["t"] / 1000) for d in data])

        if earliest_data_timestamp > from_timestamp:
            more_data = await IBKRStockMarketData.__get_ohlc_data(contract_id, from_timestamp, earliest_data_timestamp)
            return list(itertools.chain(data, more_data))

        return data

    @staticmethod
    async def _get(abstract_stock: Stock, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> List["StockMarketData"]:
        from_timestamp = common.get_next_business_day_adjusted_date(from_timestamp)
        to_timestamp = common.get_previous_business_day_adjusted_date(to_timestamp)
        stock = cast(IBKRStock, await IBKRStock._get_local_object(abstract_stock))
        raw_ohlc_data_list: List[Dict[str, float]] = await IBKRStockMarketData.__get_ohlc_data(stock.contract_id, from_timestamp, to_timestamp)

        return [IBKRStockMarketData(
            open=Decimal(str(ohlc_data["o"])),
            high=Decimal(str(ohlc_data["h"])),
            low=Decimal(str(ohlc_data["l"])),
            close=Decimal(str(ohlc_data["c"])),
            timestamp=datetime.datetime.fromtimestamp(ohlc_data["t"] / 1000),
            stock=stock)
            for ohlc_data in raw_ohlc_data_list
            if from_timestamp.timestamp() <= ohlc_data["t"] / 1000 <= to_timestamp.timestamp()]

    @staticmethod
    @alru_cache(maxsize=50, ttl=600)  # 5 min cache
    async def get_latest_price(contract_id: int) -> Decimal:
        is_response_valid: Callable = lambda r: "31" in r.data[0].keys() and r.data[0]["31"] != ""
        number_of_tries: int = 1
        response: HTTPResponse = await session.get(f"{base_url}iserver/marketdata/snapshot", query_params={"conids": contract_id, "fields": "7295,70,71,31,87"})
        while number_of_tries < 5 and not is_response_valid(response):
            await asyncio.sleep(0.1)
            response = await session.get(f"{base_url}iserver/marketdata/snapshot", query_params={"conids": contract_id, "fields": "7295,70,71,31,87"})
            number_of_tries = number_of_tries + 1

        if not is_response_valid(response):
            raise ServerSideException("Did not retrieve any market data.")

        return Decimal(response.data[0]["31"].replace("H", "").replace("C", ""))
