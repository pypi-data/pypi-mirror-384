import datetime
import os
from _decimal import Decimal
from abc import ABC
from enum import Enum
from pathlib import Path
from typing import Any, Dict

from beanie import Document
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict
from starlette import status

from sirius.constants import EnvironmentVariable, EnvironmentSecret
from sirius.exceptions import ApplicationException


class Environment(Enum):
    Production = "Production"
    Test = "Test"
    Development = "Development"
    CI_CD_PIPELINE = "CI/CD Pipeline"


class Currency(Enum):
    AED = "AED"
    AUD = "AUD"
    BDT = "BDT"
    BGN = "BGN"
    CAD = "CAD"
    CHF = "CHF"
    CLP = "CLP"
    CNY = "CNY"
    CRC = "CRC"
    CZK = "CZK"
    DKK = "DKK"
    EGP = "EGP"
    EUR = "EUR"
    GBP = "GBP"
    GEL = "GEL"
    HKD = "HKD"
    HUF = "HUF"
    IDR = "IDR"
    ILS = "ILS"
    INR = "INR"
    JPY = "JPY"
    KES = "KES"
    KRW = "KRW"
    LKR = "LKR"
    MAD = "MAD"
    MXN = "MXN"
    MYR = "MYR"
    NGN = "NGN"
    NOK = "NOK"
    NPR = "NPR"
    NZD = "NZD"
    PHP = "PHP"
    PKR = "PKR"
    PLN = "PLN"
    RON = "RON"
    SEK = "SEK"
    SGD = "SGD"
    THB = "THB"
    TRY = "TRY"
    TZS = "TZS"
    UAH = "UAH"
    UGX = "UGX"
    USD = "USD"
    UYU = "UYU"
    VND = "VND"
    XOF = "XOF"
    ZAR = "ZAR"


class DataClass(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class PersistedDataClass(Document, ABC):
    pass


def get_environmental_variable(environmental_variable: EnvironmentVariable | str) -> str:
    environmental_variable_key: str = environmental_variable.value if isinstance(environmental_variable,
                                                                                 EnvironmentVariable) else environmental_variable
    value: str | None = os.getenv(environmental_variable_key)
    if value is None:
        raise ApplicationException(f"Environment variable with the key is not available: {environmental_variable_key}")

    return value


def get_environmental_secret(environmental_secret: EnvironmentSecret | str, default_value: str | None = None) -> str:
    environmental_secret_key: str = environmental_secret.value if isinstance(environmental_secret, EnvironmentSecret) else environmental_secret
    environmental_secret_value: str = os.getenv(environmental_secret_key)

    return environmental_secret_value if environmental_secret_value else default_value


def get_environment() -> Environment:
    environment: str | None = os.getenv(EnvironmentVariable.ENVIRONMENT.value)
    try:
        return Environment.Development if environment is None else Environment(environment)
    except ValueError:
        raise ApplicationException(f"Invalid environment variable setup: {environment}")


def is_production_environment() -> bool:
    return Environment.Production == get_environment()


def is_test_environment() -> bool:
    return Environment.Test == get_environment()


# TODO: Create redundancy check (if a test/production environment is identified as development, no authentication is done)
def is_development_environment() -> bool:
    return Environment.Development == get_environment() or is_ci_cd_pipeline_environment()


def is_ci_cd_pipeline_environment() -> bool:
    return Environment.CI_CD_PIPELINE == get_environment()


def get_application_name() -> str:
    return get_environmental_secret(EnvironmentSecret.APPLICATION_NAME) or Path.cwd().name.title()


def is_dict_include_another_dict(one_dict: Dict[Any, Any], another_dict: Dict[Any, Any]) -> bool:
    if not all(key in one_dict for key in another_dict):
        return False

    for key, value in one_dict.items():
        if another_dict[key] != value:
            return False

    return True


def get_decimal_str(decimal: Decimal) -> str:
    return "{:,.2f}".format(float(decimal))


def get_date_string(date: datetime.date) -> str:
    return date.strftime("%d/%b/%Y")


def get_central_finite_curve_authentication_headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {get_environmental_secret("API_KEY")}"} if is_production_environment() else {"Authorization": f"Bearer NULL"}


def verify_token(token: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))) -> None:
    if not is_production_environment():
        return

    if token.credentials != get_environmental_secret("API_KEY"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Bearer"}, )


def get_previous_business_day(timestamp: datetime.datetime) -> datetime.datetime:
    previous_business_day: datetime.datetime = timestamp - datetime.timedelta(days=1)
    previous_business_day = previous_business_day.replace(hour=23, minute=59, second=59, microsecond=0)
    return get_previous_business_day_adjusted_date(previous_business_day)


def get_next_business_day_adjusted_date(timestamp: datetime.datetime) -> datetime.datetime:
    next_day: datetime.datetime = timestamp
    while next_day.weekday() >= 5:
        next_day += datetime.timedelta(days=1)
        next_day = next_day.replace(hour=0, minute=0, second=0, microsecond=0)

    return next_day


def get_previous_business_day_adjusted_date(timestamp: datetime.datetime) -> datetime.datetime:
    prev_day: datetime.datetime = timestamp
    while prev_day.weekday() >= 5:
        prev_day -= datetime.timedelta(days=1)
        prev_day = prev_day.replace(hour=23, minute=59, second=59, microsecond=0)

    return prev_day
