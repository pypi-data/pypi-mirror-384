from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import polars as pl

from kabukit.utils.config import get_cache_dir

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any, Self

    from polars import DataFrame
    from polars._typing import IntoExprColumn


class Base:
    data: DataFrame

    def __init__(
        self,
        data: DataFrame | None = None,
        *,
        path: str | Path | None = None,
    ) -> None:
        if data is not None:
            self.data = data
            return

        data_dir = self.__class__.data_dir()
        filename = get_filename(path, data_dir)
        self.data = pl.read_parquet(filename)

    @classmethod
    def data_dir(cls) -> Path:
        clsname = cls.__name__.lower()
        return get_cache_dir() / clsname

    def write(self) -> Path:
        data_dir = self.__class__.data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        path = datetime.datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d")
        filename = data_dir / f"{path}.parquet"
        self.data.write_parquet(filename)
        return filename

    def filter(
        self,
        *predicates: IntoExprColumn | Iterable[IntoExprColumn] | bool | list[bool],
        **constraints: Any,
    ) -> Self:
        """Filter the data with given predicates and constraints."""
        data = self.data.filter(*predicates, **constraints)
        return self.__class__(data)


def get_filename(path: str | Path | None, data_dir: Path) -> Path:
    if path:
        if isinstance(path, str):
            path = Path(path)

        if path.exists():
            return path

        filename = data_dir / path

        if not filename.exists():
            msg = f"File not found: {filename}"
            raise FileNotFoundError(msg)

        return filename

    filenames = sorted(data_dir.glob("*.parquet"))

    if not filenames:
        msg = f"No data found in {data_dir}"
        raise FileNotFoundError(msg)

    return filenames[-1]
