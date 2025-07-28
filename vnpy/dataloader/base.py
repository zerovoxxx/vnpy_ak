"""
数据下载器基础模块

定义了数据下载器的抽象基类和相关数据结构。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum

from vnpy.trader.object import BarData
from vnpy.trader.constant import Exchange, Interval


class DataSource(Enum):
    """数据源枚举"""
    VNPY = "vnpy"
    YFINANCE = "yfinance" 
    AKSHARE = "akshare"


@dataclass
class DownloadRequest:
    """数据下载请求"""
    symbol: str                     # 股票代码，如 AAPL
    exchange: Exchange = Exchange.NYSE  # 交易所，默认纽约证券交易所
    start_date: Optional[datetime] = None   # 开始时间
    end_date: Optional[datetime] = None     # 结束时间
    interval: Interval = Interval.DAILY     # 数据间隔
    
    def __post_init__(self):
        """后处理"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass  
class DownloadResult:
    """数据下载结果"""
    request: DownloadRequest        # 原始请求
    bars: List[BarData]            # 下载的K线数据
    success: bool                  # 是否成功
    error_msg: str = ""            # 错误信息
    total_count: int = 0           # 总数据量
    
    def __post_init__(self):
        """后处理"""
        if self.bars:
            self.total_count = len(self.bars)
            self.success = True
        else:
            self.success = False


class BaseStockDownloader(ABC):
    """股票数据下载器抽象基类"""
    
    def __init__(self, name: str):
        """初始化"""
        self.name = name
        self.source = None
        
    @abstractmethod
    def init_connection(self, **kwargs) -> bool:
        """
        初始化连接
        
        Args:
            **kwargs: 连接参数
            
        Returns:
            bool: 是否初始化成功
        """
        pass
        
    @abstractmethod
    def download_bars(self, request: DownloadRequest) -> DownloadResult:
        """
        下载K线数据
        
        Args:
            request: 下载请求
            
        Returns:
            DownloadResult: 下载结果
        """
        pass
        
    def is_support_interval(self, interval: Interval) -> bool:
        """
        检查是否支持指定的时间间隔
        
        Args:
            interval: 时间间隔
            
        Returns:
            bool: 是否支持
        """
        return True
        
    def get_supported_intervals(self) -> List[Interval]:
        """
        获取支持的时间间隔列表
        
        Returns:
            List[Interval]: 支持的时间间隔
        """
        return [Interval.DAILY, Interval.HOUR, Interval.MINUTE]
        
    def get_supported_exchanges(self) -> List[Exchange]:
        """
        获取支持的交易所列表
        
        Returns:
            List[Exchange]: 支持的交易所
        """
        return [
            Exchange.NYSE,      # 纽约证券交易所
            Exchange.NASDAQ,    # 纳斯达克
            Exchange.AMEX,      # 美国证券交易所
        ]
        
    def validate_request(self, request: DownloadRequest) -> tuple[bool, str]:
        """
        验证下载请求
        
        Args:
            request: 下载请求
            
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        # 检查交易所
        if request.exchange not in self.get_supported_exchanges():
            return False, f"不支持的交易所: {request.exchange}"
            
        # 检查时间间隔
        if not self.is_support_interval(request.interval):
            return False, f"不支持的时间间隔: {request.interval}"
            
        # 检查股票代码
        if not request.symbol:
            return False, "股票代码不能为空"
            
        return True, ""
        
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.name}({self.source})" 