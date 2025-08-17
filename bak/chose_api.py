# %% 选股模型
import pandas as pd
import numpy as np
import datetime
from copy import deepcopy
import os
import akshare as ak
import concurrent.futures

# 获取当前文件所在的绝对路径
current_file_path = os.path.abspath(__file__)

# 获取当前文件的父目录
root_dir = os.path.dirname(current_file_path)

stock_board_concept_name_em_df = ak.stock_board_concept_name_em()
c_date = datetime.datetime.now().strftime("%Y_%m_%d")

# 概念板块
stock_board_concept_name_em_df.to_csv(
    f"{root_dir}/data/borad/stock_board_concept_{c_date}", index=False
)

# 行业板块
stock_board_industry_name_em_df = ak.stock_board_industry_summary_ths()
stock_board_industry_name_em_df.to_csv(
    f"{root_dir}/data/borad/stock_board_industry_{c_date}", index=False
)
print(ak.stock_board_industry_info_ths(symbol="半导体"))
