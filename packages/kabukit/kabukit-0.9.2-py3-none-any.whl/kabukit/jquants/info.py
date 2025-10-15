from __future__ import annotations

import polars as pl
from polars import DataFrame


def clean(df: DataFrame) -> DataFrame:
    return df.with_columns(
        pl.col("Date").str.to_date("%Y-%m-%d"),
        pl.col("^.*CodeName$", "ScaleCategory").cast(pl.Categorical),
    ).drop("^.+Code$", "CompanyNameEnglish")


async def get_info(code: str | None = None, /) -> DataFrame:
    """上場銘柄一覧銘を取得する。

    Returns:
        銘柄情報を含むDataFrame。

    Raises:
        HTTPStatusError: APIリクエストが失敗した場合。
    """
    from .client import JQuantsClient

    async with JQuantsClient() as client:
        return await client.get_info(code)


async def get_target_codes() -> list[str]:
    """分析対象となる銘柄コードのリストを返す。

    以下の条件を満たす銘柄は対象外とする。

    - 市場: TOKYO PRO MARKET
    - 業種: その他 -- (投資信託など)
    - 優先株式
    """
    info = await get_info()

    return (
        info.filter(
            pl.col("MarketCodeName") != "TOKYO PRO MARKET",
            pl.col("Sector17CodeName") != "その他",
            ~pl.col("CompanyName").str.contains("優先株式"),
        )
        .get_column("Code")
        .to_list()
    )
