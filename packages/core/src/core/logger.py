from loguru import logger
import sys
from pathlib import Path


class LogHelper:
    def __init__(
        self,
        log_dir: str = "logs",
        retention: str = "7 days",
        rotation: str = "1 day",
        compression: str = "zip",
        level: str = "DEBUG",
    ):
        """
        日志工具类
        :param log_dir: 日志目录
        :param retention: 日志保留时间（7 days, 30 days, None）
        :param rotation: 日志切分周期（1 day, 500 MB）
        :param compression: 日志压缩方式（zip, tar, None）
        :param level: 最低日志等级
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 移除默认的 logger
        logger.remove()

        # 控制台输出（彩色）
        logger.add(
            sys.stdout,
            level=level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>",
        )

        # 文件输出（按日期切分）
        logger.add(
            self.log_dir / "app_{time:YYYY-MM-DD}.log",
            level=level,
            rotation=rotation,
            retention=retention,
            compression=compression,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            encoding="utf-8",
        )

        self.logger = logger

    def get_logger(self):
        """获取 logger 对象"""
        return self.logger


# 创建全局日志对象
log = LogHelper().get_logger()


# 如果需要异常自动捕获，可以用装饰器
@log.catch
def test_error():
    1 / 0


if __name__ == "__main__":
    log.debug("调试信息")
    log.info("普通信息")
    log.warning("警告信息")
    log.error("错误信息")
    test_error()
