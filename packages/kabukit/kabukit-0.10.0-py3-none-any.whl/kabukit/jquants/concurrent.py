from __future__ import annotations

from typing import TYPE_CHECKING

from kabukit.utils import concurrent

from .client import JQuantsClient
from .info import get_target_codes

if TYPE_CHECKING:
    from collections.abc import Iterable

    from polars import DataFrame

    from kabukit.utils.concurrent import Callback, Progress


async def get(
    resource: str,
    codes: Iterable[str] | None = None,
    /,
    max_items: int | None = None,
    max_concurrency: int | None = None,
    progress: Progress | None = None,
    callback: Callback | None = None,
) -> DataFrame:
    """複数の銘柄の各種データを取得し、単一のDataFrameにまとめて返す。

    Args:
        resource (str): 取得するデータの種類。JQuantsClientのメソッド名から"get_"を
            除いたものを指定する。
        codes (Iterable[str] | None): 取得対象の銘柄コードのリスト。
            指定しないときはすべての銘柄が対象となる。
        max_items (int | None, optional): 取得する銘柄数の上限。
            指定しないときはすべての銘柄が対象となる。
        max_concurrency (int | None, optional): 同時に実行するリクエストの最大数。
            指定しないときはデフォルト値が使用される。
        progress (Progress | None, optional): 進捗表示のための関数。
            tqdm, marimoなどのライブラリを使用できる。
            指定しないときは進捗表示は行われない。
        callback (Callback | None, optional): 各DataFrameに対して適用する
            コールバック関数。指定しないときはそのままのDataFrameが使用される。

    Returns:
        DataFrame:
            すべての銘柄の財務情報を含む単一のDataFrame。
    """
    if codes is None:
        codes = await get_target_codes()

    data = await concurrent.get(
        JQuantsClient,
        resource,
        codes,
        max_items=max_items,
        max_concurrency=max_concurrency,
        progress=progress,
        callback=callback,
    )
    return data.sort("Code", "Date")


async def get_statements(
    codes: Iterable[str] | str | None = None,
    /,
    max_items: int | None = None,
    max_concurrency: int = 12,
    progress: Progress | None = None,
    callback: Callback | None = None,
) -> DataFrame:
    """四半期毎の決算短信サマリーおよび業績・配当の修正に関する開示情報を取得する。

    Args:
        codes (Iterable[str] | str | None): 財務情報を取得する銘柄のコード。
            Noneが指定された場合、全銘柄が対象となる。
        max_items (int | None, optional): 取得する銘柄数の上限。
            指定しないときはすべての銘柄が対象となる。
        max_concurrency (int | None, optional): 同時に実行するリクエストの最大数。
            デフォルト値12。
        progress (Progress | None, optional): 進捗表示のための関数。
            tqdm, marimoなどのライブラリを使用できる。
            指定しないときは進捗表示は行われない。
        callback (Callback | None, optional): 各DataFrameに対して適用する
            コールバック関数。指定しないときはそのままのDataFrameが使用される。

    Returns:
        財務情報を含むDataFrame。

    Raises:
        HTTPStatusError: APIリクエストが失敗した場合。
    """
    if isinstance(codes, str):
        async with JQuantsClient() as client:
            return await client.get_statements(codes)

    return await get(
        "statements",
        codes,
        max_items=max_items,
        max_concurrency=max_concurrency,
        progress=progress,
        callback=callback,
    )


async def get_prices(
    codes: Iterable[str] | str | None = None,
    /,
    max_items: int | None = None,
    max_concurrency: int = 8,
    progress: Progress | None = None,
    callback: Callback | None = None,
) -> DataFrame:
    """日々の株価四本値を取得する。

    株価は分割・併合を考慮した調整済み株価（小数点第２位四捨五入）と調整前の株価を取得できる。

    Args:
        codes (Iterable[str] | str | None): 財務情報を取得する銘柄のコード。
            Noneが指定された場合、全銘柄が対象となる。
        max_items (int | None, optional): 取得する銘柄数の上限。
            指定しないときはすべての銘柄が対象となる。
        max_concurrency (int | None, optional): 同時に実行するリクエストの最大数。
            デフォルト値8。
        progress (Progress | None, optional): 進捗表示のための関数。
            tqdm, marimoなどのライブラリを使用できる。
            指定しないときは進捗表示は行われない。
        callback (Callback | None, optional): 各DataFrameに対して適用する
            コールバック関数。指定しないときはそのままのDataFrameが使用される。

    Returns:
        日々の株価四本値を含むDataFrame。

    Raises:
        HTTPStatusError: APIリクエストが失敗した場合。
    """
    if isinstance(codes, str):
        async with JQuantsClient() as client:
            return await client.get_prices(codes)

    return await get(
        "prices",
        codes,
        max_items=max_items,
        max_concurrency=max_concurrency,
        progress=progress,
        callback=callback,
    )
