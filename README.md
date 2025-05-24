# 🚀 Hacker News 智能爬虫系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production-brightgreen.svg)]()

一个功能完整的 Hacker News 爬虫系统，支持自动爬取、翻译、摘要生成和 Telegram 推送。

## 📋 目录

- [功能特性](#-功能特性)
- [系统架构](#-系统架构)
- [快速开始](#-快速开始)
- [配置说明](#-配置说明)
- [使用指南](#-使用指南)
- [部署方案](#-部署方案)
- [故障排除](#-故障排除)
- [开发指南](#-开发指南)
- [更新日志](#-更新日志)

## ✨ 功能特性

### 🔥 核心功能
- **智能爬取**: 获取 HN 首页所有新闻，无数量限制
- **自动翻译**: 标题和摘要中英文双语支持
- **内容摘要**: 智能提取文章关键信息
- **去重机制**: 严格的数据去重，避免重复推送
- **增量更新**: 只处理新增内容，高效节能

### 📱 推送功能
- **Telegram 集成**: 美观的消息格式，支持链接预览
- **批量发送**: 智能分批推送，避免 API 限制
- **发送状态**: 完整的发送状态跟踪和重试机制
- **商务格式**: 专业的消息排版，包含热度分析

### 🛠 系统功能
- **守护进程**: 后台持续运行，支持自动重启
- **进程管理**: 完整的进程生命周期管理
- **日志系统**: 详细的运行日志和错误追踪
- **网络代理**: 支持 HTTP/HTTPS 代理配置
- **数据持久化**: CSV 格式数据存储，便于分析

## 🏗 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   HN 首页       │───▶│   爬虫引擎      │───▶│   数据处理      │
│   新闻源        │    │   网络请求      │    │   翻译/摘要     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram      │◀───│   消息推送      │◀───│   CSV 存储      │
│   用户接收      │    │   格式化发送    │    │   状态管理      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: Linux, macOS, Windows
- **网络**: 稳定的互联网连接
- **Telegram**: Bot Token 和 Chat ID

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <your-repository-url>
   cd hacker-news-crawler
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境**
   ```bash
   cp config.env.example config.env
   # 编辑 config.env 文件，填入必要配置
   ```

4. **测试运行**
   ```bash
   python run_once.py
   ```

5. **启动守护进程**
   ```bash
   python run_daemon.py
   ```

## ⚙️ 配置说明

### 必需配置

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot 令牌 | `123456:ABC-DEF...` |
| `TELEGRAM_CHAT_ID` | 目标聊天 ID | `-1001234567890` |

### 可选配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MAX_NEWS_COUNT` | `100` | 最大新闻数量（实际获取所有） |
| `MIN_SCORE` | `0` | 最低分数阈值 |
| `CHECK_INTERVAL_MINUTES` | `5` | 检查间隔（分钟） |
| `ENABLE_PROXY` | `false` | 是否启用代理 |
| `PROXY_HTTP` | - | HTTP 代理地址 |
| `PROXY_HTTPS` | - | HTTPS 代理地址 |

### 代理配置示例

```env
# 启用代理
ENABLE_PROXY=true
PROXY_HTTP=http://127.0.0.1:7890
PROXY_HTTPS=http://127.0.0.1:7890

# 或使用环境变量
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
```

## 📙 配置管理

### 配置文件结构

所有重要配置都集中在 `config.env` 文件中，支持以下配置类别：

#### 必需配置
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

#### 网络配置
```bash
BASE_URL=https://news.ycombinator.com
REQUEST_TIMEOUT=15
CONNECTION_TEST_TIMEOUT=10
TRANSLATION_TIMEOUT=10
TELEGRAM_TIMEOUT=15
MAX_RETRIES=3
REQUEST_INTERVAL=0.3
USER_AGENT=Mozilla/5.0...
```

#### 消息发送配置
```bash
MESSAGE_SEND_INTERVAL=1.0
MESSAGE_RETRY_INTERVAL=2.0
BULK_MESSAGE_INTERVAL=3.0
MESSAGE_MAX_RETRIES=2
```

#### 数据存储配置
```bash
DATA_DIR=data
CSV_ENCODING=utf-8
CSV_COLUMNS=id,title,title_cn,url,hn_url,score,comments,content_summary,content_summary_cn,crawl_time,sent_time,is_sent
```

#### 日志配置
```bash
LOG_LEVEL=INFO
LOG_FILE=hn_crawler.log
LOG_FORMAT=%(asctime)s - %(levelname)s - %(message)s
```

#### 功能开关
```bash
ENABLE_TRANSLATION=true
ENABLE_CONTENT_SUMMARY=true
ENABLE_PROXY=false
ENABLE_WEB=false
```

#### 进程管理配置
```bash
DAEMON_CHECK_INTERVAL=30
PROCESS_WAIT_TIME=2
PROCESS_STOP_WAIT_TIME=3
```

### 配置验证

运行配置验证脚本检查所有配置项：

```bash
python3 validate_config.py
```

该脚本会：
- ✅ 验证所有配置项是否正确加载
- 🧪 测试配置类型转换
- 📊 显示配置统计信息
- 🔒 隐藏敏感信息（如Token）

### 配置最佳实践

1. **备份配置**：修改前备份 `config.env`
2. **环境隔离**：不同环境使用不同的配置文件
3. **安全性**：不要将包含敏感信息的配置文件提交到版本控制
4. **验证配置**：修改后运行 `validate_config.py` 验证
5. **重启生效**：修改配置后需要重启爬虫进程

## 📖 使用指南

### 运行模式

#### 1. 单次运行
```bash
python run_once.py
```
- 执行一次完整的爬取和发送流程
- 适合测试和手动触发

#### 2. 守护进程模式
```bash
python run_daemon.py
```
- 后台持续运行
- 定时自动执行
- 支持文件锁防止重复启动

#### 3. 进程管理
```bash
python manage_crawler.py
```
- 查看运行状态
- 启动/停止进程
- 进程监控

### 数据管理

#### CSV 文件结构
```
data/hn_news_YYYY-MM-DD.csv
├── id              # 新闻 ID
├── title           # 原标题
├── title_cn        # 中文标题
├── url             # 原文链接
├── hn_url          # HN 讨论链接
├── score           # 分数
├── comments        # 评论数
├── content_summary # 英文摘要
├── content_summary_cn # 中文摘要
├── crawl_time      # 爬取时间
├── sent_time       # 发送时间
└── is_sent         # 发送状态
```

#### 日志文件
- `hn_crawler.log`: 主要运行日志
- 包含详细的执行过程和错误信息
- 支持日志轮转和压缩

## 🚀 部署方案

### 本地部署

1. **开发环境**
   ```bash
   # 安装开发依赖
   pip install -r requirements.txt
   
   # 运行测试
   python test_crawler.py
   
   # 启动开发服务
   python run_once.py
   ```

2. **生产环境**
   ```bash
   # 后台运行
   nohup python run_daemon.py > /dev/null 2>&1 &
   
   # 或使用 systemd
   sudo systemctl enable hn-crawler
   sudo systemctl start hn-crawler
   ```

### 服务器部署

#### 使用 systemd (推荐)

1. **创建服务文件**
   ```bash
   sudo nano /etc/systemd/system/hn-crawler.service
   ```

2. **服务配置**
   ```ini
   [Unit]
   Description=Hacker News Crawler
   After=network.target
   
   [Service]
   Type=simple
   User=your-user
   WorkingDirectory=/path/to/project
   ExecStart=/usr/bin/python3 run_daemon.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **启动服务**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable hn-crawler
   sudo systemctl start hn-crawler
   ```

#### 使用 Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "run_daemon.py"]
```

## 🔧 故障排除

### 常见问题

#### 1. 网络连接问题
```bash
# 检查网络连接
python -c "import requests; print(requests.get('https://news.ycombinator.com').status_code)"

# 测试代理连接
curl -x http://127.0.0.1:7890 https://news.ycombinator.com
```

#### 2. Telegram 发送失败
```bash
# 测试 Bot Token
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# 测试发送消息
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage" \
     -d "chat_id=<YOUR_CHAT_ID>&text=Test"
```

#### 3. 进程管理问题
```bash
# 查看运行进程
ps aux | grep python | grep crawler

# 强制停止
pkill -f "run_daemon.py"

# 检查端口占用
lsof -i :8080
```

### 日志分析

#### 关键日志信息
- `✅ 网络连接正常`: 网络状态良好
- `新增 X 条新闻`: 发现新内容
- `发送成功`: 消息推送成功
- `❌ 发送失败`: 需要检查网络或配置

#### 错误代码
- `HTTP 403`: 可能被反爬虫限制
- `HTTP 429`: API 请求频率过高
- `Connection timeout`: 网络连接超时

## 👨‍💻 开发指南

### 项目结构

```
├── README.md               # 项目主文档
├── LICENSE                 # MIT许可证
├── hn_news_crawler.py      # 主爬虫程序
├── run_daemon.py           # 守护进程启动器
├── run_once.py            # 单次运行脚本
├── manage_crawler.py      # 进程管理工具
├── config.env.example     # 配置文件模板
├── requirements.txt       # Python 依赖
├── docs/                  # 详细文档
│   ├── INDEX.md           # 文档导航
│   ├── API.md             # API文档
│   ├── PROJECT_SUMMARY.md # 项目总结
│   ├── TROUBLESHOOTING.md # 故障排除
│   └── HTTPX_COMPATIBILITY_FIX.md # 兼容性修复
├── .gitignore            # Git 忽略文件
├── data/                 # 数据存储目录
│   └── hn_news_*.csv     # 每日新闻数据
└── logs/                 # 日志目录
    └── hn_crawler.log    # 运行日志
```

### 代码规范

- **PEP 8**: Python 代码风格指南
- **类型注解**: 使用 typing 模块
- **文档字符串**: 详细的函数和类说明
- **错误处理**: 完善的异常捕获和处理

### 扩展开发

#### 添加新的数据源
```python
def get_new_source(self):
    """添加新的新闻源"""
    # 实现新的爬取逻辑
    pass
```

#### 自定义消息格式
```python
def custom_format_message(self, news):
    """自定义消息格式"""
    # 实现自定义格式
    pass
```

## 📚 详细文档

更多详细文档请查看 `docs` 目录：

- **[📋 文档导航](docs/INDEX.md)** - 所有文档的索引
- **[📚 API文档](docs/API.md)** - 详细的API接口说明
- **[📊 项目总结](docs/PROJECT_SUMMARY.md)** - 项目概述和技术架构
- **[🔧 故障排除](docs/TROUBLESHOOTING.md)** - 详细的问题解决指南
- **[🔧 兼容性修复](docs/HTTPX_COMPATIBILITY_FIX.md)** - httpx兼容性问题解决方案

## 📝 更新日志

### v2.1.0 (2025-05-24)
- 🔧 修复 httpx 兼容性问题
- 📚 重新整理文档结构，遵循国际惯例
- 🔒 清理敏感信息
- ✨ 优化配置管理系统

### v2.0.0 (2025-05-24)
- ✨ 重构核心爬虫引擎
- 🐛 修复 CSV 文件覆盖问题
- 🚀 优化守护进程管理
- 📱 改进 Telegram 消息格式
- 🔧 完善错误处理机制

### v1.0.0 (2025-05-23)
- 🎉 初始版本发布
- 📰 基础爬虫功能
- 🤖 Telegram 推送集成
- 🌐 代理支持

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

如有问题，请通过以下方式联系：
- 🐛 Issues: GitHub Issues
- 📧 邮件: 项目维护者

---

⭐ 如果这个项目对您有帮助，请给个 Star！