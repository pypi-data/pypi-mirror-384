from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from polars import DataFrame


def clean(df: DataFrame) -> DataFrame:
    df = df.select(pl.exclude(r"^.*\(REIT\)$"))
    return df.pipe(_rename).pipe(_cast)


def _rename(df: DataFrame) -> DataFrame:
    return df.rename(
        {
            "LocalCode": "Code",
            "NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock": "IssuedShares",  # noqa: E501
            "NumberOfTreasuryStockAtTheEndOfFiscalYear": "TreasuryShares",
            "AverageNumberOfShares": "AverageOutstandingShares",
        },
    )


def _cast(df: DataFrame) -> DataFrame:
    return (
        df.with_columns(
            pl.col("^.*Date$").str.to_date("%Y-%m-%d", strict=False),
            pl.col("DisclosedTime").str.to_time("%H:%M:%S", strict=False),
            pl.col("TypeOfCurrentPeriod").cast(pl.Categorical),
        )
        .pipe(_cast_float)
        .pipe(_cast_bool)
    )


def _cast_float(df: DataFrame) -> DataFrame:
    return df.with_columns(
        pl.col(f"^.*{name}.*$").cast(pl.Float64, strict=False)
        for name in [
            "Assets",
            "BookValue",
            "Cash",
            "Distributions",
            "Dividend",
            "Earnings",
            "Equity",
            "NetSales",
            "PayoutRatio",
            "Profit",
        ]
    ).with_columns(
        pl.col(
            "IssuedShares",
            "TreasuryShares",
        ).cast(pl.Int64, strict=False),
        pl.col(
            "AverageOutstandingShares",
        ).cast(pl.Float64, strict=False),
    )


def _cast_bool(df: DataFrame) -> DataFrame:
    columns = df.select(pl.col("^.*Changes.*$")).columns
    columns.append("RetrospectiveRestatement")

    return df.with_columns(
        pl.when(pl.col(col) == "true")
        .then(True)  # noqa: FBT003
        .when(pl.col(col) == "false")
        .then(False)  # noqa: FBT003
        .otherwise(None)
        .alias(col)
        for col in columns
    )


def with_date(df: DataFrame, holidays: list[datetime.date]) -> DataFrame:
    """`Date`列を追加する。

    開示日が休日のとき、あるいは、開示時刻が15時30分以降の場合、Dateを開示日の翌営業日に設定する。
    """
    is_after_hours = pl.col("DisclosedTime").is_null() | (
        pl.col("DisclosedTime") >= datetime.time(15, 30)
    )

    return df.select(
        pl.when(is_after_hours)
        .then(pl.col("DisclosedDate") + datetime.timedelta(days=1))
        .otherwise(pl.col("DisclosedDate"))
        .dt.add_business_days(0, holidays=holidays, roll="forward")
        .alias("Date"),
        pl.all(),
    )
