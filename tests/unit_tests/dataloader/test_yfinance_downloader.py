"""
YfinanceStockDownloader单元测试

测试基于yfinance的股票数据下载器的所有功能。
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from vnpy.trader.object import BarData
from vnpy.trader.constant import Exchange, Interval
from vnpy.dataloader.base import DownloadRequest, DownloadResult, DataSource
from vnpy.dataloader.yfinance_downloader import YfinanceStockDownloader


class TestYfinanceStockDownloader:
    """YfinanceStockDownloader测试类"""

    def setup_method(self):
        """每个测试方法执行前的准备工作"""
        self.downloader = YfinanceStockDownloader()

    def test_init_should_create_instance_with_correct_attributes(self):
        """测试初始化应该创建具有正确属性的实例"""
        # Assert
        assert self.downloader.name == "YfinanceStockDownloader"
        assert self.downloader.source == DataSource.YFINANCE
        assert self.downloader.yf is None

    def test_init_connection_with_yfinance_available_should_return_true(self):
        """测试yfinance可用时初始化连接应该返回True"""
        # Arrange
        mock_yf = Mock()
        
        # Act & Assert
        with patch.dict('sys.modules', {'yfinance': mock_yf}):
            result = self.downloader.init_connection()
                
        assert result is True
        assert self.downloader.yf is not None

    def test_init_connection_with_yfinance_not_available_should_return_false(self):
        """测试yfinance不可用时初始化连接应该返回False"""
        # Act & Assert
        with patch('builtins.__import__', side_effect=ImportError("No module named 'yfinance'")):
            result = self.downloader.init_connection()
            
        assert result is False
        assert self.downloader.yf is None

    def test_init_connection_with_exception_should_return_false(self):
        """测试初始化连接遇到异常时应该返回False"""
        # Act & Assert
        with patch('builtins.__import__', side_effect=Exception("Unknown error")):
            result = self.downloader.init_connection()
            
        assert result is False
        assert self.downloader.yf is None

    @pytest.mark.parametrize("interval,expected", [
        (Interval.MINUTE, "1m"),
        (Interval.HOUR, "1h"),
        (Interval.DAILY, "1d"),
    ])
    def test_convert_interval_to_yf_should_return_correct_format(self, interval, expected):
        """测试时间间隔转换应该返回正确格式"""
        # Act
        result = self.downloader._convert_interval_to_yf(interval)
        
        # Assert
        assert result == expected

    def test_convert_interval_to_yf_with_unsupported_interval_should_return_default(self):
        """测试不支持的时间间隔转换应该返回默认值"""
        # Arrange
        unsupported_interval = Mock()
        
        # Act
        result = self.downloader._convert_interval_to_yf(unsupported_interval)
        
        # Assert
        assert result == "1d"

    @pytest.mark.parametrize("exchange,expected", [
        (Exchange.NYSE, ""),
        (Exchange.NASDAQ, ""),
        (Exchange.AMEX, ""),
        (Exchange.SMART, ""),
    ])
    def test_convert_exchange_to_yf_suffix_should_return_empty_string(self, exchange, expected):
        """测试交易所转换应该返回空字符串（美股不需要后缀）"""
        # Act
        result = self.downloader._convert_exchange_to_yf_suffix(exchange)
        
        # Assert
        assert result == expected

    def test_convert_yf_data_to_vnpy_with_valid_data_should_return_bar_list(self, mock_yfinance_data):
        """测试有效数据转换应该返回BarData列表"""
        # Arrange
        symbol = "AAPL"
        exchange = Exchange.NASDAQ
        interval = Interval.DAILY
        
        # Act
        result = self.downloader._convert_yf_data_to_vnpy(
            mock_yfinance_data, symbol, exchange, interval
        )
        
        # Assert
        assert len(result) == 3
        assert all(isinstance(bar, BarData) for bar in result)
        
        # 检查第一个BarData的属性
        first_bar = result[0]
        assert first_bar.symbol == symbol
        assert first_bar.exchange == exchange
        assert first_bar.interval == interval
        assert first_bar.open_price == 150.0
        assert first_bar.high_price == 155.0
        assert first_bar.low_price == 149.0
        assert first_bar.close_price == 154.0
        assert first_bar.volume == 1000000.0
        assert first_bar.gateway_name == "yfinance"

    def test_convert_yf_data_to_vnpy_with_empty_data_should_return_empty_list(self, mock_yfinance_empty_data):
        """测试空数据转换应该返回空列表"""
        # Arrange
        symbol = "AAPL"
        exchange = Exchange.NASDAQ
        interval = Interval.DAILY
        
        # Act
        result = self.downloader._convert_yf_data_to_vnpy(
            mock_yfinance_empty_data, symbol, exchange, interval
        )
        
        # Assert
        assert result == []

    def test_convert_yf_data_to_vnpy_with_none_data_should_return_empty_list(self):
        """测试None数据转换应该返回空列表"""
        # Arrange
        symbol = "AAPL"
        exchange = Exchange.NASDAQ
        interval = Interval.DAILY
        
        # Act
        result = self.downloader._convert_yf_data_to_vnpy(
            None, symbol, exchange, interval
        )
        
        # Assert
        assert result == []

    def test_download_bars_with_valid_request_should_return_success_result(self, sample_download_request, mock_yfinance_data):
        """测试有效请求下载K线数据应该返回成功结果"""
        # Arrange
        mock_yf = Mock()
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_yfinance_data
        mock_yf.Ticker.return_value = mock_ticker
        self.downloader.yf = mock_yf
        
        # Act
        result = self.downloader.download_bars(sample_download_request)
        
        # Assert
        assert isinstance(result, DownloadResult)
        assert result.success is True
        assert len(result.bars) == 3
        assert result.error_msg == ""
        assert result.request == sample_download_request
        
        # 验证yfinance调用
        mock_yf.Ticker.assert_called_once_with("AAPL")
        mock_ticker.history.assert_called_once_with(
            start=sample_download_request.start_date,
            end=sample_download_request.end_date,
            interval="1d",
            auto_adjust=True,
            prepost=False,
            actions=False
        )

    def test_download_bars_with_invalid_request_should_return_failure_result(self):
        """测试无效请求下载K线数据应该返回失败结果"""
        # Arrange
        invalid_request = DownloadRequest(
            symbol="",  # 空的股票代码
            exchange=Exchange.NASDAQ,
            interval=Interval.DAILY
        )
        
        # Act
        result = self.downloader.download_bars(invalid_request)
        
        # Assert
        assert isinstance(result, DownloadResult)
        assert result.success is False
        assert result.bars == []
        assert "股票代码不能为空" in result.error_msg

    def test_download_bars_without_yfinance_initialized_should_return_failure_result(self, sample_download_request):
        """测试未初始化yfinance时下载K线数据应该返回失败结果"""
        # Arrange - yf is None by default
        
        # Act
        result = self.downloader.download_bars(sample_download_request)
        
        # Assert
        assert isinstance(result, DownloadResult)
        assert result.success is False
        assert result.bars == []
        assert "yfinance未初始化" in result.error_msg

    def test_download_bars_with_yfinance_exception_should_return_failure_result(self, sample_download_request):
        """测试yfinance抛出异常时下载K线数据应该返回失败结果"""
        # Arrange
        mock_yf = Mock()
        mock_yf.Ticker.side_effect = Exception("Network error")
        self.downloader.yf = mock_yf
        
        # Act
        result = self.downloader.download_bars(sample_download_request)
        
        # Assert
        assert isinstance(result, DownloadResult)
        assert result.success is False
        assert result.bars == []
        assert "yfinance数据下载失败" in result.error_msg
        assert "Network error" in result.error_msg

    def test_download_bars_with_empty_data_should_return_failure_result(self, sample_download_request, mock_yfinance_empty_data):
        """测试下载到空数据时应该返回失败结果"""
        # Arrange
        mock_yf = Mock()
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_yfinance_empty_data
        mock_yf.Ticker.return_value = mock_ticker
        self.downloader.yf = mock_yf
        
        # Act
        result = self.downloader.download_bars(sample_download_request)
        
        # Assert
        assert isinstance(result, DownloadResult)
        assert result.success is False
        assert result.bars == []
        assert "未获取到数据或股票代码不存在" in result.error_msg

    def test_get_supported_intervals_should_return_correct_intervals(self):
        """测试获取支持的时间间隔应该返回正确的间隔列表"""
        # Act
        result = self.downloader.get_supported_intervals()
        
        # Assert
        expected = [Interval.MINUTE, Interval.HOUR, Interval.DAILY]
        assert result == expected

    @pytest.mark.parametrize("interval,expected", [
        (Interval.MINUTE, True),
        (Interval.HOUR, True),
        (Interval.DAILY, True),
    ])
    def test_is_support_interval_with_supported_intervals_should_return_true(self, interval, expected):
        """测试支持的时间间隔检查应该返回True"""
        # Act
        result = self.downloader.is_support_interval(interval)
        
        # Assert
        assert result == expected

    def test_is_support_interval_with_unsupported_interval_should_return_false(self):
        """测试不支持的时间间隔检查应该返回False"""
        # Arrange
        unsupported_interval = Mock()
        
        # Act
        result = self.downloader.is_support_interval(unsupported_interval)
        
        # Assert
        assert result is False

    def test_get_supported_exchanges_should_return_correct_exchanges(self):
        """测试获取支持的交易所应该返回正确的交易所列表"""
        # Act
        result = self.downloader.get_supported_exchanges()
        
        # Assert
        expected = [Exchange.NYSE, Exchange.NASDAQ, Exchange.AMEX, Exchange.SMART]
        assert result == expected


class TestYfinanceDataConversion:
    """yfinance数据转换测试类"""

    def setup_method(self):
        """每个测试方法执行前的准备工作"""
        self.downloader = YfinanceStockDownloader()

    def test_convert_yf_data_with_timezone_naive_timestamps_should_handle_correctly(self):
        """测试处理无时区信息的时间戳应该正确处理"""
        # Arrange
        data = {
            'Open': [150.0],
            'High': [155.0],
            'Low': [149.0],
            'Close': [154.0],
            'Volume': [1000000]
        }
        
        # 创建无时区的时间索引
        dates = pd.date_range(start='2023-01-01', periods=1, freq='D')  # 默认无时区
        df = pd.DataFrame(data, index=dates)
        
        # Act
        result = self.downloader._convert_yf_data_to_vnpy(
            df, "AAPL", Exchange.NASDAQ, Interval.DAILY
        )
        
        # Assert
        assert len(result) == 1
        assert isinstance(result[0], BarData)
        assert result[0].datetime is not None

    def test_convert_yf_data_with_missing_columns_should_handle_gracefully(self):
        """测试处理缺失列的数据应该优雅处理"""
        # Arrange - 创建只有部分列的数据
        data = {
            'Open': [150.0],
            'Close': [154.0],
            # 缺少 High, Low, Volume
        }
        
        dates = pd.date_range(
            start='2023-01-01',
            periods=1,
            freq='D',
            tz='America/New_York'
        )
        df = pd.DataFrame(data, index=dates)
        
        # Act
        result = self.downloader._convert_yf_data_to_vnpy(
            df, "AAPL", Exchange.NASDAQ, Interval.DAILY
        )
        
        # Assert
        assert len(result) == 1
        bar = result[0]
        assert bar.open_price == 150.0
        assert bar.close_price == 154.0
        assert bar.high_price == 0.0  # 默认值
        assert bar.low_price == 0.0   # 默认值
        assert bar.volume == 0.0      # 默认值


class TestYfinanceIntegration:
    """yfinance集成测试类"""

    def setup_method(self):
        """每个测试方法执行前的准备工作"""
        self.downloader = YfinanceStockDownloader()

    def test_full_workflow_download_bars_should_work_correctly(self, sample_download_request, mock_yfinance_data):
        """测试完整的下载工作流程应该正确工作"""
        # Arrange
        mock_yf_module = Mock()
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_yfinance_data
        mock_yf_module.Ticker.return_value = mock_ticker
        
        # Act & Assert
        with patch.dict('sys.modules', {'yfinance': mock_yf_module}):
            # 1. 初始化连接
            init_result = self.downloader.init_connection()
            
            # 2. 下载数据
            download_result = self.downloader.download_bars(sample_download_request)
            
            # Assert
            assert init_result is True
            assert download_result.success is True
            assert len(download_result.bars) == 3
            assert all(isinstance(bar, BarData) for bar in download_result.bars)

    def test_validate_request_inheritance_should_work_correctly(self):
        """测试继承的请求验证功能应该正确工作"""
        # Arrange
        invalid_request = DownloadRequest(
            symbol="AAPL",
            exchange=Exchange.SSE,  # 不支持的交易所
            interval=Interval.DAILY
        )
        
        # Act
        is_valid, error_msg = self.downloader.validate_request(invalid_request)
        
        # Assert
        assert is_valid is False
        assert "不支持的交易所" in error_msg

    def test_str_representation_should_return_correct_format(self):
        """测试字符串表示应该返回正确格式"""
        # Act
        result = str(self.downloader)
        
        # Assert
        assert result == "YfinanceStockDownloader(DataSource.YFINANCE)"


# 异常场景测试
class TestYfinanceExceptionScenarios:
    """yfinance异常场景测试类"""

    def setup_method(self):
        """每个测试方法执行前的准备工作"""
        self.downloader = YfinanceStockDownloader()

    def test_download_bars_with_network_timeout_should_handle_gracefully(self, sample_download_request):
        """测试网络超时时下载K线数据应该优雅处理"""
        # Arrange
        mock_yf = Mock()
        mock_ticker = Mock()
        mock_ticker.history.side_effect = TimeoutError("Request timeout")
        mock_yf.Ticker.return_value = mock_ticker
        self.downloader.yf = mock_yf
        
        # Act
        result = self.downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is False
        assert "Request timeout" in result.error_msg

    def test_download_bars_with_invalid_symbol_format_should_handle_gracefully(self, sample_download_request):
        """测试无效股票代码格式时下载K线数据应该优雅处理"""
        # Arrange
        mock_yf = Mock()
        mock_ticker = Mock()
        mock_ticker.history.side_effect = ValueError("Invalid symbol format")
        mock_yf.Ticker.return_value = mock_ticker
        self.downloader.yf = mock_yf
        
        # Act
        result = self.downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is False
        assert "Invalid symbol format" in result.error_msg 