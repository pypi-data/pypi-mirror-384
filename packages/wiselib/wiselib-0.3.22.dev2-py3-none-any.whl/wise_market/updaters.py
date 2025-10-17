import logging
from decimal import Decimal
from typing import Tuple

from django.conf import settings
from django.db import transaction, IntegrityError
from wise.station.updater import ModelUpdater, SkipUpdate, UpdaterHandler
from wise.utils.http import create_session

from wise_market.models import (
    Pair,
    Symbol,
    Market,
    Exchange,
    ExchangeMarket,
    ExchangeMarketPairBinding,
    Network,
    NetworkSymbolBinding,
    NetworkSymbolType,
)

logger = logging.getLogger(__name__)

market_updater_handler = UpdaterHandler(
    client=create_session(
        service_name="delphi",
        base_url=settings.ENV.delphi.url,
        retry_count=3,
    )
)


class SymbolUpdater(ModelUpdater[Symbol]):
    abbreviation: str | None
    slug: str | None

    def update(self) -> Symbol:
        defaults = {"name": self.abbreviation}
        if not self.slug or not self.abbreviation:
            raise SkipUpdate("invalid slug or abbreviation")

        symbol = Symbol.objects.update_or_create(slug=self.slug, defaults=defaults)[0]
        symbol.get_or_create_asset()
        return symbol


class PairUpdater(ModelUpdater[Pair]):
    base: SymbolUpdater
    quote: SymbolUpdater
    slug: str
    name: str

    def update(self) -> Pair:
        pair = Pair.objects.update_or_create(
            base=self.base.update(),
            quote=self.quote.update(),
            defaults={"slug": self.slug, "name": self.name},
        )[0]
        pair.get_or_create_asset()
        return pair


class MarketUpdater(ModelUpdater[Market]):
    name: str

    def update(self) -> Market:
        try:
            with transaction.atomic():
                return Market.objects.get_or_create(name=self.name)[0]
        except IntegrityError:
            return Market.objects.get(name=self.name)


class ExchangeUpdater(ModelUpdater[Exchange]):
    name: str

    def update(self) -> Exchange:
        try:
            with transaction.atomic():
                return Exchange.objects.get_or_create(name=self.name)[0]
        except IntegrityError:
            return Exchange.objects.get(name=self.name)


class ExchangeMarketUpdater(ModelUpdater[ExchangeMarket]):
    exchange: str
    market: str

    def update(self) -> ExchangeMarket:
        return ExchangeMarket.objects.get_or_create(
            exchange=ExchangeUpdater(name=self.exchange).update(),
            market=MarketUpdater(name=self.market).update(),
        )[0]


class NetworkUpdater(ModelUpdater[Network]):
    name: str | None = None
    slug: str | None = None

    def update(self) -> Network:
        if not self.slug or not self.name:
            raise SkipUpdate("invalid slug or name")

        try:
            with transaction.atomic():
                network, _ = Network.objects.get_or_create(
                    slug=self.slug, defaults={"name": self.name}
                )
            return network
        except IntegrityError:
            return Network.objects.get(slug=self.slug)


class ExchangeMarketPairBindingUpdater(ModelUpdater[ExchangeMarketPairBinding]):
    symbol_pair: PairUpdater
    market: ExchangeMarketUpdater
    network: NetworkUpdater | None
    is_trading: bool = False

    def _get_symbol_network_decimals_and_step_size(
        self, network: Network, symbol: Symbol
    ) -> Tuple[int, Decimal]:
        binding = NetworkSymbolBinding.objects.filter(
            network=network, symbol=symbol
        ).first() or market_updater_handler.pull_one(
            "symbol_network_binding",
            symbol__slug=symbol.slug,
            network__slug=network.slug,
        )

        if not binding:
            err_message = (
                f"Cannot find symbol decimals for {symbol} in {network} network"
            )
            raise SkipUpdate(err_message)

        return binding.decimals, binding.step_size

    def update(self) -> ExchangeMarketPairBinding:
        pair = self.symbol_pair.update()
        exchange_market = self.market.update()
        defaults = {"min_notional": 0.1, "is_active": self.is_trading}
        if self.network:
            network = self.network.update()
            (
                defaults["price_decimals"],
                defaults["price_step_size"],
            ) = self._get_symbol_network_decimals_and_step_size(  # type: ignore
                network, pair.quote
            )
            (
                defaults["quantity_decimals"],
                defaults["quantity_step_size"],
            ) = self._get_symbol_network_decimals_and_step_size(  # type: ignore
                network, pair.base
            )  # type: ignore
        else:
            raise SkipUpdate("Network is missing")

        return ExchangeMarketPairBinding.objects.update_or_create(
            exchange_market=exchange_market, pair=pair, defaults=defaults
        )[0]


class NetworkSymbolBindingUpdater(ModelUpdater[NetworkSymbolBinding]):
    network_slug: str
    symbol_slug: str
    symbol_network_type: str
    decimals: int | None = None
    contract_address: str | None = None
    is_deprecated: bool | None = None

    def _get_symbol(self):
        symbol = Symbol.objects.filter(
            slug=self.symbol_slug
        ).first() or market_updater_handler.pull_one("symbol", slug=self.symbol_slug)

        if not symbol:
            raise SkipUpdate(f"Can not match symbol {self.symbol_slug}")
        return symbol

    def _get_network(self) -> Network:
        network = Network.objects.filter(
            slug=self.network_slug
        ).first() or market_updater_handler.pull_one("network", slug=self.symbol_slug)

        if not network:
            raise SkipUpdate(f"Can not match network {self.network_slug}")
        return network

    def update(self) -> NetworkSymbolBinding:
        network = self._get_network()
        symbol = self._get_symbol()

        if not self.decimals and not self.contract_address:
            raise SkipUpdate("decimals or contract_address is missing.")

        defaults: dict = {"type": self.symbol_network_type}
        if self.decimals is not None:
            defaults["decimals"] = self.decimals
            defaults["step_size"] = Decimal(f"1e-{self.decimals}")
        if self.contract_address is not None:
            defaults["contract_address"] = self.contract_address

        if self.is_deprecated is not None:
            defaults["is_active"] = not self.is_deprecated

        if self.symbol_network_type == NetworkSymbolType.NATIVE_COIN:
            old_native_coin = NetworkSymbolBinding.objects.filter(
                network=network, type=NetworkSymbolType.NATIVE_COIN
            ).first()
            if old_native_coin and old_native_coin.symbol != symbol:
                renewed_native_coin = market_updater_handler.pull_one(
                    "symbol_network_binding",
                    network__slug=self.network_slug,
                    symbol__slug=old_native_coin.symbol.slug,
                )
                if (
                    renewed_native_coin
                    and renewed_native_coin.type == NetworkSymbolType.NATIVE_COIN
                ):
                    raise SkipUpdate(
                        f"Native coin for {self.network_slug} is not unique."
                    )

        return NetworkSymbolBinding.objects.update_or_create(
            network=network, symbol=symbol, defaults=defaults
        )[0]


(
    market_updater_handler.add("symbol", SymbolUpdater)
    .add("pair", PairUpdater)
    .add("exchange_market", ExchangeMarketUpdater)
    .add("network", NetworkUpdater)
    .add("symbol_network_binding", NetworkSymbolBindingUpdater)
    .add(
        "trading_supported_pair_market",
        ExchangeMarketPairBindingUpdater,
    )
)
