"""
__init__.py模块的单元测试

测试dataloader模块的导入功能和__all__定义
"""

import pytest


class TestDataloaderInit:
    """测试dataloader模块初始化"""
    
    def test_import_base_classes(self):
        """测试基础类的导入"""
        # Act & Assert
        from dataloader import BaseStockDownloader, DownloadRequest, DownloadResult
        
        assert BaseStockDownloader is not None
        assert DownloadRequest is not None
        assert DownloadResult is not None
        
    def test_import_downloader_classes(self):
        """测试下载器类的导入"""
        # Act & Assert
        from dataloader import (
            VnpyStockDownloader,
            YfinanceStockDownloader,
            AkshareStockDownloader
        )
        
        assert VnpyStockDownloader is not None
        assert YfinanceStockDownloader is not None
        assert AkshareStockDownloader is not None
        
    def test_import_manager_class(self):
        """测试管理器类的导入"""
        # Act & Assert
        from dataloader import StockDataManager
        
        assert StockDataManager is not None
        
    def test_import_all_exports(self):
        """测试所有导出项的导入"""
        # Act
        import dataloader
        
        # Assert
        expected_exports = [
            "BaseStockDownloader",
            "DownloadRequest", 
            "DownloadResult",
            "VnpyStockDownloader",
            "YfinanceStockDownloader", 
            "AkshareStockDownloader",
            "StockDataManager"
        ]
        
        assert hasattr(dataloader, '__all__')
        assert dataloader.__all__ == expected_exports
        
        # 验证所有导出项都可以访问
        for export in expected_exports:
            assert hasattr(dataloader, export)
            assert getattr(dataloader, export) is not None
            
    def test_module_docstring(self):
        """测试模块文档字符串"""
        # Act
        import dataloader
        
        # Assert
        assert dataloader.__doc__ is not None
        assert "美股股票数据下载器" in dataloader.__doc__
        assert "支持多种数据源" in dataloader.__doc__
        
    def test_downloader_classes_instantiation(self):
        """测试下载器类的实例化"""
        # Arrange
        from dataloader import (
            VnpyStockDownloader,
            YfinanceStockDownloader,
            AkshareStockDownloader
        )
        
        # Act & Assert
        vnpy_downloader = VnpyStockDownloader()
        assert vnpy_downloader.name == "VnpyStockDownloader"
        
        yfinance_downloader = YfinanceStockDownloader()
        assert yfinance_downloader.name == "YfinanceStockDownloader"
        
        akshare_downloader = AkshareStockDownloader()
        assert akshare_downloader.name == "AkshareStockDownloader"
        
    def test_manager_class_instantiation(self):
        """测试管理器类的实例化"""
        # Arrange
        from dataloader import StockDataManager
        
        # Act
        manager = StockDataManager()
        
        # Assert
        assert manager is not None
        assert hasattr(manager, 'downloaders')
        assert len(manager.downloaders) == 3
        
    def test_data_classes_instantiation(self):
        """测试数据类的实例化"""
        # Arrange
        from dataloader import DownloadRequest, DownloadResult
        from vnpy.trader.constant import Exchange, Interval
        
        # Act
        request = DownloadRequest(symbol="AAPL", exchange=Exchange.NYSE)
        result = DownloadResult(request=request, bars=[])
        
        # Assert
        assert request.symbol == "AAPL"
        assert request.exchange == Exchange.NYSE
        assert request.vt_symbol == "AAPL.NYSE"
        
        assert result.request == request
        assert result.bars == []
        assert result.success is False
        
    def test_all_imports_in_one_statement(self):
        """测试一次性导入所有类"""
        # Act & Assert
        from dataloader import (
            BaseStockDownloader,
            DownloadRequest, 
            DownloadResult,
            VnpyStockDownloader,
            YfinanceStockDownloader, 
            AkshareStockDownloader,
            StockDataManager
        )
        
        # 验证所有类都存在
        classes = [
            BaseStockDownloader,
            DownloadRequest, 
            DownloadResult,
            VnpyStockDownloader,
            YfinanceStockDownloader, 
            AkshareStockDownloader,
            StockDataManager
        ]
        
        for cls in classes:
            assert cls is not None
            
    def test_import_star(self):
        """测试星号导入"""
        # Act
        namespace = {}
        exec("from dataloader import *", namespace)
        
        # Assert
        expected_exports = [
            "BaseStockDownloader",
            "DownloadRequest", 
            "DownloadResult",
            "VnpyStockDownloader",
            "YfinanceStockDownloader", 
            "AkshareStockDownloader",
            "StockDataManager"
        ]
        
        for export in expected_exports:
            assert export in namespace
            assert namespace[export] is not None 