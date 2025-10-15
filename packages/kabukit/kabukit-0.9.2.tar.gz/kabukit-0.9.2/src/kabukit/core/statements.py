from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from .base import Base

if TYPE_CHECKING:
    from polars import DataFrame


class Statements(Base):
    """財務諸表データを保持し、分析に必要な項目を抽出するメソッドを提供する。

    このクラスは、Polars DataFrameを内部で利用して、J-Quants APIなどから
    取得した財務諸表の時系列データを格納する。
    純資産、予想利益、配当といった分析のキーとなる項目を、使いやすい形に
    正規化して抽出する機能を提供する。

    Attributes:
        data (pl.DataFrame): 財務諸表の時系列データ。
    """

    def shares(self) -> DataFrame:
        """発行済株式数と自己株式数を時系列データとして抽出する。

        財務データの中から、株式数に関連する情報（発行済株式数、自己株式数）を
        時系列データとして抽出する。

        Returns:
            pl.DataFrame: Date, Code, IssuedShares, TreasuryShares 列を
            持つDataFrame。
        """
        return self.data.filter(
            pl.col("IssuedShares").is_not_null(),
        ).select(
            "Date",
            "Code",
            "IssuedShares",
            "TreasuryShares",
        )

    def equity(self) -> DataFrame:
        """純資産を時系列データとして抽出する。

        財務データの中から、純資産の情報を時系列データとして抽出する。

        Returns:
            pl.DataFrame: Date, Code, Equity 列を持つDataFrame。
        """
        return self.data.filter(
            pl.col("Equity").is_not_null(),
        ).select("Date", "Code", "Equity")

    def forecast_profit(self) -> DataFrame:
        """予想純利益を時系列データとして抽出する。

        決算種別(`TypeOfDocument`)に応じて、通期決算（FY）の場合は
        来期予想 (`NextYearForecastProfit`) を、それ以外の場合は
        当期予想 (`ForecastProfit`) を「予想純利益」として正規化する。

        Returns:
            pl.DataFrame: Date, Code, ForecastProfit 列を持つDataFrame。
        """
        return (
            self.data.with_columns(
                pl.when(pl.col("TypeOfDocument").str.starts_with("FY"))
                .then(pl.col("NextYearForecastProfit"))
                .otherwise(pl.col("ForecastProfit"))
                .alias("ForecastProfit"),
            )
            .filter(pl.col("ForecastProfit").is_not_null())
            .select("Date", "Code", "ForecastProfit")
        )

    def forecast_dividend(self) -> DataFrame:
        """予想年間配当総額を時系列データとして抽出する。

        J-Quants APIでは配当総額の予想値が直接提供されないため、
        他の予想値から逆算して算出する。具体的には、予想EPSと予想純利益から
        「予想の基準となる株式数」を算出し、それに予想1株あたり配当を乗じて
        配当総額を計算する。

        決算種別に応じて、当期予想と来期予想を使い分ける。

        Returns:
            pl.DataFrame: Date, Code, ForecastDividend 列を持つDataFrame。
        """
        # 予想株式数を計算
        forecast_shares = (
            pl.when(pl.col("TypeOfDocument").str.starts_with("FY"))
            .then(
                pl.col("NextYearForecastProfit")
                / pl.col("NextYearForecastEarningsPerShare"),
            )
            .otherwise(pl.col("ForecastProfit") / pl.col("ForecastEarningsPerShare"))
            .alias("ForecastShares")
        )

        # 年間配当総額を計算
        annual_forecast_dividend = (
            pl.when(pl.col("TypeOfDocument").str.starts_with("FY"))
            .then(
                pl.col("NextYearForecastDividendPerShareAnnual")
                * pl.col("ForecastShares"),
            )
            .otherwise(
                pl.col("ForecastDividendPerShareAnnual") * pl.col("ForecastShares"),
            )
            .round(0)
            .alias("ForecastDividend")
        )

        return (
            self.data.with_columns(forecast_shares)
            .with_columns(annual_forecast_dividend)
            .filter(pl.col("ForecastDividend").is_not_null())
            .select("Date", "Code", "ForecastDividend")
        )
