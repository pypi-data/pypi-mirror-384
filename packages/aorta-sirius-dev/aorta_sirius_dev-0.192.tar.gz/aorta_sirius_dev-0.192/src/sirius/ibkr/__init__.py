import asyncio
from enum import Enum, auto
from typing import List

import httpx

from sirius import common
from sirius.common import DataClass
from sirius.http_requests import AsyncHTTPSession, HTTPResponse

_account_list: List["IBKRAccount"] = []
_account_list_lock = asyncio.Lock()

base_url: str = common.get_environmental_secret("IBKR_SERVICE_BASE_URL", "https://ibkr-service:5000/v1/api/")
session: AsyncHTTPSession = AsyncHTTPSession(base_url)
session.client = httpx.AsyncClient(verify=False, timeout=60)
OPTIONS_DATE_FORMAT: str = "%b%y"


class ContractType(Enum):
    STOCK = "STK"
    OPTION = "OPT"
    FUTURE = "FUT"
    FUTURE_OPTION = "FOP"
    BOND = "BND"


class OptionContractType(Enum):
    PUT = auto()
    CALL = auto()


class IBKRAccount(DataClass):
    id: str
    name: str

    @staticmethod
    async def get_all_ibkr_accounts() -> List["IBKRAccount"]:
        global _account_list
        if len(_account_list) == 0:
            async with _account_list_lock:
                if len(_account_list) == 0:
                    response: HTTPResponse = await session.get(f"{base_url}/portfolio/accounts/")
                    _account_list = [IBKRAccount(id=data["id"], name=data["accountAlias"] if data["accountAlias"] else data["id"]) for data in response.data]

        return _account_list

#
#

#
# class OptionPerformanceAnalysis(DataClass):
#     option_contract: OptionContract
#     contract_performance_analysis: ContractPerformanceAnalysis
#     itm_probability: Decimal
#
#     @staticmethod
#     async def get(option_contract: OptionContract) -> "OptionPerformanceAnalysis":
#         today: datetime.date = datetime.datetime.now().date()
#         number_of_days_to_analyse: int = (today - today.replace(year=today.year - 10)).days
#         number_of_days_invested: int = (option_contract.expiry_date - datetime.datetime.now().date()).days
#         underlying_price: Decimal = await MarketData.get_latest_price(option_contract.underlying_contract.id)
#         itm_required_absolute_return: Decimal = (option_contract.strike_price - underlying_price) / underlying_price
#         contract_performance_analysis: ContractPerformanceAnalysis = await ContractPerformanceAnalysis.get(option_contract.underlying_contract.id, number_of_days_invested, number_of_days_to_analyse)
#         itm_probability_func: Callable[[], Decimal] = lambda: Decimal(str(norm.cdf(float(itm_required_absolute_return), float(contract_performance_analysis.mean_absolute_return), float(contract_performance_analysis.standard_deviation_absolute_return))))
#         itm_probability: Decimal = itm_probability_func() if option_contract.type == OptionContractType.PUT else Decimal("1") - itm_probability_func()
#
#         return OptionPerformanceAnalysis(
#             option_contract=option_contract,
#             contract_performance_analysis=contract_performance_analysis,
#             itm_probability=itm_probability
#         )
