from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from polars import DataFrame


def clean(df: DataFrame) -> DataFrame:
    return df.select(
        pl.col("Date").str.to_date("%Y-%m-%d"),
        pl.lit("TOPIX").alias("Code"),
        pl.exclude("Date"),
    )
