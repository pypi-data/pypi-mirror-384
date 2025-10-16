import logging
from datetime import datetime, date
from functools import cached_property
from pathlib import Path
from typing import List, TYPE_CHECKING, Type, Union, Any, Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Engine, create_engine, insert, func
from sqlmodel import Session, select
from sqlmodel.main import SQLModel


from bearish.database.schemas import (
    EquityORM,
    CurrencyORM,
    CryptoORM,
    EtfORM,
    FinancialMetricsORM,
    CashFlowORM,
    BalanceSheetORM,
    PriceORM,
    SourcesORM,
    EarningsDateORM,
    QuarterlyFinancialMetricsORM,
    QuarterlyCashFlowORM,
    QuarterlyBalanceSheetORM,
    PriceTrackerORM,
    FinancialsTrackerORM,
)
from bearish.database.scripts.upgrade import upgrade
from bearish.exchanges.exchanges import ExchangeQuery
from bearish.interface.interface import BearishDbBase
from bearish.models.assets.assets import Assets
from bearish.models.base import (
    TrackerQuery,
    Ticker,
    BaseTracker,
    FinancialsTracker,
    PriceTracker,
)
from bearish.models.financials.balance_sheet import BalanceSheet, QuarterlyBalanceSheet
from bearish.models.financials.base import Financials, ManyFinancials
from bearish.models.financials.cash_flow import CashFlow, QuarterlyCashFlow
from bearish.models.financials.earnings_date import EarningsDate
from bearish.models.financials.metrics import (
    FinancialMetrics,
    QuarterlyFinancialMetrics,
)
from bearish.models.price.price import Price
from bearish.utils.utils import batch

if TYPE_CHECKING:
    from bearish.models.query.query import AssetQuery

logger = logging.getLogger(__name__)

BATCH_SIZE = 5000


class BearishDb(BearishDbBase):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    database_path: Path
    auto_migration: bool = True

    @cached_property
    def _engine(self) -> Engine:
        database_url = f"sqlite:///{Path(self.database_path)}"
        if self.auto_migration:
            upgrade(database_url)
        engine = create_engine(database_url)
        return engine

    def model_post_init(self, __context: Any) -> None:
        self._engine  # noqa: B018

    def _write_assets(self, assets: Assets) -> None:
        with Session(self._engine) as session:
            objects_orm = (
                [EquityORM(**object.model_dump()) for object in assets.equities]
                + [CurrencyORM(**object.model_dump()) for object in assets.currencies]
                + [CryptoORM(**object.model_dump()) for object in assets.cryptos]
                + [EtfORM(**object.model_dump()) for object in assets.etfs]
            )
            logger.debug(
                f"writing assets to database. Number of assets: {len(objects_orm)}"
            )

            session.add_all(objects_orm)
            session.commit()

    def _write_series(self, series: List["Price"]) -> None:
        with Session(self._engine) as session:
            data = [serie.model_dump() for serie in series]
            chunks = batch(data, BATCH_SIZE)
            for chunk in chunks:
                stmt = insert(PriceORM).prefix_with("OR REPLACE").values(chunk)
                session.exec(stmt)  # type: ignore
            session.commit()

    def _write_financials(self, financials: List[Financials]) -> None:
        many_financials = ManyFinancials(financials=financials)
        self._write_financials_series(
            many_financials.get("financial_metrics"), FinancialMetricsORM  # type: ignore
        )
        self._write_financials_series(many_financials.get("cash_flows"), CashFlowORM)  # type: ignore
        self._write_financials_series(
            many_financials.get("balance_sheets"), BalanceSheetORM  # type: ignore
        )
        self._write_financials_series(
            many_financials.get("earnings_date"), EarningsDateORM  # type: ignore
        )
        self._write_financials_series(
            many_financials.get("quarterly_financial_metrics"),  # type: ignore
            QuarterlyFinancialMetricsORM,
        )
        self._write_financials_series(
            many_financials.get("quarterly_cash_flows"), QuarterlyCashFlowORM  # type: ignore
        )
        self._write_financials_series(
            many_financials.get("quarterly_balance_sheets"), QuarterlyBalanceSheetORM  # type: ignore
        )

    def _write_financials_series(
        self,
        series: Union[
            List[CashFlow],
            List[FinancialMetrics],
            List[BalanceSheet],
            List[EarningsDate],
            List[QuarterlyCashFlow],
            List[QuarterlyFinancialMetrics],
            List[QuarterlyBalanceSheet],
        ],
        table: Type[SQLModel],
    ) -> None:
        if not series:
            logger.warning(f"No data found for '{[serie.symbol for serie in series]}'")
            return None
        with Session(self._engine) as session:
            data = [serie.model_dump() for serie in series]
            chunks = batch(data, BATCH_SIZE)
            for chunk in chunks:
                stmt = insert(table).prefix_with("OR REPLACE").values(chunk)
                session.exec(stmt)  # type: ignore
            session.commit()

    def _read_series(self, query: "AssetQuery", months: int = 1) -> List[Price]:
        end_date = datetime.now()
        start_date = end_date - pd.Timedelta(days=months * 31)
        with Session(self._engine) as session:
            query_ = select(PriceORM)
            query_ = query_.where(PriceORM.symbol.in_(query.symbols.all())).where(  # type: ignore
                PriceORM.date.between(start_date, end_date)  # type: ignore
            )
            series = session.exec(query_).all()
            return [Price.model_validate(serie) for serie in series]

    def _read_financials(self, query: "AssetQuery") -> Financials:
        with Session(self._engine) as session:
            financial_metrics = self._read_asset_type(
                session, FinancialMetrics, FinancialMetricsORM, query
            )
            cash_flows = self._read_asset_type(session, CashFlow, CashFlowORM, query)
            balance_sheets = self._read_asset_type(
                session, BalanceSheet, BalanceSheetORM, query
            )
            earnings_date = self._read_asset_type(
                session, EarningsDate, EarningsDateORM, query
            )
            quarterly_financial_metrics = self._read_asset_type(
                session, QuarterlyFinancialMetrics, QuarterlyFinancialMetricsORM, query
            )
            quarterly_cash_flows = self._read_asset_type(
                session, QuarterlyCashFlow, QuarterlyCashFlowORM, query
            )
            quarterly_balance_sheets = self._read_asset_type(
                session, QuarterlyBalanceSheet, QuarterlyBalanceSheetORM, query
            )
            return Financials(
                financial_metrics=financial_metrics,
                cash_flows=cash_flows,
                balance_sheets=balance_sheets,
                quarterly_financial_metrics=quarterly_financial_metrics,
                quarterly_cash_flows=quarterly_cash_flows,
                quarterly_balance_sheets=quarterly_balance_sheets,
                earnings_date=earnings_date,
            )

    def _read_assets(self, query: "AssetQuery") -> Assets:
        with Session(self._engine) as session:
            from bearish.models.assets.equity import Equity
            from bearish.models.assets.crypto import Crypto
            from bearish.models.assets.currency import Currency
            from bearish.models.assets.etfs import Etf

            equities = self._read_asset_type(session, Equity, EquityORM, query)
            currencies = self._read_asset_type(session, Currency, CurrencyORM, query)
            cryptos = self._read_asset_type(session, Crypto, CryptoORM, query)
            etfs = self._read_asset_type(session, Etf, EtfORM, query)
            return Assets(
                equities=equities, currencies=currencies, cryptos=cryptos, etfs=etfs
            )

    def _read_asset_type(
        self,
        session: Session,
        table: Type[BaseModel],
        orm_table: Type[
            Union[
                EquityORM,
                CurrencyORM,
                CryptoORM,
                EtfORM,
                BalanceSheetORM,
                CashFlowORM,
                FinancialMetricsORM,
                QuarterlyBalanceSheetORM,
                QuarterlyCashFlowORM,
                QuarterlyFinancialMetricsORM,
                EarningsDateORM,
            ]
        ],
        query: "AssetQuery",
    ) -> List[BaseModel]:
        if query.symbols.all():
            query_ = select(orm_table).where(orm_table.symbol.in_(query.symbols.all()))  # type: ignore
        else:
            query_ = select(orm_table)
            if query.countries:
                query_ = query_.where(orm_table.country.in_(query.countries))  # type: ignore
            if query.exchanges:
                query_ = query_.where(orm_table.exchange.in_(query.exchanges))  # type: ignore
        if query.excluded_sources:
            query_ = query_.where(~orm_table.source.in_(query.excluded_sources))  # type: ignore

        assets = session.exec(query_).all()
        return [table.model_validate(asset) for asset in assets]

    def _read_sources(self) -> List[str]:
        with Session(self._engine) as session:
            query_ = select(SourcesORM).distinct()
            sources = session.exec(query_).all()
            return [source.source for source in sources]

    def _write_source(self, source: str) -> None:
        with Session(self._engine) as session:
            stmt = (
                insert(SourcesORM)
                .prefix_with("OR REPLACE")
                .values([{"source": source}])
            )

            session.exec(stmt)  # type: ignore
            session.commit()

    def _write_trackers(
        self,
        trackers: List[FinancialsTracker] | List[PriceTracker],
        tracker_type: Type[BaseTracker],
    ) -> None:
        with Session(self._engine) as session:
            orm_class = (
                PriceTrackerORM
                if tracker_type is PriceTracker
                else FinancialsTrackerORM
            )
            stmt = (
                insert(orm_class)
                .prefix_with("OR REPLACE")
                .values([t.model_dump() for t in trackers])
            )
            session.exec(stmt)  # type: ignore
            session.commit()

    def _read_tracker(
        self,
        tracker_query: TrackerQuery,
        tracker_type: Union[Type[PriceTracker], Type[FinancialsTracker]],
    ) -> List[Ticker]:
        with Session(self._engine) as session:
            tracker_orm = (
                PriceTrackerORM
                if tracker_type is PriceTracker
                else FinancialsTrackerORM
            )
            query = select(tracker_orm.symbol, tracker_orm.exchange, tracker_orm.source)
            if tracker_query.exchange:
                query = query.where(tracker_orm.exchange == tracker_query.exchange)
            if tracker_query.reference_date:
                query = query.where(
                    func.abs(
                        func.julianday(tracker_orm.date)
                        - func.julianday(tracker_query.reference_date)
                    )
                    >= tracker_query.delay
                )
            tracker_orm = session.exec(query).all()  # type: ignore
            return [
                Ticker(symbol=t[0], exchange=t[1], source=t[2]) for t in tracker_orm  # type: ignore
            ]

    def _get_tickers(self, exchange_query: ExchangeQuery) -> List[Ticker]:
        if not exchange_query.sources:
            query = f"""SELECT symbol, exchange from equity where {exchange_query.to_suffixes_sql_statement()} 
                OR exchange IN {exchange_query.to_aliases_sql_statement()};"""
        else:
            query = f"""SELECT symbol, exchange from equity where source IN {exchange_query.to_sources_sql_statement()} 
            AND ( {exchange_query.to_suffixes_sql_statement()} 
                 OR exchange IN {exchange_query.to_aliases_sql_statement()});"""

        symbols = pd.read_sql(
            query,
            con=self._engine,
        )
        return [
            Ticker(symbol=symbol["symbol"], exchange=symbol["exchange"])
            for symbol in symbols.to_dict(orient="records")
        ]

    def _read_query(self, query: str) -> pd.DataFrame:
        return pd.read_sql(
            query,
            con=self._engine,
        )

    def read_price_tracker(self, symbol: str) -> Optional[date]:
        with Session(self._engine) as session:
            query = select(PriceTrackerORM.date).where(PriceTrackerORM.symbol == symbol)  # type: ignore
            result = session.exec(query).first()
            if result is None:
                return None
            return result  # type: ignore
