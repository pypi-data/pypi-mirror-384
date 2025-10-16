from __future__ import annotations

import polars as pl
from polars import DataFrame


def clean(df: DataFrame) -> DataFrame:
    return df.with_columns(
        pl.col("Date").str.to_date("%Y-%m-%d"),
        pl.col("^.*CodeName$", "ScaleCategory").cast(pl.Categorical),
    ).drop("^.+Code$", "CompanyNameEnglish")
