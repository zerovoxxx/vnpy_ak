"""
vnpy_downloader.py模块的单元测试

测试VnpyStockDownloader类的所有功能方法
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData, HistoryRequest

from dataloader.base import DataSource, DownloadRequest, DownloadResult
from dataloader.vnpy_downloader import VnpyStockDownloader


class TestVnpyStockDownloader:
    """测试VnpyStockDownloader类"""
    
    def test_vnpy_downloader_initialization(self):
        """测试vnpy下载器初始化"""
        # Act
        downloader = VnpyStockDownloader()
        
        # Assert
        assert downloader.name == "VnpyStockDownloader"
        assert downloader.source == DataSource.VNPY
        assert downloader.datafeed is None
        
    @patch('dataloader.vnpy_downloader.get_datafeed')
    @patch('dataloader.vnpy_downloader.SETTINGS')
    def test_init_connection_success(self, mock_settings, mock_get_datafeed, mock_vnpy_datafeed):
        """测试vnpy数据源连接初始化成功"""
        # Arrange
        downloader = VnpyStockDownloader()
        mock_get_datafeed.return_value = mock_vnpy_datafeed
        mock_vnpy_datafeed.init.return_value = True
        
        # Act
        result = downloader.init_connection(
            datafeed_name="rqdata",
            username="test_user",
            password="test_pass"
        )
        
        # Assert
        assert result is True
        assert downloader.datafeed == mock_vnpy_datafeed
        assert mock_settings.__setitem__.call_count >= 3
        mock_get_datafeed.assert_called_once()
        mock_vnpy_datafeed.init.assert_called_once()
        
    @patch('dataloader.vnpy_downloader.get_datafeed')
    def test_init_connection_no_init_method(self, mock_get_datafeed, mock_vnpy_datafeed):
        """测试数据源没有init方法的情况"""
        # Arrange
        downloader = VnpyStockDownloader()
        mock_get_datafeed.return_value = mock_vnpy_datafeed
        # 模拟没有init方法
        delattr(mock_vnpy_datafeed, 'init')
        
        # Act
        result = downloader.init_connection()
        
        # Assert
        assert result is True
        assert downloader.datafeed == mock_vnpy_datafeed
        
    @patch('dataloader.vnpy_downloader.get_datafeed')
    def test_init_connection_failure(self, mock_get_datafeed):
        """测试vnpy数据源初始化失败"""
        # Arrange
        downloader = VnpyStockDownloader()
        mock_get_datafeed.side_effect = Exception("数据源连接失败")
        
        # Act
        result = downloader.init_connection()
        
        # Assert
        assert result is False
        assert downloader.datafeed is None
        
    @patch('dataloader.vnpy_downloader.get_datafeed')
    def test_init_connection_init_failure(self, mock_get_datafeed, mock_vnpy_datafeed):
        """测试数据源init方法返回False"""
        # Arrange
        downloader = VnpyStockDownloader()
        mock_get_datafeed.return_value = mock_vnpy_datafeed
        mock_vnpy_datafeed.init.return_value = False
        
        # Act
        result = downloader.init_connection()
        
        # Assert
        assert result is False
        assert downloader.datafeed == mock_vnpy_datafeed
        
    def test_download_bars_not_initialized(self, sample_download_request):
        """测试数据源未初始化时下载数据"""
        # Arrange
        downloader = VnpyStockDownloader()
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is False
        assert "数据源未初始化" in result.error_msg
        
    def test_download_bars_invalid_request(self, mock_vnpy_datafeed):
        """测试无效请求下载数据"""
        # Arrange
        downloader = VnpyStockDownloader()
        downloader.datafeed = mock_vnpy_datafeed
        
        invalid_request = DownloadRequest(
            symbol="",  # 空股票代码
            exchange=Exchange.NYSE
        )
        
        # Act
        result = downloader.download_bars(invalid_request)
        
        # Assert
        assert result.success is False
        assert "股票代码不能为空" in result.error_msg
        
    def test_download_bars_success(self, sample_download_request, sample_bar_data_list, mock_vnpy_datafeed):
        """测试成功下载数据"""
        # Arrange
        downloader = VnpyStockDownloader()
        downloader.datafeed = mock_vnpy_datafeed
        mock_vnpy_datafeed.query_bar_history.return_value = sample_bar_data_list
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is True
        assert len(result.bars) == len(sample_bar_data_list)
        
        # 验证调用参数
        mock_vnpy_datafeed.query_bar_history.assert_called_once()
        call_args = mock_vnpy_datafeed.query_bar_history.call_args[0][0]
        assert isinstance(call_args, HistoryRequest)
        assert call_args.symbol == sample_download_request.symbol
        assert call_args.exchange == sample_download_request.exchange
        
    def test_download_bars_empty_result(self, sample_download_request, mock_vnpy_datafeed):
        """测试下载空结果"""
        # Arrange
        downloader = VnpyStockDownloader()
        downloader.datafeed = mock_vnpy_datafeed
        mock_vnpy_datafeed.query_bar_history.return_value = []  # 空列表
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is False
        assert "未获取到数据" in result.error_msg
        
    def test_download_bars_exception(self, sample_download_request, mock_vnpy_datafeed):
        """测试下载过程中发生异常"""
        # Arrange
        downloader = VnpyStockDownloader()
        downloader.datafeed = mock_vnpy_datafeed
        mock_vnpy_datafeed.query_bar_history.side_effect = Exception("网络错误")
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is False
        assert "数据下载失败" in result.error_msg
        assert "网络错误" in result.error_msg
        
    def test_download_bars_gateway_name_handling(self, sample_download_request, mock_vnpy_datafeed):
        """测试gateway_name处理"""
        # Arrange
        downloader = VnpyStockDownloader()
        downloader.datafeed = mock_vnpy_datafeed
        
        # 创建没有gateway_name的BarData
        bar_without_gateway = BarData(
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
            gateway_name=""  # 空的gateway_name
        )
        
        mock_vnpy_datafeed.query_bar_history.return_value = [bar_without_gateway]
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is True
        assert len(result.bars) == 1
        assert result.bars[0].gateway_name == "vnpy_datafeed"
        
    def test_download_bars_existing_gateway_name(self, sample_download_request, mock_vnpy_datafeed):
        """测试已有gateway_name的情况"""
        # Arrange
        downloader = VnpyStockDownloader()
        downloader.datafeed = mock_vnpy_datafeed
        
        # 创建有gateway_name的BarData
        bar_with_gateway = BarData(
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
            gateway_name="existing_gateway"
        )
        
        mock_vnpy_datafeed.query_bar_history.return_value = [bar_with_gateway]
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is True
        assert len(result.bars) == 1
        assert result.bars[0].gateway_name == "existing_gateway"  # 保持原有的gateway_name
        
    def test_get_supported_intervals(self):
        """测试获取支持的时间间隔"""
        # Arrange
        downloader = VnpyStockDownloader()
        
        # Act
        intervals = downloader.get_supported_intervals()
        
        # Assert
        assert Interval.DAILY in intervals
        assert Interval.HOUR in intervals
        assert Interval.MINUTE in intervals
        assert len(intervals) == 3
        
    def test_is_support_interval(self):
        """测试时间间隔支持检查"""
        # Arrange
        downloader = VnpyStockDownloader()
        
        # Act & Assert
        assert downloader.is_support_interval(Interval.DAILY) is True
        assert downloader.is_support_interval(Interval.HOUR) is True
        assert downloader.is_support_interval(Interval.MINUTE) is True
        
    def test_is_support_interval_unsupported(self):
        """测试不支持的时间间隔"""
        # Arrange
        downloader = VnpyStockDownloader()
        
        # Act & Assert
        assert downloader.is_support_interval(Interval.WEEKLY) is False
        
    def test_get_supported_exchanges(self):
        """测试获取支持的交易所"""
        # Arrange
        downloader = VnpyStockDownloader()
        
        # Act
        exchanges = downloader.get_supported_exchanges()
        
        # Assert
        assert Exchange.NYSE in exchanges
        assert Exchange.NASDAQ in exchanges
        assert Exchange.AMEX in exchanges
        assert Exchange.SMART in exchanges
        assert len(exchanges) == 4
        
    @pytest.mark.parametrize("interval", [Interval.DAILY, Interval.HOUR, Interval.MINUTE])
    def test_supported_intervals_parametrized(self, interval):
        """参数化测试支持的时间间隔"""
        # Arrange
        downloader = VnpyStockDownloader()
        
        # Act
        intervals = downloader.get_supported_intervals()
        
        # Assert
        assert interval in intervals
        
    @pytest.mark.parametrize("exchange", [Exchange.NYSE, Exchange.NASDAQ, Exchange.AMEX, Exchange.SMART])
    def test_supported_exchanges_parametrized(self, exchange):
        """参数化测试支持的交易所"""
        # Arrange
        downloader = VnpyStockDownloader()
        
        # Act
        exchanges = downloader.get_supported_exchanges()
        
        # Assert
        assert exchange in exchanges
        
    def test_history_request_creation(self, mock_vnpy_datafeed):
        """测试HistoryRequest对象的创建"""
        # Arrange
        downloader = VnpyStockDownloader()
        downloader.datafeed = mock_vnpy_datafeed
        mock_vnpy_datafeed.query_bar_history.return_value = []
        
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
        mock_vnpy_datafeed.query_bar_history.assert_called_once()
        call_args = mock_vnpy_datafeed.query_bar_history.call_args[0][0]
        
        assert isinstance(call_args, HistoryRequest)
        assert call_args.symbol == "AAPL"
        assert call_args.exchange == Exchange.NYSE
        assert call_args.start == datetime(2023, 1, 1)
        assert call_args.end == datetime(2023, 12, 31)
        assert call_args.interval == Interval.HOUR
        
    @patch('dataloader.vnpy_downloader.SETTINGS')
    @patch('dataloader.vnpy_downloader.get_datafeed')
    def test_init_connection_settings_handling(self, mock_get_datafeed, mock_settings, mock_vnpy_datafeed):
        """测试连接初始化时的设置处理"""
        # Arrange
        downloader = VnpyStockDownloader()
        mock_get_datafeed.return_value = mock_vnpy_datafeed
        mock_vnpy_datafeed.init.return_value = True
        
        # Act
        result = downloader.init_connection(
            datafeed_name="wind",
            username="test_user",
            password="test_password",
            extra_param="extra_value"
        )
        
        # Assert
        assert result is True
        
        # 验证设置被正确配置
        expected_calls = [
            (("datafeed.name", "wind"),),
            (("datafeed.username", "test_user"),),
            (("datafeed.password", "test_password"),)
        ]
        
        actual_calls = mock_settings.__setitem__.call_args_list
        for expected_call in expected_calls:
            assert expected_call in actual_calls
            
    @patch('dataloader.vnpy_downloader.get_datafeed')
    def test_init_connection_minimal_params(self, mock_get_datafeed, mock_vnpy_datafeed):
        """测试最小参数的连接初始化"""
        # Arrange
        downloader = VnpyStockDownloader()
        mock_get_datafeed.return_value = mock_vnpy_datafeed
        mock_vnpy_datafeed.init.return_value = True
        
        # Act
        result = downloader.init_connection()
        
        # Assert
        assert result is True
        assert downloader.datafeed == mock_vnpy_datafeed 