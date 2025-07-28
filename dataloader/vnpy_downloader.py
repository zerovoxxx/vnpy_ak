"""
基于vnpy自带数据源的股票数据下载器

利用vnpy.trader.datafeed接口下载美股数据
"""

from datetime import datetime
from typing import List, Optional

from vnpy.trader.datafeed import get_datafeed
from vnpy.trader.object import BarData, HistoryRequest
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.setting import SETTINGS

from .base import BaseStockDownloader, DownloadRequest, DownloadResult, DataSource


class VnpyStockDownloader(BaseStockDownloader):
    """基于vnpy自带数据源的股票下载器"""
    
    def __init__(self):
        """初始化"""
        super().__init__("VnpyStockDownloader")
        self.source = DataSource.VNPY
        self.datafeed = None
        
    def init_connection(self, 
                       datafeed_name: str = "",
                       username: str = "", 
                       password: str = "",
                       **kwargs) -> bool:
        """
        初始化vnpy数据源连接
        
        Args:
            datafeed_name: 数据源名称，如 rqdata, xt, wind等
            username: 用户名
            password: 密码
            **kwargs: 其他参数
            
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 配置vnpy数据源设置
            if datafeed_name:
                SETTINGS["datafeed.name"] = datafeed_name
            if username:
                SETTINGS["datafeed.username"] = username  
            if password:
                SETTINGS["datafeed.password"] = password
                
            # 获取数据源实例
            self.datafeed = get_datafeed()
            
            # 初始化数据源
            if hasattr(self.datafeed, 'init'):
                return self.datafeed.init()
            else:
                return True
                
        except Exception as e:
            print(f"vnpy数据源初始化失败: {e}")
            return False
            
    def download_bars(self, request: DownloadRequest) -> DownloadResult:
        """
        下载K线数据
        
        Args:
            request: 下载请求
            
        Returns:
            DownloadResult: 下载结果
        """
        # 验证请求
        is_valid, error_msg = self.validate_request(request)
        if not is_valid:
            return DownloadResult(
                request=request,
                bars=[],
                success=False,
                error_msg=error_msg
            )
            
        # 检查数据源是否已初始化
        if not self.datafeed:
            return DownloadResult(
                request=request,
                bars=[],
                success=False,
                error_msg="数据源未初始化，请先调用init_connection"
            )
            
        try:
            # 创建vnpy历史数据请求
            history_req = HistoryRequest(
                symbol=request.symbol,
                exchange=request.exchange,
                start=request.start_date,
                end=request.end_date,
                interval=request.interval
            )
            
            # 下载数据
            bars = self.datafeed.query_bar_history(history_req)
            
            # 转换数据格式（添加gateway_name）
            converted_bars = []
            for bar in bars:
                # 确保每个bar都有gateway_name
                if not hasattr(bar, 'gateway_name') or not bar.gateway_name:
                    bar.gateway_name = "vnpy_datafeed"
                converted_bars.append(bar)
            
            return DownloadResult(
                request=request,
                bars=converted_bars,
                success=True if converted_bars else False,
                error_msg="" if converted_bars else "未获取到数据"
            )
            
        except Exception as e:
            return DownloadResult(
                request=request,
                bars=[],
                success=False,
                error_msg=f"数据下载失败: {str(e)}"
            )
            
    def get_supported_intervals(self) -> List[Interval]:
        """
        获取支持的时间间隔（取决于配置的具体数据源）
        
        Returns:
            List[Interval]: 支持的时间间隔
        """
        # 基本支持的间隔，具体取决于配置的数据源
        return [Interval.DAILY, Interval.HOUR, Interval.MINUTE]
        
    def is_support_interval(self, interval: Interval) -> bool:
        """
        检查是否支持指定的时间间隔
        
        Args:
            interval: 时间间隔
            
        Returns:
            bool: 是否支持
        """
        return interval in self.get_supported_intervals()
        
    def get_supported_exchanges(self) -> List[Exchange]:
        """
        获取支持的交易所（美股相关）
        
        Returns:
            List[Exchange]: 支持的交易所
        """
        return [
            Exchange.NYSE,      # 纽约证券交易所
            Exchange.NASDAQ,    # 纳斯达克
            Exchange.AMEX,      # 美国证券交易所
            Exchange.SMART,     # 智能路由
        ] 