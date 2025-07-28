"""
base.py模块的单元测试

测试BaseStockDownloader抽象基类、DownloadRequest和DownloadResult数据类
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

from dataloader.base import (
    BaseStockDownloader, 
    DownloadRequest, 
    DownloadResult, 
    DataSource
)


class TestDataSource:
    """测试DataSource枚举"""
    
    def test_data_source_enum_values(self):
        """测试数据源枚举值是否正确"""
        assert DataSource.VNPY.value == "vnpy"
        assert DataSource.YFINANCE.value == "yfinance"
        assert DataSource.AKSHARE.value == "akshare"
        
    def test_data_source_enum_count(self):
        """测试数据源枚举数量"""
        assert len(list(DataSource)) == 3


class TestDownloadRequest:
    """测试DownloadRequest数据类"""
    
    def test_download_request_basic_creation(self):
        """测试基本的下载请求创建"""
        # Arrange
        symbol = "AAPL"
        exchange = Exchange.NYSE
        
        # Act
        request = DownloadRequest(symbol=symbol, exchange=exchange)
        
        # Assert
        assert request.symbol == symbol
        assert request.exchange == exchange
        assert request.start_date is None
        assert request.end_date is None
        assert request.interval == Interval.DAILY
        assert request.vt_symbol == f"{symbol}.{exchange.value}"
        
    def test_download_request_full_creation(self):
        """测试完整参数的下载请求创建"""
        # Arrange
        symbol = "MSFT"
        exchange = Exchange.NASDAQ
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        interval = Interval.HOUR
        
        # Act
        request = DownloadRequest(
            symbol=symbol,
            exchange=exchange,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        # Assert
        assert request.symbol == symbol
        assert request.exchange == exchange
        assert request.start_date == start_date
        assert request.end_date == end_date
        assert request.interval == interval
        assert request.vt_symbol == f"{symbol}.{exchange.value}"
        
    def test_download_request_vt_symbol_generation(self):
        """测试vt_symbol自动生成"""
        # Arrange & Act
        request = DownloadRequest(symbol="GOOGL", exchange=Exchange.NASDAQ)
        
        # Assert
        assert request.vt_symbol == "GOOGL.NASDAQ"
        
    @pytest.mark.parametrize("symbol,exchange,expected_vt", [
        ("AAPL", Exchange.NYSE, "AAPL.NYSE"),
        ("MSFT", Exchange.NASDAQ, "MSFT.NASDAQ"),
        ("TSLA", Exchange.AMEX, "TSLA.AMEX"),
    ])
    def test_download_request_vt_symbol_various_exchanges(self, symbol, exchange, expected_vt):
        """参数化测试不同交易所的vt_symbol生成"""
        # Act
        request = DownloadRequest(symbol=symbol, exchange=exchange)
        
        # Assert
        assert request.vt_symbol == expected_vt


class TestDownloadResult:
    """测试DownloadResult数据类"""
    
    def test_download_result_with_empty_bars(self, sample_download_request):
        """测试空数据的下载结果"""
        # Arrange
        bars = []
        
        # Act
        result = DownloadResult(request=sample_download_request, bars=bars)
        
        # Assert
        assert result.request == sample_download_request
        assert result.bars == bars
        assert result.success is False
        assert result.error_msg == ""
        assert result.total_count == 0
        
    def test_download_result_with_bars(self, sample_download_request, sample_bar_data_list):
        """测试有数据的下载结果"""
        # Act
        result = DownloadResult(request=sample_download_request, bars=sample_bar_data_list)
        
        # Assert
        assert result.request == sample_download_request
        assert result.bars == sample_bar_data_list
        assert result.success is True
        assert result.error_msg == ""
        assert result.total_count == len(sample_bar_data_list)
        
    def test_download_result_with_error(self, sample_download_request):
        """测试带错误信息的下载结果"""
        # Arrange
        error_msg = "网络连接失败"
        
        # Act
        result = DownloadResult(
            request=sample_download_request,
            bars=[],
            success=False,
            error_msg=error_msg
        )
        
        # Assert
        assert result.request == sample_download_request
        assert result.bars == []
        assert result.success is False
        assert result.error_msg == error_msg
        assert result.total_count == 0
        
    def test_download_result_post_init_with_data(self, sample_download_request, sample_bar_data):
        """测试__post_init__方法正确设置成功状态"""
        # Arrange
        bars = [sample_bar_data]
        
        # Act
        result = DownloadResult(request=sample_download_request, bars=bars)
        
        # Assert
        assert result.success is True
        assert result.total_count == 1


class ConcreteDownloader(BaseStockDownloader):
    """具体的下载器实现类，用于测试抽象基类"""
    
    def init_connection(self, **kwargs) -> bool:
        return True
        
    def download_bars(self, request: DownloadRequest) -> DownloadResult:
        return DownloadResult(request=request, bars=[], success=True)


class TestBaseStockDownloader:
    """测试BaseStockDownloader抽象基类"""
    
    def test_concrete_downloader_creation(self):
        """测试具体下载器的创建"""
        # Arrange
        name = "TestDownloader"
        
        # Act
        downloader = ConcreteDownloader(name)
        
        # Assert
        assert downloader.name == name
        assert downloader.source is None
        assert str(downloader) == f"{name}(None)"
        
    def test_get_supported_intervals_default(self):
        """测试默认支持的时间间隔"""
        # Arrange
        downloader = ConcreteDownloader("Test")
        
        # Act
        intervals = downloader.get_supported_intervals()
        
        # Assert
        assert Interval.DAILY in intervals
        assert Interval.HOUR in intervals
        assert Interval.MINUTE in intervals
        
    def test_get_supported_exchanges_default(self):
        """测试默认支持的交易所"""
        # Arrange
        downloader = ConcreteDownloader("Test")
        
        # Act
        exchanges = downloader.get_supported_exchanges()
        
        # Assert
        assert Exchange.NYSE in exchanges
        assert Exchange.NASDAQ in exchanges
        assert Exchange.AMEX in exchanges
        
    def test_is_support_interval_default(self):
        """测试默认时间间隔支持检查"""
        # Arrange
        downloader = ConcreteDownloader("Test")
        
        # Act & Assert
        assert downloader.is_support_interval(Interval.DAILY) is True
        assert downloader.is_support_interval(Interval.HOUR) is True
        assert downloader.is_support_interval(Interval.MINUTE) is True
        
    def test_validate_request_valid(self, sample_download_request):
        """测试有效请求的验证"""
        # Arrange
        downloader = ConcreteDownloader("Test")
        
        # Act
        is_valid, error_msg = downloader.validate_request(sample_download_request)
        
        # Assert
        assert is_valid is True
        assert error_msg == ""
        
    def test_validate_request_invalid_exchange(self):
        """测试无效交易所的请求验证"""
        # Arrange
        downloader = ConcreteDownloader("Test")
        request = DownloadRequest(symbol="AAPL", exchange=Exchange.SSE)  # 上海证券交易所
        
        # Act
        is_valid, error_msg = downloader.validate_request(request)
        
        # Assert
        assert is_valid is False
        assert "不支持的交易所" in error_msg
        
    def test_validate_request_empty_symbol(self):
        """测试空股票代码的请求验证"""
        # Arrange
        downloader = ConcreteDownloader("Test")
        request = DownloadRequest(symbol="", exchange=Exchange.NYSE)
        
        # Act
        is_valid, error_msg = downloader.validate_request(request)
        
        # Assert
        assert is_valid is False
        assert "股票代码不能为空" in error_msg
        
    def test_validate_request_unsupported_interval(self):
        """测试不支持的时间间隔验证"""
        # Arrange
        class LimitedDownloader(BaseStockDownloader):
            def init_connection(self, **kwargs):
                return True
                
            def download_bars(self, request):
                return DownloadResult(request=request, bars=[])
                
            def is_support_interval(self, interval):
                return interval == Interval.DAILY
                
        downloader = LimitedDownloader("Limited")
        request = DownloadRequest(symbol="AAPL", exchange=Exchange.NYSE, interval=Interval.MINUTE)
        
        # Act
        is_valid, error_msg = downloader.validate_request(request)
        
        # Assert
        assert is_valid is False
        assert "不支持的时间间隔" in error_msg
        
    def test_str_representation(self):
        """测试字符串表示"""
        # Arrange
        downloader = ConcreteDownloader("TestDownloader")
        downloader.source = DataSource.YFINANCE
        
        # Act
        str_repr = str(downloader)
        
        # Assert
        assert str_repr == "TestDownloader(yfinance)"
        
    def test_str_representation_no_source(self):
        """测试无数据源时的字符串表示"""
        # Arrange
        downloader = ConcreteDownloader("TestDownloader")
        
        # Act
        str_repr = str(downloader)
        
        # Assert
        assert str_repr == "TestDownloader(None)"
        
    @pytest.mark.parametrize("interval", [Interval.DAILY, Interval.HOUR, Interval.MINUTE])
    def test_is_support_interval_parametrized(self, interval):
        """参数化测试时间间隔支持"""
        # Arrange
        downloader = ConcreteDownloader("Test")
        
        # Act & Assert
        assert downloader.is_support_interval(interval) is True
        
    @pytest.mark.parametrize("exchange", [Exchange.NYSE, Exchange.NASDAQ, Exchange.AMEX])
    def test_supported_exchanges_parametrized(self, exchange):
        """参数化测试支持的交易所"""
        # Arrange
        downloader = ConcreteDownloader("Test")
        
        # Act
        exchanges = downloader.get_supported_exchanges()
        
        # Assert
        assert exchange in exchanges 