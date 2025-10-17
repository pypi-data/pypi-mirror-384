import asyncio
import time
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from bidict import bidict

from hummingbot.connector.constants import s_decimal_NaN
from hummingbot.connector.exchange.vindax import (
    vindax_constants as CONSTANTS,
    vindax_utils,
    vindax_web_utils as web_utils,
)
from hummingbot.connector.exchange.vindax.vindax_api_order_book_data_source import VindaxAPIOrderBookDataSource
from hummingbot.connector.exchange.vindax.vindax_api_user_stream_data_source import VindaxAPIUserStreamDataSource
from hummingbot.connector.exchange.vindax.vindax_auth import VindaxAuth
from hummingbot.connector.exchange_py_base import ExchangePyBase
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.connector.utils import TradeFillOrderDetails, combine_to_hb_trading_pair
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderState, OrderUpdate, TradeUpdate
from hummingbot.core.data_type.order_book_tracker_data_source import OrderBookTrackerDataSource
from hummingbot.core.data_type.trade_fee import (
    AddedToCostTradeFee,
    DeductedFromReturnsTradeFee,
    TokenAmount,
    TradeFeeBase,
)
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.event.events import MarketEvent, OrderFilledEvent
from hummingbot.core.utils.async_utils import safe_gather
from hummingbot.core.web_assistant.connections.data_types import RESTMethod
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory

if TYPE_CHECKING:
    from hummingbot.client.config.config_helpers import ClientConfigAdapter


class VindaxExchange(ExchangePyBase):
    UPDATE_ORDER_STATUS_MIN_INTERVAL = 10.0

    web_utils = web_utils

    def __init__(self,
                 client_config_map: "ClientConfigAdapter",
                 vindax_api_key: str,
                 vindax_api_secret: str,
                 #  disable_user_stream: bool = False,
                 trading_pairs: Optional[List[str]] = None,
                 trading_required: bool = True,
                 domain: str = CONSTANTS.DEFAULT_DOMAIN,
                 ):
        self.api_key = vindax_api_key
        # self._disable_user_stream = disable_user_stream
        # if disable_user_stream:
        #     self._user_stream_tracker = None
        self.secret_key = vindax_api_secret
        self._domain = domain
        self._trading_required = trading_required
        self._trading_pairs = trading_pairs
        self._last_trades_poll_vindax_timestamp = 1.0
        # self._order_queue = asyncio.Queue(maxsize=100)
        self._create_order_queue = asyncio.Queue()
        self._cancel_order_queue = asyncio.Queue()
        self._delay_seconds = CONSTANTS.ORDER_DELAY_TIME  # delay CREATE or CANCEL order TIME seconds
        asyncio.create_task(self._process_order_queue())
        asyncio.create_task(self._process_cancel_order_queue())
        super().__init__(client_config_map)

    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> float:
        """Parse ISO 8601 timestamp string to Unix timestamp in seconds"""
        try:
            # Parse ISO 8601 format: "2025-02-10T10:17:56.028Z"
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.timestamp()
        except (ValueError, AttributeError):
            # Fallback: try to parse as float (Unix timestamp)
            try:
                return float(timestamp_str)
            except (ValueError, TypeError):
                return 0.0

    @staticmethod
    def vindax_order_type(order_type: OrderType) -> str:
        return order_type.name.lower()

    @staticmethod
    def to_hb_order_type(vindax_type: str) -> OrderType:
        return OrderType[vindax_type.upper()]

    @property
    def authenticator(self):
        return VindaxAuth(
            api_key=self.api_key,
            secret_key=self.secret_key,
            time_provider=self._time_synchronizer)

    @property
    def name(self) -> str:
        if self._domain == "com":
            return "vindax"
        else:
            return f"vindax_{self._domain}"

    @property
    def rate_limits_rules(self):
        return CONSTANTS.RATE_LIMITS

    @property
    def domain(self):
        return self._domain

    @property
    def client_order_id_max_length(self):
        return CONSTANTS.MAX_ORDER_ID_LEN

    @property
    def client_order_id_prefix(self):
        return CONSTANTS.HBOT_ORDER_ID_PREFIX

    @property
    def trading_rules_request_path(self):
        return CONSTANTS.EXCHANGE_INFO_PATH_URL

    @property
    def trading_pairs_request_path(self):
        return CONSTANTS.EXCHANGE_INFO_PATH_URL

    @property
    def check_network_request_path(self):
        return CONSTANTS.PING_PATH_URL

    @property
    def trading_pairs(self):
        return self._trading_pairs

    @property
    def is_cancel_request_in_exchange_synchronous(self) -> bool:
        return True

    @property
    def is_trading_required(self) -> bool:
        return self._trading_required

    def supported_order_types(self):
        return [OrderType.LIMIT, OrderType.MARKET]

    async def get_all_pairs_prices(self) -> List[Dict[str, Any]]:
        # self.logger().info("Requesting all pairs prices")

        pairs_prices = await self._api_get(path_url=CONSTANTS.TICKER_BOOK_PATH_URL)
        # self.logger().info(f"All pairs prices response: {pairs_prices}")

        if isinstance(pairs_prices, dict):
            pairs_prices = [pairs_prices]
        return pairs_prices

    def _is_request_exception_related_to_time_synchronizer(self, request_exception: Exception):
        error_description = str(request_exception)
        is_time_synchronizer_related = ("-1021" in error_description
                                        and "Timestamp for this request" in error_description)
        return is_time_synchronizer_related

    def _is_order_not_found_during_status_update_error(self, status_update_exception: Exception) -> bool:
        # Xử lý lỗi khi order không tìm thấy trong quá trình cập nhật status
        error_message = str(status_update_exception).lower()
        return (
            "order not found" in error_message or
            "order does not exist" in error_message or
            "invalid order id" in error_message or
            "order already filled" in error_message or
            "order already cancelled" in error_message
        )

    def _is_order_not_found_during_cancelation_error(self, cancelation_exception: Exception) -> bool:
        # Xử lý lỗi khi order đã được filled và không thể cancel
        error_message = str(cancelation_exception).lower()
        return (
            "can't cancel order filled" in error_message or
            "order not found" in error_message or
            "order already filled" in error_message or
            "order already cancelled" in error_message
        )

    def _create_web_assistants_factory(self) -> WebAssistantsFactory:
        return web_utils.build_api_factory(
            throttler=self._throttler,
            time_synchronizer=self._time_synchronizer,
            domain=self._domain,
            auth=self._auth)

    def _create_order_book_data_source(self) -> OrderBookTrackerDataSource:
        return VindaxAPIOrderBookDataSource(
            trading_pairs=self._trading_pairs or [],
            connector=self,
            domain=self.domain,
            api_factory=self._web_assistants_factory)

    def _create_user_stream_data_source(self) -> UserStreamTrackerDataSource:
        return VindaxAPIUserStreamDataSource(
            auth=self._auth,
            trading_pairs=self._trading_pairs,
            connector=self,
            api_factory=self._web_assistants_factory
        )

    def _get_fee(self,
                 base_currency: str,
                 quote_currency: str,
                 order_type: OrderType,
                 order_side: TradeType,
                 amount: Decimal,
                 price: Decimal = s_decimal_NaN,
                 is_maker: Optional[bool] = None) -> TradeFeeBase:
        is_maker = order_type is OrderType.LIMIT_MAKER
        return AddedToCostTradeFee(percent=self.estimate_fee_pct(is_maker))

    # Vindax xu li delay order
    async def _process_order_queue(self):
        while True:
            order_payload, future = await self._create_order_queue.get()
            try:
                await asyncio.sleep(self._delay_seconds)  # optional delay
                order_result = await self._api_post(
                    path_url=CONSTANTS.ORDER_PATH_URL,
                    data=order_payload,
                    is_auth_required=True
                )
                o_id = str(order_result["orderId"])
                transact_time = order_result["time"] * 1e-3
                future.set_result((o_id, transact_time))
            except Exception as e:
                future.set_exception(e)
            finally:
                self._create_order_queue.task_done()

    async def _place_order(self,
                           order_id: str,
                           trading_pair: str,
                           amount: Decimal,
                           trade_type: TradeType,
                           order_type: OrderType,
                           price: Decimal,
                           **kwargs) -> Tuple[str, float]:

        # Vindax không hỗ trợ MARKET order
        if order_type is OrderType.MARKET:
            if trade_type is TradeType.BUY:
                price = await self._get_last_traded_price(trading_pair, price_type="ask")
            else:
                price = await self._get_last_traded_price(trading_pair, price_type="bid")

        amount_str = f"{amount:.4f}"
        # type_str = "limit" if order_type in [OrderType.LIMIT, OrderType.LIMIT_MAKER] else "market"
        type_str = "limit"  # Vindax chỉ hỗ trợ limit order
        action_str = "buy" if trade_type is TradeType.BUY else "sell"
        symbol = await self.exchange_symbol_associated_to_pair(trading_pair=trading_pair)

        api_params = {
            "symbol": symbol,
            "action": action_str,
            "type": type_str,
            "quantity": float(amount_str),
        }
        api_params["price"] = float(f"{price:.7f}")

        self.logger().info(f"Order Create, params: {api_params}, url: {CONSTANTS.ORDER_PATH_URL}")

        future: asyncio.Future = asyncio.get_event_loop().create_future()
        await self._create_order_queue.put((api_params, future))

        try:
            o_id, transact_time = await future
        except IOError as e:
            error_description = str(e)
            is_server_overloaded = ("status is 503" in error_description
                                    and "Unknown error, please check your request or try again later." in error_description)
            if is_server_overloaded:
                o_id = "UNKNOWN"
                transact_time = self._time_synchronizer.time()
            else:
                raise
        return o_id, transact_time

    # Vindax xu li delay order
    async def _process_cancel_order_queue(self):
        while True:
            cancel_order_payload, future = await self._cancel_order_queue.get()
            try:
                await asyncio.sleep(self._delay_seconds)  # optional delay
                cancel_result = await self._api_delete(
                    path_url=CONSTANTS.ORDER_PATH_URL,
                    params=cancel_order_payload,
                    is_auth_required=True)
                # self.logger().info(f"Order cancellation response: {cancel_result}")

                future.set_result(cancel_result)
            except Exception as e:
                future.set_exception(e)
            finally:
                self._cancel_order_queue.task_done()

    async def _place_cancel(self, order_id: str, tracked_order: InFlightOrder):
        # Requesting to cancel an empty order seems to hang the request
        if tracked_order.exchange_order_id is None:
            self.logger().warning(f"Failed to cancel order {order_id} with exchange_id: None")
            self.logger().debug(f"tracked_order: {tracked_order.attributes}")
            return False
        if tracked_order.exchange_order_id == "":
            self.logger().warning(f"Failed to cancel order {order_id} with an empty exchange_id in tracked_order")
            self.logger().debug(f"tracked_order: {tracked_order.attributes}")
            return False
        if tracked_order.exchange_order_id == "UNKNOWN":
            self.logger().error(f"Failed to cancel order {order_id} without exchange_id: UNKNOWN"
                                "File a bug report with the Hummingbot team.")
            raise ValueError(f"Failed to cancel order {order_id} with exchange_id: UNKNOWN")

        symbol = await self.exchange_symbol_associated_to_pair(trading_pair=tracked_order.trading_pair)
        api_params = {
            "symbol": symbol,
            "orderId": tracked_order.exchange_order_id,
        }
        # self.logger().info(f"Order cancellation, params: {api_params}")
        try:
            # tạo future để nhận kết quả
            future: asyncio.Future = asyncio.get_event_loop().create_future()
            await self._cancel_order_queue.put((api_params, future))

            cancel_result = await future  # ✅ Đợi kết quả từ queue

            # Theo response mẫu, status trả về là "CANCELING"
            status = cancel_result.get("status", "").upper()
            if status in ["CANCELING", "CANCELED"]:
                # Tạo OrderUpdate để thông báo cho client về việc cancel
                order_update = OrderUpdate(
                    client_order_id=tracked_order.client_order_id,
                    exchange_order_id=str(cancel_result.get("orderId", order_id)),
                    trading_pair=tracked_order.trading_pair,
                    update_timestamp=cancel_result.get("updateTime", int(time.time() * 1000)) * 1e-3,
                    new_state=CONSTANTS.ORDER_STATE.get(status, OrderState.CANCELED),
                )
                # Cập nhật trạng thái order trong client
                self._order_tracker.process_order_update(order_update)
                return True
            return False
        except Exception as e:
            error_message = str(e).lower()
            if "can't cancel order filled" in error_message:
                self.logger().warning(f"Cannot cancel order {order_id} because it's already filled: {e}")
                # Order đã được filled, coi như cancel thành công
                return True
            elif "order was cancel" in error_message:
                self.logger().warning(f"Cannot cancel order {order_id} , it's already canceled : {e}")
                return True
            else:
                # Re-raise exception cho các lỗi khác
                raise e

    async def _format_trading_rules(self, exchange_info_dict: Dict[str, Any]) -> List[TradingRule]:
        """
        Example:
        {
            "symbol": "ETHBTC",
            "baseAssetPrecision": 8,
            "quotePrecision": 8,
            "orderTypes": ["LIMIT", "MARKET"],
            "filters": [
                {
                    "filterType": "PRICE_FILTER",
                    "minPrice": "0.00000100",
                    "maxPrice": "100000.00000000",
                    "tickSize": "0.00000100"
                }, {
                    "filterType": "LOT_SIZE",
                    "minQty": "0.00100000",
                    "maxQty": "100000.00000000",
                    "stepSize": "0.00100000"
                }, {
                    "filterType": "MIN_NOTIONAL",
                    "minNotional": "0.00100000"
                }
            ]
        }
        """
        trading_pair_rules = exchange_info_dict.get("symbols", [])
        # self.logger().warning(f"trading_pair_rules list {trading_pair_rules} .")
        retval = []
        for rule in trading_pair_rules:
            try:
                trading_pair = await self.trading_pair_associated_to_exchange_symbol(symbol=rule.get("symbol"))
                filters = rule.get("filters", [])
                price_filter = next(f for f in filters if f.get("filterType") == "PRICE_FILTER")
                lot_size_filter = next(f for f in filters if f.get("filterType") == "LOT_SIZE")
                # Vindax không có type MIN_NOTIONAL
                min_notional_filter = next((f for f in filters if f.get("filterType") == "MIN_NOTIONAL"), None)
                if min_notional_filter is not None:
                    min_notional = Decimal(min_notional_filter.get("minNotional"))
                else:
                    # self.logger().warning(f"MIN_NOTIONAL filter missing for {trading_pair}, using 0 as default.")
                    min_notional = Decimal("0")

                min_order_size = Decimal(lot_size_filter.get("minQty"))
                tick_size = Decimal(price_filter.get("tickSize"))
                step_size = Decimal(lot_size_filter.get("stepSize"))

                retval.append(
                    TradingRule(
                        trading_pair,
                        min_order_size=min_order_size,
                        min_price_increment=tick_size,
                        min_base_amount_increment=step_size,
                        min_notional_size=Decimal(str(min_notional))
                    )
                )
            except Exception:
                self.logger().exception(f"Error parsing the trading pair rule {rule}. Skipping.")
                continue
        return retval

    async def _status_polling_loop_fetch_updates(self):
        await self._update_order_fills_from_trades()
        await super()._status_polling_loop_fetch_updates()

    async def _update_trading_fees(self):
        """
        Update fees information from the exchange
        """
        pass

    async def _user_stream_event_listener(self):
        user_stream = self._user_stream_tracker.user_stream
        while True:
            try:
                order_by_exchange_id_map = {}
                for order in self._order_tracker.all_fillable_orders.values():
                    order_by_exchange_id_map[order.exchange_order_id] = order

                event_message = await user_stream.get()
                # self.logger().info(f"User stream event: {event_message}")
                event_type = event_message.get("event_type")
                # Refer to https://github.com/binance-exchange/binance-official-api-docs/blob/master/user-data-stream.md
                # As per the order update section in Binance the ID of the order being canceled is under the "C" key
                if event_type == "executionReport":
                    execution_type = event_message.get("orderStatus")
                    trackorder = order_by_exchange_id_map[event_message["orderId"]] if event_message["orderId"] in order_by_exchange_id_map else None
                    if trackorder is None:
                        self.logger().warning(f"Received executionReport for unknown orderId: {event_message['orderId']}")
                        continue

                    if execution_type != "CANCELED":
                        # client_order_id = event_message.get("c", "")
                        client_order_id = trackorder.client_order_id
                    else:
                        # client_order_id = event_message.get("C", "")
                        client_order_id = trackorder.client_order_id

                    if execution_type == "TRADE":
                        tracked_order = self._order_tracker.all_fillable_orders.get(client_order_id)

                        if tracked_order is not None:
                            fee = TradeFeeBase.new_spot_fee(
                                fee_schema=self.trade_fee_schema(),
                                trade_type=tracked_order.trade_type,
                                percent_token=event_message["feeAsset"],
                                flat_fees=[TokenAmount(amount=Decimal(event_message["fee"]), token=event_message["feeAsset"])]
                            )
                            trade_update = TradeUpdate(
                                trade_id=str(event_message["trade_id"]),
                                client_order_id=tracked_order.client_order_id,
                                exchange_order_id=str(event_message["orderId"]),
                                trading_pair=tracked_order.trading_pair,
                                fee=fee,
                                fill_base_amount=Decimal(event_message["qty"]),
                                fill_quote_amount=Decimal(event_message["qty"]) * Decimal(event_message["price"]),
                                fill_price=Decimal(event_message["price"]),
                                fill_timestamp=event_message["time"] * 1e-3,
                            )
                            self._order_tracker.process_trade_update(trade_update)

                    tracked_order = self._order_tracker.all_updatable_orders.get(client_order_id)
                    if tracked_order is not None:
                        order_update = OrderUpdate(
                            trading_pair=tracked_order.trading_pair,
                            update_timestamp=event_message["eventTime"] * 1e-3,
                            new_state=CONSTANTS.ORDER_STATE[event_message["orderStatus"]],
                            client_order_id=client_order_id,
                            exchange_order_id=str(event_message["orderId"]),
                        )
                        self._order_tracker.process_order_update(order_update=order_update)

                elif event_type == "outboundAccountPosition":
                    balances = event_message["balances"]
                    for balance_entry in balances:
                        asset_name = balance_entry["asset"]
                        free_balance = Decimal(balance_entry["free"])
                        total_balance = Decimal(balance_entry["free"]) + Decimal(balance_entry["locked"])
                        self._account_available_balances[asset_name] = free_balance
                        self._account_balances[asset_name] = total_balance

            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().error("Unexpected error in user stream listener loop.", exc_info=True)
                await self._sleep(5.0)

    async def _update_order_fills_from_trades(self):
        """
        This is intended to be a backup measure to get filled events with trade ID for orders,
        in case Vindax's user stream events are not working.
        NOTE: It is not required to copy this functionality in other connectors.
        This is separated from _update_order_status which only updates the order status without producing filled
        events, since Vindax's get order endpoint does not return trade IDs.
        The minimum poll interval for order status is 10 seconds.
        """
        small_interval_last_tick = self._last_poll_timestamp / self.UPDATE_ORDER_STATUS_MIN_INTERVAL
        small_interval_current_tick = self.current_timestamp / self.UPDATE_ORDER_STATUS_MIN_INTERVAL
        long_interval_last_tick = self._last_poll_timestamp / self.LONG_POLL_INTERVAL
        long_interval_current_tick = self.current_timestamp / self.LONG_POLL_INTERVAL

        if (long_interval_current_tick > long_interval_last_tick
                or (self.in_flight_orders and small_interval_current_tick > small_interval_last_tick)):
            query_time = int(self._last_trades_poll_vindax_timestamp * 1e3)
            self._last_trades_poll_vindax_timestamp = self._time_synchronizer.time()
            order_by_exchange_id_map = {}
            for order in self._order_tracker.all_fillable_orders.values():
                order_by_exchange_id_map[order.exchange_order_id] = order

            tasks = []
            trading_pairs = self.trading_pairs
            for trading_pair in trading_pairs:
                params = {
                    "symbol": await self.exchange_symbol_associated_to_pair(trading_pair=trading_pair)
                }
                if self._last_poll_timestamp > 0:
                    params["startTime"] = query_time
                tasks.append(self._api_get(
                    path_url=CONSTANTS.MY_TRADES_PATH_URL,
                    params=params,
                    is_auth_required=True))

            self.logger().debug(f"Polling for order fills of {len(tasks)} trading pairs.")
            # self.logger().info(f"show order_by_exchange_id_map for order: {len(order_by_exchange_id_map)} trading pairs.")
            results = await safe_gather(*tasks, return_exceptions=True)

            for trades, trading_pair in zip(results, trading_pairs):

                if isinstance(trades, Exception):
                    self.logger().network(
                        f"Error fetching trades update for the order {trading_pair}: {trades}.",
                        app_warning_msg=f"Failed to fetch trade update for {trading_pair}."
                    )
                    continue
                for trade in trades:
                    exchange_order_id = str(trade["trade_id"])
                    if exchange_order_id in order_by_exchange_id_map:
                        # This is a fill for a tracked order
                        tracked_order = order_by_exchange_id_map[exchange_order_id]
                        fee = TradeFeeBase.new_spot_fee(
                            fee_schema=self.trade_fee_schema(),
                            trade_type=tracked_order.trade_type,
                            percent_token=trade["feeAsset"],
                            flat_fees=[TokenAmount(amount=Decimal(trade["fee"]), token=trade["feeAsset"])]
                        )
                        trade_update = TradeUpdate(
                            trade_id=str(trade["trade_id"]),
                            client_order_id=tracked_order.client_order_id,
                            exchange_order_id=exchange_order_id,
                            trading_pair=trading_pair,
                            fee=fee,
                            fill_base_amount=Decimal(trade["qty"]),
                            fill_quote_amount=Decimal(trade["quoteQty"]),
                            fill_price=Decimal(trade["price"]),
                            fill_timestamp=trade["time"] * 1e-3,
                        )
                        self._order_tracker.process_trade_update(trade_update)
                    elif self.is_confirmed_new_order_filled_event(str(trade["trade_id"]), exchange_order_id, trading_pair):
                        # This is a fill of an order registered in the DB but not tracked any more
                        self._current_trade_fills.add(TradeFillOrderDetails(
                            market=self.display_name,
                            exchange_trade_id=str(trade["trade_id"]),
                            symbol=trading_pair))
                        self.trigger_event(
                            MarketEvent.OrderFilled,
                            OrderFilledEvent(
                                timestamp=float(trade["time"]) * 1e-3,
                                order_id=self._exchange_order_ids.get(str(trade["trade_id"]), None),
                                trading_pair=trading_pair,
                                trade_type=TradeType.BUY if trade["isBuyer"] else TradeType.SELL,
                                order_type=OrderType.LIMIT_MAKER if trade["isMaker"] else OrderType.LIMIT,
                                price=Decimal(trade["price"]),
                                amount=Decimal(trade["qty"]),
                                trade_fee=DeductedFromReturnsTradeFee(
                                    flat_fees=[
                                        TokenAmount(
                                            trade["feeAsset"],
                                            Decimal(trade["fee"])
                                        )
                                    ]
                                ),
                                exchange_trade_id=str(trade["trade_id"])
                            ))
                        self.logger().info(f"Recreating missing trade in TradeFill: {trade}")

    async def _all_trade_updates_for_order(self, order: InFlightOrder) -> List[TradeUpdate]:
        trade_updates = []

        if order.exchange_order_id is not None:
            exchange_order_id = order.exchange_order_id
            trading_pair = await self.exchange_symbol_associated_to_pair(trading_pair=order.trading_pair)
            # self.logger().info(f"Fetching all fills for order {exchange_order_id} on {trading_pair}")
            all_fills_response = await self._api_get(
                path_url=CONSTANTS.MY_TRADES_PATH_URL,
                params={
                    "symbol": trading_pair,
                    "fromId": exchange_order_id
                },
                is_auth_required=True,
                limit_id=CONSTANTS.MY_TRADES_PATH_URL)

            for trade in all_fills_response:
                exchange_order_id = str(trade.get("orderId", ""))
                fee = TradeFeeBase.new_spot_fee(
                    fee_schema=self.trade_fee_schema(),
                    trade_type=order.trade_type,
                    percent_token=trade["feeAsset"],
                    flat_fees=[TokenAmount(amount=Decimal(trade["fee"]), token=trade["feeAsset"])]
                )
                trade_update = TradeUpdate(
                    trade_id=str(trade.get("trade_id", trade.get("id", ""))),
                    client_order_id=order.client_order_id,
                    exchange_order_id=exchange_order_id,
                    trading_pair=trading_pair,
                    fee=fee,
                    fill_base_amount=Decimal(trade.get("qty", "0")),
                    fill_quote_amount=Decimal(trade.get("totalQuota", trade.get("quoteQty", "0"))),
                    fill_price=Decimal(trade.get("price", "0")),
                    fill_timestamp=self._parse_timestamp(trade.get("time", "0")),
                )
                trade_updates.append(trade_update)

        return trade_updates

    async def _request_order_status(self, tracked_order: InFlightOrder) -> OrderUpdate:
        """
        Queries Order status by order_id.
        https://docs.cdp.coinbase.com/advanced-trade/reference/retailbrokerageapi_gethistoricalorder

        :param tracked_order: InFlightOrder
        :return: OrderUpdate
        """
        if (
                tracked_order.exchange_order_id is None or
                tracked_order.exchange_order_id == "" or
                tracked_order.exchange_order_id == "UNKNOWN"
        ):
            return OrderUpdate(
                client_order_id=tracked_order.client_order_id,
                exchange_order_id="",
                trading_pair=tracked_order.trading_pair,
                update_timestamp=self._time_synchronizer.time(),
                new_state=OrderState.FAILED,
            )

        trading_pair = await self.exchange_symbol_associated_to_pair(trading_pair=tracked_order.trading_pair)
        updated_order_data = await self._api_get(
            path_url=CONSTANTS.ORDER_PATH_URL,
            params={
                "symbol": trading_pair,
                "orderId": tracked_order.exchange_order_id},
            is_auth_required=True)

        # self.logger().info(f"Resulf _request_order_status updated_order_data: {updated_order_data} of trading_pair: {trading_pair} ")
        new_state = CONSTANTS.ORDER_STATE[updated_order_data["status"]]
        order_update = OrderUpdate(
            client_order_id=tracked_order.client_order_id,
            exchange_order_id=str(updated_order_data["orderId"]),
            trading_pair=tracked_order.trading_pair,
            # update_timestamp=updated_order_data["time"] * 1e-3,
            update_timestamp=int(time.time()),
            new_state=new_state,
        )

        return order_update

    async def _update_balances(self):
        local_asset_names = set(self._account_balances.keys())

        remote_asset_names = set()

        try:
            # self.logger().info("Requesting account balances")
            account_info = await self._api_get(
                path_url=CONSTANTS.ACCOUNTS_PATH_URL,
                is_auth_required=True)
            # self.logger().info(f"Account balances response: {account_info}")
        except Exception as e:
            self.logger().error(f"Error fetching account info: {e}", exc_info=True)
            return

        # Kiểm tra canTrade status từ API response
        can_trade_value = account_info.get("canTrade", 0)
        if can_trade_value == 1:
            self._can_trade = True
        else:
            self._can_trade = False

        if not self._can_trade:
            self.logger().warning(f"Trading is disabled for this account. canTrade value: {can_trade_value}")

        balances = account_info["balances"]
        for balance_entry in balances:
            asset_name = balance_entry["asset"]
            free_balance = Decimal(balance_entry["free"])
            total_balance = Decimal(balance_entry["free"]) + Decimal(balance_entry["locked"])
            self._account_available_balances[asset_name] = free_balance
            self._account_balances[asset_name] = total_balance
            remote_asset_names.add(asset_name)

        # self.logger().info(f"Account _account_available_balances: {self._account_available_balances}")
        # self.logger().info(f"Account _account_balances: {self._account_balances}")
        asset_names_to_remove = local_asset_names.difference(remote_asset_names)
        for asset_name in asset_names_to_remove:
            del self._account_available_balances[asset_name]
            del self._account_balances[asset_name]
        # self.logger().info(f"Account self._account_available_balances: {self._account_available_balances}, self._account_balances: {self._account_balances}")

    def _initialize_trading_pair_symbols_from_exchange_info(self, exchange_info: Dict[str, Any]):
        mapping = bidict()
        for symbol_data in filter(vindax_utils.is_exchange_information_valid, exchange_info["symbols"]):
            mapping[symbol_data["symbol"]] = combine_to_hb_trading_pair(base=symbol_data["baseAsset"],
                                                                        quote=symbol_data["quoteAsset"])
        # self.logger().info(f"hahahahaha symbol_map: {mapping} !!")
        self._set_trading_pair_symbol_map(mapping)

    async def _get_last_traded_price(self, trading_pair: str, price_type: str = "last") -> float:
        """
        Lấy giá gần nhất / ask / bid của cặp giao dịch.

        :param trading_pair: cặp giao dịch, ví dụ "BTC-USDT"
        :param price_type: loại giá cần lấy ("last", "ask", "bid")
        :return: giá trị float, hoặc 0.0 nếu không có
        """
        params = {
            "symbol": await self.exchange_symbol_associated_to_pair(trading_pair=trading_pair)
        }

        resp_json = await self._api_request(
            method=RESTMethod.GET,
            path_url=CONSTANTS.TICKER_PRICE_CHANGE_PATH_URL,
            params=params
        )

        # return float(resp_json.get("lastPrice", 0))
        # Tùy vào kiểu giá cần lấy
        if price_type == "ask":
            return float(resp_json.get("askPrice", 0))
        elif price_type == "bid":
            return float(resp_json.get("bidPrice", 0))
        else:
            return float(resp_json.get("lastPrice", 0))
