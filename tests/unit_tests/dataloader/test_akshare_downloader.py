"""
akshare_downloader.py模块的单元测试

测试AkshareStockDownloader类的所有功能方法
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

from dataloader.base import DataSource, DownloadRequest, DownloadResult
from dataloader.akshare_downloader import AkshareStockDownloader


class TestAkshareStockDownloader:
    """测试AkshareStockDownloader类"""
    
    def test_akshare_downloader_initialization(self):
        """测试akshare下载器初始化"""
        # Act
        downloader = AkshareStockDownloader()
        
        # Assert
        assert downloader.name == "AkshareStockDownloader"
        assert downloader.source == DataSource.AKSHARE
        assert downloader.ak is None
        
    @patch('dataloader.akshare_downloader.akshare')
    def test_init_connection_success(self, mock_ak):
        """测试akshare连接初始化成功"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # Act
        result = downloader.init_connection()
        
        # Assert
        assert result is True
        assert downloader.ak == mock_ak
        
    def test_init_connection_import_error(self):
        """测试akshare库未安装的情况"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # Act
        with patch('dataloader.akshare_downloader.akshare', side_effect=ImportError()):
            result = downloader.init_connection()
        
        # Assert
        assert result is False
        assert downloader.ak is None
        
    def test_init_connection_general_error(self):
        """测试akshare初始化一般错误"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # Act
        with patch('dataloader.akshare_downloader.akshare', side_effect=Exception("初始化失败")):
            result = downloader.init_connection()
        
        # Assert
        assert result is False
        assert downloader.ak is None
        
    def test_convert_interval_to_ak(self):
        """测试时间间隔转换为akshare格式"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # Act & Assert
        assert downloader._convert_interval_to_ak(Interval.DAILY) == "daily"
        
    def test_convert_interval_to_ak_unsupported(self):
        """测试不支持的时间间隔转换"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # Act
        result = downloader._convert_interval_to_ak(Interval.MINUTE)
        
        # Assert
        assert result == "daily"  # 默认返回日线
        
    def test_convert_ak_data_to_vnpy_empty_data(self):
        """测试空DataFrame转换"""
        # Arrange
        downloader = AkshareStockDownloader()
        empty_df = pd.DataFrame()
        
        # Act
        bars = downloader._convert_ak_data_to_vnpy(
            empty_df, "AAPL", Exchange.NYSE, Interval.DAILY
        )
        
        # Assert
        assert bars == []
        
    def test_convert_ak_data_to_vnpy_none_data(self):
        """测试None数据转换"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # Act
        bars = downloader._convert_ak_data_to_vnpy(
            None, "AAPL", Exchange.NYSE, Interval.DAILY
        )
        
        # Assert
        assert bars == []
        
    def test_convert_ak_data_to_vnpy_valid_data_with_date_column(self, mock_akshare_data):
        """测试有效akshare数据转换（含date列）"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # Act
        bars = downloader._convert_ak_data_to_vnpy(
            mock_akshare_data, "AAPL", Exchange.NYSE, Interval.DAILY
        )
        
        # Assert
        assert len(bars) == 3
        assert all(isinstance(bar, BarData) for bar in bars)
        assert bars[0].symbol == "AAPL"
        assert bars[0].exchange == Exchange.NYSE
        assert bars[0].interval == Interval.DAILY
        assert bars[0].open_price == 150.0
        assert bars[0].gateway_name == "akshare"
        
    def test_convert_ak_data_to_vnpy_uppercase_columns(self):
        """测试大写列名的akshare数据转换"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        test_data = {
            'Date': ['2023-01-01', '2023-01-02'],
            'Open': [150.0, 151.0],
            'High': [155.0, 156.0],
            'Low': [149.0, 150.0],
            'Close': [152.0, 153.0],
            'Volume': [1000000, 1100000]
        }
        df = pd.DataFrame(test_data)
        
        # Act
        bars = downloader._convert_ak_data_to_vnpy(
            df, "AAPL", Exchange.NYSE, Interval.DAILY
        )
        
        # Assert
        assert len(bars) == 2
        assert bars[0].open_price == 150.0
        
    def test_convert_ak_data_to_vnpy_index_as_date(self):
        """测试使用索引作为日期的akshare数据转换"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        test_data = {
            'open': [150.0],
            'high': [155.0],
            'low': [149.0],
            'close': [152.0],
            'volume': [1000000]
        }
        
        # 使用日期字符串作为索引
        df = pd.DataFrame(test_data, index=['2023-01-01'])
        
        # Act
        bars = downloader._convert_ak_data_to_vnpy(
            df, "AAPL", Exchange.NYSE, Interval.DAILY
        )
        
        # Assert
        assert len(bars) == 1
        assert bars[0].open_price == 150.0
        
    def test_convert_ak_data_to_vnpy_yyyymmdd_format(self):
        """测试YYYYMMDD格式日期的akshare数据转换"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        test_data = {
            'date': ['20230101'],
            'open': [150.0],
            'high': [155.0],
            'low': [149.0],
            'close': [152.0],
            'volume': [1000000]
        }
        df = pd.DataFrame(test_data)
        
        # Act
        bars = downloader._convert_ak_data_to_vnpy(
            df, "AAPL", Exchange.NYSE, Interval.DAILY
        )
        
        # Assert
        assert len(bars) == 1
        assert bars[0].open_price == 150.0
        
    def test_convert_ak_data_to_vnpy_conversion_error(self):
        """测试数据转换过程中发生错误"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # 创建有问题的数据（价格为字符串）
        test_data = {
            'date': ['2023-01-01'],
            'open': ['invalid'],  # 无效的价格数据
            'high': [155.0],
            'low': [149.0],
            'close': [152.0],
            'volume': [1000000]
        }
        df = pd.DataFrame(test_data)
        
        # Act
        bars = downloader._convert_ak_data_to_vnpy(
            df, "AAPL", Exchange.NYSE, Interval.DAILY
        )
        
        # Assert
        assert bars == []  # 转换失败应返回空列表
        
    def test_download_bars_not_initialized(self, sample_download_request):
        """测试akshare未初始化时下载数据"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is False
        assert "akshare未初始化" in result.error_msg
        
    def test_download_bars_invalid_request(self):
        """测试无效请求下载数据"""
        # Arrange
        downloader = AkshareStockDownloader()
        downloader.ak = Mock()
        
        invalid_request = DownloadRequest(
            symbol="",  # 空股票代码
            exchange=Exchange.NYSE
        )
        
        # Act
        result = downloader.download_bars(invalid_request)
        
        # Assert
        assert result.success is False
        assert "股票代码不能为空" in result.error_msg
        
    def test_download_bars_unsupported_interval(self):
        """测试不支持的时间间隔"""
        # Arrange
        downloader = AkshareStockDownloader()
        downloader.ak = Mock()
        
        request = DownloadRequest(
            symbol="AAPL",
            exchange=Exchange.NYSE,
            interval=Interval.MINUTE  # akshare不支持分钟线
        )
        
        # Act
        result = downloader.download_bars(request)
        
        # Assert
        assert result.success is False
        assert "仅支持日线数据" in result.error_msg
        
    @patch('dataloader.akshare_downloader.akshare')
    def test_download_bars_success(self, mock_ak, sample_download_request, mock_akshare_data):
        """测试成功下载数据"""
        # Arrange
        downloader = AkshareStockDownloader()
        downloader.ak = mock_ak
        mock_ak.stock_us_hist.return_value = mock_akshare_data
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is True
        assert len(result.bars) > 0
        mock_ak.stock_us_hist.assert_called_once_with(symbol="AAPL")
        
    @patch('dataloader.akshare_downloader.akshare')
    def test_download_bars_fallback_api(self, mock_ak, sample_download_request, mock_akshare_data):
        """测试API回退机制"""
        # Arrange
        downloader = AkshareStockDownloader()
        downloader.ak = mock_ak
        
        # 第一个API不可用，回退到第二个
        mock_ak.stock_us_hist.side_effect = AttributeError("API不存在")
        mock_ak.stock_us_daily.return_value = mock_akshare_data
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is True
        mock_ak.stock_us_hist.assert_called_once()
        mock_ak.stock_us_daily.assert_called_once_with(symbol="AAPL")
        
    @patch('dataloader.akshare_downloader.akshare')
    def test_download_bars_both_apis_unavailable(self, mock_ak, sample_download_request):
        """测试两个API都不可用"""
        # Arrange
        downloader = AkshareStockDownloader()
        downloader.ak = mock_ak
        
        # 两个API都不可用
        mock_ak.stock_us_hist.side_effect = AttributeError("API不存在")
        mock_ak.stock_us_daily.side_effect = AttributeError("API不存在")
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is False
        assert "akshare美股数据接口不可用" in result.error_msg
        
    @patch('dataloader.akshare_downloader.akshare')
    def test_download_bars_with_date_range(self, mock_ak, mock_akshare_data):
        """测试带日期范围的数据下载"""
        # Arrange
        downloader = AkshareStockDownloader()
        downloader.ak = mock_ak
        
        # 创建有日期列的DataFrame
        test_df = mock_akshare_data.copy()
        test_df['date'] = pd.to_datetime(test_df['date'])
        mock_ak.stock_us_hist.return_value = test_df
        
        request = DownloadRequest(
            symbol="AAPL",
            exchange=Exchange.NYSE,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 2),
            interval=Interval.DAILY
        )
        
        # Act
        result = downloader.download_bars(request)
        
        # Assert
        assert result.success is True
        
    @patch('dataloader.akshare_downloader.akshare')
    def test_download_bars_empty_result(self, mock_ak, sample_download_request):
        """测试下载空结果"""
        # Arrange
        downloader = AkshareStockDownloader()
        downloader.ak = mock_ak
        mock_ak.stock_us_hist.return_value = pd.DataFrame()  # 空DataFrame
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is False
        assert "未获取到数据" in result.error_msg
        
    @patch('dataloader.akshare_downloader.akshare')
    def test_download_bars_exception(self, mock_ak, sample_download_request):
        """测试下载过程中发生异常"""
        # Arrange
        downloader = AkshareStockDownloader()
        downloader.ak = mock_ak
        mock_ak.stock_us_hist.side_effect = Exception("网络错误")
        
        # Act
        result = downloader.download_bars(sample_download_request)
        
        # Assert
        assert result.success is False
        assert "akshare数据下载失败" in result.error_msg
        assert "网络错误" in result.error_msg
        
    def test_get_supported_intervals(self):
        """测试获取支持的时间间隔"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # Act
        intervals = downloader.get_supported_intervals()
        
        # Assert
        assert Interval.DAILY in intervals
        assert len(intervals) == 1  # akshare仅支持日线
        
    def test_is_support_interval(self):
        """测试时间间隔支持检查"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # Act & Assert
        assert downloader.is_support_interval(Interval.DAILY) is True
        assert downloader.is_support_interval(Interval.HOUR) is False
        assert downloader.is_support_interval(Interval.MINUTE) is False
        
    def test_get_supported_exchanges(self):
        """测试获取支持的交易所"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # Act
        exchanges = downloader.get_supported_exchanges()
        
        # Assert
        assert Exchange.NYSE in exchanges
        assert Exchange.NASDAQ in exchanges
        assert Exchange.AMEX in exchanges
        assert len(exchanges) == 3
        
    @pytest.mark.parametrize("exchange", [Exchange.NYSE, Exchange.NASDAQ, Exchange.AMEX])
    def test_supported_exchanges_parametrized(self, exchange):
        """参数化测试支持的交易所"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # Act
        exchanges = downloader.get_supported_exchanges()
        
        # Assert
        assert exchange in exchanges
        
    def test_date_format_conversion_edge_cases(self):
        """测试日期格式转换的边缘情况"""
        # Arrange
        downloader = AkshareStockDownloader()
        
        # 测试各种日期格式
        test_cases = [
            {
                'data': {'date': ['20230101'], 'open': [150.0], 'high': [155.0], 'low': [149.0], 'close': [152.0], 'volume': [1000000]},
                'description': 'YYYYMMDD格式'
            },
            {
                'data': {'Date': ['2023-01-01'], 'Open': [150.0], 'High': [155.0], 'Low': [149.0], 'Close': [152.0], 'Volume': [1000000]},
                'description': '大写列名格式'
            }
        ]
        
        for case in test_cases:
            df = pd.DataFrame(case['data'])
            
            # Act
            bars = downloader._convert_ak_data_to_vnpy(
                df, "AAPL", Exchange.NYSE, Interval.DAILY
            )
            
            # Assert
            assert len(bars) == 1, f"失败的测试用例: {case['description']}"
            assert bars[0].open_price == 150.0, f"失败的测试用例: {case['description']}" 