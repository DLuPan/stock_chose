# 全自动选股策略
import pandas as pd
import numpy as np
import datetime
from copy import deepcopy
import os
import akshare as ak

from stock_data_spider import stock_spider
from stock_rule3 import Rule3
from stock_show import stock_savefig

# 获取当前文件所在的绝对路径
current_file_path = os.path.abspath(__file__)

# 获取当前文件的父目录
root_dir = os.path.dirname(current_file_path)
os.makedirs(f"{root_dir}/data/chose", exist_ok=True)

# 当前时间
c_date = datetime.datetime.now().strftime("%Y_%m_%d")

# 下载股票简介
stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
stock_zh_a_spot_em_df.to_csv(f"{root_dir}/data/stock_info.csv", index=False)

# 下载股票详情
stock_spider(all_symbols=stock_zh_a_spot_em_df["代码"].to_list())

# 执行规则
filter_rule3_stock_info = Rule3().chose()
# 执行绘图
for symbol in filter_rule3_stock_info["代码"].to_list():
    stock_savefig(symbol=symbol, rule="rule3")
