from __future__ import annotations

import asyncio
import contextlib
from itertools import islice
from typing import TYPE_CHECKING, Any, Protocol

import polars as pl

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterable,
        AsyncIterator,
        Awaitable,
        Callable,
        Iterable,
    )
    from typing import Any

    from marimo._plugins.stateless.status import progress_bar
    from polars import DataFrame
    from tqdm.asyncio import tqdm

    from kabukit.core.client import Client

    class _Progress(Protocol):
        def __call__(
            self,
            aiterable: AsyncIterable[Any],
            /,
            total: int | None = None,
            *args: Any,
            **kwargs: Any,
        ) -> AsyncIterator[Any]: ...


MAX_CONCURRENCY = 12


async def collect[R](
    awaitables: Iterable[Awaitable[R]],
    /,
    max_concurrency: int | None = None,
) -> AsyncIterator[R]:
    max_concurrency = max_concurrency or MAX_CONCURRENCY
    semaphore = asyncio.Semaphore(max_concurrency)

    async def run(awaitable: Awaitable[R]) -> R:
        async with semaphore:
            return await awaitable

    tasks = {asyncio.create_task(run(awaitable)) for awaitable in awaitables}

    try:
        for future in asyncio.as_completed(tasks):  # async for (python 3.13+)
            with contextlib.suppress(asyncio.CancelledError):
                yield await future
    finally:
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


async def collect_fn[T, R](
    function: Callable[[T], Awaitable[R]],
    args: Iterable[T],
    /,
    max_concurrency: int | None = None,
) -> AsyncIterator[R]:
    max_concurrency = max_concurrency or MAX_CONCURRENCY
    awaitables = (function(arg) for arg in args)

    async for item in collect(awaitables, max_concurrency=max_concurrency):
        yield item


async def concat(
    awaitables: Iterable[Awaitable[DataFrame]],
    /,
    max_concurrency: int | None = None,
) -> DataFrame:
    dfs = collect(awaitables, max_concurrency=max_concurrency)
    dfs = [df async for df in dfs]
    return pl.concat(df for df in dfs if not df.is_empty())


async def concat_fn[T](
    function: Callable[[T], Awaitable[DataFrame]],
    args: Iterable[T],
    /,
    max_concurrency: int | None = None,
) -> DataFrame:
    dfs = collect_fn(function, args, max_concurrency=max_concurrency)
    dfs = [df async for df in dfs]
    return pl.concat(df for df in dfs if not df.is_empty())


type Callback = Callable[[DataFrame], DataFrame | None]
type Progress = type[progress_bar[Any] | tqdm[Any]] | _Progress


async def get_stream(
    client: Client,
    resource: str,
    args: list[Any],
    max_concurrency: int | None = None,
) -> AsyncIterator[DataFrame]:
    fn = getattr(client, f"get_{resource}")

    async for df in collect_fn(fn, args, max_concurrency):
        yield df


async def get(
    cls: type[Client],
    resource: str,
    args: Iterable[Any],
    /,
    max_items: int | None = None,
    max_concurrency: int | None = None,
    progress: Progress | None = None,
    callback: Callback | None = None,
) -> DataFrame:
    """各種データを取得し、単一のDataFrameにまとめて返す。

    Args:
        cls (type[Client]): 使用するClientクラス。
            JQuantsClientやEdinetClientなど、Clientを継承したクラス
        resource (str): 取得するデータの種類。Clientのメソッド名から"get_"を
            除いたものを指定する。
        args (Iterable[Any]): 取得対象の引数のリスト。
        max_items (int | None, optional): 取得数する上限。
        max_concurrency (int | None, optional): 同時に実行するリクエストの最大数。
            指定しないときはデフォルト値が使用される。
        progress (Progress | None, optional): 進捗表示のための関数。
            tqdm, marimoなどのライブラリを使用できる。
            指定しないときは進捗表示は行われない。
        callback (Callback | None, optional): 各DataFrameに対して適用する
            コールバック関数。指定しないときはそのままのDataFrameが使用される。

    Returns:
        DataFrame:
            すべての情報を含む単一のDataFrame。
    """
    args = list(islice(args, max_items))

    async with cls() as client:
        stream = get_stream(client, resource, args, max_concurrency)

        if progress:
            stream = progress(stream, total=len(args))

        if callback:
            stream = (x if (r := callback(x)) is None else r async for x in stream)

        dfs = [df async for df in stream if not df.is_empty()]  # ty: ignore[not-iterable]
        return pl.concat(dfs) if dfs else pl.DataFrame()
