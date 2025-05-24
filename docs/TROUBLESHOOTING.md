# 🔧 故障排除指南

## 概述

本文档提供了 Hacker News 爬虫系统常见问题的解决方案和调试方法。

## 🚨 常见问题

### 1. 启动问题

#### 问题：程序无法启动，提示配置错误

**错误信息**:
```
ValueError: 请配置TELEGRAM_BOT_TOKEN和TELEGRAM_CHAT_ID
```

**解决方案**:
1. 检查 `config.env` 文件是否存在
2. 确认配置文件中包含必需的配置项
3. 验证配置值格式正确

```bash
# 检查配置文件
cat config.env | grep -E "(TELEGRAM_BOT_TOKEN|TELEGRAM_CHAT_ID)"

# 验证 Bot Token 格式（应该类似：123456789:ABC-DEF...）
# 验证 Chat ID 格式（应该是数字，可能为负数）
```

#### 问题：依赖包安装失败

**错误信息**:
```
ModuleNotFoundError: No module named 'requests'
```

**解决方案**:
```bash
# 重新安装依赖
pip install -r requirements.txt

# 如果使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 2. 网络连接问题

#### 问题：无法访问 Hacker News

**错误信息**:
```
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='news.ycombinator.com', port=443)
```

**诊断步骤**:
```bash
# 1. 测试基本网络连接
ping news.ycombinator.com

# 2. 测试 HTTPS 连接
curl -I https://news.ycombinator.com

# 3. 检查代理设置
echo $http_proxy
echo $https_proxy
```

**解决方案**:
1. **网络问题**: 检查网络连接，确认可以访问外网
2. **防火墙**: 检查防火墙设置，确保允许 HTTPS 连接
3. **代理配置**: 如果需要代理，正确配置代理设置

```env
# 在 config.env 中启用代理
ENABLE_PROXY=true
PROXY_HTTP=http://your-proxy:port
PROXY_HTTPS=http://your-proxy:port
```

#### 问题：代理连接失败

**错误信息**:
```
requests.exceptions.ProxyError: HTTPSConnectionPool(host='127.0.0.1', port=7890)
```

**解决方案**:
1. 确认代理服务正在运行
2. 验证代理地址和端口正确
3. 测试代理连接

```bash
# 测试代理连接
curl -x http://127.0.0.1:7890 https://news.ycombinator.com

# 检查代理服务状态
netstat -an | grep 7890
```

### 3. Telegram 发送问题

#### 问题：Telegram 消息发送失败

**错误信息**:
```
telegram.error.Unauthorized: 401 Unauthorized
```

**诊断步骤**:
```bash
# 1. 验证 Bot Token
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# 2. 测试发送消息
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage" \
     -d "chat_id=<YOUR_CHAT_ID>&text=Test Message"
```

**解决方案**:
1. **Token 错误**: 重新获取 Bot Token
2. **权限问题**: 确保 Bot 有发送消息权限
3. **Chat ID 错误**: 重新获取正确的 Chat ID

#### 问题：消息发送频率限制

**错误信息**:
```
telegram.error.RetryAfter: Flood control exceeded. Retry in 30 seconds
```

**解决方案**:
1. 增加消息发送间隔
2. 减少批量发送数量

```env
# 在 config.env 中调整发送间隔
MESSAGE_SEND_INTERVAL=3.0
BULK_MESSAGE_INTERVAL=5.0
```

### 4. 数据处理问题

#### 问题：CSV 文件损坏

**错误信息**:
```
pandas.errors.ParserError: Error tokenizing data
```

**解决方案**:
```bash
# 1. 备份损坏的文件
cp data/hn_news_2025-05-24.csv data/hn_news_2025-05-24.csv.backup

# 2. 检查文件内容
head -10 data/hn_news_2025-05-24.csv
tail -10 data/hn_news_2025-05-24.csv

# 3. 重新创建文件（如果无法修复）
rm data/hn_news_2025-05-24.csv
python run_once.py
```

#### 问题：重复数据

**症状**: CSV 文件中出现重复的新闻记录

**解决方案**:
```python
# 使用内置的清理功能
from hn_news_crawler import HackerNewsCrawler
crawler = HackerNewsCrawler()
crawler.clean_duplicate_data()
```

### 5. 进程管理问题

#### 问题：多个进程同时运行

**症状**: 日志显示"新增新闻但没有发送"

**诊断**:
```bash
# 查看运行中的爬虫进程
ps aux | grep -E "(hn_news_crawler|run_daemon)" | grep -v grep
```

**解决方案**:
```bash
# 停止所有爬虫进程
pkill -f "hn_news_crawler.py"
pkill -f "run_daemon.py"

# 使用管理工具
python manage_crawler.py
```

#### 问题：进程无法启动（文件锁）

**错误信息**:
```
❌ 另一个实例正在运行，退出
```

**解决方案**:
```bash
# 检查锁文件
ls -la /tmp/hn_crawler.lock

# 删除锁文件（确保没有进程运行）
rm /tmp/hn_crawler.lock

# 重新启动
python run_daemon.py
```

### 6. 翻译问题

#### 问题：翻译服务失败

**错误信息**:
```
翻译失败: HTTPSConnectionPool(host='translate.googleapis.com', port=443)
```

**解决方案**:
1. 检查网络连接到 Google 服务
2. 确认代理配置正确
3. 临时禁用翻译功能

```env
# 临时禁用翻译
ENABLE_TRANSLATION=false
```

## 🔍 调试方法

### 1. 启用调试模式

```env
# 在 config.env 中启用调试
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

### 2. 查看详细日志

```bash
# 实时查看日志
tail -f hn_crawler.log

# 查看最近的错误
grep -i error hn_crawler.log | tail -20

# 查看特定时间的日志
grep "2025-05-24 21:" hn_crawler.log
```

### 3. 网络诊断

```bash
# 测试网络连接
python -c "
from hn_news_crawler import HackerNewsCrawler
crawler = HackerNewsCrawler()
print('网络测试:', crawler.test_network_connection())
"
```

### 4. 数据诊断

```python
# 检查 CSV 数据状态
import pandas as pd
from datetime import datetime

today = datetime.now().strftime('%Y-%m-%d')
df = pd.read_csv(f'data/hn_news_{today}.csv')

print(f"总记录数: {len(df)}")
print(f"已发送: {df['is_sent'].sum()}")
print(f"未发送: {(~df['is_sent']).sum()}")
```

## 📊 性能优化

### 1. 内存使用优化

```env
# 限制内存使用
MEMORY_LIMIT=256
CONCURRENT_REQUESTS=3
```

### 2. 网络优化

```env
# 调整网络参数
REQUEST_TIMEOUT=10
MAX_RETRIES=2
REQUEST_INTERVAL=0.5
```

### 3. 数据库优化

```bash
# 定期清理旧数据
find data/ -name "hn_news_*.csv" -mtime +30 -delete

# 压缩日志文件
gzip hn_crawler.log.old
```

## 🚨 紧急恢复

### 1. 完全重置

```bash
# 停止所有进程
pkill -f "hn_news_crawler"
pkill -f "run_daemon"

# 清理锁文件
rm -f /tmp/hn_crawler.lock

# 备份数据
cp -r data/ data_backup_$(date +%Y%m%d_%H%M%S)/

# 重新启动
python run_daemon.py
```

### 2. 数据恢复

```bash
# 从备份恢复
cp data_backup_20250524_210000/* data/

# 或重新开始
rm data/hn_news_*.csv
python run_once.py
```

## 📞 获取帮助

### 1. 收集诊断信息

```bash
# 创建诊断报告
echo "=== 系统信息 ===" > diagnosis.txt
python --version >> diagnosis.txt
pip list | grep -E "(requests|pandas|telegram)" >> diagnosis.txt

echo "=== 配置信息 ===" >> diagnosis.txt
cat config.env | grep -v TOKEN | grep -v SECRET >> diagnosis.txt

echo "=== 进程信息 ===" >> diagnosis.txt
ps aux | grep python >> diagnosis.txt

echo "=== 最近日志 ===" >> diagnosis.txt
tail -50 hn_crawler.log >> diagnosis.txt
```

### 2. 联系支持

提供以下信息：
- 操作系统和 Python 版本
- 错误信息和日志
- 配置文件（隐藏敏感信息）
- 重现步骤

### 3. 社区资源

- GitHub Issues: 报告 Bug 和功能请求
- 文档: 查看最新文档和示例
- FAQ: 常见问题快速解答

## 📝 预防措施

### 1. 定期维护

```bash
# 创建维护脚本
cat > maintenance.sh << 'EOF'
#!/bin/bash
# 每周维护脚本

# 清理旧日志
find . -name "*.log.*" -mtime +7 -delete

# 备份数据
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# 检查磁盘空间
df -h .

# 重启服务
python manage_crawler.py restart
EOF

chmod +x maintenance.sh
```

### 2. 监控设置

```bash
# 添加到 crontab
crontab -e

# 每小时检查进程状态
0 * * * * /path/to/project/scripts/health_check.sh

# 每天备份数据
0 2 * * * /path/to/project/maintenance.sh
```

### 3. 日志轮转

```env
# 启用日志轮转
ENABLE_LOG_ROTATION=true
LOG_MAX_SIZE=10
LOG_BACKUP_COUNT=5
``` 