"""kabukit CLI."""

from __future__ import annotations

import typer
from async_typer import AsyncTyper  # pyright: ignore[reportMissingTypeStubs]

from . import auth, cache, get

app = AsyncTyper(
    add_completion=False,
    help="J-Quants/EDINETデータツール",
)
app.add_typer(auth.app, name="auth")
app.add_typer(get.app, name="get")
app.add_typer(cache.app, name="cache")


@app.command()
def version() -> None:  # pragma: no cover
    """バージョン情報を表示します。"""
    from importlib.metadata import version

    typer.echo(f"kabukit version: {version('kabukit')}")
