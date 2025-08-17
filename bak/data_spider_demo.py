# 数据采集工具
import concurrent.futures
import datetime
from copy import deepcopy
import os
import akshare as ak

# 获取当前文件所在的绝对路径
current_file_path = os.path.abspath(__file__)

# 获取当前文件的父目录
root_dir = os.path.dirname(current_file_path)
os.makedirs(f"{root_dir}/data/info", exist_ok=True)

# 当前时间
c_date = datetime.datetime.now().strftime("%Y_%m_%d")
stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
stock_board_map = {}
stock_board_industry_name_em_df = ak.stock_board_industry_name_em()
for index, row in stock_board_industry_name_em_df.iterrows():
    stock_board_industry_cons_em_df = ak.stock_board_industry_cons_em(
        symbol=f"{row['板块名称']}"
    )
    for df_index, df_row in stock_board_industry_cons_em_df.iterrows():
        if df_row["代码"] in stock_board_map:
            stock_board_map[df_row["代码"]] = (
                stock_board_map.get(df_row["代码"]) + "," + row["板块名称"]
            )
        else:
            stock_board_map[df_row["代码"]] = row["板块名称"]


def assign_board(symbol):
    if symbol in stock_board_map:
        return stock_board_map[symbol]
    else:
        return "Other"


stock_zh_a_spot_em_df["板块信息"] = stock_zh_a_spot_em_df["代码"].apply(assign_board)
stock_zh_a_spot_em_df.to_csv(f"{root_dir}/data/stock_info.csv", index=False)
