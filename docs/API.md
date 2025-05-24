# 📚 API 文档

## 概述

本文档详细介绍了 Hacker News 爬虫系统的 API 接口和核心类方法。

## 核心类

### HackerNewsCrawler

主要的爬虫类，负责所有爬取、处理和发送功能。

#### 初始化

```python
crawler = HackerNewsCrawler()
```

**功能**: 初始化爬虫实例，加载配置，设置网络代理，初始化 Telegram Bot。

**异常**: 
- `ValueError`: 当缺少必需的配置项时抛出

#### 核心方法

##### `get_hn_frontpage()`

```python
news_list = crawler.get_hn_frontpage()
```

**功能**: 获取 Hacker News 首页所有新闻

**返回值**: `List[Dict]` - 新闻列表，每个新闻包含以下字段：
- `id`: 新闻 ID
- `title`: 标题
- `url`: 原文链接
- `score`: 分数
- `comments`: 评论数
- `hn_url`: HN 讨论链接
- `rank`: 排名

**示例**:
```python
news_list = crawler.get_hn_frontpage()
for news in news_list:
    print(f"{news['title']} - {news['score']} points")
```

##### `save_news_to_csv(news_item)`

```python
is_new = crawler.save_news_to_csv(news_item)
```

**功能**: 保存新闻到 CSV 文件，自动去重

**参数**:
- `news_item`: `Dict` - 新闻数据字典

**返回值**: `bool` - True 表示新增记录，False 表示更新现有记录

**示例**:
```python
news = {
    'id': '12345',
    'title': 'Example News',
    'url': 'https://example.com',
    'score': 100,
    'comments': 50,
    'hn_url': 'https://news.ycombinator.com/item?id=12345'
}
is_new = crawler.save_news_to_csv(news)
```

##### `get_unsent_news_from_csv()`

```python
unsent_news = crawler.get_unsent_news_from_csv()
```

**功能**: 获取所有未发送的新闻

**返回值**: `List[Dict]` - 未发送新闻列表

**示例**:
```python
unsent = crawler.get_unsent_news_from_csv()
print(f"Found {len(unsent)} unsent news")
```

##### `mark_news_as_sent(news_id)`

```python
success = crawler.mark_news_as_sent(news_id)
```

**功能**: 标记新闻为已发送

**参数**:
- `news_id`: `str` - 新闻 ID

**返回值**: `bool` - 操作是否成功

##### `translate_text(text)`

```python
translated = crawler.translate_text("Hello World")
```

**功能**: 翻译文本为中文

**参数**:
- `text`: `str` - 待翻译文本

**返回值**: `str` - 翻译后的文本

**特性**:
- 自动检测中文内容，避免重复翻译
- 限制文本长度，避免API限制
- 支持代理访问

##### `get_article_content(url)`

```python
content = crawler.get_article_content(url)
```

**功能**: 获取文章内容

**参数**:
- `url`: `str` - 文章链接

**返回值**: `str` - 文章内容摘要

**特性**:
- 智能内容提取
- 错误处理和超时控制
- 支持多种网站格式

##### `clean_and_summarize_content(content)`

```python
summary = crawler.clean_and_summarize_content(content)
```

**功能**: 清理和摘要内容

**参数**:
- `content`: `str` - 原始内容

**返回值**: `str` - 清理后的摘要

##### `send_telegram_message(message)`

```python
success = await crawler.send_telegram_message(message)
```

**功能**: 发送 Telegram 消息

**参数**:
- `message`: `str` - 消息内容

**返回值**: `bool` - 发送是否成功

**特性**:
- 异步发送
- 自动重试机制
- 支持 HTML 格式

##### `format_message(news, index, total)`

```python
message = crawler.format_message(news, 1, 10)
```

**功能**: 格式化新闻消息

**参数**:
- `news`: `Dict` - 新闻数据
- `index`: `int` - 当前索引
- `total`: `int` - 总数量

**返回值**: `str` - 格式化的消息

##### `crawl_and_send()`

```python
await crawler.crawl_and_send()
```

**功能**: 执行完整的爬取和发送流程

**特性**:
- 异步执行
- 完整的错误处理
- 自动去重和状态管理

##### `test_network_connection()`

```python
is_connected = crawler.test_network_connection()
```

**功能**: 测试网络连接

**返回值**: `bool` - 连接是否正常

**测试项目**:
- HN 网站连接
- Telegram API 连接
- 代理配置验证

## 工具函数

### 进程管理

#### `get_crawler_processes()`

```python
from manage_crawler import get_crawler_processes
processes = get_crawler_processes()
```

**功能**: 获取运行中的爬虫进程

**返回值**: `List[Dict]` - 进程信息列表

#### `stop_crawler_processes()`

```python
from manage_crawler import stop_crawler_processes
stopped = stop_crawler_processes()
```

**功能**: 停止所有爬虫进程

**返回值**: `int` - 停止的进程数量

#### `show_status()`

```python
from manage_crawler import show_status
show_status()
```

**功能**: 显示爬虫运行状态

## 配置管理

### 环境变量

所有配置通过环境变量管理，支持的配置项请参考 `config.env.example`。

#### 必需配置

- `TELEGRAM_BOT_TOKEN`: Telegram Bot 令牌
- `TELEGRAM_CHAT_ID`: 目标聊天 ID

#### 可选配置

- `MAX_NEWS_COUNT`: 最大新闻数量（默认: 100）
- `MIN_SCORE`: 最低分数阈值（默认: 0）
- `CHECK_INTERVAL_MINUTES`: 检查间隔（默认: 5）
- `ENABLE_PROXY`: 是否启用代理（默认: false）

### 配置加载

```python
from dotenv import load_dotenv
import os

load_dotenv('config.env')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
```

## 数据结构

### 新闻数据结构

```python
news_item = {
    'id': str,                    # 新闻 ID
    'title': str,                 # 原标题
    'title_cn': str,              # 中文标题
    'url': str,                   # 原文链接
    'hn_url': str,                # HN 讨论链接
    'score': int,                 # 分数
    'comments': int,              # 评论数
    'content_summary': str,       # 英文摘要
    'content_summary_cn': str,    # 中文摘要
    'crawl_time': str,            # 爬取时间 (ISO格式)
    'sent_time': str,             # 发送时间 (ISO格式)
    'is_sent': bool,              # 是否已发送
    'rank': int                   # 排名 (可选)
}
```

### CSV 文件结构

CSV 文件包含以下列：

| 列名 | 类型 | 说明 |
|------|------|------|
| id | string | 新闻 ID |
| title | string | 原标题 |
| title_cn | string | 中文标题 |
| url | string | 原文链接 |
| hn_url | string | HN 讨论链接 |
| score | integer | 分数 |
| comments | integer | 评论数 |
| content_summary | string | 英文摘要 |
| content_summary_cn | string | 中文摘要 |
| crawl_time | datetime | 爬取时间 |
| sent_time | datetime | 发送时间 |
| is_sent | boolean | 是否已发送 |

## 错误处理

### 异常类型

- `ValueError`: 配置错误
- `requests.RequestException`: 网络请求错误
- `pandas.errors.ParserError`: CSV 解析错误
- `telegram.error.TelegramError`: Telegram API 错误

### 错误处理示例

```python
try:
    crawler = HackerNewsCrawler()
    await crawler.crawl_and_send()
except ValueError as e:
    print(f"配置错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 最佳实践

### 1. 错误处理

```python
import logging

try:
    result = crawler.some_method()
except Exception as e:
    logging.error(f"操作失败: {e}")
    # 适当的错误处理
```

### 2. 异步操作

```python
import asyncio

async def main():
    crawler = HackerNewsCrawler()
    await crawler.crawl_and_send()

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. 配置管理

```python
import os
from dotenv import load_dotenv

# 加载配置
load_dotenv('config.env')

# 验证必需配置
required_configs = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
for config in required_configs:
    if not os.getenv(config):
        raise ValueError(f"缺少必需配置: {config}")
```

### 4. 日志记录

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("应用启动")
```

## 扩展开发

### 添加新的数据源

```python
class CustomCrawler(HackerNewsCrawler):
    def get_custom_source(self):
        """添加自定义数据源"""
        # 实现自定义爬取逻辑
        pass
```

### 自定义消息格式

```python
def custom_format_message(self, news):
    """自定义消息格式"""
    return f"📰 {news['title']}\n🔗 {news['url']}"
```

### 添加新的翻译服务

```python
def translate_with_custom_service(self, text):
    """使用自定义翻译服务"""
    # 实现自定义翻译逻辑
    pass
``` 