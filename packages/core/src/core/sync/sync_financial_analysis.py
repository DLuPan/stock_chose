import akshare as ak
import pandas as pd
import numpy as np
import datetime
import traceback
from typing import List, Dict
from core.models import StockFinancialAnalysisDB, StockSpotDB
from core.database import get_db_session
from core.logger import log
from .sync_business_composition import format_a_stock_symbol


def sync_stock_financial_analysis(symbol: str, start_year: str = None) -> List[Dict]:
    """
    同步单个股票的新浪财经财务指标数据

    Args:
        symbol: 股票代码，如 "SH688041" 或 "688041"
        start_year: 开始查询的年份，如 "2020"，默认为当前年份-10年

    Returns:
        List of financial analysis records
    """
    # 格式化股票代码
    formatted_symbol = format_a_stock_symbol(symbol)
    if formatted_symbol != symbol:
        log.info(f"股票代码已从 {symbol} 格式化为 {formatted_symbol}")

    # 如果没有指定开始年份，默认为当前年份-10年
    if start_year is None:
        start_year = str(datetime.datetime.now().year - 10)

    try:
        # 获取新浪财经财务指标数据
        financial_analysis_df = ak.stock_financial_analysis_indicator(
            symbol=formatted_symbol.split("SH")[-1].split("SZ")[-1].split("BJ")[-1], 
            start_year=start_year
        )
        log.info(f"[{formatted_symbol}] 获取到 {len(financial_analysis_df)} 条财务指标数据")

        if financial_analysis_df.empty:
            log.info(f"[{formatted_symbol}] 未获取到财务指标数据")
            return []

        # 重命名列以匹配数据库模型
        financial_analysis_df.rename(
            columns={
                "日期": "date",
                "摊薄每股收益(元)": "diluted_earnings_per_share",
                "加权每股收益(元)": "weighted_earnings_per_share",
                "每股收益_调整后(元)": "adjusted_earnings_per_share",
                "扣除非经常性损益后的每股收益(元)": "non_recurring_earnings_per_share",
                "每股净资产_调整前(元)": "net_assets_per_share_before",
                "每股净资产_调整后(元)": "net_assets_per_share_after",
                "每股经营性现金流(元)": "operating_cash_flow_per_share",
                "每股资本公积金(元)": "capital_reserve_per_share",
                "每股未分配利润(元)": "undistributed_profit_per_share",
                "调整后的每股净资产(元)": "adjusted_net_assets_per_share",
                "总资产利润率(%)": "total_asset_profitability",
                "主营业务利润率(%)": "main_business_profitability",
                "总资产净利润率(%)": "total_asset_net_profit",
                "成本费用利润率(%)": "cost_expense_profitability",
                "营业利润率(%)": "operating_profitability",
                "主营业务成本率(%)": "main_business_cost_ratio",
                "销售净利率(%)": "sale_net_profit_ratio",
                "股本报酬率(%)": "capital_reward_ratio",
                "净资产报酬率(%)": "net_asset_reward_ratio",
                "资产报酬率(%)": "asset_reward_ratio",
                "销售毛利率(%)": "sale_gross_profit_ratio",
                "三项费用比重": "three_expenses_ratio",
                "非主营比重": "non_main_business_ratio",
                "主营利润比重": "main_profit_ratio",
                "股息发放率(%)": "dividend_payment_ratio",
                "投资收益率(%)": "investment_return_ratio",
                "主营业务利润(元)": "main_business_profit",
                "净资产收益率(%)": "roe",
                "加权净资产收益率(%)": "weighted_roe",
                "扣除非经常性损益后的净利润(元)": "non_recurring_net_profit",
                "主营业务收入增长率(%)": "main_business_income_growth",
                "净利润增长率(%)": "net_profit_growth",
                "净资产增长率(%)": "net_asset_growth",
                "总资产增长率(%)": "total_asset_growth",
                "应收账款周转率(次)": "accounts_receivable_turnover",
                "应收账款周转天数(天)": "accounts_receivable_turnover_days",
                "存货周转天数(天)": "inventory_turnover_days",
                "存货周转率(次)": "inventory_turnover_rate",
                "固定资产周转率(次)": "fixed_asset_turnover",
                "总资产周转率(次)": "total_asset_turnover",
                "总资产周转天数(天)": "total_asset_turnover_days",
                "流动资产周转率(次)": "current_asset_turnover",
                "流动资产周转天数(天)": "current_asset_turnover_days",
                "股东权益周转率(次)": "equity_turnover",
                "流动比率": "current_ratio",
                "速动比率": "quick_ratio",
                "现金比率(%)": "cash_ratio",
                "利息支付倍数": "interest_coverage",
                "长期债务与营运资金比率(%)": "long_debt_to_working_capital",
                "股东权益比率(%)": "equity_ratio",
                "长期负债比率(%)": "long_term_debt_ratio",
                "股东权益与固定资产比率(%)": "equity_to_fixed_asset_ratio",
                "负债与所有者权益比率(%)": "debt_to_equity_ratio",
                "长期资产与长期资金比率(%)": "long_asset_to_long_fund_ratio",
                "资本化比率(%)": "capitalization_ratio",
                "固定资产净值率(%)": "fixed_asset_net_value_ratio",
                "资本固定化比率(%)": "capital_immobilization_ratio",
                "产权比率(%)": "property_ratio",
                "清算价值比率(%)": "liquidation_value_ratio",
                "固定资产比重(%)": "fixed_asset_ratio",
                "资产负债率(%)": "asset_liability_ratio",
                "总资产(元)": "total_assets",
                "经营现金净流量对销售收入比率(%)": "operating_cash_flow_to_sales_ratio",
                "资产的经营现金流量回报率(%)": "asset_cash_flow_return_ratio",
                "经营现金净流量与净利润的比率(%)": "operating_cash_flow_to_net_profit_ratio",
                "经营现金净流量对负债比率(%)": "operating_cash_flow_to_debt_ratio",
                "现金流量比率(%)": "cash_flow_ratio",
                "短期股票投资(元)": "short_term_stock_investment",
                "短期债券投资(元)": "short_term_bond_investment",
                "短期其它经营性投资(元)": "short_term_other_operating_investment",
                "长期股票投资(元)": "long_term_stock_investment",
                "长期债券投资(元)": "long_term_bond_investment",
                "长期其它经营性投资(元)": "long_term_other_operating_investment",
                "1年以内应收帐款(元)": "accounts_receivable_within_1_year",
                "1-2年以内应收帐款(元)": "accounts_receivable_between_1_and_2_year",
                "2-3年以内应收帐款(元)": "accounts_receivable_between_2_and_3_year",
                "3年以内应收帐款(元)": "accounts_receivable_within_3_year",
                "1年以内预付货款(元)": "prepaid_payment_within_1_year",
                "1-2年以内预付货款(元)": "prepaid_payment_between_1_and_2_year",
                "2-3年以内预付货款(元)": "prepaid_payment_between_2_and_3_year",
                "3年以内预付货款(元)": "prepaid_payment_within_3_year",
                "1年以内其它应收款(元)": "other_receivables_within_1_year",
                "1-2年以内其它应收款(元)": "other_receivables_between_1_and_2_year",
                "2-3年以内其它应收款(元)": "other_receivables_between_2_and_3_year",
                "3年以内其它应收款(元)": "other_receivables_within_3_year",
            },
            inplace=True,
        )

        # 添加股票代码列
        financial_analysis_df["symbol"] = formatted_symbol

        # 处理数值列中的 NaN 值
        numeric_columns = financial_analysis_df.select_dtypes(include=[np.number]).columns
        financial_analysis_df[numeric_columns] = financial_analysis_df[numeric_columns].fillna(0)

        # 处理字符串列中的 NaN 值
        string_columns = financial_analysis_df.select_dtypes(include=["object"]).columns
        financial_analysis_df[string_columns] = financial_analysis_df[string_columns].fillna("")

        # 转换为记录列表
        financial_analyses = financial_analysis_df.to_dict("records")

        # 转换 numpy 类型为 Python 原生类型
        for record in financial_analyses:
            for key, value in record.items():
                if isinstance(value, np.integer):
                    record[key] = int(value)
                elif isinstance(value, np.floating):
                    record[key] = float(value)
                elif isinstance(value, pd.Timestamp):
                    record[key] = str(value)

        # 保存到数据库
        db = get_db_session()
        try:
            # 删除该股票已有的财务指标数据
            db.query(StockFinancialAnalysisDB).filter(
                StockFinancialAnalysisDB.symbol == formatted_symbol
            ).delete()
            
            # 批量插入新数据
            if financial_analyses:
                db.bulk_insert_mappings(StockFinancialAnalysisDB, financial_analyses)
                db.commit()
                log.info(f"[{formatted_symbol}] 成功同步 {len(financial_analyses)} 条财务指标数据")
            
        except Exception as e:
            db.rollback()
            log.error(f"[{formatted_symbol}] 数据库操作失败: {e}")
            raise
        finally:
            db.close()

        return financial_analyses

    except Exception as e:
        log.error(f"[{formatted_symbol}] 获取财务指标数据失败: {e}")
        log.error(f"[{formatted_symbol}] 详细错误信息:\n{traceback.format_exc()}")
        raise


def sync_all_stock_financial_analyses(max_workers: int = 5, start_year: str = None):
    """
    同步所有股票的财务指标数据

    Args:
        max_workers: 最大并发数
        start_year: 开始查询的年份，如 "2020"，默认为当前年份-10年
    """
    # 如果没有指定开始年份，默认为当前年份-10年
    if start_year is None:
        start_year = str(datetime.datetime.now().year - 10)
        
    log.info(f"开始同步所有股票的财务指标数据，开始年份: {start_year}")

    # 获取所有股票代码
    db = get_db_session()
    try:
        symbols = [s[0] for s in db.query(StockSpotDB.symbol).all() if s[0]]
        log.info(f"获取到 {len(symbols)} 个股票代码")
    except Exception as e:
        log.error(f"获取股票代码失败: {e}")
        log.error(f"详细错误信息:\n{traceback.format_exc()}")
        raise
    finally:
        db.close()

    # 逐个同步财务指标数据
    success_count = 0
    fail_count = 0

    for i, symbol in enumerate(symbols, 1):
        try:
            sync_stock_financial_analysis(symbol, start_year)
            success_count += 1
            log.info(f"进度: {i}/{len(symbols)} - [{symbol}] 同步成功")
        except Exception as e:
            fail_count += 1
            log.error(f"进度: {i}/{len(symbols)} - [{symbol}] 同步失败: {e}")
            log.error(f"[{symbol}] 详细错误信息:\n{traceback.format_exc()}")

        # 显示进度
        if i % 100 == 0 or i == len(symbols):
            log.info(
                f"财务指标数据同步进度: {i}/{len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
            )

    log.info(
        f"财务指标数据同步完成，总计: {len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
    )