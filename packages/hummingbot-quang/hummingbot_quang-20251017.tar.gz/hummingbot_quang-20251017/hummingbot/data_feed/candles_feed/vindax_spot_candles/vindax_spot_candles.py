import asyncio
import logging
from typing import List, Optional

import numpy as np
import socketio

from hummingbot.core.network_iterator import NetworkStatus
from hummingbot.core.utils.async_utils import safe_ensure_future
from hummingbot.data_feed.candles_feed.candles_base import CandlesBase
from hummingbot.data_feed.candles_feed.vindax_spot_candles import constants as CONSTANTS
from hummingbot.logger import HummingbotLogger


class VindaxSpotCandles(CandlesBase):
    _logger: Optional[HummingbotLogger] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._logger is None:
            cls._logger = logging.getLogger(__name__)
        return cls._logger

    def __init__(self, trading_pair: str, interval: str = "1m", max_records: int = 150):
        super().__init__(trading_pair, interval, max_records)

        self._consecutive_empty_responses = 0

        # Task management for polling
        self._polling_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._is_running = False

        # 👇 Thêm dòng này để chứa nhiều client
        self._sio: Optional[socketio.AsyncClient] = None

    @property
    def name(self):
        return f"vindax_{self._trading_pair}"

    @property
    def rest_url(self):
        return CONSTANTS.REST_URL

    @property
    def wss_url(self):
        return CONSTANTS.WSS_URL

    @property
    def health_check_url(self):
        return self.rest_url + CONSTANTS.HEALTH_CHECK_ENDPOINT

    @property
    def candles_url(self):
        return self.rest_url + CONSTANTS.CANDLES_ENDPOINT

    @property
    def candles_endpoint(self):
        return CONSTANTS.CANDLES_ENDPOINT

    @property
    def candles_max_result_per_rest_request(self):
        return CONSTANTS.MAX_RESULTS_PER_CANDLESTICK_REST_REQUEST

    @property
    def rate_limits(self):
        return CONSTANTS.RATE_LIMITS

    @property
    def intervals(self):
        return CONSTANTS.INTERVALS

    async def start_network(self):
        """
        Start the network and begin polling.
        """
        await self.stop_network()
        await self.initialize_exchange_data()
        self._is_running = True
        self._shutdown_event.clear()
        self._polling_task = asyncio.create_task(self._polling_loop())

    async def stop_network(self):
        """
        Stop the network by gracefully shutting down the polling task.
        """
        if self._polling_task and not self._polling_task.done():
            self._is_running = False
            self._shutdown_event.set()

            try:
                # Wait for graceful shutdown
                await asyncio.wait_for(self._polling_task, timeout=10.0)
            except asyncio.TimeoutError:
                self.logger().warning("Polling task didn't stop gracefully, cancelling...")
                self._polling_task.cancel()
                try:
                    await self._polling_task
                except asyncio.CancelledError:
                    pass

        self._polling_task = None
        self._is_running = False

    async def check_network(self) -> NetworkStatus:
        rest_assistant = await self._api_factory.get_rest_assistant()
        await rest_assistant.execute_request(url=self.health_check_url,
                                             throttler_limit_id=CONSTANTS.HEALTH_CHECK_ENDPOINT)
        return NetworkStatus.CONNECTED

    def get_exchange_trading_pair(self, trading_pair):
        return trading_pair.replace("-", "")

    def _get_rest_candles_params(self,
                                 start_time: Optional[int] = None,
                                 end_time: Optional[int] = None,
                                 limit: Optional[int] = CONSTANTS.MAX_RESULTS_PER_CANDLESTICK_REST_REQUEST) -> dict:
        params = {
            "symbol": self._ex_trading_pair,
            "interval": self.interval,
            "limit": limit
        }
        if end_time:
            params["endTime"] = end_time * 1000
        self.logger().info(f"[VINDAX_CANDLES] _get_rest_candles_params: {params}")
        return params

    def _parse_rest_candles(self, data: dict, end_time: Optional[int] = None) -> List[List[float]]:
        self.logger().info(f"[VINDAX_CANDLES] _parse_rest_candles: {data}")
        return [
            [self.ensure_timestamp_in_seconds(row[0]), row[1], row[2], row[3], row[4], row[5],
             row[7], row[8], row[9], row[10]]
            for row in data
        ]

    async def _polling_loop(self):
        """
        Main polling loop - separated from listen_for_subscriptions for better testability.
        This method can be cancelled cleanly and tested independently.
        """
        try:
            self.logger().info(f"Starting constant polling for {self._trading_pair} candles")

            # Initial setup
            # await self._initialize_candles()

            while self._is_running and not self._shutdown_event.is_set():
                candle_params = f"{self._ex_trading_pair.lower()}_kline_{self.interval}"
                namespace = f"/{candle_params}"
                self._sio = socketio.AsyncClient(
                    reconnection=True,
                    reconnection_attempts=5,
                    reconnection_delay=1,
                    reconnection_delay_max=5,
                )
                # self._sio_clients[self._trading_pair] = sio

                # ----- Default namespace -----
                @self._sio.event
                def connect():
                    print("✅ [VINDAX WS-Candles] Connected to /")

                @self._sio.event
                def disconnect():
                    print("❌ [VINDAX WS-Candles] Disconnected from /")

                @self._sio.event
                def message(data):
                    print(f"📩 [VINDAX WS-Candles] Message from /: {data}")

                @self._sio.on("connect", namespace=namespace)
                async def on_connect():
                    self.logger().info(f"✅ [VINDAX WS-Candles] Connected to namespace {namespace} for {self._trading_pair}")

                @self._sio.on("message", namespace=namespace)
                async def handle_kline(data):
                    self.logger().info(f"📊 [VINDAX WS] Received message for {namespace}: {data}")
                    await asyncio.wait_for(self._process_websocket_messages_task(data),
                                           timeout=self._ping_timeout)

                @self._sio.on("disconnect", namespace=namespace)
                async def on_disconnect():
                    self.logger().warning(f"⚠️ [VINDAX WS-Candles] Disconnected from namespace {namespace} for {self._trading_pair}")

                @self._sio.on("reconnect", namespace=namespace)
                async def on_reconnect():
                    self.logger().info(f"🔄 Reconnected to {self._trading_pair}")

                @self._sio.on("connect_error", namespace=namespace)
                async def on_connect_error(data):
                    self.logger().error(f"❌ [VINDAX WS-Candles] Connection error for {self._trading_pair}: {data}")

                try:
                    self.logger().info(f"🔌 [VINDAX WS-Candles] Connecting to {CONSTANTS.WSS_URL} with namespace {namespace}")
                    await self._sio.connect(
                        CONSTANTS.WSS_URL,
                        namespaces=["/", namespace],
                        transports=['websocket']
                    )

                    await self._sio.wait()
                except Exception as e:
                    self.logger().error(f"❌ [VINDAX WS-Candles] SocketIO error on {self._trading_pair}: {str(e)}")
                finally:
                    self.logger().info(f"❌ [VINDAX WS-Candles] Disconnecting from {self._trading_pair}")
                    await self._sio.disconnect()

        finally:
            self.logger().info("Polling loop stopped")
            self._is_running = False

    async def listen_for_subscriptions(self):
        """
        Legacy method for compatibility with base class.
        Now just delegates to the task-based approach.
        """
        if not self._is_running:
            await self.start_network()

        # Wait for the polling task to complete
        if self._polling_task:
            try:
                await self._polling_task
            except asyncio.CancelledError:
                self.logger().info("Listen for subscriptions cancelled")
                raise

    def ws_subscription_payload(self):
        """Not used for Vindax since WebSocket is not supported for candles."""
        raise NotImplementedError("WebSocket not supported for Vindax Markets candles")

    def _parse_websocket_message(self, data: dict):
        candles_row_dict = {}
        if data is not None and data.get("eventType") == "kline":  # data will be None when the websocket is disconnected
            candles_row_dict["timestamp"] = self.ensure_timestamp_in_seconds(data["kline"]["time"])
            candles_row_dict["open"] = data["kline"]["open"]
            candles_row_dict["high"] = data["kline"]["high"]
            candles_row_dict["low"] = data["kline"]["low"]
            candles_row_dict["close"] = data["kline"]["close"]
            candles_row_dict["volume"] = data["kline"]["volume"]
            candles_row_dict["quote_asset_volume"] = data["kline"]["quoteVolume"]
            candles_row_dict["n_trades"] = data["kline"]["count"]
            # candles_row_dict["taker_buy_base_volume"] = data["kline"]["V"]
            # candles_row_dict["taker_buy_quote_volume"] = data["kline"]["Q"]
            candles_row_dict["taker_buy_base_volume"] = 0.
            candles_row_dict["taker_buy_quote_volume"] = 0.
            return candles_row_dict

    async def _process_websocket_messages_task(self, data):
        """
        Xử lý message nhận được từ socket.io (event: candle_update).
        :param data: dict chứa dữ liệu nến từ socket.io
        """
        try:
            self.logger().info(f"✅ [VINDAX Candles] _process_websocket_messages_task: {data}")
            data = data
            parsed_message = self._parse_websocket_message(data)
            if isinstance(parsed_message, dict):
                candles_row = np.array([parsed_message["timestamp"],
                                        parsed_message["open"],
                                        parsed_message["high"],
                                        parsed_message["low"],
                                        parsed_message["close"],
                                        parsed_message["volume"],
                                        parsed_message["quote_asset_volume"],
                                        parsed_message["n_trades"],
                                        parsed_message["taker_buy_base_volume"],
                                        parsed_message["taker_buy_quote_volume"]]).astype(float)
                if len(self._candles) == 0:
                    self._candles.append(candles_row)
                    self._ws_candle_available.set()
                    safe_ensure_future(self.fill_historical_candles())
                else:
                    latest_timestamp = int(self._candles[-1][0])
                    current_timestamp = int(parsed_message["timestamp"])
                    if current_timestamp > latest_timestamp:
                        self._candles.append(candles_row)
                    elif current_timestamp == latest_timestamp:
                        self._candles[-1] = candles_row
        except Exception as e:
            self.logger().error(f"Error processing WebSocket message: {str(e)}")
            raise e
