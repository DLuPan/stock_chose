from abc import ABC, abstractmethod


class Rule(ABC):

    @abstractmethod
    def chose(self):
        """
        选股方法，子类需要实现具体的选股逻辑。
        """
        raise NotImplementedError("子类必须实现 chose 方法。")
