from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo


def get_dates(days: int | None = None, years: int | None = None) -> list[datetime.date]:
    """過去days日またはyears年の日付リストを返す。

    Args:
        days (int | None): 過去days日の日付リストを取得する。
        years (int | None): 過去years年の日付リストを取得する。
            daysが指定されている場合は無視される。
    """
    end_date = datetime.datetime.now(ZoneInfo("Asia/Tokyo")).date()

    if days is not None:
        start_date = end_date - datetime.timedelta(days=days)
    elif years is not None:
        start_date = end_date.replace(year=end_date.year - years)
    else:
        msg = "daysまたはyearsのいずれかを指定してください。"
        raise ValueError(msg)

    return [
        start_date + datetime.timedelta(days=i)
        for i in range(1, (end_date - start_date).days + 1)
    ]
