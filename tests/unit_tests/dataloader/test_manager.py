"""
manager.py模块的单元测试

测试StockDataManager类的所有功能方法
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

from dataloader.base import DataSource, DownloadRequest, DownloadResult
from dataloader.manager import StockDataManager


class TestStockDataManager:
    """测试StockDataManager类"""
    
    def test_stock_data_manager_initialization(self):
        """测试数据管理器初始化"""
        # Act
        manager = StockDataManager()
        
        # Assert
        assert manager.database is None
        assert len(manager.downloaders) == 3
        assert DataSource.VNPY in manager.downloaders
        assert DataSource.YFINANCE in manager.downloaders
        assert DataSource.AKSHARE in manager.downloaders
        
    @patch('dataloader.manager.get_database')
    def test_init_database_success(self, mock_get_database, mock_database):
        """测试数据库初始化成功"""
        # Arrange
        manager = StockDataManager()
        mock_get_database.return_value = mock_database
        
        # Act
        result = manager.init_database()
        
        # Assert
        assert result is True
        assert manager.database == mock_database
        mock_get_database.assert_called_once()
        
    @patch('dataloader.manager.get_database')
    def test_init_database_failure(self, mock_get_database):
        """测试数据库初始化失败"""
        # Arrange
        manager = StockDataManager()
        mock_get_database.side_effect = Exception("数据库连接失败")
        
        # Act
        result = manager.init_database()
        
        # Assert
        assert result is False
        assert manager.database is None
        
    def test_init_datasource_success(self):
        """测试数据源初始化成功"""
        # Arrange
        manager = StockDataManager()
        mock_downloader = Mock()
        mock_downloader.init_connection.return_value = True
        manager.downloaders[DataSource.YFINANCE] = mock_downloader
        
        # Act
        result = manager.init_datasource(DataSource.YFINANCE, api_key="test")
        
        # Assert
        assert result is True
        mock_downloader.init_connection.assert_called_once_with(api_key="test")
        
    def test_init_datasource_unsupported(self):
        """测试初始化不支持的数据源"""
        # Arrange
        manager = StockDataManager()
        invalid_source = "invalid_source"
        
        # Act & Assert
        with pytest.raises(AttributeError):
            manager.init_datasource(invalid_source)
            
    def test_init_datasource_failure(self):
        """测试数据源初始化失败"""
        # Arrange
        manager = StockDataManager()
        mock_downloader = Mock()
        mock_downloader.init_connection.return_value = False
        manager.downloaders[DataSource.YFINANCE] = mock_downloader
        
        # Act
        result = manager.init_datasource(DataSource.YFINANCE)
        
        # Assert
        assert result is False
        
    def test_download_stock_data_success(self, sample_bar_data_list, mock_database):
        """测试单个股票数据下载成功"""
        # Arrange
        manager = StockDataManager()
        manager.database = mock_database
        
        # 模拟下载器
        mock_downloader = Mock()
        mock_result = DownloadResult(
            request=DownloadRequest("AAPL", Exchange.NYSE),
            bars=sample_bar_data_list,
            success=True
        )
        mock_downloader.download_bars.return_value = mock_result
        manager.downloaders[DataSource.YFINANCE] = mock_downloader
        
        # Act
        result = manager.download_stock_data(
            symbol="AAPL",
            source=DataSource.YFINANCE,
            save_to_db=True
        )
        
        # Assert
        assert result.success is True
        assert len(result.bars) == len(sample_bar_data_list)
        mock_downloader.download_bars.assert_called_once()
        mock_database.save_bar_data.assert_called_once_with(sample_bar_data_list)
        
    def test_download_stock_data_unsupported_source(self):
        """测试下载不支持的数据源"""
        # Arrange
        manager = StockDataManager()
        # 清空下载器字典模拟不支持的数据源
        manager.downloaders.clear()
        
        # Act
        result = manager.download_stock_data(
            symbol="AAPL",
            source=DataSource.YFINANCE
        )
        
        # Assert
        assert result.success is False
        assert "不支持的数据源" in result.error_msg
        
    @patch('dataloader.manager.get_database')
    def test_download_stock_data_save_to_db_auto_init(self, mock_get_database, 
                                                     sample_bar_data_list, mock_database):
        """测试下载数据时自动初始化数据库"""
        # Arrange
        manager = StockDataManager()
        mock_get_database.return_value = mock_database
        
        mock_downloader = Mock()
        mock_result = DownloadResult(
            request=DownloadRequest("AAPL", Exchange.NYSE),
            bars=sample_bar_data_list,
            success=True
        )
        mock_downloader.download_bars.return_value = mock_result
        manager.downloaders[DataSource.YFINANCE] = mock_downloader
        
        # Act
        result = manager.download_stock_data(
            symbol="AAPL",
            source=DataSource.YFINANCE,
            save_to_db=True
        )
        
        # Assert
        assert result.success is True
        mock_get_database.assert_called_once()
        mock_database.save_bar_data.assert_called_once()
        
    def test_download_stock_data_save_failure(self, sample_bar_data_list, mock_database):
        """测试数据保存失败的情况"""
        # Arrange
        manager = StockDataManager()
        manager.database = mock_database
        mock_database.save_bar_data.side_effect = Exception("保存失败")
        
        mock_downloader = Mock()
        mock_result = DownloadResult(
            request=DownloadRequest("AAPL", Exchange.NYSE),
            bars=sample_bar_data_list,
            success=True
        )
        mock_downloader.download_bars.return_value = mock_result
        manager.downloaders[DataSource.YFINANCE] = mock_downloader
        
        # Act
        result = manager.download_stock_data(
            symbol="AAPL",
            source=DataSource.YFINANCE,
            save_to_db=True
        )
        
        # Assert
        assert result.success is True  # 下载成功，保存失败不影响返回结果
        
    def test_download_multiple_stocks_success(self, sample_bar_data_list):
        """测试批量下载多个股票成功"""
        # Arrange
        manager = StockDataManager()
        symbols = ["AAPL", "MSFT", "GOOGL"]
        
        mock_downloader = Mock()
        mock_result = DownloadResult(
            request=DownloadRequest("AAPL", Exchange.NYSE),
            bars=sample_bar_data_list,
            success=True
        )
        mock_downloader.download_bars.return_value = mock_result
        manager.downloaders[DataSource.YFINANCE] = mock_downloader
        
        # Act
        results = manager.download_multiple_stocks(
            symbols=symbols,
            source=DataSource.YFINANCE,
            save_to_db=False
        )
        
        # Assert
        assert len(results) == len(symbols)
        assert all(result.success for result in results)
        assert mock_downloader.download_bars.call_count == len(symbols)
        
    def test_download_multiple_stocks_mixed_results(self, sample_bar_data_list):
        """测试批量下载多个股票的混合结果"""
        # Arrange
        manager = StockDataManager()
        symbols = ["AAPL", "INVALID"]
        
        mock_downloader = Mock()
        # 第一个成功，第二个失败
        mock_downloader.download_bars.side_effect = [
            DownloadResult(
                request=DownloadRequest("AAPL", Exchange.NYSE),
                bars=sample_bar_data_list,
                success=True
            ),
            DownloadResult(
                request=DownloadRequest("INVALID", Exchange.NYSE),
                bars=[],
                success=False,
                error_msg="股票代码不存在"
            )
        ]
        manager.downloaders[DataSource.YFINANCE] = mock_downloader
        
        # Act
        results = manager.download_multiple_stocks(
            symbols=symbols,
            source=DataSource.YFINANCE,
            save_to_db=False
        )
        
        # Assert
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        
    def test_get_downloader_info_valid_source(self):
        """测试获取有效数据源的下载器信息"""
        # Arrange
        manager = StockDataManager()
        mock_downloader = Mock()
        mock_downloader.name = "TestDownloader"
        mock_downloader.source = DataSource.YFINANCE
        mock_downloader.get_supported_intervals.return_value = [Interval.DAILY]
        mock_downloader.get_supported_exchanges.return_value = [Exchange.NYSE]
        manager.downloaders[DataSource.YFINANCE] = mock_downloader
        
        # Act
        info = manager.get_downloader_info(DataSource.YFINANCE)
        
        # Assert
        assert info["name"] == "TestDownloader"
        assert info["source"] == "yfinance"
        assert info["supported_intervals"] == ["1d"]
        assert info["supported_exchanges"] == ["NYSE"]
        
    def test_get_downloader_info_invalid_source(self):
        """测试获取无效数据源的下载器信息"""
        # Arrange
        manager = StockDataManager()
        manager.downloaders.clear()
        
        # Act
        info = manager.get_downloader_info(DataSource.YFINANCE)
        
        # Assert
        assert info == {}
        
    def test_list_all_downloaders(self):
        """测试列出所有下载器信息"""
        # Arrange
        manager = StockDataManager()
        
        # 模拟下载器信息
        for source in DataSource:
            mock_downloader = Mock()
            mock_downloader.name = f"{source.value}_downloader"
            mock_downloader.source = source
            mock_downloader.get_supported_intervals.return_value = [Interval.DAILY]
            mock_downloader.get_supported_exchanges.return_value = [Exchange.NYSE]
            manager.downloaders[source] = mock_downloader
        
        # Act
        all_info = manager.list_all_downloaders()
        
        # Assert
        assert len(all_info) == len(DataSource)
        for source in DataSource:
            assert source.value in all_info
            assert all_info[source.value]["name"] == f"{source.value}_downloader"
            
    def test_validate_download_request_valid(self):
        """测试有效下载请求的验证"""
        # Arrange
        manager = StockDataManager()
        mock_downloader = Mock()
        mock_downloader.get_supported_exchanges.return_value = [Exchange.NYSE]
        mock_downloader.is_support_interval.return_value = True
        manager.downloaders[DataSource.YFINANCE] = mock_downloader
        
        # Act
        is_valid, error_msg = manager.validate_download_request(
            symbol="AAPL",
            source=DataSource.YFINANCE,
            exchange=Exchange.NYSE,
            interval=Interval.DAILY
        )
        
        # Assert
        assert is_valid is True
        assert error_msg == ""
        
    def test_validate_download_request_unsupported_source(self):
        """测试不支持数据源的请求验证"""
        # Arrange
        manager = StockDataManager()
        manager.downloaders.clear()
        
        # Act
        is_valid, error_msg = manager.validate_download_request(
            symbol="AAPL",
            source=DataSource.YFINANCE,
            exchange=Exchange.NYSE,
            interval=Interval.DAILY
        )
        
        # Assert
        assert is_valid is False
        assert "不支持的数据源" in error_msg
        
    def test_validate_download_request_unsupported_exchange(self):
        """测试不支持交易所的请求验证"""
        # Arrange
        manager = StockDataManager()
        mock_downloader = Mock()
        mock_downloader.get_supported_exchanges.return_value = [Exchange.NYSE]
        manager.downloaders[DataSource.YFINANCE] = mock_downloader
        
        # Act
        is_valid, error_msg = manager.validate_download_request(
            symbol="AAPL",
            source=DataSource.YFINANCE,
            exchange=Exchange.SSE,  # 不支持的交易所
            interval=Interval.DAILY
        )
        
        # Assert
        assert is_valid is False
        assert "不支持交易所" in error_msg
        
    def test_validate_download_request_unsupported_interval(self):
        """测试不支持时间间隔的请求验证"""
        # Arrange
        manager = StockDataManager()
        mock_downloader = Mock()
        mock_downloader.get_supported_exchanges.return_value = [Exchange.NYSE]
        mock_downloader.is_support_interval.return_value = False
        manager.downloaders[DataSource.YFINANCE] = mock_downloader
        
        # Act
        is_valid, error_msg = manager.validate_download_request(
            symbol="AAPL",
            source=DataSource.YFINANCE,
            exchange=Exchange.NYSE,
            interval=Interval.MINUTE
        )
        
        # Assert
        assert is_valid is False
        assert "不支持时间间隔" in error_msg
        
    @patch('dataloader.manager.get_database')
    def test_get_database_overview_success(self, mock_get_database, mock_database):
        """测试获取数据库概览成功"""
        # Arrange
        manager = StockDataManager()
        mock_get_database.return_value = mock_database
        mock_overview = ["AAPL.NYSE", "MSFT.NASDAQ"]
        mock_database.get_bar_overview.return_value = mock_overview
        
        # Act
        overview = manager.get_database_overview()
        
        # Assert
        assert overview == mock_overview
        mock_database.get_bar_overview.assert_called_once()
        
    @patch('dataloader.manager.get_database')
    def test_get_database_overview_failure(self, mock_get_database, mock_database):
        """测试获取数据库概览失败"""
        # Arrange
        manager = StockDataManager()
        mock_get_database.return_value = mock_database
        mock_database.get_bar_overview.side_effect = Exception("查询失败")
        
        # Act
        overview = manager.get_database_overview()
        
        # Assert
        assert overview == []
        
    @patch('dataloader.manager.get_database')
    def test_delete_stock_data_success(self, mock_get_database, mock_database):
        """测试删除股票数据成功"""
        # Arrange
        manager = StockDataManager()
        mock_get_database.return_value = mock_database
        mock_database.delete_bar_data.return_value = 100  # 删除了100条数据
        
        # Act
        result = manager.delete_stock_data("AAPL", Exchange.NYSE, Interval.DAILY)
        
        # Assert
        assert result is True
        mock_database.delete_bar_data.assert_called_once_with("AAPL", Exchange.NYSE, Interval.DAILY)
        
    @patch('dataloader.manager.get_database')
    def test_delete_stock_data_failure(self, mock_get_database, mock_database):
        """测试删除股票数据失败"""
        # Arrange
        manager = StockDataManager()
        mock_get_database.return_value = mock_database
        mock_database.delete_bar_data.side_effect = Exception("删除失败")
        
        # Act
        result = manager.delete_stock_data("AAPL", Exchange.NYSE, Interval.DAILY)
        
        # Assert
        assert result is False
        
    def test_str_representation(self):
        """测试字符串表示"""
        # Arrange
        manager = StockDataManager()
        
        # Act
        str_repr = str(manager)
        
        # Assert
        assert "StockDataManager" in str_repr
        assert "数据源数量: 3" in str_repr
        
    @pytest.mark.parametrize("source", list(DataSource))
    def test_all_downloaders_initialized(self, source):
        """参数化测试所有数据源下载器都已初始化"""
        # Arrange
        manager = StockDataManager()
        
        # Act & Assert
        assert source in manager.downloaders
        assert manager.downloaders[source] is not None 