# 全自动选股策略
import pandas as pd
import numpy as np
import datetime
from copy import deepcopy
import os
import akshare as ak

from bot import send_to_group
from stock_data_spider import stock_spider
from stock_rule3 import Rule3
from stock_show import stock_savefig
import argparse
import asyncio

# 获取当前文件所在的绝对路径
current_file_path = os.path.abspath(__file__)

# 获取当前文件的父目录
root_dir = os.path.dirname(current_file_path)
os.makedirs(f"{root_dir}/data/chose", exist_ok=True)

# 当前时间
c_date = datetime.datetime.now().strftime("%Y_%m_%d")

stock_board_map = {}


def assign_board(symbol):
    if symbol in stock_board_map:
        return stock_board_map[symbol]
    else:
        return "Other"


def download(symbol=None):
    # 下载股票简介
    stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
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
    stock_zh_a_spot_em_df["板块信息"] = stock_zh_a_spot_em_df["代码"].apply(
        assign_board
    )
    stock_zh_a_spot_em_df.to_csv(f"{root_dir}/data/stock_info.csv", index=False)
    # 下载股票
    if symbol is None:
        # # 下载股票详情
        stock_spider(all_symbols=stock_zh_a_spot_em_df["代码"].to_list())
    else:
        stock_spider(all_symbols=[symbol])


def chose(rule):
    if rule == "rule3":
        # 执行规则
        filter_stock_info = Rule3().chose()
    else:
        print(f"不支持的规则策略:{rule}")

    show(all_symbols=filter_stock_info, rule=rule)


def show(all_symbols, rule):
    # 执行绘图
    os.makedirs(f"{root_dir}/data/chose/{c_date}/{rule}", exist_ok=True)
    for index, row in all_symbols.iterrows():
        stock_savefig(symbol=row["代码"], name=row["名称"], rule=rule)


if __name__ == "__main__":
    # 创建解析器
    parser = argparse.ArgumentParser(description="输入执行指令")
    # 添加参数
    parser.add_argument("--show", type=str, help="绘制图形")
    parser.add_argument(
        "--download",
        nargs="?",
        const="ALL",
        help="执行下载功能并指定股票代码（留空下载所有）",
    )
    parser.add_argument("--chose", type=str, help="执行指定策略")
    parser.add_argument("--group", type=str, nargs="+", help="绘制图形")
    parser.add_argument("--token", type=str, help="绘制图形")

    # 解析参数
    args = parser.parse_args()
    if args.show:
        # 读取代码内容
        stock_info = pd.read_csv(f"{root_dir}/data/stock_info.csv", dtype={"代码": str})
        stock_info = stock_info[(stock_info["代码"] == args.show)]
        show(stock_info, "show")
    if args.download:
        if args.download == "ALL":
            download()
            pass
        else:
            download(args.download)
    if args.chose:
        chose(args.chose)
        # 创建事件循环
        loop = asyncio.get_event_loop()

        # 创建协程任务

        for item in args.group:
            task = loop.create_task(send_to_group(args.chose, args.token, item))

            # 运行事件循环，直到任务完成
            loop.run_until_complete(task)

        # 主动关闭事件循环
        loop.stop()
        print("Event loop stopped")
