from typing import Any, Self
import polars as pl
import aiocache
from aiocache import Cache

from ziplime.assets.domain.asset_type import AssetType
from ziplime.assets.entities.asset import Asset
from ziplime.assets.entities.symbol_universe import SymbolsUniverse
from ziplime.assets.models.asset_router import AssetRouter
from ziplime.assets.entities.commodity import Commodity
from ziplime.assets.entities.currency import Currency
from ziplime.assets.entities.equity import Equity
from ziplime.assets.models.equity_symbol_mapping_model import EquitySymbolMappingModel
from ziplime.assets.models.exchange_info import ExchangeInfo
from ziplime.assets.models.futures_contract_model import FuturesContractModel
from ziplime.trading.models.trading_pair import TradingPair


class AssetRepository:

    async def save_equities(self, equities: list[Equity]) -> None: ...
    async def save_symbol_universe(self, symbol_universe: SymbolsUniverse): ...

    async def save_commodities(self, commodities: list[Commodity]) -> None: ...

    async def save_asset_routers(self, asset_routers: list[AssetRouter]) -> None: ...

    async def save_currencies(self, currencies: list[Currency]) -> None: ...

    async def save_exchanges(self, exchanges: list[ExchangeInfo]) -> None: ...

    async def save_trading_pairs(self, trading_pairs: list[TradingPair]) -> None: ...

    async def save_equity_symbol_mappings(self, equity_symbol_mappings: list[EquitySymbolMappingModel]) -> None: ...

    async def get_asset_by_sid(self, sid: int) -> Asset: ...
    async def get_assets_by_sids(self, sids: list[int]) -> list[Asset]: ...

    async def get_equity_by_symbol(self, symbol: str, exchange_name: str) -> Equity | None: ...
    async def get_equities_by_symbols(self, symbols: list[str]) -> list[Equity]: ...
    async def get_equities_by_symbols_and_exchange(self, symbols: list[str], exchange_name: str) -> list[Equity]: ...
    async def get_symbols_universe(self, symbol: str) -> SymbolsUniverse | None: ...

    @aiocache.cached(cache=Cache.MEMORY)
    async def get_asset_by_symbol(self, symbol: str, asset_type: AssetType, exchange_name: str) -> Asset | None:
        match asset_type:
            case AssetType.EQUITY:
                return await self.get_equity_by_symbol(symbol=symbol, exchange_name=exchange_name)
            case AssetType.FUTURES_CONTRACT:
                return await self.get_futures_contract_by_symbol(symbol=symbol, exchange_name=exchange_name)
            case AssetType.CURRENCY:
                return await self.get_currency_by_symbol(symbol=symbol, exchange_name=exchange_name)
            case AssetType.COMMODITY:
                return await self.get_commodity_by_symbol(symbol=symbol, exchange_name=exchange_name)
            # case AssetType.OPTIONS_CONTRACT:
            #     return await self.get_options_contract_by_symbol(symbol=symbol, exchange_name=exchange_name)
            case _:
                raise ValueError(f"Unsupported asset type: {asset_type}")

    async def get_futures_contract_by_symbol(self, symbol: str, exchange_name: str) -> FuturesContractModel | None: ...

    async def get_currency_by_symbol(self, symbol: str, exchange_name:str) -> Currency | None: ...

    async def get_commodity_by_symbol(self, symbol: str, exchange_name:str) -> Commodity | None: ...
    # async def get_options_contract_by_symbol(self, symbol: str, exchange_name:str) -> Commodity | None: ...

    def to_json(self): ...

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self: ...
