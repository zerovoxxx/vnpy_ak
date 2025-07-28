# 美股股票数据下载器

一个基于vnpy框架的美股股票历史数据下载工具，支持多种数据源，可自动将数据转换为vnpy格式并存储到数据库中。

## 功能特性

- 🌍 **多数据源支持**: vnpy自带数据源、yfinance、akshare
- 📊 **多时间维度**: 支持日线、小时线、分钟线数据
- 🏪 **多交易所**: 纽约证券交易所(NYSE)、纳斯达克(NASDAQ)、美国证券交易所(AMEX)
- 🔄 **自动格式转换**: 自动转换为vnpy BarData格式
- 💾 **数据库存储**: 自动存储到vnpy MySQL/SQLite数据库
- 🏗️ **良好扩展性**: 易于扩展其他数据源
- 🧩 **模块化设计**: 通用方法抽象复用

## 安装依赖

```bash
# 安装yfinance（用于Yahoo Finance数据）
pip install yfinance

# 安装akshare（用于akshare数据源）
pip install akshare

# 可选：安装vnpy官方数据源插件
pip install vnpy_rqdata    # RQData数据源
pip install vnpy_xt        # 迅投研数据源
pip install vnpy_wind      # Wind数据源
```

## 项目结构

```
dataloader/
├── __init__.py              # 包初始化，导出主要类
├── base.py                  # 抽象基类和数据结构定义
├── vnpy_downloader.py       # vnpy自带数据源下载器
├── yfinance_downloader.py   # yfinance数据源下载器
├── akshare_downloader.py    # akshare数据源下载器
├── manager.py               # 数据管理器，统一管理多数据源
├── example_usage.py         # 使用示例代码
└── README.md               # 本文档
```

## 快速开始

### 1. 基础使用

```python
from datetime import datetime, timedelta
from vnpy.trader.constant import Exchange, Interval
from dataloader import StockDataManager, DataSource

# 创建数据管理器
manager = StockDataManager()

# 初始化yfinance数据源
manager.init_datasource(DataSource.YFINANCE)

# 下载苹果公司最近30天的日线数据
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

result = manager.download_stock_data(
    symbol="AAPL",
    source=DataSource.YFINANCE,
    exchange=Exchange.NASDAQ,
    start_date=start_date,
    end_date=end_date,
    interval=Interval.DAILY,
    save_to_db=True
)

if result.success:
    print(f"下载成功! 获取数据量: {result.total_count}")
else:
    print(f"下载失败: {result.error_msg}")
```

### 2. 批量下载多只股票

```python
# 科技股票代码列表
tech_stocks = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]

# 批量下载
results = manager.download_multiple_stocks(
    symbols=tech_stocks,
    source=DataSource.YFINANCE,
    exchange=Exchange.NASDAQ,
    start_date=start_date,
    end_date=end_date,
    interval=Interval.DAILY,
    save_to_db=True
)

# 统计结果
success_count = sum(1 for r in results if r.success)
print(f"批量下载完成: 成功 {success_count}/{len(tech_stocks)} 只股票")
```

### 3. 使用vnpy自带数据源

```python
# 配置vnpy数据源（以RQData为例）
success = manager.init_datasource(
    DataSource.VNPY,
    datafeed_name="rqdata",  # 可选: rqdata, xt, wind等
    username="license",      # RQData的用户名统一为"license"
    password="your_license"  # 替换为实际的license
)

# 下载数据
result = manager.download_stock_data(
    symbol="AAPL",
    source=DataSource.VNPY,
    exchange=Exchange.NASDAQ,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    interval=Interval.DAILY,
    save_to_db=True
)
```

## API 文档

### 核心类

#### StockDataManager
主要的数据管理器类，统一管理所有数据源。

**主要方法:**
- `init_datasource(source, **kwargs)`: 初始化指定数据源
- `download_stock_data(...)`: 下载单只股票数据
- `download_multiple_stocks(...)`: 批量下载多只股票数据
- `list_all_downloaders()`: 列出所有可用下载器信息
- `get_database_overview()`: 获取数据库数据概览

#### DownloadRequest
数据下载请求数据结构。

**字段:**
- `symbol`: 股票代码 (str)
- `exchange`: 交易所 (Exchange)
- `start_date`: 开始时间 (datetime)
- `end_date`: 结束时间 (datetime)
- `interval`: 数据间隔 (Interval)

#### DownloadResult
数据下载结果数据结构。

**字段:**
- `request`: 原始请求 (DownloadRequest)
- `bars`: 下载的K线数据 (List[BarData])
- `success`: 是否成功 (bool)
- `error_msg`: 错误信息 (str)
- `total_count`: 总数据量 (int)

### 数据源类型

#### DataSource.VNPY
vnpy自带数据源，支持RQData、迅投研、Wind等。

**支持的时间间隔:**
- 日线 (DAILY)
- 小时线 (HOUR) 
- 分钟线 (MINUTE)

**初始化参数:**
- `datafeed_name`: 数据源名称 (rqdata/xt/wind等)
- `username`: 用户名
- `password`: 密码或license

#### DataSource.YFINANCE
基于Yahoo Finance的免费数据源。

**支持的时间间隔:**
- 日线 (DAILY)
- 小时线 (HOUR)
- 分钟线 (MINUTE)

**特点:**
- 免费使用
- 数据质量较好
- 支持实时和历史数据

#### DataSource.AKSHARE
基于akshare库的数据源。

**支持的时间间隔:**
- 日线 (DAILY)

**特点:**
- 免费使用
- 主要支持日线数据
- 美股数据支持有限

## 支持的交易所

- **NYSE**: 纽约证券交易所
- **NASDAQ**: 纳斯达克交易所  
- **AMEX**: 美国证券交易所
- **SMART**: 智能路由（部分数据源支持）

## 支持的时间间隔

- **DAILY**: 日线数据
- **HOUR**: 小时线数据
- **MINUTE**: 分钟线数据

> 注意：不同数据源对时间间隔的支持程度不同，详见各数据源说明。

## 数据库配置

### SQLite（默认）
```python
from vnpy.trader.setting import SETTINGS
SETTINGS["database.name"] = "sqlite"
```

### MySQL
```python
SETTINGS["database.name"] = "mysql"
SETTINGS["database.host"] = "localhost"
SETTINGS["database.port"] = 3306
SETTINGS["database.database"] = "vnpy"
SETTINGS["database.user"] = "root"
SETTINGS["database.password"] = "123456"
```

## 常见问题

### Q: 如何处理数据下载失败？
A: 检查网络连接、数据源配置和股票代码是否正确。查看DownloadResult.error_msg获取详细错误信息。

### Q: 如何扩展新的数据源？
A: 继承BaseStockDownloader类，实现init_connection()和download_bars()方法。

### Q: yfinance下载速度慢怎么办？
A: 可以尝试减少时间范围或使用其他数据源。yfinance有访问频率限制。

### Q: 如何查看已下载的数据？
A: 使用manager.get_database_overview()查看数据库中的数据概览。

## 扩展开发

### 添加新的数据源

1. 创建新的下载器类:
```python
from .base import BaseStockDownloader, DownloadRequest, DownloadResult

class CustomDownloader(BaseStockDownloader):
    def __init__(self):
        super().__init__("CustomDownloader")
        self.source = DataSource.CUSTOM  # 需要在DataSource枚举中添加
        
    def init_connection(self, **kwargs) -> bool:
        # 实现连接初始化逻辑
        pass
        
    def download_bars(self, request: DownloadRequest) -> DownloadResult:
        # 实现数据下载逻辑
        pass
```

2. 在manager.py中注册新的下载器:
```python
def _init_downloaders(self) -> None:
    # ... 现有代码 ...
    self.downloaders[DataSource.CUSTOM] = CustomDownloader()
```

## 许可证

本项目遵循vnpy项目的许可证协议。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 版本历史

- v1.0.0: 初始版本，支持vnpy、yfinance、akshare三种数据源 