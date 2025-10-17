import asyncio

# import threading
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import socketio

from hummingbot.connector.exchange.vindax import vindax_constants as CONSTANTS, vindax_web_utils as web_utils
from hummingbot.connector.exchange.vindax.vindax_order_book import VindaxOrderBook
from hummingbot.core.data_type.order_book_message import OrderBookMessage
from hummingbot.core.data_type.order_book_tracker_data_source import OrderBookTrackerDataSource
from hummingbot.core.web_assistant.connections.data_types import RESTMethod
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory

# from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger

if TYPE_CHECKING:
    from hummingbot.connector.exchange.vindax.vindax_exchange import VindaxExchange


class VindaxAPIOrderBookDataSource(OrderBookTrackerDataSource):
    HEARTBEAT_TIME_INTERVAL = 30.0
    TRADE_STREAM_ID = 1
    DIFF_STREAM_ID = 2
    ONE_HOUR = 60 * 60

    _logger: Optional[HummingbotLogger] = None

    def __init__(self,
                 trading_pairs: List[str],
                 connector: 'VindaxExchange',
                 api_factory: WebAssistantsFactory,
                 domain: str = CONSTANTS.DEFAULT_DOMAIN):
        super().__init__(trading_pairs)
        self._connector = connector
        self._trade_messages_queue_key = CONSTANTS.TRADE_EVENT_TYPE
        self._diff_messages_queue_key = CONSTANTS.DIFF_EVENT_TYPE
        self._domain = domain
        self._api_factory = api_factory
        self._sio: Optional[socketio.AsyncClient] = None
        self._namespace_prefix = "/"  # Each trading pair has its own namespace
        # 👇 Thêm dòng này để chứa nhiều client
        self._sio_clients: Dict[str, socketio.AsyncClient] = {}

    async def get_last_traded_prices(self,
                                     trading_pairs: List[str],
                                     domain: Optional[str] = None) -> Dict[str, float]:
        return await self._connector.get_last_traded_prices(trading_pairs=trading_pairs)

    async def _parse_order_book_diff_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        # self.logger().info(f"✅ [VINDAX] _parse_order_book_diff_message raw_message for: {raw_message}")
        if "result" not in raw_message:
            trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(symbol=raw_message["s"])
            order_book_message: OrderBookMessage = VindaxOrderBook.diff_message_from_exchange(
                raw_message, time.time(), {"trading_pair": trading_pair})
            message_queue.put_nowait(order_book_message)

    async def _parse_trade_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        # self.logger().info(f"✅ [VINDAX] _parse_trade_message raw_message for: {raw_message}")
        if "result" not in raw_message:
            trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(symbol=raw_message["symbol"])
            trade_message = VindaxOrderBook.trade_message_from_exchange(
                raw_message, {"trading_pair": trading_pair})
            message_queue.put_nowait(trade_message)

    # def _channel_originating_message(self, event_message: Dict[str, Any]) -> str:
    #     return self._diff_messages_queue_key
    def _channel_originating_message(self, event_message: Dict[str, Any]) -> str:
        channel = ""
        if "result" not in event_message:
            event_type = event_message.get("e")
            channel = (self._diff_messages_queue_key if event_type == CONSTANTS.DIFF_EVENT_TYPE
                       else self._trade_messages_queue_key)
        return channel

    async def _connected_websocket_assistant(self):
        # Không dùng WSAssistant, thay bằng socketio
        raise NotImplementedError("Not applicable with socketio")

    async def _subscribe_channels(self, ws):
        # Không dùng với socketio
        raise NotImplementedError("Not applicable with socketio")

    async def listen_for_subscriptions(self):
        tasks = [self._listen_to_pair(pair) for pair in self._trading_pairs]
        await asyncio.gather(*tasks)

    async def _listen_to_pair(self, trading_pair: str):
        namespace = f"/{trading_pair.replace('-', '').lower()}"
        namespace_Trade = f"/{trading_pair.replace('-', '').lower() + "_aggTrade"}"
        sio = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=1,
            reconnection_delay_max=5,
        )
        self._sio_clients[trading_pair] = sio

        # self.logger().info(f"[VINDAX WS] Setting up WebSocket for {trading_pair} with namespace: {namespace}")

        # ----- Default namespace -----
        @sio.event
        def connect():
            print("✅ Connected to /")

        @sio.event
        def disconnect():
            print("❌ Disconnected from /")

        @sio.event
        def message(data):
            print(f"📩 Message from /: {data}")

        @sio.on("connect", namespace=namespace)
        async def on_connect():
            self.logger().info(f"✅ [VINDAX WS] Connected to namespace {namespace} for {trading_pair}")

        @sio.on("message", namespace=namespace)
        async def handle_depth(data):
            # self.logger().info(f"📊 [VINDAX WS] Received message for {trading_pair}: {data}")
            await self._message_queue[self._diff_messages_queue_key].put(data)

        @sio.on("connect", namespace=namespace_Trade)
        async def on_connect_trade():
            self.logger().info(f"✅ [VINDAX WS] Connected to namespace {namespace_Trade} for {trading_pair}")

        @sio.on("message", namespace=namespace_Trade)
        async def handle_trade(data):
            # self.logger().info(f"📊 [VINDAX WS] Received message for {namespace_Trade}: {data}")
            await self._message_queue[self._trade_messages_queue_key].put(data)

        @sio.on("disconnect", namespace=namespace_Trade)
        async def on_disconnect_trade():
            self.logger().warning(f"⚠️ [VINDAX WS] Disconnected from namespace {namespace_Trade} for {trading_pair}")

        @sio.on("disconnect", namespace=namespace)
        async def on_disconnect():
            self.logger().warning(f"⚠️ [VINDAX WS] Disconnected from namespace {namespace} for {trading_pair}")

        @sio.on("reconnect", namespace=namespace)
        async def on_reconnect():
            self.logger().info(f"🔄 Reconnected to {trading_pair} for nameSpace: {namespace}")

        @sio.on("reconnect", namespace=namespace_Trade)
        async def on_reconnect_Trade():
            self.logger().info(f"🔄 Reconnected to {trading_pair} for nameSpace: {namespace_Trade}")

        @sio.on("connect_error", namespace=namespace)
        async def on_connect_error(data):
            self.logger().error(f"❌ [VINDAX WS] Connection error for {trading_pair}: {data}")

        @sio.on("connect_error", namespace=namespace_Trade)
        async def on_connect_error_trade(data):
            self.logger().error(f"❌ [VINDAX WS] Connection error for {namespace_Trade}: {data}")

        # ----- Manual keep-alive -----
        # def keep_alive():
        #     while True:
        #         try:
        #             sio.emit("ping", namespace=namespace)
        #             print("🔄 Sent manual ping")
        #             time.sleep(10)
        #         except Exception:
        #             break

        try:
            self.logger().info(f"🔌 [VINDAX WS] Connecting to https://gracelynn-socket.vindax.com with namespace {namespace}")
            await sio.connect(
                "https://gracelynn-socket.vindax.com",
                namespaces=["/", namespace, namespace_Trade],
                transports=['websocket']
            )
            # Start keep-alive thread
            # threading.Thread(target=keep_alive, daemon=True).start()

            await sio.wait()
        except Exception as e:
            self.logger().error(f"❌ [VINDAX WS] SocketIO error on {trading_pair}: {str(e)}")
        finally:
            self.logger().info(f"❌ [VINDAX WS] Disconnecting from {trading_pair}")
            await sio.disconnect()

    async def _order_book_snapshot(self, trading_pair: str) -> OrderBookMessage:
        # self.logger().info(f"✅ [VINDAX _order_book_snapshot] _order_book_snapshot from {trading_pair}")
        snapshot: Dict[str, Any] = await self._request_order_book_snapshot(trading_pair)
        snapshot_timestamp: float = time.time()
        snapshot_msg: OrderBookMessage = VindaxOrderBook.snapshot_message_from_exchange(
            snapshot,
            snapshot_timestamp,
            metadata={"trading_pair": trading_pair}
        )
        # self.logger().info(f"✅ [VINDAX snapshot_msg] snapshot_msg result {snapshot_msg} and snapshot: {snapshot}")
        return snapshot_msg

    async def _request_order_book_snapshot(self, trading_pair: str) -> Dict[str, Any]:
        """
        Retrieves a copy of the full order book from the exchange, for a particular trading pair.

        :param trading_pair: the trading pair for which the order book will be retrieved

        :return: the response from the exchange (JSON dictionary)
        """
        params = {
            "symbol": await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair),
            "limit": "100"
        }
        self.logger().info(f"✅ [VINDAX ORDER BOOK] _request_order_book_snapshot from {trading_pair} with params: {params}")

        rest_assistant = await self._api_factory.get_rest_assistant()
        data = await rest_assistant.execute_request(
            url=web_utils.public_rest_url(path_url=CONSTANTS.SNAPSHOT_PATH_URL, domain= CONSTANTS.DEFAULT_DOMAIN),
            params=params,
            method=RESTMethod.GET,
            throttler_limit_id=CONSTANTS.SNAPSHOT_PATH_URL,
        )

        return data
