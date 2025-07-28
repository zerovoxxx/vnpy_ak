"""
dataloader测试的共享fixtures

定义测试中使用的公共fixture和mock对象
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
import pandas as pd

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

from dataloader.base import DownloadRequest, DownloadResult, DataSource


@pytest.fixture
def sample_download_request():
    """创建测试用的下载请求"""
    return DownloadRequest(
        symbol="AAPL",
        exchange=Exchange.NYSE,
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        interval=Interval.DAILY
    )


@pytest.fixture
def sample_bar_data():
    """创建测试用的BarData"""
    return BarData(
        symbol="AAPL",
        exchange=Exchange.NYSE,
        datetime=datetime(2023, 1, 1, 9, 30),
        interval=Interval.DAILY,
        volume=1000000.0,
        turnover=0.0,
        open_interest=0.0,
        open_price=150.0,
        high_price=155.0,
        low_price=149.0,
        close_price=152.0,
        gateway_name="test"
    )


@pytest.fixture
def sample_bar_data_list(sample_bar_data):
    """创建测试用的BarData列表"""
    bars = []
    for i in range(5):
        bar = BarData(
            symbol=sample_bar_data.symbol,
            exchange=sample_bar_data.exchange,
            datetime=datetime(2023, 1, i+1, 9, 30),
            interval=sample_bar_data.interval,
            volume=sample_bar_data.volume + i * 1000,
            turnover=0.0,
            open_interest=0.0,
            open_price=sample_bar_data.open_price + i,
            high_price=sample_bar_data.high_price + i,
            low_price=sample_bar_data.low_price + i,
            close_price=sample_bar_data.close_price + i,
            gateway_name=sample_bar_data.gateway_name
        )
        bars.append(bar)
    return bars


@pytest.fixture
def sample_download_result_success(sample_download_request, sample_bar_data_list):
    """创建测试用的成功下载结果"""
    return DownloadResult(
        request=sample_download_request,
        bars=sample_bar_data_list,
        success=True,
        error_msg=""
    )


@pytest.fixture
def sample_download_result_failure(sample_download_request):
    """创建测试用的失败下载结果"""
    return DownloadResult(
        request=sample_download_request,
        bars=[],
        success=False,
        error_msg="下载失败"
    )


@pytest.fixture
def mock_database():
    """模拟数据库对象"""
    mock_db = Mock()
    mock_db.save_bar_data.return_value = True
    mock_db.get_bar_overview.return_value = []
    mock_db.delete_bar_data.return_value = 0
    return mock_db


@pytest.fixture
def mock_yfinance_ticker():
    """模拟yfinance Ticker对象"""
    mock_ticker = Mock()
    
    # 创建测试用的DataFrame
    test_data = {
        'Open': [150.0, 151.0, 152.0],
        'High': [155.0, 156.0, 157.0],
        'Low': [149.0, 150.0, 151.0],
        'Close': [152.0, 153.0, 154.0],
        'Volume': [1000000, 1100000, 1200000]
    }
    
    dates = pd.date_range('2023-01-01', periods=3, freq='D')
    df = pd.DataFrame(test_data, index=dates)
    
    mock_ticker.history.return_value = df
    return mock_ticker


@pytest.fixture
def mock_akshare_data():
    """模拟akshare返回的数据"""
    test_data = {
        'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'open': [150.0, 151.0, 152.0],
        'high': [155.0, 156.0, 157.0],
        'low': [149.0, 150.0, 151.0],
        'close': [152.0, 153.0, 154.0],
        'volume': [1000000, 1100000, 1200000]
    }
    
    return pd.DataFrame(test_data)


@pytest.fixture
def mock_vnpy_datafeed():
    """模拟vnpy数据源"""
    mock_datafeed = Mock()
    mock_datafeed.init.return_value = True
    mock_datafeed.query_bar_history.return_value = []
    return mock_datafeed 