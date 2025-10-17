from datetime import datetime, timedelta
from typing import Any

from django.conf import settings
from django.utils import timezone
from requests import HTTPError

from wise.settings.dependencies import DelphinusSettings
from wise.utils.candles import Candle, Resolution
from wise.utils.exception import optional_exception_handling
from wise.utils.http import create_session
from wise.utils.tracing import with_trace

CANDLES_PAGINATION_PERIOD_TIMEDELTA = timedelta(days=10)

TETHER_SLUG = "tether"
USD_COIN_SLUG = "usd-coin"

TETHER_USD_PAIR = "USDTUSD"
USDC_USDT_PAIR = "USDCUSDT"

BINANCE_EXCHANGE = "BINANCE"
BINANCE_US_EXCHANGE = "BINANCEUS"

SPOT_MARKET = "SPOT"


class DelphinusClient:
    def __init__(self):
        self.config: DelphinusSettings = settings.ENV.delphinus
        self._candles_pagination_period_seconds = int(
            CANDLES_PAGINATION_PERIOD_TIMEDELTA.total_seconds()
        )
        self.http_client = create_session(service_name="delphinus")

    @with_trace("_get_delphi")
    def _get(self, path: str, **kwargs: Any) -> dict:
        api_name = kwargs.pop("_api_name", "unknown")

        response = self.http_client.get(
            f"{self.config.url}{path}",
            **kwargs,
            _api_name=api_name,
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _get_last_candle(
        self,
        *,
        path: str,
        api_name: str,
        params: dict,
        market: str,
        exchange: str | None = None,
        network_slug: str | None = None,
        usd: bool,
    ) -> Candle:
        params["market"] = market
        if exchange:
            params["exchange"] = exchange
        if network_slug:
            params["network"] = network_slug
        if usd:
            params["convert_to_usd"] = "true"

        resp = self._get(
            path,
            params=params,
            _api_name=api_name,
        )
        return self._candle_from_response(resp["candle"], Resolution.R1M, is_open=True)

    @with_trace("get_current_candle")
    @optional_exception_handling()
    def get_current_candle(
        self,
        base_slug: str,
        quote_slug: str,
        market: str,
        exchange: str | None = None,
        network_slug: str | None = None,
        usd: bool = False,
    ) -> Candle:
        return self._get_last_candle(
            path=self.config.last_candle_by_slug_path,
            api_name="last_candle_by_slug",
            params={"base": base_slug, "quote": quote_slug},
            market=market,
            exchange=exchange,
            network_slug=network_slug,
            usd=usd,
        )

    @optional_exception_handling()
    def get_current_candle_if_exists(self, *args, **kwargs) -> Candle | None:
        try:
            return self.get_current_candle(*args, **kwargs)
        except HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    @with_trace("get_current_usd_coin_usd_candle")
    @optional_exception_handling()
    def get_current_usd_coin_usd_candle(self) -> Candle:
        return self._get_last_candle(
            path=self.config.last_candle_by_pair_path,
            api_name="last_candle_by_pair",
            params={"pair": USDC_USDT_PAIR},
            market=SPOT_MARKET,
            exchange=BINANCE_EXCHANGE,
            usd=True,
        )

    @with_trace("get_current_tether_usd_candle")
    @optional_exception_handling()
    def get_current_tether_usd_candle(self) -> Candle:
        return self._get_last_candle(
            path=self.config.last_candle_by_pair_path,
            api_name="last_candle_by_pair",
            params={"pair": TETHER_USD_PAIR},
            market=SPOT_MARKET,
            exchange=BINANCE_US_EXCHANGE,
            usd=False,
        )

    @with_trace("get_last_price")
    @optional_exception_handling()
    def get_last_price(
        self,
        base_slug: str,
        quote_slug: str,
        market: str,
        exchange: str | None = None,
        network_slug: str | None = None,
        usd: bool = False,
    ) -> float:
        candle = self.get_current_candle(
            base_slug, quote_slug, market, exchange, network_slug, usd=usd
        )
        return candle.close

    @optional_exception_handling()
    def get_last_price_if_exists(self, *args, **kwargs) -> float | None:
        try:
            return self.get_last_price(*args, **kwargs)
        except HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    @with_trace("get_last_tether_usd_price")
    @optional_exception_handling()
    def get_last_usd_coin_usd_price(self) -> float:
        candle = self.get_current_usd_coin_usd_candle()
        return candle.close

    @with_trace("get_last_tether_usd_price")
    @optional_exception_handling()
    def get_last_tether_usd_price(self) -> float:
        candle = self.get_current_tether_usd_candle()
        return candle.close

    @with_trace("_get_candles_delphi")
    def _get_candles(
        self,
        *,
        path: str,
        api_name: str,
        params: dict,
        start: int,
        end: int,
        resolution: str,
        market: str,
        exchange: str | None = None,
        network_slug: str | None = None,
        usd: bool = False,
    ) -> list[Candle]:
        params.update(
            {
                "market": market,
                "resolution": resolution,
                "start": datetime.utcfromtimestamp(start).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "end": datetime.utcfromtimestamp(end).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
        if exchange:
            params["exchange"] = exchange
        if network_slug:
            params["network"] = network_slug
        if usd:
            params["convert_to_usd"] = "true"

        resp = self._get(
            path,
            params=params,
            _api_name=api_name,
        )
        return [
            self._candle_from_response(c, resolution=Resolution(resolution))
            for c in resp["candles"]
        ]

    def _get_candles_paginate(self, *args, **kwargs) -> list[Candle]:
        candles: list[Candle] = []

        start = kwargs.pop("start")
        end = kwargs.pop("end")

        period_size = self._candles_pagination_period_seconds
        for cur_start in range(start, end + 1, period_size + 1):
            cur_end = min(end, cur_start + period_size)
            candles += self._get_candles(*args, **kwargs, start=cur_start, end=cur_end)

        return candles

    @with_trace("get_candles")
    @optional_exception_handling()
    def get_candles(
        self,
        base_slug: str,
        quote_slug: str,
        start: int,
        end: int,
        resolution: str,
        market: str,
        exchange: str | None = None,
        network_slug: str | None = None,
        usd: bool = False,
    ) -> list[Candle]:
        return self._get_candles_paginate(
            path=self.config.candles_by_slug_path,
            api_name="candles_by_slug",
            params={"base": base_slug, "quote": quote_slug},
            start=start,
            end=end,
            resolution=resolution,
            market=market,
            exchange=exchange,
            network_slug=network_slug,
            usd=usd,
        )

    @optional_exception_handling()
    def get_tether_usd_candles(
        self, start: int, end: int, resolution: str
    ) -> list[Candle]:
        return self._get_candles_paginate(
            path=self.config.candles_by_pair_path,
            api_name="candles_by_pair",
            params={"pair": TETHER_USD_PAIR},
            start=start,
            end=end,
            resolution=resolution,
            market=SPOT_MARKET,
            exchange=BINANCE_US_EXCHANGE,
            usd=False,
        )

    @optional_exception_handling()
    def get_symbol_last_price_usd(
        self,
        symbol_slug: str,
        market: str,
        exchange: str | None = None,
        network_slug: str | None = None,
        default_quote_str=TETHER_SLUG,
    ) -> float | None:
        if symbol_slug == TETHER_SLUG:
            return self.get_last_tether_usd_price()
        if symbol_slug == USD_COIN_SLUG:
            return self.get_last_usd_coin_usd_price()
        return self.get_last_price_if_exists(
            base_slug=symbol_slug,
            quote_slug=default_quote_str,
            market=market,
            exchange=exchange,
            network_slug=network_slug,
            usd=True,
        )

    @staticmethod
    def _candle_from_response(
        c: dict,
        resolution: Resolution = Resolution.R1M,
        is_open: bool = False,
        now: datetime | None = None,
    ) -> Candle:
        candle = Candle(time=datetime.fromisoformat(c["related_at"]), **c)
        if is_open:
            candle.close_time = now if now else timezone.now()
        else:
            candle.close_time = candle.time + resolution.get_timedelta()
        return candle

    @optional_exception_handling()
    def usd_price_by_address(self, network, symbol_address) -> None | float:
        response = self._get(
            self.config.usd_price_by_address_path,
            params={
                "network": network,
                "asset": symbol_address,
            },
            _api_name="usd_price_by_address",
        )
        if len(response["prices"]) == 1:
            return float(response["prices"][0]["price"])
        return None

    @optional_exception_handling()
    def pair_price_by_address(self, network, base_address, quote_address) -> float:
        response = self._get(
            self.config.pair_price_by_address_path,
            params={
                "network": network,
                "base": base_address,
                "quote": quote_address,
            },
            _api_name="pair_price_by_address",
        )

        return float(response["price"])


delphinus_client = DelphinusClient()
