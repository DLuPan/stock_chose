# %% 选股模型
import dateutil
import dateutil.tz
import pandas as pd
import numpy as np
import datetime
from copy import deepcopy
import os
import akshare as ak
import concurrent.futures
import matplotlib.pyplot as plt
import mplfinance as mpf
from matplotlib.dates import DateFormatter, DayLocator, WeekdayLocator
import pytz  # 用于处理时区


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


# 获取当前文件所在的绝对路径
current_file_path = os.path.abspath(__file__)

# 获取当前文件的父目录
root_dir = os.path.dirname(current_file_path)

# 当前时间
c_date = datetime.datetime.now().strftime("%Y_%m_%d")


def IS_INCREASING(series, window_size):
    return series.tail(window_size).is_monotonic_increasing


adjust = "hfq"


def SHOW(symbol, rule,adjust = "hfq", window_size=5):
    daily_price = pd.read_csv(
        f"{root_dir}/data/stock_{adjust}_{symbol}.csv", parse_dates=["datetime"]
    )
    # 转换为绘制K线所需的格式
    daily_price["datetime"] = pd.to_datetime(daily_price["datetime"])
    daily_price.set_index("datetime", inplace=True)
    daily_price = daily_price[["open", "high", "low", "close", "volume"]]
    daily_price["SMA10"] = SMA(daily_price.close, window_size=10)
    daily_price["SMA20"] = SMA(daily_price.close, window_size=20)
    daily_price["SMA30"] = SMA(daily_price.close, window_size=30)
    recent_sma10_up = IS_INCREASING(daily_price["SMA10"], window_size)
    recent_sma20_up = IS_INCREASING(daily_price["SMA20"], window_size)
    recent_sma30_up = IS_INCREASING(daily_price["SMA30"], window_size)
    # 输出结果
    print(f"SMA10 最近5天是否上升: {recent_sma10_up}")
    print(f"SMA20 最近5天是否上升: {recent_sma20_up}")
    print(f"SMA30 最近5天是否上升: {recent_sma30_up}")
    df_last_60 = daily_price.tail(60)
    print(df_last_60)

    # 绘制K线和均线
    apds = [
        mpf.make_addplot(
            df_last_60["SMA10"], color="blue", width=1.0, linestyle="-", label="SMA10"
        ),
        mpf.make_addplot(
            df_last_60["SMA20"], color="orange", width=1.0, linestyle="-", label="SMA20"
        ),
        mpf.make_addplot(
            df_last_60["SMA30"], color="green", width=1.0, linestyle="-", label="SMA30"
        ),
    ]

    # 绘制图表
    fig, axes = mpf.plot(
        df_last_60,
        type="candle",  # K线图
        style="yahoo",  # 图表样式
        addplot=apds,
        volume=True,  # 显示交易量
        title=f"Stock K-line {symbol} with {rule} (Last 60 days)",
        ylabel="Price",
        ylabel_lower="Volume",
        figsize=(14, 8),
        returnfig=True,  # 返回fig和axes
    )

    # # 设置日期格式（东八区）
    # date_format = DateFormatter("%m-%d")
    # # date_format.tz = pytz.timezone("Asia/Shanghai")  # 设置时区为东八区

    # # 应用日期格式到 x 轴
    # axes[0].xaxis.set_major_formatter(date_format)
    # 调整日期标签旋转角度，避免重叠
    axes[0].tick_params(axis="x", rotation=45)

    # 设置x轴主刻度为每周
    # axes[0].xaxis.set_major_locator(WeekdayLocator())
    fig.savefig(
        f"{root_dir}/data/chose/{rule}/{symbol}_{c_date}.png",
        dpi=300,
        bbox_inches="tight",
    )  # 保存为高分辨率图片
    # # 旋转x轴标签以避免重叠
    # plt.xticks(rotation=45)

    # # 显示图表
    # plt.show()


SHOW("000012", "rule3")
