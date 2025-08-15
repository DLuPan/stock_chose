from abc import ABC, abstractmethod
import pandas as pd


class Rule(ABC):
    def __init__(self, rule_name: str = None) -> None:
        super().__init__()
        self.rule_name = rule_name

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

    @abstractmethod
    def chose(self):
        """
        选股方法，子类需要实现具体的选股逻辑。
        """
        raise NotImplementedError("子类必须实现 chose 方法。")

    @abstractmethod
    def generate_stock_report(
        self,
        stock_spot_data: pd.DataFrame,
        stock_history_data: pd.DataFrame,
        stock_business_data: pd.DataFrame,
        stock_business_composition: pd.DataFrame,
        stock_pledge_ratio_data: pd.DataFrame,
        report_date: str = None,
    ):
        """
        生成选股报告，子类需要实现具体的报告生成逻辑。
        """
        raise NotImplementedError("子类必须实现 generate_stock_report 方法。")
