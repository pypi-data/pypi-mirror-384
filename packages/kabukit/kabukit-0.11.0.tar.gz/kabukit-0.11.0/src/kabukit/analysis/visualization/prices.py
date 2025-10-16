"""チャート作成のためのモジュール"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import altair as alt

if TYPE_CHECKING:
    from kabukit.core.prices import Prices


def plot_prices(
    prices: Prices,
    kind: Literal["candlestick"] = "candlestick",
) -> alt.VConcatChart:
    if kind == "candlestick":
        chart_price = plot_prices_candlestick(prices)
        chart_price_volume = plot_prices_volume(prices)
        return alt.vconcat(chart_price, chart_price_volume)

    raise NotImplementedError  # pyright: ignore[reportUnreachable]


def plot_prices_candlestick(prices: Prices) -> alt.LayerChart:
    rule = alt.Chart(prices.data, mark="rule").encode(y="Low:Q", y2="High:Q")
    bar = alt.Chart(prices.data, mark="bar").encode(y="Open:Q", y2="Close:Q")

    color_condition = alt.condition(
        "datum.Open < datum.Close",
        alt.value("#ff3030"),
        alt.value("#3030ff"),
    )

    return alt.layer(rule, bar, height=200).encode(
        x=alt.X("Date:T", axis=alt.Axis(title="日付", format="%Y-%m-%d")),
        y=alt.Y(title="株価", scale=alt.Scale(zero=False)),
        color=color_condition,
        tooltip=[
            alt.Tooltip("Date:T", title="日付"),
            alt.Tooltip("Open:Q", title="始値"),
            alt.Tooltip("High:Q", title="高値"),
            alt.Tooltip("Low:Q", title="安値"),
            alt.Tooltip("Close:Q", title="終値"),
        ],
    )


def plot_prices_volume(prices: Prices) -> alt.Chart:
    return alt.Chart(prices.data, mark="bar", height=50).encode(
        x=alt.X("Date:T", axis=alt.Axis(title="日付", format="%Y-%m-%d")),
        y=alt.Y("Volume:Q", title="出来高"),
        tooltip=[
            alt.Tooltip("Date:T", title="日付"),
            alt.Tooltip("Volume:Q", title="出来高"),
        ],
    )
