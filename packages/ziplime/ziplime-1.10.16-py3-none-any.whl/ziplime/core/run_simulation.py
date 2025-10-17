import datetime
from pathlib import Path

from ziplime.utils.calendar_utils import get_calendar

from ziplime.assets.domain.ordered_contracts import CHAIN_PREDICATES
from ziplime.assets.repositories.sqlalchemy_adjustments_repository import SqlAlchemyAdjustmentRepository
from ziplime.assets.repositories.sqlalchemy_asset_repository import SqlAlchemyAssetRepository
from ziplime.assets.services.asset_service import AssetService
from ziplime.core.algorithm_file import AlgorithmFile
from ziplime.data.services.data_source import DataSource
from ziplime.finance.commission import PerShare, DEFAULT_PER_SHARE_COST, DEFAULT_MINIMUM_COST_PER_EQUITY_TRADE, \
    PerContract, DEFAULT_PER_CONTRACT_COST, DEFAULT_MINIMUM_COST_PER_FUTURE_TRADE
from ziplime.finance.constants import FUTURE_EXCHANGE_FEES_BY_SYMBOL
from ziplime.finance.metrics import default_metrics
from ziplime.finance.slippage.fixed_basis_points_slippage import FixedBasisPointsSlippage
from ziplime.finance.slippage.slippage_model import DEFAULT_FUTURE_VOLUME_SLIPPAGE_BAR_LIMIT
from ziplime.finance.slippage.volatility_volume_share import VolatilityVolumeShare
from ziplime.gens.domain.simulation_clock import SimulationClock
from ziplime.exchanges.exchange import Exchange
from ziplime.exchanges.simulation_exchange import SimulationExchange
from ziplime.utils.run_algo import run_algorithm
import polars as pl


async def _run_simulation(
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        trading_calendar: str,
        emission_rate: datetime.timedelta,
        cash_balance: float,
        market_data_source: DataSource,
        custom_data_sources: list[DataSource],
        algorithm_file: str,
        stop_on_error: bool,
        exchange: Exchange = None,
        config_file: str | None = None,
        benchmark_asset_symbol: str | None = None,
        benchmark_returns: pl.Series | None = None,
        asset_service: AssetService =None
):
    # benchmark_spec = BenchmarkSpec(
    #     benchmark_returns=None,
    #     benchmark_sid=benchmark_sid,
    #     benchmark_symbol=benchmark_symbol,
    #     benchmark_file=benchmark_file,
    #     no_benchmark=no_benchmark,
    # )

    calendar = get_calendar(trading_calendar)

    algo = AlgorithmFile(algorithm_file=algorithm_file, algorithm_config_file=config_file)

    clock = SimulationClock(
        trading_calendar=calendar,
        start_date=start_date,
        end_date=end_date,
        emission_rate=emission_rate,
    )
    if exchange is None:
        exchange = SimulationExchange(
            name="LIME",
            country_code="US",
            trading_calendar=calendar,
            data_bundle=market_data_source,
            equity_slippage=FixedBasisPointsSlippage(),
            equity_commission=PerShare(
                cost=DEFAULT_PER_SHARE_COST,
                min_trade_cost=DEFAULT_MINIMUM_COST_PER_EQUITY_TRADE,

            ),
            future_slippage=VolatilityVolumeShare(
                volume_limit=DEFAULT_FUTURE_VOLUME_SLIPPAGE_BAR_LIMIT,
            ),
            future_commission=PerContract(
                cost=DEFAULT_PER_CONTRACT_COST,
                exchange_fee=FUTURE_EXCHANGE_FEES_BY_SYMBOL,
                min_trade_cost=DEFAULT_MINIMUM_COST_PER_FUTURE_TRADE
            ),
            cash_balance=cash_balance,
            clock=clock
        )

    if asset_service is None:
        assets_db_url= f"sqlite+aiosqlite:///{str(Path(Path.home(), ".ziplime", "assets.sqlite").absolute())}"
        assets_repository = SqlAlchemyAssetRepository(db_url=assets_db_url, future_chain_predicates=CHAIN_PREDICATES)
        adjustments_repository = SqlAlchemyAdjustmentRepository(db_url=assets_db_url)
        asset_service = AssetService(asset_repository=assets_repository, adjustments_repository=adjustments_repository)

    return await run_algorithm(
        algorithm=algo,
        asset_service=asset_service,
        print_algo=True,
        metrics_set=default_metrics(),
        # benchmark_spec=benchmark_spec,
        custom_loader=None,
        exchanges=[exchange],
        clock=clock,
        benchmark_returns=benchmark_returns,
        benchmark_asset_symbol=benchmark_asset_symbol,
        stop_on_error=stop_on_error,
        custom_data_sources=custom_data_sources,
    )


async def run_simulation(start_date: datetime.datetime,
                         end_date: datetime.datetime,
                         emission_rate: datetime.timedelta,
                         trading_calendar: str,
                         algorithm_file: str,
                         total_cash: float,
                         market_data_source: DataSource,
                         custom_data_sources: list[DataSource],
                         stop_on_error: bool,
                         config_file: str | None = None,
                         exchange: Exchange | None = None,
                         benchmark_asset_symbol: str | None = None,
                         benchmark_returns: pl.Series | None = None,
                         asset_service:AssetService | None = None
                         ):
    return await _run_simulation(start_date=start_date, end_date=end_date, trading_calendar=trading_calendar,
                                 cash_balance=total_cash,
                                 algorithm_file=algorithm_file,
                                 config_file=config_file,
                                 market_data_source=market_data_source,
                                 custom_data_sources=custom_data_sources,
                                 exchange=exchange,
                                 emission_rate=emission_rate,
                                 benchmark_asset_symbol=benchmark_asset_symbol,
                                 benchmark_returns=benchmark_returns,
                                 stop_on_error=stop_on_error,
                                 asset_service=asset_service
                                 )
