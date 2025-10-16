from __future__ import annotations

from typing import TYPE_CHECKING

import altair as alt

if TYPE_CHECKING:
    from polars import DataFrame

# pyright: reportUnknownMemberType=false


def plot_topix_timeseries(df: DataFrame) -> alt.Chart:
    """TOPIXの時系列データを折れ線グラフでプロットする。"""
    return (
        alt.Chart(df, title="TOPIX 時系列チャート")
        .mark_line()
        .encode(
            x=alt.X("Date:T", title="日付"),
            y=alt.Y("Close:Q", title="終値", scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip("Date:T", title="日付"),
                alt.Tooltip("Open:Q", title="始値"),
                alt.Tooltip("High:Q", title="高値"),
                alt.Tooltip("Low:Q", title="安値"),
                alt.Tooltip("Close:Q", title="終値"),
            ],
        )
    )
