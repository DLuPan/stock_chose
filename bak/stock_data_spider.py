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


def process_symbol(symbol, adjust, root_dir):
    """处理单个股票代码的数据采集和保存"""
    print(f"采集当前代码:{symbol}")
    try:
        # 获取历史数据
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
        # 保存到 CSV 文件
        stock_zh_a_hist_df.to_csv(
            f"{root_dir}/data/info/stock_{adjust}_{symbol}.csv", index=False
        )
    except Exception as e:
        print(f"发生错误: {e}")


def stock_spider(all_symbols, adjust="hfq", max_workers=20):
    """
    股票采集
    """
    # 创建线程池
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:

        # 提交任务到线程池
        futures = [
            executor.submit(process_symbol, symbol, adjust, root_dir)
            for symbol in all_symbols
        ]
        # 等待所有线程完成
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()  # 检查是否有异常
            except Exception as exc:
                print(f"线程执行中发生异常: {exc}")
