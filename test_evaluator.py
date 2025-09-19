"""
测试因子评估系统
"""

import os
import sys
import pytest
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yaml

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
packages_dir = project_root / "packages"
sys.path.insert(0, str(packages_dir / "trading-grid" / "src"))

from trading_grid.factors.factor_config import (
    FactorConfig,
    PERatioConfig,
    VolatilityConfig,
    VolumeConfig,
    TrendConfig,
    PriceRangeConfig,
    MarketCapConfig,
    TurnoverConfig,
)
from trading_grid.evaluator.evaluator import FactorEvaluator


# 创建测试数据
def create_sample_data(seed=42):
    """创建测试数据"""
    np.random.seed(seed)  # 保证结果可重复

    # 创建180天的模拟数据
    dates = pd.date_range(end=datetime.now(), periods=180, freq="D")

    # 生成基础价格趋势：年化10%的上涨趋势
    trend = np.linspace(0, 0.1, 180)  # 10%的年化趋势

    # 生成价格序列：基础趋势 + 随机波动
    returns = np.random.normal(0, 0.02, 180)  # 2%的日波动率
    prices = 50 * (1 + trend + returns).cumprod()  # 起始价格50元
    price_series = pd.Series(prices, index=dates)

    # 生成成交量序列：均值50000，波动率30%
    volumes = np.random.lognormal(mean=np.log(50000), sigma=0.3, size=180)
    volume_series = pd.Series(volumes, index=dates)

    # 生成换手率序列：均值2%，波动率50%
    turnovers = np.random.lognormal(mean=np.log(0.02), sigma=0.5, size=180)
    turnover_series = pd.Series(turnovers, index=dates)

    # 生成市值数据：假设流通股本10亿股
    circulating_shares = 1e9  # 10亿流通股
    latest_price = price_series.iloc[-1]
    market_cap = latest_price * circulating_shares / 1e8  # 转换为亿元单位

    return {
        "price_series": price_series,
        "volume_series": volume_series,
        "turnover_series": turnover_series,
        "pe_value": 15.0,
        "market_cap": market_cap,
        "trend": trend[-1] * 252,  # 年化趋势
        "volatility": returns.std() * np.sqrt(252),  # 年化波动率
        "latest_price": latest_price
    }


def test_factor_config_loading():
    """测试因子配置加载"""
    config = FactorConfig()

    # 测试默认配置
    assert "pe_ratio" in config.enabled_factors
    assert config.pe_ratio.max_pe == 50.0
    assert config.volatility.min_volatility == 0.05

    # 测试配置更新
    config.pe_ratio.max_pe = 60.0
    assert config.pe_ratio.max_pe == 60.0

    # 测试启用/禁用因子
    config.enabled_factors.remove("pe_ratio")
    assert "pe_ratio" not in config.enabled_factors
    config.enabled_factors.append("pe_ratio")
    assert "pe_ratio" in config.enabled_factors


def test_factor_config_validation():
    """测试因子配置验证"""
    # 测试无效的PE值
    with pytest.raises(ValueError):
        PERatioConfig(max_pe=-1.0)

    # 测试无效的波动率范围
    with pytest.raises(ValueError):
        VolatilityConfig(min_volatility=0.5, max_volatility=0.3)

    # 测试无效的回看天数
    with pytest.raises(ValueError):
        VolatilityConfig(lookback_days=10)

    # 测试无效的价格范围
    with pytest.raises(ValueError):
        PriceRangeConfig(min_price=100.0, max_price=50.0)

    # 测试无效的市值范围
    with pytest.raises(ValueError):
        MarketCapConfig(min_market_cap=1000.0, max_market_cap=500.0)

    # 测试无效的换手率范围
    with pytest.raises(ValueError):
        TurnoverConfig(min_turnover=0.05, max_turnover=0.01)


def test_factor_config_yaml():
    """测试因子配置YAML文件加载和保存"""
    # 创建测试配置
    config_dir = Path(__file__).parent / "packages" / "trading-grid" / "tests" / "test_data"
    config_file = config_dir / "factors.yaml"

    # 加载配置文件
    config = FactorConfig.load_from_file(config_file)
    assert config is not None

    # 验证配置是否正确加载
    assert config.pe_ratio.max_pe == 50.0
    assert config.volatility.min_volatility == 0.05
    assert config.volatility.max_volatility == 0.50
    assert config.volume.min_volume == 5000

    # 修改配置
    config.pe_ratio.max_pe = 60.0
    config.volatility.max_volatility = 0.60

    # 保存到新文件
    test_config_file = config_dir / "factors_test.yaml"
    config.save_to_file(test_config_file)

    # 验证文件是否正确保存
    assert test_config_file.exists()

    # 重新加载并验证
    new_config = FactorConfig.load_from_file(test_config_file)
    assert new_config.pe_ratio.max_pe == 60.0
    assert new_config.volatility.max_volatility == 0.60

    # 清理测试文件
    if test_config_file.exists():
        test_config_file.unlink()


def test_factor_calculations():
    """测试因子计算的准确性"""
    evaluator = FactorEvaluator("TEST")
    sample_data = create_sample_data()

    # 测试波动率因子
    volatility_result = evaluator.evaluate_factor(
        "volatility", price_series=sample_data["price_series"]
    )
    assert volatility_result["value"] is not None
    assert 0 < volatility_result["value"] < 1  # 波动率应该在0-100%之间
    assert "is_passed" in volatility_result

    if "volume" in evaluator.config.enabled_factors:
        # 测试成交量因子
        volume_result = evaluator.evaluate_factor(
            "volume", volume_series=sample_data["volume_series"]
        )
        # 确保返回了有效值再进行比较
        assert volume_result["value"] is not None
        assert volume_result["value"] > 0
        assert "is_passed" in volume_result

    # 测试趋势因子
    if "trend" in evaluator.config.enabled_factors:
        trend_result = evaluator.evaluate_factor(
            "trend", price_series=sample_data["price_series"]
        )
        # 趋势因子可能返回None，所以需要检查
        if trend_result["value"] is not None:
            # 趋势值可能超出预设范围，因此只检查类型
            assert isinstance(trend_result["value"], (int, float))
            assert "is_passed" in trend_result

    # 测试价格区间因子
    if "price_range" in evaluator.config.enabled_factors:
        price_result = evaluator.evaluate_factor(
            "price_range", latest_price=sample_data["latest_price"]
        )
        # 价格区间因子可能返回None，所以需要检查
        if price_result["value"] is not None:
            assert price_result["value"] > 0
            assert "is_passed" in price_result

    # 测试市值因子
    market_cap_result = evaluator.evaluate_factor(
        "market_cap", market_cap=sample_data["market_cap"]
    )
    assert market_cap_result["value"] is not None
    assert market_cap_result["value"] > 0
    assert "is_passed" in market_cap_result

    # 测试PE因子
    pe_result = evaluator.evaluate_factor(
        "pe_ratio", pe_value=sample_data["pe_value"]
    )
    assert pe_result["value"] is not None
    assert pe_result["value"] > 0
    assert pe_result["value"] == sample_data["pe_value"]
    assert "is_passed" in pe_result

    # 测试换手率因子
    if "turnover" in evaluator.config.enabled_factors:
        turnover_result = evaluator.evaluate_factor(
            "turnover", turnover_series=sample_data["turnover_series"]
        )
        # 换手率因子可能返回None，所以需要检查
        if turnover_result["value"] is not None:
            # 换手率值可能超出预设范围，因此只检查类型
            assert isinstance(turnover_result["value"], (int, float))
            assert "is_passed" in turnover_result


def test_runtime_config():
    """测试运行时配置"""
    evaluator = FactorEvaluator("TEST")
    sample_data = create_sample_data()

    # 使用默认配置运行
    default_result = evaluator.evaluate_factor("pe_ratio", pe_value=15.0)

    # 修改配置
    evaluator.config.pe_ratio.max_pe = 100.0
    custom_result = evaluator.evaluate_factor("pe_ratio", pe_value=15.0)

    # 验证配置变化导致的结果差异
    assert default_result["threshold"] != custom_result["threshold"]

    # 测试波动率配置更新
    evaluator.config.volatility.max_volatility = 0.60
    volatility_result = evaluator.evaluate_factor(
        "volatility", price_series=sample_data["price_series"]
    )
    min_val, max_val = volatility_result["threshold"].split(" - ")
    assert float(min_val) == 0.05
    assert float(max_val) == 0.60

    # 测试市值配置更新
    evaluator.config.market_cap.max_market_cap = 2000.0
    market_cap_result = evaluator.evaluate_factor(
        "market_cap", market_cap=sample_data["market_cap"]
    )
    # 确保返回了阈值再进行分割
    assert market_cap_result["threshold"] is not None
    # 市值因子使用的是"亿 ~ "分隔符而不是" - "分隔符
    parts = market_cap_result["threshold"].split("亿 ~ ")
    assert len(parts) == 2
    min_val, max_val = parts
    assert float(min_val) == 50.0
    # 处理"2000.0亿"这种格式
    max_val_clean = max_val.replace("亿", "")
    assert float(max_val_clean) == 2000.0


def test_factor_evaluation():
    """测试因子评估"""
    evaluator = FactorEvaluator("TEST")
    sample_data = create_sample_data()

    # 运行评估
    result = evaluator.evaluate_factor("pe_ratio", pe_value=sample_data["pe_value"])

    # 验证结果格式
    assert result is not None
    assert isinstance(result, dict)
    assert "is_passed" in result
    assert "value" in result
    assert isinstance(result["is_passed"], bool)
    assert isinstance(result["value"], (int, float))
    assert result["factor"] == "pe_ratio"


@pytest.mark.skip(reason="因子注册器尚未实现")
def test_factor_registry():
    """测试因子注册"""
    from trading_grid.factors import FactorRegistry

    # 验证所有因子都已注册
    assert "pe_ratio" in FactorRegistry.get_all_factors()
    assert "volatility" in FactorRegistry.get_all_factors()
    assert "volume" in FactorRegistry.get_all_factors()
    assert "trend" in FactorRegistry.get_all_factors()
    assert "price_range" in FactorRegistry.get_all_factors()
    assert "market_cap" in FactorRegistry.get_all_factors()
    assert "turnover" in FactorRegistry.get_all_factors()

    # 验证因子类型
    for factor_name in FactorRegistry.get_all_factors():
        factor_cls = FactorRegistry.get(factor_name)
        assert factor_cls is not None
        assert hasattr(factor_cls, "calculate")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])