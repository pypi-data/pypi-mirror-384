import asyncio
import logging
from decimal import Decimal
from typing import Optional
from urllib.parse import parse_qs, urlparse

import aiohttp

from hummingbot.core.network_base import NetworkBase
from hummingbot.core.network_iterator import NetworkStatus
from hummingbot.core.utils.async_utils import safe_ensure_future
from hummingbot.logger import HummingbotLogger


class CustomAPIDataFeed(NetworkBase):
    cadf_logger: Optional[HummingbotLogger] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls.cadf_logger is None:
            cls.cadf_logger = logging.getLogger(__name__)
        return cls.cadf_logger

    def __init__(self, api_url, update_interval: float = 5.0):
        super().__init__()
        self._ready_event = asyncio.Event()
        self._shared_client: Optional[aiohttp.ClientSession] = None
        self._api_url = api_url
        self._check_network_interval = 30.0
        self._ev_loop = asyncio.get_event_loop()
        self._price: Decimal = Decimal("0")
        self._update_interval: float = update_interval
        self._fetch_price_task: Optional[asyncio.Task] = None
        # self.headers: None
        self.headers = {"X-CMC_PRO_API_KEY": "30e754ea-7c99-4f6e-8fdb-50282fa98837"}

    @property
    def name(self):
        return "custom_api"

    @property
    def health_check_endpoint(self):
        return self._api_url

    def _http_client(self) -> aiohttp.ClientSession:
        if self._shared_client is None:
            self._shared_client = aiohttp.ClientSession()
        return self._shared_client

    async def check_network(self) -> NetworkStatus:
        client = self._http_client()
        async with client.request("GET", self.health_check_endpoint, headers=self.headers) as resp:
            status_text = await resp.text()
            if resp.status != 200:
                raise Exception(f"Custom API Feed {self.name} server error: {status_text}")
        return NetworkStatus.CONNECTED

    def get_price(self) -> Decimal:
        return self._price

    async def get_symbol_from_url(self, url: str) -> str:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        symbol = query_params.get("symbol", [None])[0]

        if not symbol:  # None hoặc chuỗi rỗng
            raise ValueError("Missing required query parameter: symbol")

        return symbol

    async def fetch_price_loop(self):
        while True:
            try:
                await self.fetch_price()
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().network(f"Error fetching a new price from {self._api_url}.", exc_info=True,
                                      app_warning_msg="Couldn't fetch newest price from CustomAPI. "
                                                      "Check network connection.")

            await asyncio.sleep(self._update_interval)

    async def fetch_price(self):
        client = self._http_client()

        async with client.request("GET", self._api_url, headers=self.headers) as resp:
            resp_text = await resp.text()
            if resp.status != 200:
                raise Exception(f"Custom API Feed {self.name} server error: {resp_text}")
            # self._price = Decimal(str(resp_text))
            try:
                data = await resp.json()
                payload = data.get("data")
                if isinstance(payload, list) and len(payload) > 0:
                    # Trường hợp trả về mảng
                    self._price = Decimal(str(payload[0]["priceUsd"]))
                elif isinstance(payload, dict):
                    # Trường hợp trả về object
                    symbol = await self.get_symbol_from_url(self._api_url)
                    self._price = Decimal(str(payload[symbol][0]["quote"]["USD"]["price"]))
                else:
                    raise ValueError("Invalid data format from API")
            except Exception:
                self._price = Decimal(str(resp_text))
        self._ready_event.set()

    async def start_network(self):
        await self.stop_network()
        self._fetch_price_task = safe_ensure_future(self.fetch_price_loop())

    async def stop_network(self):
        if self._fetch_price_task is not None:
            self._fetch_price_task.cancel()
            self._fetch_price_task = None

    def start(self):
        NetworkBase.start(self)

    def stop(self):
        NetworkBase.stop(self)
