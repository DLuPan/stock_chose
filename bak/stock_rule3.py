from rule_base import Rule
import pandas as pd
import numpy as np
import datetime
from copy import deepcopy
import os
import akshare as ak

from stock_data_spider import stock_spider
from stock_show import stock_savefig

# 获取当前文件所在的绝对路径
current_file_path = os.path.abspath(__file__)

# 获取当前文件的父目录
root_dir = os.path.dirname(current_file_path)
os.makedirs(f"{root_dir}/data/chose/rule3", exist_ok=True)

# 当前时间
c_date = datetime.datetime.now().strftime("%Y_%m_%d")


class Rule3(Rule):
    def __init__(self) -> None:
        super().__init__()

    def _SMA(data, window_size):
        """
        使用 Pandas 计算简单移动平均（SMA），并将 NaN 值填充为下一个有效值。

        参数:
            data (pd.Series or pd.DataFrame): 输入的 Pandas 数据对象。
            window_size (int): 移动窗口的大小。

        返回:
            pd.Series: 简单移动平均值序列。
        """
        if isinstance(data, pd.Series):
            sma = data.rolling(window=window_size).mean()
            return sma.fillna(method="bfill")  # 后向填充 NaN 值
        elif isinstance(data, pd.DataFrame):
            sma = data.rolling(window=window_size).mean()
            return sma.fillna(method="bfill")  # 后向填充 NaN 值
        else:
            raise ValueError("输入数据必须是 Pandas DataFrame 或 Series 对象。")

    def _is_increasing(series, window_size=5):
        return series.tail(window_size).is_monotonic_increasing

    def _chose(row):
        try:
            symobl = row.代码
            adjust = "hfq"

            daily_price = pd.read_csv(
                f"{root_dir}/data/info/stock_{adjust}_{symobl}.csv",
                parse_dates=["datetime"],
            )

            sma250 = Rule3._SMA(daily_price.close, window_size=250)
            sma10 = Rule3._SMA(daily_price.close, window_size=10)
            sma20 = Rule3._SMA(daily_price.close, window_size=20)
            sma30 = Rule3._SMA(daily_price.close, window_size=30)
            daily_price["sma250"] = sma250
            daily_price["sma10"] = sma10
            daily_price["sma20"] = sma20
            daily_price["sma30"] = sma30
            daily_price["negative2"] = sma250 * 0.98
            daily_price["positive2"] = sma250 * 1.05
            daily_price["250_signal"] = (
                daily_price["close"] >= daily_price["negative2"]
            ) & (daily_price["close"] <= daily_price["positive2"])
            trend_window_size = 5
            recent_sma10_up = Rule3._is_increasing(
                daily_price["sma10"], trend_window_size
            )
            recent_sma20_up = Rule3._is_increasing(
                daily_price["sma20"], trend_window_size
            )
            recent_sma30_up = Rule3._is_increasing(
                daily_price["sma30"], trend_window_size
            )
            # 从最后一行开始，检查是否连续 15 行都满足条件
            return (
                daily_price["250_signal"].iloc[-15:].all()
            )
        except Exception as e:
            print(f"异常:{e}")
            return False

    def chose(self):
        # 15天内持续收盘价在250日均线上下&10\20\30线趋势向上
        stock_info = pd.read_csv(f"{root_dir}/data/stock_info.csv", dtype={"代码": str})
        # 250+趋势过滤
        print(stock_info)
        stock_info["rule3_sinal"] = stock_info.apply(Rule3._chose, axis=1)
        filter_stock_info = stock_info[stock_info["rule3_sinal"]]
        filter_stock_info.to_csv(
            f"{root_dir}/data/chose/stock_chose_rule3_{c_date}.csv",
            index=False,
        )
        return filter_stock_info
