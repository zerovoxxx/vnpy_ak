"""
基于akshare的股票数据下载器

使用akshare库下载美股数据
"""

from datetime import datetime
from typing import List, Optional
import pandas as pd

from vnpy.trader.object import BarData
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.database import convert_tz

from .base import BaseStockDownloader, DownloadRequest, DownloadResult, DataSource


class AkshareStockDownloader(BaseStockDownloader):
    """基于akshare的股票下载器"""
    
    def __init__(self):
        """初始化"""
        super().__init__("AkshareStockDownloader") 
        self.source = DataSource.AKSHARE
        self.ak = None
        
    def init_connection(self, **kwargs) -> bool:
        """
        初始化akshare连接
        
        Args:
            **kwargs: 其他参数
            
        Returns:
            bool: 是否初始化成功
        """
        try:
            import akshare as ak
            self.ak = ak
            return True
        except ImportError:
            print("akshare库未安装，请运行: pip install akshare")
            return False
        except Exception as e:
            print(f"akshare初始化失败: {e}")
            return False
            
    def _convert_interval_to_ak(self, interval: Interval) -> str:
        """
        将vnpy的时间间隔转换为akshare格式
        
        Args:
            interval: vnpy时间间隔
            
        Returns:
            str: akshare时间间隔
        """
        # akshare对美股数据的间隔支持有限
        interval_map = {
            Interval.DAILY: "daily",  
            # akshare的美股数据主要支持日线
            # 分钟和小时线数据支持有限
        }
        return interval_map.get(interval, "daily")
        
    def _convert_ak_data_to_vnpy(self, df: pd.DataFrame, symbol: str, exchange: Exchange, interval: Interval) -> List[BarData]:
        """
        将akshare数据转换为vnpy BarData格式
        
        Args:
            df: akshare返回的DataFrame
            symbol: 股票代码
            exchange: 交易所
            interval: 时间间隔
            
        Returns:
            List[BarData]: vnpy BarData列表
        """
        bars = []
        
        if df is None or df.empty:
            return bars
            
        for index, row in df.iterrows():
            try:
                # 处理日期时间
                if 'date' in df.columns:
                    date_str = str(row['date'])
                elif 'Date' in df.columns:
                    date_str = str(row['Date']) 
                else:
                    # 使用索引作为日期
                    date_str = str(index)
                
                # 转换日期格式
                if len(date_str) == 8:  # YYYYMMDD格式
                    dt = datetime.strptime(date_str, '%Y%m%d')
                elif len(date_str) == 10:  # YYYY-MM-DD格式
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                else:
                    dt = pd.to_datetime(date_str)
                    if hasattr(dt, 'to_pydatetime'):
                        dt = dt.to_pydatetime()
                        
                # 转换为vnpy数据库时区
                dt = convert_tz(dt)
                
                # 提取价格和成交量数据（支持不同的列名格式）
                open_price = float(row.get('open', row.get('Open', 0)))
                high_price = float(row.get('high', row.get('High', 0)))
                low_price = float(row.get('low', row.get('Low', 0)))
                close_price = float(row.get('close', row.get('Close', 0)))
                volume = float(row.get('volume', row.get('Volume', 0)))
                
                # 创建BarData对象
                bar = BarData(
                    symbol=symbol,
                    exchange=exchange,
                    datetime=dt,
                    interval=interval,
                    volume=volume,
                    turnover=0.0,  # akshare美股数据通常不包含成交额
                    open_interest=0.0,  # 股票没有持仓量
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    gateway_name="akshare"
                )
                bars.append(bar)
                
            except Exception as e:
                print(f"转换akshare数据行失败: {e}, 行数据: {row}")
                continue
                
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
            
        # 检查akshare是否已初始化
        if not self.ak:
            return DownloadResult(
                request=request,
                bars=[],
                success=False,
                error_msg="akshare未初始化，请先调用init_connection"
            )
            
        # 检查时间间隔支持
        if request.interval != Interval.DAILY:
            return DownloadResult(
                request=request,
                bars=[],
                success=False,
                error_msg="akshare美股数据目前仅支持日线数据"
            )
            
        try:
            # 准备时间参数
            start_date = request.start_date.strftime('%Y%m%d') if request.start_date else "19700101"
            end_date = request.end_date.strftime('%Y%m%d') if request.end_date else datetime.now().strftime('%Y%m%d')
            
            # 使用akshare下载美股数据
            # akshare的美股数据接口可能有变化，这里使用常见的接口
            try:
                # 尝试使用美股历史数据接口
                df = self.ak.stock_us_hist(symbol=request.symbol)
            except AttributeError:
                try:
                    # 备用接口
                    df = self.ak.stock_us_daily(symbol=request.symbol)
                except AttributeError:
                    return DownloadResult(
                        request=request,
                        bars=[],
                        success=False,
                        error_msg="akshare美股数据接口不可用，请检查akshare版本"
                    )
            
            # 如果有时间范围限制，进行过滤
            if request.start_date or request.end_date:
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    if request.start_date:
                        df = df[df['date'] >= request.start_date]
                    if request.end_date:
                        df = df[df['date'] <= request.end_date]
                        
            # 转换为vnpy格式
            bars = self._convert_ak_data_to_vnpy(df, request.symbol, request.exchange, request.interval)
            
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
                error_msg=f"akshare数据下载失败: {str(e)}"
            )
            
    def get_supported_intervals(self) -> List[Interval]:
        """
        获取akshare支持的时间间隔
        
        Returns:
            List[Interval]: 支持的时间间隔
        """
        # akshare的美股数据主要支持日线
        return [Interval.DAILY]
        
    def is_support_interval(self, interval: Interval) -> bool:
        """
        检查akshare是否支持指定的时间间隔
        
        Args:
            interval: 时间间隔
            
        Returns:
            bool: 是否支持
        """
        return interval in self.get_supported_intervals()
        
    def get_supported_exchanges(self) -> List[Exchange]:
        """
        获取akshare支持的交易所
        
        Returns:
            List[Exchange]: 支持的交易所
        """
        return [
            Exchange.NYSE,      # 纽约证券交易所
            Exchange.NASDAQ,    # 纳斯达克
            Exchange.AMEX,      # 美国证券交易所
        ] 