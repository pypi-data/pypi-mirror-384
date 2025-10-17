import asyncio
import socketio
import time
import logging
from typing import TYPE_CHECKING, List, Optional

from hummingbot.connector.exchange.vindax import vindax_constants as CONSTANTS, vindax_web_utils as web_utils
from hummingbot.connector.exchange.vindax.vindax_auth import VindaxAuth
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.utils.async_utils import safe_ensure_future
from hummingbot.core.web_assistant.connections.data_types import RESTMethod
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger

if TYPE_CHECKING:
    from hummingbot.connector.exchange.vindax.vindax_exchange import VindaxExchange


class VindaxAPIUserStreamDataSource:
    
    _logger: Optional[HummingbotLogger] = None
    
    def __init__(self,
                 auth: VindaxAuth,
                 trading_pairs: List[str],
                 connector: 'VindaxExchange',
                 api_factory: WebAssistantsFactory):

        self._auth: VindaxAuth = auth
        self._connector = connector
        self._api_factory = api_factory
        self._sio: Optional[socketio.AsyncClient] = None
        self._running = False
        self.last_recv_time: float = 0
        self._namespace = "/7c17d423f7eabc8fb5c33f59fef1edf9"  # correct Vindax socket namespace
        
    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._logger is None:
            cls._logger = logging.getLogger(HummingbotLogger.logger_name_for_class(cls))
        return cls._logger

    # @property
    # def last_recv_time(self) -> float:
    #     if self.last_recv_time:
    #         return self.last_recv_time
    #     return 0

    async def listen_for_user_stream(self, output: asyncio.Queue):
        self._sio = socketio.AsyncClient()
        # ----- Default namespace -----
        @self._sio.event
        def connect():
            self.logger().info("✅ Connected to /")

        @self._sio.event
        def disconnect():
            self.logger().info("❌ Disconnected from user stream: /")

        @self._sio.event
        def message(data):
            self.logger().info(f"📩 Message from /: {data}")

        @self._sio.on("connect", namespace=self._namespace)
        async def on_connect():
            self.last_recv_time = time.time()
            self.logger().info("✅ User stream connected")

        @self._sio.on("message", namespace=self._namespace)
        async def handle_message(data):
            # self.logger().info(f"📩 Message from user namespace: {data}")
            self.last_recv_time = time.time()
            await output.put(data)
        
        @self._sio.on("disconnect", namespace=self._namespace)
        async def on_disconnect():
            self.logger().warning(f"⚠️ [VINDAX WS] Disconnected from namespace {self._namespace} for user stream")

        try:
            await self._sio.connect(
                "https://gracelynn-socket.vindax.com",
                namespaces=["/", self._namespace],
                transports=["websocket"]
            )
            await self._sio.wait()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.logger().error(f"❌ User stream error: {e}")
        finally:
            if self._sio.connected:
                await self._sio.disconnect()
