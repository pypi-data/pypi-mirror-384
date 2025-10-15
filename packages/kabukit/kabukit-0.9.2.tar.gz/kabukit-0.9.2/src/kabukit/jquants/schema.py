from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from polars import DataFrame


class BaseColumns(Enum):
    @classmethod
    def rename(cls, df: DataFrame, *, strict: bool = False) -> DataFrame:
        """DataFrameの列名を日本語から英語に変換する。"""
        return df.rename({x.name: x.value for x in cls}, strict=strict)


class InfoColumns(BaseColumns):
    Date = "日付"
    Code = "銘柄コード"
    CompanyName = "会社名"
    Sector17CodeName = "17業種コード名"
    Sector33CodeName = "33業種コード名"
    ScaleCategory = "規模コード"
    MarketCodeName = "市場区分名"
    MarginCodeName = "貸借信用区分名"


class PriceColumns(BaseColumns):
    Date = "日付"
    Code = "銘柄コード"
    Open = "始値"
    High = "高値"
    Low = "安値"
    Close = "終値"
    UpperLimit = "ストップ高?"
    LowerLimit = "ストップ安?"
    Volume = "出来高"
    TurnoverValue = "売買代金"
    AdjustmentFactor = "調整係数"
    RawOpen = "調整前始値"
    RawHigh = "調整前高値"
    RawLow = "調整前安値"
    RawClose = "調整前終値"
    RawVolume = "調整前出来高"


class StatementColumns(BaseColumns):
    Date = "日付"
    DisclosedDate = "開示日"
    DisclosedTime = "開示時刻"
    Code = "銘柄コード"
    DisclosureNumber = "開示番号"
    TypeOfDocument = "開示書類種別"
    TypeOfCurrentPeriod = "当会計期間の種類"
    CurrentPeriodStartDate = "当会計期間開始日"
    CurrentPeriodEndDate = "当会計期間終了日"
    CurrentFiscalYearStartDate = "当事業年度開始日"
    CurrentFiscalYearEndDate = "当事業年度終了日"
    NextFiscalYearStartDate = "翌事業年度開始日"
    NextFiscalYearEndDate = "翌事業年度終了日"

    NetSales = "売上高"
    OperatingProfit = "営業利益"
    OrdinaryProfit = "経常利益"
    Profit = "当期純利益"
    EarningsPerShare = "一株あたり当期純利益"
    DilutedEarningsPerShare = "潜在株式調整後一株あたり当期純利益"

    TotalAssets = "総資産"
    Equity = "純資産"
    EquityToAssetRatio = "自己資本比率"
    BookValuePerShare = "一株あたり純資産"

    CashFlowsFromOperatingActivities = "営業活動によるキャッシュフロー"
    CashFlowsFromInvestingActivities = "投資活動によるキャッシュフロー"
    CashFlowsFromFinancingActivities = "財務活動によるキャッシュフロー"
    CashAndEquivalents = "現金及び現金同等物期末残高"

    ResultDividendPerShare1stQuarter = "一株あたり配当実績_第1四半期末"
    ResultDividendPerShare2ndQuarter = "一株あたり配当実績_第2四半期末"
    ResultDividendPerShare3rdQuarter = "一株あたり配当実績_第3四半期末"
    ResultDividendPerShareFiscalYearEnd = "一株あたり配当実績_期末"
    ResultDividendPerShareAnnual = "一株あたり配当実績_合計"
    ResultTotalDividendPaidAnnual = "配当金総額"
    ResultPayoutRatioAnnual = "配当性向"

    ForecastDividendPerShare1stQuarter = "一株あたり配当予想_第1四半期末"
    ForecastDividendPerShare2ndQuarter = "一株あたり配当予想_第2四半期末"
    ForecastDividendPerShare3rdQuarter = "一株あたり配当予想_第3四半期末"
    ForecastDividendPerShareFiscalYearEnd = "一株あたり配当予想_期末"
    ForecastDividendPerShareAnnual = "一株あたり配当予想_合計"
    ForecastTotalDividendPaidAnnual = "予想配当金総額"
    ForecastPayoutRatioAnnual = "予想配当性向"

    NextYearForecastDividendPerShare1stQuarter = "一株あたり配当予想_翌事業年度第1四半期末"
    NextYearForecastDividendPerShare2ndQuarter = "一株あたり配当予想_翌事業年度第2四半期末"
    NextYearForecastDividendPerShare3rdQuarter = "一株あたり配当予想_翌事業年度第3四半期末"
    NextYearForecastDividendPerShareFiscalYearEnd = "一株あたり配当予想_翌事業年度期末"
    NextYearForecastDividendPerShareAnnual = "一株あたり配当予想_翌事業年度合計"
    NextYearForecastPayoutRatioAnnual = "翌事業年度予想配当性向"

    ForecastNetSales2ndQuarter = "売上高_予想_第2四半期末"
    ForecastOperatingProfit2ndQuarter = "営業利益_予想_第2四半期末"
    ForecastOrdinaryProfit2ndQuarter = "経常利益_予想_第2四半期末"
    ForecastProfit2ndQuarter = "当期純利益_予想_第2四半期末"
    ForecastEarningsPerShare2ndQuarter = "一株あたり当期純利益_予想_第2四半期末"

    NextYearForecastNetSales2ndQuarter = "売上高_予想_翌事業年度第2四半期末"
    NextYearForecastOperatingProfit2ndQuarter = "営業利益_予想_翌事業年度第2四半期末"
    NextYearForecastOrdinaryProfit2ndQuarter = "経常利益_予想_翌事業年度第2四半期末"
    NextYearForecastProfit2ndQuarter = "当期純利益_予想_翌事業年度第2四半期末"
    NextYearForecastEarningsPerShare2ndQuarter = "一株あたり当期純利益_予想_翌事業年度第2四半期末"

    ForecastNetSales = "売上高_予想_期末"
    ForecastOperatingProfit = "営業利益_予想_期末"
    ForecastOrdinaryProfit = "経常利益_予想_期末"
    ForecastProfit = "当期純利益_予想_期末"
    ForecastEarningsPerShare = "一株あたり当期純利益_予想_期末"

    NextYearForecastNetSales = "売上高_予想_翌事業年度期末"
    NextYearForecastOperatingProfit = "営業利益_予想_翌事業年度期末"
    NextYearForecastOrdinaryProfit = "経常利益_予想_翌事業年度期末"
    NextYearForecastProfit = "当期純利益_予想_翌事業年度期末"
    NextYearForecastEarningsPerShare = "一株あたり当期純利益_予想_翌事業年度期末"

    MaterialChangesInSubsidiaries = "期中における重要な子会社の異動"
    SignificantChangesInTheScopeOfConsolidation = "期中における連結範囲の重要な変更"
    ChangesBasedOnRevisionsOfAccountingStandard = "会計基準等の改正に伴う会計方針の変更"
    ChangesOtherThanOnesBasedOnRevisionsOfAccountingStandard = "会計基準等の改正に伴う変更以外の会計方針の変更"
    ChangesInAccountingEstimates = "会計上の見積りの変更"
    RetrospectiveRestatement = "修正再表示"

    IssuedShares = "期末発行済株式数" # 自己株式を含む (NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock)
    TreasuryShares = "期末自己株式数" # (NumberOfTreasuryStockAtTheEndOfFiscalYear)
    AverageOutstandingShares = "期中平均株式数" # 自己株式を除く。EPSなどの計算に使用される (AverageNumberOfShares)

    NonConsolidatedNetSales = "売上高_非連結"
    NonConsolidatedOperatingProfit = "営業利益_非連結"
    NonConsolidatedOrdinaryProfit = "経常利益_非連結"
    NonConsolidatedProfit = "当期純利益_非連結"
    NonConsolidatedEarningsPerShare = "一株あたり当期純利益_非連結"

    NonConsolidatedTotalAssets = "総資産_非連結"
    NonConsolidatedEquity = "純資産_非連結"
    NonConsolidatedEquityToAssetRatio = "自己資本比率_非連結"
    NonConsolidatedBookValuePerShare = "一株あたり純資産_非連結"

    ForecastNonConsolidatedNetSales2ndQuarter = "売上高_予想_第2四半期末_非連結"
    ForecastNonConsolidatedOperatingProfit2ndQuarter = "営業利益_予想_第2四半期末_非連結"
    ForecastNonConsolidatedOrdinaryProfit2ndQuarter = "経常利益_予想_第2四半期末_非連結"
    ForecastNonConsolidatedProfit2ndQuarter = "当期純利益_予想_第2四半期末_非連結"
    ForecastNonConsolidatedEarningsPerShare2ndQuarter = "一株あたり当期純利益_予想_第2四半期末_非連結"

    NextYearForecastNonConsolidatedNetSales2ndQuarter = "売上高_予想_翌事業年度第2四半期末_非連結"
    NextYearForecastNonConsolidatedOperatingProfit2ndQuarter = "営業利益_予想_翌事業年度第2四半期末_非連結"
    NextYearForecastNonConsolidatedOrdinaryProfit2ndQuarter = "経常利益_予想_翌事業年度第2四半期末_非連結"
    NextYearForecastNonConsolidatedProfit2ndQuarter = "当期純利益_予想_翌事業年度第2四半期末_非連結"
    NextYearForecastNonConsolidatedEarningsPerShare2ndQuarter = "一株あたり当期純利益_予想_翌事業年度第2四半期末_非連結"

    ForecastNonConsolidatedNetSales = "売上高_予想_期末_非連結"
    ForecastNonConsolidatedOperatingProfit = "営業利益_予想_期末_非連結"
    ForecastNonConsolidatedOrdinaryProfit = "経常利益_予想_期末_非連結"
    ForecastNonConsolidatedProfit = "当期純利益_予想_期末_非連結"
    ForecastNonConsolidatedEarningsPerShare = "一株あたり当期純利益_予想_期末_非連結"

    NextYearForecastNonConsolidatedNetSales = "売上高_予想_翌事業年度期末_非連結"
    NextYearForecastNonConsolidatedOperatingProfit = "営業利益_予想_翌事業年度期末_非連結"
    NextYearForecastNonConsolidatedOrdinaryProfit = "経常利益_予想_翌事業年度期末_非連結"
    NextYearForecastNonConsolidatedProfit = "当期純利益_予想_翌事業年度期末_非連結"
    NextYearForecastNonConsolidatedEarningsPerShare = "一株あたり当期純利益_予想_翌事業年度期末_非連結"


def rename(df: DataFrame, *, strict: bool = False) -> DataFrame:
    """DataFrameの列名を日本語から英語に変換する。"""
    for enum in (InfoColumns, PriceColumns, StatementColumns):
        df = enum.rename(df, strict=strict)
    return df
