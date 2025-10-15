from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from kabukit.utils import concurrent
from kabukit.utils.date import get_dates

from .client import EdinetClient

if TYPE_CHECKING:
    from collections.abc import Iterable

    from polars import DataFrame

    from kabukit.utils.concurrent import Callback, Progress


async def get(
    resource: str,
    args: Iterable[str | datetime.date],
    /,
    max_items: int | None = None,
    max_concurrency: int | None = None,
    progress: Progress | None = None,
    callback: Callback | None = None,
) -> DataFrame:
    """引数に対応する各種データを取得し、単一のDataFrameにまとめて返す。

    Args:
        resource (str): 取得するデータの種類。EdinetClientのメソッド名から"get_"を
            除いたものを指定する。
        args (Iterable[str | datetime.date]): 取得対象の引数のリスト。
        max_items (int | None, optional): 取得数の上限。
            指定しないときはすべてを取得する。
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
    return await concurrent.get(
        EdinetClient,
        resource,
        args,
        max_items=max_items,
        max_concurrency=max_concurrency,
        progress=progress,
        callback=callback,
    )


async def get_entries(
    dates: Iterable[datetime.date | str] | datetime.date | str | None = None,
    /,
    days: int | None = None,
    years: int | None = None,
    max_items: int | None = None,
    max_concurrency: int | None = None,
    progress: Progress | None = None,
    callback: Callback | None = None,
) -> DataFrame:
    """過去 days 日または years 年の文書一覧を取得し、単一の DataFrame にまとめて返す。

    Args:
        dates (Iterable[datetime.date | str] | datetime.date | str | None):
            取得対象の日付のリスト。None の場合は days または years に基づいて
            日付リストを生成する。
        days (int | None): 過去 days 日の日付リストを取得する。
        years (int | None): 過去 years 年の日付リストを取得する。
            daysが指定されている場合は無視される。
        max_items (int | None, optional): 取得数の上限。
        max_concurrency (int | None, optional): 同時に実行するリクエストの最大数。
            指定しないときはデフォルト値が使用される。
        progress (Progress | None, optional): 進捗表示のための関数。
            tqdm, marimoなどのライブラリを使用できる。
            指定しないときは進捗表示は行われない。
        callback (Callback | None, optional): 各DataFrameに対して適用する
            コールバック関数。指定しないときはそのままのDataFrameが使用される。

    Returns:
        DataFrame:
            文書一覧を含む単一のDataFrame。
    """
    if isinstance(dates, (str, datetime.date)):
        async with EdinetClient() as client:
            return await client.get_entries(dates)

    if dates is None:
        dates = get_dates(days=days, years=years)

    df = await get(
        "entries",
        dates,
        max_items=max_items,
        max_concurrency=max_concurrency,
        progress=progress,
        callback=callback,
    )

    if df.is_empty():
        return df

    return df.sort("Code", "Date")


async def get_documents(
    doc_ids: Iterable[str] | str,
    /,
    max_items: int | None = None,
    max_concurrency: int | None = None,
    progress: Progress | None = None,
    callback: Callback | None = None,
    *,
    pdf: bool = False,
) -> DataFrame:
    """文書をCSV形式あるいはPDF形式で取得し、単一のDataFrameにまとめて返す。

    Args:
        doc_ids (Iterable[str] | str): 取得対象の文書IDのリスト。
        max_items (int | None, optional): 取得数の上限。
        max_concurrency (int | None, optional): 同時に実行するリクエストの最大数。
            指定しないときはデフォルト値が使用される。
        progress (Progress | None, optional): 進捗表示のための関数。
            tqdm, marimoなどのライブラリを使用できる。
            指定しないときは進捗表示は行われない。
        callback (Callback | None, optional): 各DataFrameに対して適用する
            コールバック関数。指定しないときはそのままのDataFrameが使用される。
        pdf (bool): PDF形式で取得する場合はTrue、CSV形式で取得する場合はFalse。

    Returns:
        DataFrame:
            文書含む単一のDataFrame。
    """
    if isinstance(doc_ids, str):
        async with EdinetClient() as client:
            return await client.get_document(doc_ids, pdf=pdf)

    df = await get(
        "pdf" if pdf else "csv",
        doc_ids,
        max_items=max_items,
        max_concurrency=max_concurrency,
        progress=progress,
        callback=callback,
    )
    return df.sort("docID")
