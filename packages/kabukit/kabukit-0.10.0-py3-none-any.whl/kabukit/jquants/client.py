from __future__ import annotations

import asyncio
import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, final
from zoneinfo import ZoneInfo

import polars as pl
from polars import DataFrame

from kabukit.core.client import Client
from kabukit.utils.config import get_config_value
from kabukit.utils.params import get_params

from . import calendar, info, prices, statements, topix

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from httpx import HTTPStatusError  # noqa: F401
    from httpx._types import QueryParamTypes


@final
class _CalendarCacheManager:
    def __init__(self) -> None:
        self._holidays: list[datetime.date] | None = None
        self._lock = asyncio.Lock()

    async def get_holidays(self, client: JQuantsClient) -> list[datetime.date]:
        async with self._lock:
            if self._holidays is None:
                df = await client.get_calendar()
                holidays = df.filter(pl.col("IsHoliday"))["Date"]
                self._holidays = holidays.to_list()
            return self._holidays


_calendar_cache_manager = _CalendarCacheManager()


API_VERSION = "v1"
BASE_URL = f"https://api.jquants.com/{API_VERSION}"


class AuthKey(StrEnum):
    """J-Quants認証のための環境変数キー。"""

    MAILADDRESS = "JQUANTS_MAILADDRESS"
    PASSWORD = "JQUANTS_PASSWORD"  # noqa: S105
    ID_TOKEN = "JQUANTS_ID_TOKEN"  # noqa: S105


class JQuantsClient(Client):
    """J-Quants APIと非同期に対話するためのクライアント。

    `httpx.AsyncClient` をラップし、認証トークンの管理、ページネーションの
    自動処理、APIレスポンスの `polars.DataFrame` への変換などを行う。

    Attributes:
        client (httpx.AsyncClient): APIリクエストを行うための非同期HTTPクライアント。
    """

    def __init__(self, id_token: str | None = None) -> None:
        super().__init__(BASE_URL)
        self.set_id_token(id_token)

    def set_id_token(self, id_token: str | None = None) -> None:
        """HTTPヘッダーにIDトークンを設定する。

        Args:
            id_token: 設定するIDトークン。Noneの場合、設定ファイルまたは
                環境変数から読み込む。
        """
        if id_token is None:
            id_token = get_config_value(AuthKey.ID_TOKEN)

        if id_token:
            self.client.headers["Authorization"] = f"Bearer {id_token}"

    async def post(self, url: str, json: Any | None = None) -> Any:
        """指定されたURLにPOSTリクエストを送信する。

        Args:
            url: POSTリクエストのURLパス。
            json: リクエストボディのJSONペイロード。

        Returns:
            APIからのJSONレスポンス。

        Raises:
            HTTPStatusError: APIリクエストがHTTPエラーステータスを返した場合。
        """
        resp = await self.client.post(url, json=json)
        resp.raise_for_status()
        return resp.json()

    async def get(self, url: str, params: QueryParamTypes | None = None) -> Any:
        """指定されたURLにGETリクエストを送信する。

        Args:
            url: GETリクエストのURLパス。
            params: リクエストのクエリパラメータ。

        Returns:
            APIからのJSONレスポンス。

        Raises:
            HTTPStatusError: APIリクエストがHTTPエラーステータスを返した場合。
        """
        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def auth(
        self,
        mailaddress: str | None = None,
        password: str | None = None,
    ) -> str:
        """メールアドレスとパスワードで認証し、IDトークンを返す。

        Args:
            mailaddress (str | None): J-Quantsに登録したメールアドレス。
                Noneの場合、設定ファイルまたは環境変数から読み込む。
            password (str | None): J-Quantsのパスワード。
                Noneの場合、設定ファイルまたは環境変数から読み込む。

        Returns:
            str: 認証によって取得されたIDトークン。

        Raises:
            ValueError: メールアドレスまたはパスワードが指定されていない場合。
            HTTPStatusError: 認証APIリクエストが失敗した場合。
        """
        mailaddress = mailaddress or get_config_value(AuthKey.MAILADDRESS)
        password = password or get_config_value(AuthKey.PASSWORD)

        if not mailaddress or not password:
            msg = "メールアドレスとパスワードを指定するか、"
            msg += "環境変数に設定する必要がある。"
            raise ValueError(msg)

        json_data = {"mailaddress": mailaddress, "password": password}
        data = await self.post("/token/auth_user", json=json_data)
        refresh_token = data["refreshToken"]

        url = f"/token/auth_refresh?refreshtoken={refresh_token}"
        data = await self.post(url)
        id_token = data["idToken"]
        self.set_id_token(id_token)
        return id_token

    async def iter_pages(
        self,
        url: str,
        params: dict[str, Any] | None,
        name: str,
    ) -> AsyncIterator[DataFrame]:
        """ページ分割されたAPIレスポンスを非同期に反復処理する。

        J-Quants APIのページネーション仕様（`pagination_key`）に対応し、
        複数ページにまたがるデータを自動的に取得する。

        Args:
            url: APIエンドポイントのURLパス。
            params: クエリパラメータの辞書。
            name: アイテムのリストを含むJSONレスポンスのキー。

        Yields:
            pl.DataFrame: データの各ページに対応するDataFrame。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        params = params or {}

        while True:
            data = await self.get(url, params)
            yield DataFrame(data[name])
            if "pagination_key" in data:
                params["pagination_key"] = data["pagination_key"]
            else:
                break

    async def get_info(
        self,
        code: str | None = None,
        date: str | datetime.date | None = None,
        *,
        clean: bool = True,
    ) -> DataFrame:
        """上場銘柄一覧を取得する (listed/info)。

        Args:
            code: 情報を取得する銘柄コード (例: "86970")。
            date: 情報を取得する日付 (例: "2025-10-01")。
            clean: 取得したデータを整形するかどうか。

        Returns:
            pl.DataFrame: 銘柄情報を含むDataFrame。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        params = get_params(code=code, date=date)
        url = "/listed/info"
        data = await self.get(url, params)
        df = DataFrame(data["info"])
        return info.clean(df) if clean else df

    async def get_statements(
        self,
        code: str | None = None,
        date: str | datetime.date | None = None,
        *,
        clean: bool = True,
        with_date: bool = True,
    ) -> DataFrame:
        """財務情報を取得する (fins/statements)。

        Args:
            code: 財務情報を取得する銘柄コード。
            date: 財務情報を取得する日付。
            clean: 取得したデータを整形するかどうか。
            with_date: 整形後に営業日ベースの開示翌日(`Date`列)を追加するかどうか。

        Returns:
            pl.DataFrame: 財務情報を含むDataFrame。

        Raises:
            ValueError: `code`と`date`が両方とも指定されない場合。
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        if not code and not date:
            msg = "codeまたはdateのどちらかを指定する必要がある。"
            raise ValueError(msg)

        params = get_params(code=code, date=date)
        url = "/fins/statements"
        name = "statements"

        dfs = [df async for df in self.iter_pages(url, params, name)]
        df = pl.concat(dfs)

        if df.is_empty() or not clean:
            return df

        df = statements.clean(df)

        if not with_date:
            return df

        holidays = await _calendar_cache_manager.get_holidays(self)
        return statements.with_date(df, holidays=holidays)

    async def get_prices(
        self,
        code: str | None = None,
        date: str | datetime.date | None = None,
        from_: str | datetime.date | None = None,
        to: str | datetime.date | None = None,
        *,
        clean: bool = True,
    ) -> DataFrame:
        """日々の株価四本値を取得する (prices/daily_quotes)。

        Args:
            code: 株価を取得する銘柄コード。
            date: 株価を取得する日付。`from_`または`to`とは併用不可。
            from_: 取得期間の開始日。`date`とは併用不可。
            to: 取得期間の終了日。`date`とは併用不可。
            clean: 取得したデータを整形するかどうか。

        Returns:
            pl.DataFrame: 日々の株価四本値を含むDataFrame。

        Raises:
            ValueError: `date`と`from_`/`to`が同時に指定された場合。
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        if not date and not code:
            return await self.get_latest_available_prices(clean=clean)

        if date and (from_ or to):
            msg = "dateとfrom/toを同時に指定することはできない。"
            raise ValueError(msg)

        params = get_params(code=code, date=date, from_=from_, to=to)

        url = "/prices/daily_quotes"
        name = "daily_quotes"

        dfs = [df async for df in self.iter_pages(url, params, name)]
        df = pl.concat(dfs)

        if df.is_empty():
            return df

        return prices.clean(df) if clean else df

    async def get_latest_available_prices(
        self,
        num_days: int = 30,
        *,
        clean: bool = True,
    ) -> DataFrame:
        """直近利用可能な日付の株価を取得する。

        `get_prices` のためのフォールバック処理。今日から過去`num_days`の範囲で
        データが存在する最初の日の全銘柄データを返す。

        Args:
            num_days: 遡って検索する最大日数。
            clean: 取得したデータを整形するかどうか。

        Returns:
            pl.DataFrame: データが見つかった場合はその日の株価DataFrame、
            見つからない場合は空のDataFrame。
        """
        today = datetime.datetime.now(ZoneInfo("Asia/Tokyo")).date()

        for days in range(num_days):
            date = today - datetime.timedelta(days)
            df = await self.get_prices(date=date, clean=clean)

            if not df.is_empty():
                return df

        return DataFrame()

    async def get_announcement(self) -> DataFrame:
        """翌日発表予定の決算情報を取得する (fins/announcement)。

        Returns:
            pl.DataFrame: 翌日発表予定の決算開示情報を含むDataFrame。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        url = "fins/announcement"
        name = "announcement"

        dfs = [df async for df in self.iter_pages(url, {}, name)]
        df = pl.concat(dfs)
        if df.is_empty():
            return df

        return df.with_columns(pl.col("Date").str.to_date("%Y-%m-%d"))

    async def get_trades_spec(
        self,
        section: str | None = None,
        from_: str | datetime.date | None = None,
        to: str | datetime.date | None = None,
    ) -> DataFrame:
        """投資部門別売買状況を取得する (markets/trades_spec)。

        Args:
            section: 絞り込み対象のセクション (例: "TSE")。
            from_: 取得期間の開始日。
            to: 取得期間の終了日。

        Returns:
            pl.DataFrame: 投資部門別売買状況を含むDataFrame。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        params = get_params(section=section, from_=from_, to=to)

        url = "/markets/trades_spec"
        name = "trades_spec"

        dfs = [df async for df in self.iter_pages(url, params, name)]
        df = pl.concat(dfs)
        if df.is_empty():
            return df

        return df.with_columns(pl.col("^.*Date$").str.to_date("%Y-%m-%d"))

    async def get_topix(
        self,
        from_: str | datetime.date | None = None,
        to: str | datetime.date | None = None,
    ) -> DataFrame:
        """TOPIXの時系列データを取得する (indices/topix)。

        Args:
            from_: 取得期間の開始日。
            to: 取得期間の終了日。

        Returns:
            pl.DataFrame: 日次のTOPIX指数データを含むDataFrame。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        params = get_params(from_=from_, to=to)

        url = "/indices/topix"
        name = "topix"

        dfs = [df async for df in self.iter_pages(url, params, name)]
        df = pl.concat(dfs)
        if df.is_empty():
            return df

        return topix.clean(df)

    async def get_calendar(
        self,
        holidaydivision: str | None = None,
        from_: str | datetime.date | None = None,
        to: str | datetime.date | None = None,
    ) -> DataFrame:
        """市場の営業日カレンダーを取得する (markets/trading_calendar)。

        Args:
            holidaydivision: 祝日区分 ("0":非営業日, "1":営業日など)。
            from_: 取得期間の開始日。
            to: 取得期間の終了日。

        Returns:
            pl.DataFrame: 市場の営業日・休業日データを含むDataFrame。

        Raises:
            HTTPStatusError: APIリクエストが失敗した場合。
        """
        params = get_params(holidaydivision=holidaydivision, from_=from_, to=to)

        url = "/markets/trading_calendar"
        name = "trading_calendar"

        dfs = [df async for df in self.iter_pages(url, params, name)]
        df = pl.concat(dfs)
        if df.is_empty():
            return df

        return calendar.clean(df)
