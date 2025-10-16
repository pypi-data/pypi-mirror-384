from __future__ import annotations

import os
from typing import Annotated

import typer
from async_typer import AsyncTyper  # pyright: ignore[reportMissingTypeStubs]
from httpx import HTTPStatusError
from typer import Exit, Option

from kabukit.edinet.client import AuthKey as EdinetAuthKey
from kabukit.jquants.client import AuthKey as JQuantsAuthKey
from kabukit.utils.config import get_config_path, get_config_value, save_config_key

# pyright: reportUnknownMemberType=false

app = AsyncTyper(
    add_completion=False,
    help="J-QuantsまたはEDINETの認証トークンを保存します。",
)


Mailaddress = Annotated[
    str | None,
    Option(
        "--mailaddress",
        help="J-Quantsに登録したメールアドレス。",
    ),
]
Password = Annotated[
    str | None,
    Option(
        "--password",
        hide_input=True,
        help="J-Quantsのパスワード。",
    ),
]


@app.async_command()
async def jquants(mailaddress: Mailaddress = None, password: Password = None) -> None:
    """J-Quants APIの認証を行い、トークンを設定ファイルに保存します。(エイリアス: j)"""
    await auth_jquants(mailaddress, password)


@app.async_command(name="j", hidden=True)
async def jquants_alias(
    mailaddress: Mailaddress = None,
    password: Password = None,
) -> None:
    await auth_jquants(mailaddress, password)


async def auth_jquants(mailaddress: str | None, password: str | None) -> None:
    """J-Quants APIの認証を行い、トークンを設定ファイルに保存します。"""
    from kabukit.jquants.client import JQuantsClient

    mailaddress = mailaddress or get_config_value(JQuantsAuthKey.MAILADDRESS)

    if mailaddress is None:
        mailaddress = typer.prompt("J-Quantsに登録したメールアドレス")
        if not mailaddress or mailaddress.strip() == "":
            typer.echo("メールアドレスが入力されていません。")
            raise Exit(1)

    password = password or get_config_value(JQuantsAuthKey.PASSWORD)

    if password is None:
        password = typer.prompt("J-Quantsのパスワード", hide_input=True)
        if not password or password.strip() == "":
            typer.echo("パスワードが入力されていません。")
            raise Exit(1)

    async with JQuantsClient() as client:
        try:
            id_token = await client.auth(mailaddress, password)
        except HTTPStatusError:
            typer.echo("認証に失敗しました。")
            raise Exit(1) from None

    save_config_key(JQuantsAuthKey.ID_TOKEN, id_token)
    typer.echo("J-QuantsのIDトークンを保存しました。")


ApiKey = Annotated[
    str,
    Option(
        default_factory=lambda: os.environ.get(EdinetAuthKey.API_KEY)
        or typer.prompt("取得したEDINET APIキー"),
        help="取得したEDINET APIキー。",
    ),
]


@app.command()
def edinet(api_key: ApiKey) -> None:
    """EDINET APIのAPIキーを設定ファイルに保存します。(エイリアス: e)"""
    auth_edinet(api_key)


@app.command(name="e", hidden=True)
def edinet_alias(api_key: ApiKey) -> None:
    auth_edinet(api_key)


def auth_edinet(api_key: str) -> None:
    """EDINET APIのAPIキーを設定ファイルに保存します。"""
    if not api_key or api_key.strip() == "":
        typer.echo("APIキーが入力されていません。")
        raise Exit(1)

    save_config_key(EdinetAuthKey.API_KEY, api_key)
    typer.echo("EDINETのAPIキーを保存しました。")


@app.command()
def show() -> None:
    """設定ファイルに保存したトークン・APIキーを表示します。"""
    path = get_config_path()
    typer.echo(f"設定ファイル: {path}")

    if path.exists():
        typer.echo("----")
        text = path.read_text(encoding="utf-8")
        typer.echo(text.rstrip())
        typer.echo("----")
