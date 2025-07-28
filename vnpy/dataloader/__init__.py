"""
美股股票数据下载器

支持多种数据源的美股股票历史数据下载功能，包括：
- vnpy自带数据源
- yfinance
- akshare

支持的数据维度：
- 日线数据
- 小时线数据  
- 分钟线数据

数据自动转换为vnpy格式并存储到数据库中。
"""

from .base import BaseStockDownloader, DownloadRequest, DownloadResult
from .vnpy_downloader import VnpyStockDownloader  
from .yfinance_downloader import YfinanceStockDownloader
from .akshare_downloader import AkshareStockDownloader
from .manager import StockDataManager

__all__ = [
    "BaseStockDownloader",
    "DownloadRequest", 
    "DownloadResult",
    "VnpyStockDownloader",
    "YfinanceStockDownloader", 
    "AkshareStockDownloader",
    "StockDataManager"
] 