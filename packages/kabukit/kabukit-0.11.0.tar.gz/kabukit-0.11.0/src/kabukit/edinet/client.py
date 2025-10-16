from __future__ import annotations

import io
import zipfile
from enum import StrEnum
from typing import TYPE_CHECKING

import httpx
from polars import DataFrame
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from kabukit.core.client import Client
from kabukit.utils.config import get_config_value
from kabukit.utils.params import get_params

from .doc import clean_csv, clean_entries, clean_pdf, read_csv

if TYPE_CHECKING:
    import datetime

    from httpx import Response
    from httpx._types import QueryParamTypes

API_VERSION = "v2"
BASE_URL = f"https://api.edinet-fsa.go.jp/api/{API_VERSION}"


def is_retryable(e: BaseException) -> bool:
    """例外がリトライ可能なネットワークエラーであるかを判定する。"""
    return isinstance(e, (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError))


class AuthKey(StrEnum):
    """EDINET認証のための環境変数キー。"""

    API_KEY = "EDINET_API_KEY"


class EdinetClient(Client):
    """EDINET API v2と非同期に対話するためのクライアント。

    `httpx.AsyncClient` をラップし、APIキー認証、指数関数的バックオフを
    用いたリトライ処理、APIレスポンスの `polars.DataFrame` への変換などを行う。

    Attributes:
        client (httpx.AsyncClient): APIリクエストを行うための非同期HTTPクライアント。
    """

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(BASE_URL)
        self.set_api_key(api_key)

    def set_api_key(self, api_key: str | None = None) -> None:
        """HTTPクエリパラメータにAPIキーを設定する。

        Args:
            api_key: 設定するAPIキー。Noneの場合、設定ファイルまたは
                環境変数から読み込む。
        """
        if api_key is None:
            api_key = get_config_value(AuthKey.API_KEY)

        if api_key:
            self.client.params = {"Subscription-Key": api_key}

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(is_retryable),
    )
    async def get(self, url: str, params: QueryParamTypes) -> Response:
        """リトライ処理を伴うGETリクエストを送信する。

        ネットワークエラーが発生した場合、指数関数的バックオフを用いて
        最大3回までリトライする。

        Args:
            url: GETリクエストのURLパス。
            params: リクエストのクエリパラメータ。

        Returns:
            httpx.Response: APIからのレスポンスオブジェクト。

        Raises:
            httpx.HTTPStatusError: APIリクエストがHTTPエラーステータスを返した場合。
        """
        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        return resp

    async def get_count(self, date: str | datetime.date) -> int:
        """指定日の提出書類数を取得する (documents.json, type=1)。

        Args:
            date: 取得対象の日付 (YYYY-MM-DD)。

        Returns:
            int: 指定日の提出書類数。
        """
        params = get_params(date=date, type=1)
        resp = await self.get("/documents.json", params)
        data = resp.json()
        metadata = data["metadata"]

        if metadata["status"] != "200":
            return 0

        return metadata["resultset"]["count"]

    async def get_entries(self, date: str | datetime.date) -> DataFrame:
        """指定日の提出書類一覧を取得する (documents.json, type=2)。

        Args:
            date: 取得対象の日付 (YYYY-MM-DD)。

        Returns:
            pl.DataFrame: 提出書類一覧を格納したDataFrame。
        """
        params = get_params(date=date, type=2)
        resp = await self.get("/documents.json", params)
        data = resp.json()

        if "results" not in data:
            return DataFrame()

        df = DataFrame(data["results"], infer_schema_length=None)

        if df.is_empty():
            return df

        return clean_entries(df, date)

    async def get_response(self, doc_id: str, doc_type: int) -> Response:
        """書類データをレスポンスオブジェクトとして取得する (documents/{docID})。

        Args:
            doc_id: EDINETの書類ID。
            doc_type: 書類タイプ (1:本文, 2:PDF, 3:代替書面, 4:英文, 5:CSV)。

        Returns:
            httpx.Response: APIからのレスポンスオブジェクト。
        """
        params = get_params(type=doc_type)
        return await self.get(f"/documents/{doc_id}", params)

    async def get_pdf(self, doc_id: str) -> DataFrame:
        """PDF形式の書類を取得し、テキストを抽出する。

        Args:
            doc_id: EDINETの書類ID。

        Returns:
            pl.DataFrame: 抽出したテキストデータを含むDataFrame。

        Raises:
            ValueError: レスポンスがPDF形式でない場合。
        """
        resp = await self.get_response(doc_id, doc_type=2)
        if resp.headers["content-type"] == "application/pdf":
            return clean_pdf(resp.content, doc_id)

        msg = "PDF is not available."
        raise ValueError(msg)

    async def get_zip(self, doc_id: str, doc_type: int) -> bytes:
        """ZIP形式の書類を取得する。

        Args:
            doc_id: EDINETの書類ID。
            doc_type: 書類タイプ (通常は5:CSV)。

        Returns:
            bytes: ZIPファイルのバイナリデータ。

        Raises:
            ValueError: レスポンスがZIP形式でない場合。
        """
        resp = await self.get_response(doc_id, doc_type=doc_type)
        if resp.headers["content-type"] == "application/octet-stream":
            return resp.content

        msg = "ZIP is not available."
        raise ValueError(msg)

    async def get_csv(self, doc_id: str) -> DataFrame:
        """CSV形式の書類(XBRL)を取得し、DataFrameに変換する。

        書類取得API (`type=5`) で取得したZIPファイルの中からCSVファイルを
        探し出し、DataFrameとして読み込む。

        Args:
            doc_id: EDINETの書類ID。

        Returns:
            pl.DataFrame: CSVデータを含むDataFrame。

        Raises:
            ValueError: ZIPファイル内にCSVが見つからない場合。
        """
        content = await self.get_zip(doc_id, doc_type=5)
        buffer = io.BytesIO(content)

        with zipfile.ZipFile(buffer) as zf:
            for info in zf.infolist():
                if info.filename.endswith(".csv"):
                    with zf.open(info) as f:
                        df = read_csv(f.read())
                        return clean_csv(df, doc_id)

        msg = "CSV is not available."
        raise ValueError(msg)

    async def get_document(self, doc_id: str, *, pdf: bool = False) -> DataFrame:
        """指定したIDの書類を取得する。

        Args:
            doc_id: EDINETの書類ID。
            pdf: Trueの場合PDF形式、Falseの場合CSV形式の書類を取得する。

        Returns:
            pl.DataFrame: 書類データを含むDataFrame。
        """
        if pdf:
            return await self.get_pdf(doc_id)

        return await self.get_csv(doc_id)
