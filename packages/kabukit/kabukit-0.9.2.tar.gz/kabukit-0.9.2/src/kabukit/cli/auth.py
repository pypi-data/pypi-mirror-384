from __future__ import annotations

from typing import Annotated

import typer
from async_typer import AsyncTyper  # pyright: ignore[reportMissingTypeStubs]
from httpx import HTTPStatusError
from typer import Exit, Option

app = AsyncTyper(
    add_completion=False,
    help="J-QuantsまたはEDINETの認証トークンを保存します。",
)


async def auth_jquants(mailaddress: str, password: str) -> None:
    """J-Quants APIの認証を行い、トークンを設定ファイルに保存します。"""
    from kabukit.jquants.client import JQuantsClient

    async with JQuantsClient() as client:
        try:
            id_token = await client.auth(mailaddress, password)
            client.save_id_token(id_token)
        except HTTPStatusError:
            typer.echo("認証に失敗しました。")
            raise Exit(1) from None

    typer.echo("J-QuantsのIDトークンを保存しました。")


Mailaddress = Annotated[
    str,
    Option(prompt=True, help="J-Quantsに登録したメールアドレス。"),
]
Password = Annotated[
    str,
    Option(prompt=True, hide_input=True, help="J-Quantsのパスワード。"),
]


@app.async_command()  # pyright: ignore[reportUnknownMemberType]
async def jquants(mailaddress: Mailaddress, password: Password) -> None:
    """J-Quants APIの認証を行い、トークンを設定ファイルに保存します。(エイリアス: j)"""
    await auth_jquants(mailaddress, password)


@app.async_command(name="j", hidden=True)  # pyright: ignore[reportUnknownMemberType]
async def jquants_alias(mailaddress: Mailaddress, password: Password) -> None:
    await auth_jquants(mailaddress, password)


def auth_edinet(api_key: str) -> None:
    """EDINET APIのAPIキーを設定ファイルに保存します。"""
    from kabukit.utils.config import set_key

    set_key("EDINET_API_KEY", api_key)
    typer.echo("EDINETのAPIキーを保存しました。")


ApiKey = Annotated[str, Option(prompt=True, help="取得したEDINET APIキー。")]


@app.command()
def edinet(api_key: ApiKey) -> None:
    """EDINET APIのAPIキーを設定ファイルに保存します。(エイリアス: e)"""
    auth_edinet(api_key)


@app.command(name="e", hidden=True)
def edinet_alias(api_key: ApiKey) -> None:
    auth_edinet(api_key)


@app.command()
def show() -> None:
    """設定ファイルに保存したトークン・APIキーを表示します。"""
    from dotenv import dotenv_values

    from kabukit.utils.config import get_dotenv_path

    path = get_dotenv_path()
    typer.echo(f"設定ファイル: {path}")

    if path.exists():
        config = dotenv_values(path)
        for key, value in config.items():
            typer.echo(f"{key}: {value}")
