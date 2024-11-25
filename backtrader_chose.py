# %% 选股模型
import pandas as pd
import numpy as np
import datetime
from copy import deepcopy
import os
import akshare as ak

# 获取当前文件所在的绝对路径
current_file_path = os.path.abspath(__file__)

# 获取当前文件的父目录
root_dir = os.path.dirname(current_file_path)
os.makedirs(f"{root_dir}/data/chose", exist_ok=True)


# %% sma算法
def SMA(data, window_size):
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


# %% 选股策略

stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
stock_zh_a_spot_em_df.to_csv(f"{root_dir}/data/stock_info.csv", index=False)
# 筛选市值大于100亿的数据
filtered_data = stock_zh_a_spot_em_df[
    (stock_zh_a_spot_em_df["流通市值"] > 10000000000)
    & (stock_zh_a_spot_em_df["流通市值"] < 20000000000)
]
print(
    f"保存100-200亿流通市值股票:{root_dir}/data/stock_rule1{datetime.datetime.now().strftime('%Y_%m_%d')}.csv"
)
filtered_data.to_csv(
    f"{root_dir}/data/stock_rule1{datetime.datetime.now().strftime('%Y_%m_%d')}.csv",
    index=False,
)
# %% 数据下载
adjust = "hfq"
for symbol in filtered_data["代码"]:
    print(f"采集当前代码:{symbol}")
    try:
        # 可能会发生错误的代码块
        # 执行一些操作
        stock_zh_a_hist_df = ak.stock_zh_a_hist(
            symbol=f"{symbol}", period="daily", adjust=adjust
        )
        # 处理字段命名，以符合 Backtrader 的要求
        stock_zh_a_hist_df.columns = [
            "datetime",
            "sec_code",
            "open",
            "close",
            "high",
            "low",
            "volume",
            "turnover",
            "amplitude",
            "price_change_percentage",
            "price_change_amount",
            "turnover_rate",
        ]
        stock_zh_a_hist_df.to_csv(
            f"{root_dir}/data/stock_{adjust}_{symbol}.csv", index=False
        )
    except Exception as e:
        # 错误发生时的处理代码
        # SomeError 是捕获的异常类型
        print(f"发生错误: {e}")


# %% 算法定义
def CHOSE_SMA250(row):
    try:
        symobl = row.代码
        adjust = "hfq"

        daily_price = pd.read_csv(
            f"{root_dir}/data/stock_{adjust}_{symobl}.csv", parse_dates=["datetime"]
        )

        sma250 = SMA(daily_price.close, window_size=250)
        daily_price["sma250"] = sma250
        daily_price["negative2"] = sma250 * 0.98
        daily_price["positive2"] = sma250 * 1.05
        daily_price["均线250"] = (daily_price["close"] >= daily_price["negative2"]) & (
            daily_price["close"] <= daily_price["positive2"]
        )

        # 从最后一行开始，检查是否连续 15 行都满足条件
        return daily_price["均线250"].iloc[-15:].all()
    except Exception as e:
        print(f"异常:{e}")
        return False


def CHOSE_TURNOVER(row):
    try:
        symobl = row.代码
        adjust = "hfq"

        daily_price = pd.read_csv(
            f"{root_dir}/data/stock_{adjust}_{symobl}.csv", parse_dates=["datetime"]
        )
        last_value = daily_price["turnover"].iloc[-1]  # 最后一行的值
        second_last_value = daily_price["turnover"].iloc[-2]  # 倒数第二行的值

        return last_value >= 2 * second_last_value
    except Exception as e:
        print(f"异常:{e}")
        return False


# %% 股票选择条件
# 1、流通市值在100~200亿之间
# 2、连续15日收盘价在250日均线上下

stock_info = pd.read_csv(
    f"{root_dir}/data/stock_rule1{datetime.datetime.now().strftime('%Y_%m_%d')}.csv",
    dtype={"代码": str},
)
# 计算
stock_info["均线250"] = stock_info.apply(CHOSE_SMA250, axis=1)
stock_info["成交量2倍增长"] = stock_info.apply(CHOSE_TURNOVER, axis=1)
# 筛选条件：signal2 == True
filtered_data = stock_info[stock_info["均线250"]]
filtered_data.to_csv(
    f"{root_dir}/data/chose/stock_chose_rule1_{datetime.datetime.now().strftime('%Y_%m_%d')}.csv",
    index=False,
)
# %%
