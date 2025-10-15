from __future__ import annotations

from typing import Annotated

import typer
from async_typer import AsyncTyper
from typer import Argument, Option

# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownMemberType=false


def set_table() -> None:
    import polars as pl

    pl.Config.set_tbl_rows(5)
    pl.Config.set_tbl_cols(6)
    pl.Config.set_tbl_hide_dtype_separator()


set_table()


app = AsyncTyper(
    add_completion=False,
    help="J-QuantsまたはEDINETからデータを取得します。",
)

Code = Annotated[
    str | None,
    Argument(help="銘柄コード。指定しない場合は全銘柄の情報を取得します。"),
]
Date = Annotated[
    str | None,
    Argument(help="取得する日付。指定しない場合は全期間の情報を取得します。"),
]
Quiet = Annotated[
    bool,
    Option("--quiet", "-q", help="プログレスバーを表示しません。"),
]
MaxItems = Annotated[
    int | None,
    Option("--max-items", help="取得する銘柄数の上限。全銘柄取得時にのみ有効です。"),
]


@app.async_command()
async def info(code: Code = None, *, quiet: Quiet = False) -> None:
    """上場銘柄一覧を取得します。"""
    from kabukit.core.info import Info
    from kabukit.jquants.info import get_info

    df = await get_info(code)

    if code or not quiet:
        typer.echo(df)

    if code is None:
        path = Info(df).write()
        typer.echo(f"全銘柄の情報を '{path}' に保存しました。")


@app.async_command()
async def statements(
    code: Code = None,
    *,
    quiet: Quiet = False,
    max_items: MaxItems = None,
) -> None:
    """財務情報を取得します。"""
    import tqdm.asyncio

    from kabukit.core.statements import Statements
    from kabukit.jquants.concurrent import get_statements

    progress = None if code or quiet else tqdm.asyncio.tqdm
    df = await get_statements(code, max_items=max_items, progress=progress)

    if not quiet:
        typer.echo(df)

    if code is None:
        path = Statements(df).write()
        typer.echo(f"全銘柄の財務情報を '{path}' に保存しました。")


@app.async_command()
async def prices(
    code: Code = None,
    *,
    quiet: Quiet = False,
    max_items: MaxItems = None,
) -> None:
    """株価情報を取得します。"""
    import tqdm.asyncio

    from kabukit.core.prices import Prices
    from kabukit.jquants.concurrent import get_prices

    progress = None if code or quiet else tqdm.asyncio.tqdm
    df = await get_prices(code, max_items=max_items, progress=progress)

    if not quiet:
        typer.echo(df)

    if code is None:
        path = Prices(df).write()
        typer.echo(f"全銘柄の株価情報を '{path}' に保存しました。")


@app.async_command()
async def entries(
    date: Date = None,
    *,
    quiet: Quiet = False,
    max_items: MaxItems = None,
) -> None:
    """書類一覧を取得します。"""
    import tqdm.asyncio

    from kabukit.core.entries import Entries
    from kabukit.edinet.concurrent import get_entries

    progress = None if date or quiet else tqdm.asyncio.tqdm
    df = await get_entries(date, years=10, progress=progress, max_items=max_items)

    if not quiet:
        typer.echo(df)

    if not date:
        path = Entries(df).write()
        typer.echo(f"書類一覧を '{path}' に保存しました。")


@app.async_command(name="all")
async def all_(
    code: Code = None,
    *,
    quiet: Quiet = False,
    max_items: MaxItems = None,
) -> None:
    """上場銘柄一覧、財務情報、株価情報、書類一覧を連続して取得します。"""
    typer.echo("上場銘柄一覧を取得します。")
    await info(code, quiet=quiet)

    typer.echo("---")
    typer.echo("財務情報を取得します。")
    await statements(code, quiet=quiet, max_items=max_items)

    typer.echo("---")
    typer.echo("株価情報を取得します。")
    await prices(code, quiet=quiet, max_items=max_items)

    if code is None:
        typer.echo("---")
        typer.echo("書類一覧を取得します。")
        await entries(quiet=quiet, max_items=max_items)
