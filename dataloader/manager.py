"""
股票数据管理器

统一管理多个数据源的股票数据下载和数据库存储功能。
"""

from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

from .base import BaseStockDownloader, DownloadRequest, DownloadResult, DataSource
from .vnpy_downloader import VnpyStockDownloader
from .yfinance_downloader import YfinanceStockDownloader
from .akshare_downloader import AkshareStockDownloader


class StockDataManager:
    """股票数据管理器"""
    
    def __init__(self):
        """初始化"""
        self.downloaders: Dict[DataSource, BaseStockDownloader] = {}
        self.database = None
        self._init_downloaders()
        
    def _init_downloaders(self) -> None:
        """初始化所有下载器"""
        self.downloaders[DataSource.VNPY] = VnpyStockDownloader()
        self.downloaders[DataSource.YFINANCE] = YfinanceStockDownloader()
        self.downloaders[DataSource.AKSHARE] = AkshareStockDownloader()
        
    def init_database(self, **kwargs) -> bool:
        """
        初始化数据库连接
        
        Args:
            **kwargs: 数据库连接参数
            
        Returns:
            bool: 是否初始化成功
        """
        try:
            self.database = get_database()
            return True
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            return False
            
    def init_datasource(self, source: DataSource, **kwargs) -> bool:
        """
        初始化指定数据源
        
        Args:
            source: 数据源类型
            **kwargs: 数据源连接参数
            
        Returns:
            bool: 是否初始化成功
        """
        if source not in self.downloaders:
            print(f"不支持的数据源: {source}")
            return False
            
        downloader = self.downloaders[source]
        return downloader.init_connection(**kwargs)
        
    def download_stock_data(self, 
                           symbol: str,
                           source: DataSource = DataSource.YFINANCE,
                           exchange: Exchange = Exchange.NYSE,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           interval: Interval = Interval.DAILY,
                           save_to_db: bool = True) -> DownloadResult:
        """
        下载单个股票数据
        
        Args:
            symbol: 股票代码
            source: 数据源
            exchange: 交易所
            start_date: 开始时间
            end_date: 结束时间  
            interval: 时间间隔
            save_to_db: 是否保存到数据库
            
        Returns:
            DownloadResult: 下载结果
        """
        # 检查数据源是否可用
        if source not in self.downloaders:
            return DownloadResult(
                request=DownloadRequest(symbol, exchange, start_date, end_date, interval),
                bars=[],
                success=False,
                error_msg=f"不支持的数据源: {source}"
            )
            
        downloader = self.downloaders[source]
        
        # 创建下载请求
        request = DownloadRequest(
            symbol=symbol,
            exchange=exchange,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        # 执行下载
        result = downloader.download_bars(request)
        
        # 保存到数据库
        if save_to_db and result.success and result.bars:
            if not self.database:
                self.init_database()
                
            if self.database:
                try:
                    success = self.database.save_bar_data(result.bars)
                    if success:
                        print(f"数据已保存到数据库: {symbol}, 数量: {len(result.bars)}")
                    else:
                        print(f"数据保存失败: {symbol}")
                except Exception as e:
                    print(f"数据保存异常: {symbol}, 错误: {e}")
                    
        return result
        
    def download_multiple_stocks(self,
                                symbols: List[str],
                                source: DataSource = DataSource.YFINANCE,
                                exchange: Exchange = Exchange.NYSE,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None,
                                interval: Interval = Interval.DAILY,
                                save_to_db: bool = True) -> List[DownloadResult]:
        """
        批量下载多个股票数据
        
        Args:
            symbols: 股票代码列表
            source: 数据源
            exchange: 交易所
            start_date: 开始时间
            end_date: 结束时间
            interval: 时间间隔
            save_to_db: 是否保存到数据库
            
        Returns:
            List[DownloadResult]: 下载结果列表
        """
        results = []
        
        for symbol in symbols:
            print(f"正在下载 {symbol} 数据...")
            result = self.download_stock_data(
                symbol=symbol,
                source=source,
                exchange=exchange,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                save_to_db=save_to_db
            )
            results.append(result)
            
            if result.success:
                print(f"✓ {symbol} 下载成功，数据量: {result.total_count}")
            else:
                print(f"✗ {symbol} 下载失败: {result.error_msg}")
                
        return results
        
    def get_downloader_info(self, source: DataSource) -> Dict:
        """
        获取下载器信息
        
        Args:
            source: 数据源
            
        Returns:
            Dict: 下载器信息
        """
        if source not in self.downloaders:
            return {}
            
        downloader = self.downloaders[source]
        return {
            "name": downloader.name,
            "source": downloader.source.value,
            "supported_intervals": [interval.value for interval in downloader.get_supported_intervals()],
            "supported_exchanges": [exchange.value for exchange in downloader.get_supported_exchanges()]
        }
        
    def list_all_downloaders(self) -> Dict[str, Dict]:
        """
        列出所有可用的下载器信息
        
        Returns:
            Dict[str, Dict]: 所有下载器信息
        """
        info = {}
        for source in DataSource:
            info[source.value] = self.get_downloader_info(source)
        return info
        
    def validate_download_request(self, 
                                 symbol: str,
                                 source: DataSource,
                                 exchange: Exchange,
                                 interval: Interval) -> tuple[bool, str]:
        """
        验证下载请求是否有效
        
        Args:
            symbol: 股票代码
            source: 数据源
            exchange: 交易所
            interval: 时间间隔
            
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        if source not in self.downloaders:
            return False, f"不支持的数据源: {source}"
            
        downloader = self.downloaders[source]
        
        # 检查交易所支持
        if exchange not in downloader.get_supported_exchanges():
            return False, f"数据源 {source.value} 不支持交易所 {exchange.value}"
            
        # 检查时间间隔支持
        if not downloader.is_support_interval(interval):
            return False, f"数据源 {source.value} 不支持时间间隔 {interval.value}"
            
        return True, ""
        
    def get_database_overview(self) -> List:
        """
        获取数据库中的数据概览
        
        Returns:
            List: 数据概览
        """
        if not self.database:
            self.init_database()
            
        if self.database:
            try:
                return self.database.get_bar_overview()
            except Exception as e:
                print(f"获取数据库概览失败: {e}")
                
        return []
        
    def delete_stock_data(self, symbol: str, exchange: Exchange, interval: Interval) -> bool:
        """
        删除指定股票的数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间间隔
            
        Returns:
            bool: 是否删除成功
        """
        if not self.database:
            self.init_database()
            
        if self.database:
            try:
                count = self.database.delete_bar_data(symbol, exchange, interval)
                print(f"已删除 {symbol}.{exchange.value} {interval.value} 数据，数量: {count}")
                return True
            except Exception as e:
                print(f"删除数据失败: {e}")
                
        return False
        
    def __str__(self) -> str:
        """字符串表示"""
        return f"StockDataManager(数据源数量: {len(self.downloaders)})" 