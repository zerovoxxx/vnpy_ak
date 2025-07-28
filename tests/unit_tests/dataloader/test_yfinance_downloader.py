"""
yfinance_downloader.py模块的单元测试

测试YfinanceStockDownloader类的所有功能方法
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import pytz

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

from dataloader.base import DataSource, DownloadRequest, DownloadResult
from dataloader.yfinance_downloader import YfinanceStockDownloader


class TestYfinanceStockDownloader:
    """测试YfinanceStockDownloader类"""
    
    def test_yfinance_downloader_initialization(self):
        """测试yfinance下载器初始化"""
        # Act
        downloader = YfinanceStockDownloader()
        
        # Assert
        assert downloader.name == "YfinanceStockDownloader"
        assert downloader.source == DataSource.YFINANCE
        assert downloader.yf is None
        
    @patch('dataloader.yfinance_downloader.yfinance')
    def test_init_connection_success(self, mock_yf):
        """测试yfinance连接初始化成功"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # Act
        result = downloader.init_connection()
        
        # Assert
        assert result is True
        assert downloader.yf == mock_yf
        
    @patch('dataloader.yfinance_downloader.yfinance', side_effect=ImportError())
    def test_init_connection_import_error(self, mock_yf):
        """测试yfinance库未安装的情况"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # Act
        result = downloader.init_connection()
        
        # Assert
        assert result is False
        assert downloader.yf is None
        
    @patch('dataloader.yfinance_downloader.yfinance', side_effect=Exception("初始化失败"))
    def test_init_connection_general_error(self, mock_yf):
        """测试yfinance初始化一般错误"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # Act
        result = downloader.init_connection()
        
        # Assert
        assert result is False
        assert downloader.yf is None
        
    def test_convert_interval_to_yf(self):
        """测试时间间隔转换为yfinance格式"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # Act & Assert
        assert downloader._convert_interval_to_yf(Interval.MINUTE) == "1m"
        assert downloader._convert_interval_to_yf(Interval.HOUR) == "1h"
        assert downloader._convert_interval_to_yf(Interval.DAILY) == "1d"
        
    def test_convert_interval_to_yf_unknown(self):
        """测试未知时间间隔转换"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # Act
        result = downloader._convert_interval_to_yf(Interval.WEEKLY)
        
        # Assert
        assert result == "1d"  # 默认返回日线
        
    def test_convert_exchange_to_yf_suffix(self):
        """测试交易所转换为yfinance后缀"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # Act & Assert
        # 美股通常不需要后缀
        assert downloader._convert_exchange_to_yf_suffix(Exchange.NYSE) == ""
        assert downloader._convert_exchange_to_yf_suffix(Exchange.NASDAQ) == ""
        assert downloader._convert_exchange_to_yf_suffix(Exchange.AMEX) == ""
        
    def test_convert_yf_data_to_vnpy_empty_data(self):
        """测试空DataFrame转换"""
        # Arrange
        downloader = YfinanceStockDownloader()
        empty_df = pd.DataFrame()
        
        # Act
        bars = downloader._convert_yf_data_to_vnpy(
            empty_df, "AAPL", Exchange.NYSE, Interval.DAILY
        )
        
        # Assert
        assert bars == []
        
    def test_convert_yf_data_to_vnpy_none_data(self):
        """测试None数据转换"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # Act
        bars = downloader._convert_yf_data_to_vnpy(
            None, "AAPL", Exchange.NYSE, Interval.DAILY
        )
        
        # Assert
        assert bars == []
        
    def test_convert_yf_data_to_vnpy_valid_data(self, mock_yfinance_ticker):
        """测试有效yfinance数据转换"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # 创建带时区的测试数据
        test_data = {
            'Open': [150.0, 151.0, 152.0],
            'High': [155.0, 156.0, 157.0],
            'Low': [149.0, 150.0, 151.0],
            'Close': [152.0, 153.0, 154.0],
            'Volume': [1000000, 1100000, 1200000]
        }
        
        # 创建带时区的时间索引
        dates = pd.date_range('2023-01-01', periods=3, freq='D', tz='UTC')
        df = pd.DataFrame(test_data, index=dates)
        
        # Act
        bars = downloader._convert_yf_data_to_vnpy(
            df, "AAPL", Exchange.NYSE, Interval.DAILY
        )
        
        # Assert
        assert len(bars) == 3
        assert all(isinstance(bar, BarData) for bar in bars)
        assert bars[0].symbol == "AAPL"
        assert bars[0].exchange == Exchange.NYSE
        assert bars[0].interval == Interval.DAILY
        assert bars[0].open_price == 150.0
        assert bars[0].gateway_name == "yfinance"
        
    def test_convert_yf_data_to_vnpy_no_timezone(self):
        """测试无时区的yfinance数据转换"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        test_data = {
            'Open': [150.0],
            'High': [155.0],
            'Low': [149.0],
            'Close': [152.0],
            'Volume': [1000000]
        }
        
        # 创建无时区的时间索引
        dates = pd.date_range('2023-01-01', periods=1, freq='D')
        df = pd.DataFrame(test_data, index=dates)
        
        # Act
        bars = downloader._convert_yf_data_to_vnpy(
            df, "AAPL", Exchange.NYSE, Interval.DAILY
        )
        
        # Assert
        assert len(bars) == 1
        assert bars[0].symbol == "AAPL"
        
    def test_download_bars_not_initialized(self, sample_download_request):
        """测试yfinance未初始化时下载数据"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is False
        assert "yfinance未初始化" in result.error_msg
        
    def test_download_bars_invalid_request(self):
        """测试无效请求下载数据"""
        # Arrange
        downloader = YfinanceStockDownloader()
        downloader.yf = Mock()
        
        invalid_request = DownloadRequest(
            symbol="",  # 空股票代码
            exchange=Exchange.NYSE
        )
        
        # Act
        result = downloader.download_bars(invalid_request)
        
        # Assert
        assert result.success is False
        assert "股票代码不能为空" in result.error_msg
        
    @patch('dataloader.yfinance_downloader.yfinance')
    def test_download_bars_success(self, mock_yf, sample_download_request, mock_yfinance_ticker):
        """测试成功下载数据"""
        # Arrange
        downloader = YfinanceStockDownloader()
        downloader.yf = mock_yf
        mock_yf.Ticker.return_value = mock_yfinance_ticker
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is True
        assert len(result.bars) > 0
        mock_yf.Ticker.assert_called_once_with("AAPL")
        mock_yfinance_ticker.history.assert_called_once()
        
    @patch('dataloader.yfinance_downloader.yfinance')
    def test_download_bars_with_suffix(self, mock_yf, mock_yfinance_ticker):
        """测试带后缀的股票代码下载"""
        # Arrange
        downloader = YfinanceStockDownloader()
        downloader.yf = mock_yf
        mock_yf.Ticker.return_value = mock_yfinance_ticker
        
        # 重写方法返回后缀
        downloader._convert_exchange_to_yf_suffix = Mock(return_value=".L")
        
        request = DownloadRequest(symbol="AAPL", exchange=Exchange.NYSE)
        
        # Act
        result = downloader.download_bars(request)
        
        # Assert
        mock_yf.Ticker.assert_called_once_with("AAPL.L")
        
    @patch('dataloader.yfinance_downloader.yfinance')
    def test_download_bars_empty_result(self, mock_yf, sample_download_request):
        """测试下载空结果"""
        # Arrange
        downloader = YfinanceStockDownloader()
        downloader.yf = mock_yf
        
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()  # 空DataFrame
        mock_yf.Ticker.return_value = mock_ticker
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is False
        assert "未获取到数据" in result.error_msg
        
    @patch('dataloader.yfinance_downloader.yfinance')
    def test_download_bars_exception(self, mock_yf, sample_download_request):
        """测试下载过程中发生异常"""
        # Arrange
        downloader = YfinanceStockDownloader()
        downloader.yf = mock_yf
        
        mock_yf.Ticker.side_effect = Exception("网络错误")
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is False
        assert "yfinance数据下载失败" in result.error_msg
        assert "网络错误" in result.error_msg
        
    def test_get_supported_intervals(self):
        """测试获取支持的时间间隔"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # Act
        intervals = downloader.get_supported_intervals()
        
        # Assert
        assert Interval.MINUTE in intervals
        assert Interval.HOUR in intervals
        assert Interval.DAILY in intervals
        assert len(intervals) == 3
        
    def test_is_support_interval(self):
        """测试时间间隔支持检查"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # Act & Assert
        assert downloader.is_support_interval(Interval.MINUTE) is True
        assert downloader.is_support_interval(Interval.HOUR) is True
        assert downloader.is_support_interval(Interval.DAILY) is True
        assert downloader.is_support_interval(Interval.WEEKLY) is False
        
    def test_get_supported_exchanges(self):
        """测试获取支持的交易所"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # Act
        exchanges = downloader.get_supported_exchanges()
        
        # Assert
        assert Exchange.NYSE in exchanges
        assert Exchange.NASDAQ in exchanges
        assert Exchange.AMEX in exchanges
        assert Exchange.SMART in exchanges
        assert len(exchanges) == 4
        
    @pytest.mark.parametrize("interval,expected", [
        (Interval.MINUTE, "1m"),
        (Interval.HOUR, "1h"),
        (Interval.DAILY, "1d"),
    ])
    def test_convert_interval_parametrized(self, interval, expected):
        """参数化测试时间间隔转换"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # Act
        result = downloader._convert_interval_to_yf(interval)
        
        # Assert
        assert result == expected
        
    @pytest.mark.parametrize("exchange", [Exchange.NYSE, Exchange.NASDAQ, Exchange.AMEX, Exchange.SMART])
    def test_supported_exchanges_parametrized(self, exchange):
        """参数化测试支持的交易所"""
        # Arrange
        downloader = YfinanceStockDownloader()
        
        # Act
        exchanges = downloader.get_supported_exchanges()
        
        # Assert
        assert exchange in exchanges
        
    @patch('dataloader.yfinance_downloader.yfinance')
    def test_download_bars_history_parameters(self, mock_yf, mock_yfinance_ticker):
        """测试历史数据请求参数"""
        # Arrange
        downloader = YfinanceStockDownloader()
        downloader.yf = mock_yf
        mock_yf.Ticker.return_value = mock_yfinance_ticker
        
        request = DownloadRequest(
            symbol="AAPL",
            exchange=Exchange.NYSE,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            interval=Interval.HOUR
        )
        
        # Act
        result = downloader.download_bars(request)
        
        # Assert
        mock_yfinance_ticker.history.assert_called_once_with(
            start=request.start_date,
            end=request.end_date,
            interval="1h",
            auto_adjust=True,
            prepost=False,
            actions=False
        ) 