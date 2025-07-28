"""
基于yfinance的股票数据下载器

使用yfinance库下载Yahoo Finance的美股数据
"""

from datetime import datetime
from typing import List, Optional
import pytz

from vnpy.trader.object import BarData
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.database import convert_tz

from .base import BaseStockDownloader, DownloadRequest, DownloadResult, DataSource


class YfinanceStockDownloader(BaseStockDownloader):
    """基于yfinance的股票下载器"""
    
    def __init__(self):
        """初始化"""
        super().__init__("YfinanceStockDownloader")
        self.source = DataSource.YFINANCE
        self.yf = None
        
    def init_connection(self, **kwargs) -> bool:
        """
        初始化yfinance连接
        
        Args:
            **kwargs: 其他参数
            
        Returns:
            bool: 是否初始化成功
        """
        try:
            import yfinance as yf
            self.yf = yf
            return True
        except ImportError:
            print("yfinance库未安装，请运行: pip install yfinance")
            return False
        except Exception as e:
            print(f"yfinance初始化失败: {e}")
            return False
            
    def _convert_interval_to_yf(self, interval: Interval) -> str:
        """
        将vnpy的时间间隔转换为yfinance格式
        
        Args:
            interval: vnpy时间间隔
            
        Returns:
            str: yfinance时间间隔
        """
        interval_map = {
            Interval.MINUTE: "1m",
            Interval.HOUR: "1h", 
            Interval.DAILY: "1d",
        }
        return interval_map.get(interval, "1d")
        
    def _convert_exchange_to_yf_suffix(self, exchange: Exchange) -> str:
        """
        将vnpy交易所转换为yfinance后缀
        
        Args:
            exchange: vnpy交易所
            
        Returns:
            str: yfinance后缀
        """
        # 对于美股，通常不需要后缀
        # yfinance会自动识别美股代码
        return ""
        
    def _convert_yf_data_to_vnpy(self, df, symbol: str, exchange: Exchange, interval: Interval) -> List[BarData]:
        """
        将yfinance数据转换为vnpy BarData格式
        
        Args:
            df: yfinance返回的DataFrame
            symbol: 股票代码
            exchange: 交易所
            interval: 时间间隔
            
        Returns:
            List[BarData]: vnpy BarData列表
        """
        bars = []
        
        if df is None or df.empty:
            return bars
            
        for timestamp, row in df.iterrows():
            # 处理时间戳
            if hasattr(timestamp, 'tz_localize'):
                # 如果没有时区信息，假设为UTC
                if timestamp.tz is None:
                    timestamp = timestamp.tz_localize('UTC')
                # 转换为ET（美股交易时间）
                timestamp = timestamp.tz_convert('America/New_York')
            
            # 转换为vnpy数据库时区
            dt = convert_tz(timestamp.to_pydatetime())
            
            # 创建BarData对象
            bar = BarData(
                symbol=symbol,
                exchange=exchange,
                datetime=dt,
                interval=interval,
                volume=float(row.get('Volume', 0)),
                turnover=0.0,  # yfinance不提供成交额
                open_interest=0.0,  # 股票没有持仓量
                open_price=float(row.get('Open', 0)),
                high_price=float(row.get('High', 0)),
                low_price=float(row.get('Low', 0)),
                close_price=float(row.get('Close', 0)),
                gateway_name="yfinance"
            )
            bars.append(bar)
            
        return bars
        
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
            
        # 检查yfinance是否已初始化
        if not self.yf:
            return DownloadResult(
                request=request,
                bars=[],
                success=False,
                error_msg="yfinance未初始化，请先调用init_connection"
            )
            
        try:
            # 构建yfinance股票代码
            yf_symbol = request.symbol
            suffix = self._convert_exchange_to_yf_suffix(request.exchange)
            if suffix:
                yf_symbol = f"{request.symbol}{suffix}"
                
            # 创建yfinance股票对象
            ticker = self.yf.Ticker(yf_symbol)
            
            # 转换时间间隔
            yf_interval = self._convert_interval_to_yf(request.interval)
            
            # 下载历史数据
            df = ticker.history(
                start=request.start_date,
                end=request.end_date,
                interval=yf_interval,
                auto_adjust=True,  # 自动调整价格
                prepost=False,     # 不包含盘前盘后
                actions=False      # 不包含股息分红信息
            )
            
            # 转换为vnpy格式
            bars = self._convert_yf_data_to_vnpy(df, request.symbol, request.exchange, request.interval)
            
            return DownloadResult(
                request=request,
                bars=bars,
                success=True if bars else False,
                error_msg="" if bars else "未获取到数据或股票代码不存在"
            )
            
        except Exception as e:
            return DownloadResult(
                request=request,
                bars=[],
                success=False,
                error_msg=f"yfinance数据下载失败: {str(e)}"
            )
            
    def get_supported_intervals(self) -> List[Interval]:
        """
        获取yfinance支持的时间间隔
        
        Returns:
            List[Interval]: 支持的时间间隔
        """
        return [Interval.MINUTE, Interval.HOUR, Interval.DAILY]
        
    def is_support_interval(self, interval: Interval) -> bool:
        """
        检查yfinance是否支持指定的时间间隔
        
        Args:
            interval: 时间间隔
            
        Returns:
            bool: 是否支持
        """
        return interval in self.get_supported_intervals()
        
    def get_supported_exchanges(self) -> List[Exchange]:
        """
        获取yfinance支持的交易所
        
        Returns:
            List[Exchange]: 支持的交易所
        """
        return [
            Exchange.NYSE,      # 纽约证券交易所
            Exchange.NASDAQ,    # 纳斯达克
            Exchange.AMEX,      # 美国证券交易所
            Exchange.SMART,     # 智能路由
        ] 