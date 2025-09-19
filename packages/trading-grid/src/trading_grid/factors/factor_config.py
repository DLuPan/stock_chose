"""
因子配置管理模块
提供因子参数的配置管理，支持从YAML文件加载和保存配置，以及运行时动态配置。

配置优先级（从高到低）：
1. 运行时传入的配置参数
2. 指定的配置文件
3. 环境变量 FACTOR_CONFIG_DIR 指定目录下的配置
4. 当前工作目录下的 config/factors.yaml
5. 包安装目录下的 config/factors.yaml
6. 默认配置
"""

import os
import sys
from copy import deepcopy
from typing import Dict, Any, Optional, List, Union, TypeVar, Type
from pathlib import Path
import logging

import yaml
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="BaseModel")


class BaseFactorConfig(BaseModel):
    """因子配置基类"""

    @classmethod
    def merge_configs(cls: Type[T], base: T, override: Dict[str, Any]) -> T:
        """合并配置"""
        if not override:
            return base

        merged_dict = {**base.dict(), **override}
        return cls.parse_obj(merged_dict)


class PERatioConfig(BaseFactorConfig):
    """市盈率因子配置"""

    max_pe: float = Field(default=50.0, description="最大市盈率阈值")

    @validator("max_pe")
    def validate_max_pe(cls, v):
        if v <= 0:
            raise ValueError("最大市盈率必须大于0")
        return v


class VolatilityConfig(BaseFactorConfig):
    """波动率因子配置"""

    min_volatility: float = Field(default=0.05, description="最小波动率阈值")
    max_volatility: float = Field(default=0.50, description="最大波动率阈值")
    lookback_days: int = Field(default=180, description="回看天数")

    @validator("lookback_days")
    def validate_lookback_days(cls, v):
        if v < 20:
            raise ValueError("回看天数不能小于20天")
        return v

    @validator("max_volatility")
    def validate_max_volatility(cls, v, values):
        if "min_volatility" in values and v <= values["min_volatility"]:
            raise ValueError("最大波动率必须大于最小波动率")
        return v


class VolumeConfig(BaseFactorConfig):
    """成交量因子配置"""

    min_volume: int = Field(default=5000, description="最小日均成交量（手）")
    lookback_days: int = Field(default=180, description="回看天数")

    @validator("min_volume")
    def validate_min_volume(cls, v):
        if v < 0:
            raise ValueError("最小成交量不能为负")
        return v


class TrendConfig(BaseFactorConfig):
    """趋势因子配置"""

    min_trend: float = Field(default=-0.3, description="最小年化趋势阈值")
    max_trend: float = Field(default=0.3, description="最大年化趋势阈值")
    lookback_days: int = Field(default=180, description="回看天数")

    @validator("max_trend")
    def validate_max_trend(cls, v, values):
        if "min_trend" in values and v <= values["min_trend"]:
            raise ValueError("最大趋势必须大于最小趋势")
        return v


class PriceRangeConfig(BaseFactorConfig):
    """价格区间因子配置"""

    min_price: float = Field(default=5.0, description="最小价格阈值")
    max_price: float = Field(default=100.0, description="最大价格阈值")

    @validator("max_price")
    def validate_max_price(cls, v, values):
        if "min_price" in values and v <= values["min_price"]:
            raise ValueError("最大价格必须大于最小价格")
        return v


class MarketCapConfig(BaseFactorConfig):
    """市值因子配置"""

    min_market_cap: float = Field(default=50.0, description="最小市值阈值（亿元）")
    max_market_cap: float = Field(default=1000.0, description="最大市值阈值（亿元）")

    @validator("max_market_cap")
    def validate_max_market_cap(cls, v, values):
        if "min_market_cap" in values and v <= values["min_market_cap"]:
            raise ValueError("最大市值必须大于最小市值")
        return v


class TurnoverConfig(BaseFactorConfig):
    """换手率因子配置"""

    min_turnover: float = Field(default=0.01, description="最小换手率阈值")
    max_turnover: float = Field(default=0.05, description="最大换手率阈值")
    lookback_days: int = Field(default=180, description="回看天数")

    @validator("max_turnover")
    def validate_max_turnover(cls, v, values):
        if "min_turnover" in values and v <= values["min_turnover"]:
            raise ValueError("最大换手率必须大于最小换手率")
        return v


def get_config_paths() -> List[Path]:
    """
    获取所有可能的配置文件路径，按优先级排序。
    返回值：配置文件路径列表，按优先级从高到低排序。
    """
    paths = []

    # 1. 环境变量指定的配置目录
    env_config_dir = os.environ.get("FACTOR_CONFIG_DIR")
    if env_config_dir:
        paths.append(Path(env_config_dir) / "factors.yaml")

    # 2. 当前工作目录
    paths.append(Path.cwd() / "config" / "factors.yaml")

    # 3. 包安装目录
    package_dir = Path(__file__).parent.parent.parent
    paths.append(package_dir / "config" / "factors.yaml")

    return paths


class FactorConfig(BaseModel):
    """
    因子配置总集
    管理所有因子的配置参数，支持从YAML文件加载和保存配置
    """

    # 启用的因子列表
    enabled_factors: List[str] = Field(
        default=[
            "pe_ratio",
            "volatility",
            "volume",
            "trend",
            "price_range",
            "market_cap",
            "turnover",
        ],
        description="启用的因子列表",
    )

    # 各因子的具体配置
    pe_ratio: PERatioConfig = Field(default_factory=PERatioConfig)
    volatility: VolatilityConfig = Field(default_factory=VolatilityConfig)
    volume: VolumeConfig = Field(default_factory=VolumeConfig)
    trend: TrendConfig = Field(default_factory=TrendConfig)
    price_range: PriceRangeConfig = Field(default_factory=PriceRangeConfig)
    market_cap: MarketCapConfig = Field(default_factory=MarketCapConfig)
    turnover: TurnoverConfig = Field(default_factory=TurnoverConfig)

    @classmethod
    def load_from_file(
        cls, config_path: Optional[Union[str, Path]] = None
    ) -> "FactorConfig":
        """
        从YAML文件加载配置

        Args:
            config_path: 配置文件路径，如果未指定，将按优先级搜索配置文件

        Returns:
            FactorConfig: 配置对象，如果未找到配置文件则返回默认配置
        """
        if config_path is not None:
            config_path = Path(config_path)
            if not config_path.exists():
                logger.warning(f"指定的配置文件不存在: {config_path}")
                return cls()
            paths = [config_path]
        else:
            paths = get_config_paths()

        # 遍历所有可能的配置文件路径
        for path in paths:
            if path.exists():
                logger.info(f"加载配置文件: {path}")
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        config_data = yaml.safe_load(f)
                        return cls.parse_obj(config_data)
                except Exception as e:
                    logger.error(f"加载配置文件失败: {path}, 错误: {e}")
                    continue

        logger.info("未找到配置文件，使用默认配置")
        return cls()

    def save_to_file(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """
        保存配置到YAML文件

        Args:
            config_path: 配置文件保存路径，如果未指定，将保存到第一个可写的配置路径
        """
        if config_path is not None:
            config_path = Path(config_path)
        else:
            # 使用第一个可用的配置路径
            paths = get_config_paths()
            for path in paths:
                try:
                    # 测试目录是否可写
                    if not path.parent.exists():
                        path.parent.mkdir(parents=True)
                    if os.access(str(path.parent), os.W_OK):
                        config_path = path
                        break
                except Exception:
                    continue

            if config_path is None:
                raise PermissionError("未找到可写的配置文件路径")

        # 确保配置目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存配置
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.dict(),
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
            logger.info(f"配置已保存到: {config_path}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {config_path}, 错误: {e}")
            raise

    def is_factor_enabled(self, factor_name: str) -> bool:
        """
        检查指定因子是否启用

        Args:
            factor_name: 因子名称

        Returns:
            bool: 因子是否启用
        """
        return factor_name in self.enabled_factors


# 全局配置实例
config = FactorConfig.load_from_file()
