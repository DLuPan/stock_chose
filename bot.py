from telegram import Bot
from telegram.ext import ApplicationBuilder
import asyncio
import datetime
import os
from dotenv import load_dotenv
import pandas as pd
import argparse
import time


# 获取当前文件所在的绝对路径
current_file_path = os.path.abspath(__file__)

# 获取当前文件的父目录
root_dir = os.path.dirname(current_file_path)


# 当前时间
c_date = datetime.datetime.now().strftime("%Y_%m_%d")

# 配置 Telegram Bot 和目标群组 ID
GROUP_CHAT_ID = -1002254488578  # 替换为目标群组的 Chat ID


# 发送消息和图片
async def send_to_group(rule, token, grup_chat_id):
    # 读取代码内容
    stock_info = pd.read_csv(
        f"{root_dir}/data/chose/stock_chose_{rule}_{c_date}.csv",
        dtype={"代码": str},
    )
    bot = Bot(token=token)
    for index, data in stock_info.iterrows():
        image_path = f"{root_dir}/data/chose/{c_date}/{rule}/{data['代码']}_{c_date}.png"  # 替换为您的本地图片路径
        # 格式化消息
        message = (
            f"**#{data['名称']} ({data['代码']})**\n"
            f"最新价: {data['最新价']} 元\n"
            f"涨跌幅: {data['涨跌幅']} | 涨跌额: {data['涨跌额']} 元\n"
            f"成交量: {data['成交量']} 股 | 成交额: {data['成交额']/1e8:.2f} 元\n"
            f"振幅: {data['振幅']}\n"
            f"最高: {data['最高']} | 最低: {data['最低']}\n"
            f"今开: {data['今开']} | 昨收: {data['昨收']}\n"
            f"量比: {data['量比']} | 换手率: {data['换手率']}\n"
            f"市盈率(动态): {data['市盈率-动态']} | 市净率: {data['市净率']}\n"
            f"总市值: {data['总市值']/1e8:.2f} 元 | 流通市值: {data['流通市值']/1e8:.2f} 元\n"
            f"涨速: {data['涨速']} | 5分钟涨跌: {data['5分钟涨跌']}\n"
            f"60日涨跌幅: {data['60日涨跌幅']} | 年初至今涨跌幅: {data['年初至今涨跌幅']}\n"
            f"所属板块: #{data['板块信息']}\n"
            f"Rule3 信号: {'是' if data['rule3_sinal'] else '否'}"
        )
        # 发送图片和文字
        with open(image_path, "rb") as img:
            try:
                await bot.send_photo(
                    chat_id=grup_chat_id,
                    photo=img,
                    caption=message,
                    parse_mode="Markdown",
                )
                # 休眠1s便于
                time.sleep(1)
            except Exception as e:
                print("执行异常", e)


# 确保主函数是异步的
def main(rule, token, grup_chat_id):
    # 创建事件循环
    loop = asyncio.get_event_loop()

    # 创建协程任务
    task = loop.create_task(send_to_group(rule, token, grup_chat_id))

    # 运行事件循环，直到任务完成
    loop.run_until_complete(task)

    # 主动关闭事件循环
    loop.stop()
    print("Event loop stopped")


if __name__ == "__main__":
    # 创建解析器
    parser = argparse.ArgumentParser(description="请输入推送指令")
    # 添加参数
    parser.add_argument("--group", type=str, help="绘制图形")
    parser.add_argument("--token", type=str, help="绘制图形")
    parser.add_argument("--chose", type=str, help="执行指定策略")

    # 解析参数
    args = parser.parse_args()
    if args.chose:
        main(args.chose, args.token, args.group)
