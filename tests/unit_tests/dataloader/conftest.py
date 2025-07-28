"""
dataloader模块测试配置文件

定义了dataloader测试中使用的公共fixtures和配置。
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
import pandas as pd

from vnpy.trader.object import BarData
from vnpy.trader.constant import Exchange, Interval
from vnpy.dataloader.base import DownloadRequest, DownloadResult, DataSource


@pytest.fixture
def sample_download_request():
    """创建标准的下载请求fixture"""
    return DownloadRequest(
        symbol="AAPL",
        exchange=Exchange.NASDAQ,
        start_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2023, 1, 31, tzinfo=timezone.utc),
        interval=Interval.DAILY
    )


@pytest.fixture
def sample_bar_data():
    """创建样本BarData fixture"""
    return BarData(
        symbol="AAPL",
        exchange=Exchange.NASDAQ,
        datetime=datetime(2023, 1, 1, 9, 30, tzinfo=timezone.utc),
        interval=Interval.DAILY,
        volume=1000000.0,
        turnover=0.0,
        open_interest=0.0,
        open_price=150.0,
        high_price=155.0,
        low_price=149.0,
        close_price=154.0,
        gateway_name="test"
    )


@pytest.fixture
def mock_yfinance_data():
    """创建模拟的yfinance数据DataFrame"""
    data = {
        'Open': [150.0, 151.0, 152.0],
        'High': [155.0, 156.0, 157.0],
        'Low': [149.0, 150.0, 151.0],
        'Close': [154.0, 155.0, 156.0],
        'Volume': [1000000, 1100000, 1200000]
    }
    
    # 创建带时区的时间索引
    dates = pd.date_range(
        start='2023-01-01',
        periods=3,
        freq='D',
        tz='America/New_York'
    )
    
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def mock_yfinance_empty_data():
    """创建空的yfinance数据DataFrame"""
    return pd.DataFrame()


@pytest.fixture
def mock_yfinance_ticker():
    """创建模拟的yfinance Ticker对象"""
    ticker = Mock()
    ticker.history = Mock()
    return ticker


@pytest.fixture
def mock_yfinance_module():
    """创建模拟的yfinance模块"""
    yf_module = Mock()
    yf_module.Ticker = Mock()
    return yf_module


@pytest.fixture
def successful_download_result(sample_download_request, sample_bar_data):
    """创建成功的下载结果fixture"""
    return DownloadResult(
        request=sample_download_request,
        bars=[sample_bar_data],
        success=True,
        error_msg=""
    )


@pytest.fixture
def failed_download_result(sample_download_request):
    """创建失败的下载结果fixture"""
    return DownloadResult(
        request=sample_download_request,
        bars=[],
        success=False,
        error_msg="下载失败"
    )


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """自动设置测试环境"""
    # 设置测试环境变量
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DEBUG", "true")


@pytest.fixture
def capture_logs(caplog):
    """捕获日志输出"""
    import logging
    caplog.set_level(logging.INFO)
    return caplog 