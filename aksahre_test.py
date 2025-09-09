import akshare as ak

stock_financial_debt_ths_df = ak.stock_financial_debt_ths(
    symbol="000063", indicator="按报告期"
)
print(stock_financial_debt_ths_df.info())
