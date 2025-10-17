from decimal import Decimal
from typing import Any, Dict

from pydantic import ConfigDict, Field, SecretStr

from hummingbot.client.config.config_data_types import BaseConnectorConfigMap
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

CENTRALIZED = True
EXAMPLE_PAIR = "VD-USDT"

DEFAULT_FEES = TradeFeeSchema(
    maker_percent_fee_decimal=Decimal("0.001"),
    taker_percent_fee_decimal=Decimal("0.001"),
    buy_percent_fee_deducted_from_returns=True
)


def is_exchange_information_valid(exchange_info: Dict[str, Any]) -> bool:
    """
    Verifies if a trading pair is enabled to operate with based on its exchange information
    :param exchange_info: the exchange information for a trading pair
    :return: True if the trading pair is enabled, False otherwise
    """
    # is_spot = False
    is_trading = False

    if exchange_info.get("status", None) == "TRADING":
        is_trading = True

    # permissions_sets = exchange_info.get("permissionSets", list())
    # for permission_set in permissions_sets:
    #     # PermissionSet is a list, find if in this list we have "SPOT" value or not
    #     if "SPOT" in permission_set:
    #         is_spot = True
    #         break

    # return is_trading and is_spot
    return is_trading


class VindaxConfigMap(BaseConnectorConfigMap):
    connector: str = "vindax"
    vindax_api_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": lambda cm: "Enter your Vindax API key",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )
    vindax_api_secret: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": lambda cm: "Enter your Vindax API secret",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )
    model_config = ConfigDict(title="vindax")


KEYS = VindaxConfigMap.model_construct()

OTHER_DOMAINS = ["vindax_us"]
OTHER_DOMAINS_PARAMETER = {"vindax_us": "us"}
OTHER_DOMAINS_EXAMPLE_PAIR = {"vindax_us": "BTC-USDT"}
OTHER_DOMAINS_DEFAULT_FEES = {"vindax_us": DEFAULT_FEES}


class VindaxUSConfigMap(BaseConnectorConfigMap):
    connector: str = "vindax_us"
    vindax_api_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Vindax US API key",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )
    vindax_api_secret: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Vindax US API secret",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )
    model_config = ConfigDict(title="vindax_us")


OTHER_DOMAINS_KEYS = {"vindax_us": VindaxUSConfigMap.model_construct()}
