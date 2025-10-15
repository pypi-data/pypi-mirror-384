from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import AsyncClient

if TYPE_CHECKING:
    from typing import Self


class Client:
    client: AsyncClient

    def __init__(self, base_url: str = "") -> None:
        self.client = AsyncClient(base_url=base_url, timeout=20)

    async def aclose(self) -> None:
        """HTTPクライアントを閉じる。"""
        await self.client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # pyright: ignore[reportMissingParameterType, reportUnknownParameterType]  # noqa: ANN001
        await self.aclose()
