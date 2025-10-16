from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

import polars as pl
from polars import DataFrame


def clean_entries(df: DataFrame, date: str | datetime.date) -> DataFrame:
    if isinstance(date, str):
        date = (
            datetime.datetime.strptime(date, "%Y-%m-%d")
            .replace(tzinfo=ZoneInfo("Asia/Tokyo"))
            .date()
        )

    null_columns = [c for c in df.columns if df[c].dtype == pl.Null]

    return (
        df.with_columns(
            pl.col(null_columns).cast(pl.String),
        )
        .with_columns(
            pl.lit(date).alias("Date"),
            pl.col("^.+DateTime$").str.to_datetime(
                "%Y-%m-%d %H:%M",
                strict=False,
                time_zone="Asia/Tokyo",
            ),
            pl.col("^period.+$").str.to_date("%Y-%m-%d", strict=False),
            pl.col("^.+Flag$").cast(pl.Int8).cast(pl.Boolean),
            pl.col("^.+Code$").cast(pl.String),
        )
        .rename({"secCode": "Code"})
        .select("Date", "Code", pl.exclude("Date", "Code"))
    )


def clean_pdf(content: bytes, doc_id: str) -> DataFrame:
    return DataFrame({"docID": [doc_id], "pdf": [content]})


def read_csv(data: bytes) -> DataFrame:
    return pl.read_csv(
        data,
        separator="\t",
        encoding="utf-16-le",
        infer_schema_length=None,
    )


def clean_csv(df: DataFrame, doc_id: str) -> DataFrame:
    return df.select(
        pl.lit(doc_id).alias("docID"),
        pl.all(),
    )
