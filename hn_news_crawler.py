#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hacker News 爬虫 - 完整版本

功能特性：
- 获取HN首页所有新闻（不限制数量）
- 自动翻译标题和内容摘要
- 按日期存储到CSV文件
- 发送所有未发送新闻到Telegram
- 支持代理配置
- 自动去重和错误处理

作者: Bruce Chen
版本: 2.0
更新: 2025-05-24
"""

import os
import sys
import json
import time
import asyncio
import logging
import schedule
import threading
import subprocess
import urllib.parse
import csv
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import Bot
import httpx

class HackerNewsCrawler:
    def __init__(self):
        # 加载环境变量
        load_dotenv('config.env')
        
        # 从配置文件读取所有配置
        self.base_url = os.getenv('BASE_URL', 'https://news.ycombinator.com')
        self.max_news_count = int(os.getenv('MAX_NEWS_COUNT', 100))
        self.min_score = int(os.getenv('MIN_SCORE', 0))
        
        # 网络配置
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', 15))
        self.connection_test_timeout = int(os.getenv('CONNECTION_TEST_TIMEOUT', 10))
        self.translation_timeout = int(os.getenv('TRANSLATION_TIMEOUT', 10))
        self.telegram_timeout = int(os.getenv('TELEGRAM_TIMEOUT', 15))
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.request_interval = float(os.getenv('REQUEST_INTERVAL', 0.3))
        
        # 消息发送配置
        self.message_send_interval = float(os.getenv('MESSAGE_SEND_INTERVAL', 1.0))
        self.message_retry_interval = float(os.getenv('MESSAGE_RETRY_INTERVAL', 2.0))
        self.bulk_message_interval = float(os.getenv('BULK_MESSAGE_INTERVAL', 3.0))
        self.message_max_retries = int(os.getenv('MESSAGE_MAX_RETRIES', 2))
        
        # 功能开关
        self.enable_translation = os.getenv('ENABLE_TRANSLATION', 'true').lower() == 'true'
        self.enable_content_summary = os.getenv('ENABLE_CONTENT_SUMMARY', 'true').lower() == 'true'
        
        # 性能配置
        self.max_translation_length = int(os.getenv('MAX_TRANSLATION_LENGTH', 400))
        self.max_summary_length = int(os.getenv('MAX_SUMMARY_LENGTH', 200))
        self.max_title_length = int(os.getenv('MAX_TITLE_LENGTH', 200))
        
        # Telegram配置
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("请配置TELEGRAM_BOT_TOKEN和TELEGRAM_CHAT_ID")
        
        # 配置代理 - 支持开关控制
        self.proxies = {}
        enable_proxy = os.getenv('ENABLE_PROXY', 'false').lower() == 'true'
        
        if enable_proxy:
            proxy_http = os.getenv('PROXY_HTTP') or os.getenv('http_proxy')
            proxy_https = os.getenv('PROXY_HTTPS') or os.getenv('https_proxy')
            
            if proxy_http:
                self.proxies['http'] = proxy_http
                self.proxies['https'] = proxy_https or proxy_http
                logging.info(f"✅ 代理已启用: {proxy_http}")
            else:
                logging.warning("⚠️ 代理开关已开启但未配置代理地址，使用直连模式")
        else:
            logging.info("🌐 代理开关已关闭，使用直连模式")
        
        # 初始化Telegram Bot
        self.bot = Bot(token=self.bot_token)
        logging.info("🤖 Telegram Bot 初始化成功")
        
        # HTTP请求头
        self.headers = {
            'User-Agent': os.getenv('USER_AGENT', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        }
        
        # CSV文件配置
        self.data_dir = os.getenv('DATA_DIR', 'data')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # 今日CSV文件
        today = datetime.now().strftime('%Y-%m-%d')
        self.csv_file = os.path.join(self.data_dir, f'hn_news_{today}.csv')
        
        # CSV列名 - 从配置文件读取
        csv_columns_str = os.getenv('CSV_COLUMNS', 'id,title,title_cn,url,hn_url,score,comments,content_summary,content_summary_cn,crawl_time,sent_time,is_sent')
        self.csv_columns = [col.strip() for col in csv_columns_str.split(',')]
        
        # 初始化CSV文件
        self.init_csv_file()
        
        # 配置日志
        self.setup_logging()
        
        logging.info(f"CSV文件: {self.csv_file}")
    
    def setup_logging(self):
        """配置日志系统"""
        log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper())
        log_file = os.getenv('LOG_FILE', 'hn_crawler.log')
        log_format = os.getenv('LOG_FORMAT', '%(asctime)s - %(levelname)s - %(message)s')
        
        # 清除现有的处理器
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # 重新配置日志
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def init_csv_file(self):
        """初始化CSV文件"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_columns)
                writer.writeheader()
            logging.info(f"创建新的CSV文件: {self.csv_file}")
        else:
            # 清理重复数据
            self.clean_duplicate_data()
    
    def clean_duplicate_data(self):
        """清理CSV中的重复数据，保留最新的记录"""
        try:
            df = self.load_news_data()
            
            if df.empty:
                return
            
            original_count = len(df)
            
            # 按id去重，保留最后一条记录（最新的）
            # 对于已发送的记录，优先保留已发送状态
            df['is_sent'] = df['is_sent'].fillna(False).astype(bool)
            df = df.sort_values(['id', 'is_sent'], ascending=[True, False])
            df_cleaned = df.drop_duplicates(subset=['id'], keep='first')
            
            if len(df_cleaned) < original_count:
                # 保存清理后的数据
                df_cleaned.to_csv(self.csv_file, index=False, encoding='utf-8')
                removed_count = original_count - len(df_cleaned)
                logging.info(f"清理重复数据: 移除 {removed_count} 条重复记录，保留 {len(df_cleaned)} 条")
            else:
                logging.debug("没有发现重复数据")
                
        except Exception as e:
            logging.error(f"清理重复数据失败: {e}")
    
    def load_news_data(self):
        """加载今日新闻数据"""
        try:
            if os.path.exists(self.csv_file):
                df = pd.read_csv(self.csv_file)
                return df
            else:
                return pd.DataFrame(columns=self.csv_columns)
        except Exception as e:
            logging.error(f"加载CSV数据失败: {e}")
            return pd.DataFrame(columns=self.csv_columns)
    
    def save_news_to_csv(self, news_item):
        """保存新闻到CSV，严格去重"""
        try:
            df = self.load_news_data()
            
            # 修复数据类型问题：统一转换为字符串进行比较
            news_id = str(news_item['id'])
            existing = df[df['id'].astype(str) == news_id]
            
            if not existing.empty:
                # 如果记录已存在，只更新分数和评论数（这些可能会变化）
                mask = df['id'].astype(str) == news_id
                df.loc[mask, ['score', 'comments']] = [
                    news_item['score'],
                    news_item['comments']
                ]
                
                # 保存到CSV
                df.to_csv(self.csv_file, index=False, encoding='utf-8')
                logging.debug(f"更新现有新闻分数/评论: {news_item['title']}")
                return False  # 返回False表示不是新增记录
            else:
                # 添加新记录
                new_row = {
                    'id': news_item['id'],  # 保持原始类型，CSV会自动转换
                    'title': news_item['title'],
                    'title_cn': news_item.get('title_cn', ''),
                    'url': news_item['url'],
                    'hn_url': news_item['hn_url'],
                    'score': news_item['score'],
                    'comments': news_item['comments'],
                    'content_summary': news_item.get('content_summary', ''),
                    'content_summary_cn': news_item.get('content_summary_cn', ''),
                    'crawl_time': datetime.now().isoformat(),
                    'sent_time': '',
                    'is_sent': False
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                
                # 保存到CSV
                df.to_csv(self.csv_file, index=False, encoding='utf-8')
                logging.info(f"保存新新闻: {news_item['title']}")
                return True  # 返回True表示是新增记录
            
        except Exception as e:
            logging.error(f"保存新闻失败: {e}")
            return False
    
    def mark_news_as_sent(self, news_id):
        """标记新闻为已发送"""
        try:
            df = self.load_news_data()
            
            # 修复数据类型问题：统一转换为字符串进行比较
            news_id_str = str(news_id)
            mask = (df['id'].astype(str) == news_id_str) & (df['is_sent'] == False)
            
            if mask.any():
                df.loc[mask, 'is_sent'] = True
                df.loc[mask, 'sent_time'] = datetime.now().isoformat()
                
                # 保存到CSV
                df.to_csv(self.csv_file, index=False, encoding='utf-8')
                logging.debug(f"标记为已发送: {news_id}")
                return True
            else:
                logging.warning(f"未找到可标记的新闻: {news_id}")
                return False
                
        except Exception as e:
            logging.error(f"标记失败: {e}")
            return False
    
    def get_unsent_news_from_csv(self):
        """获取所有未发送的新闻，按爬取时间顺序，不限制数量"""
        try:
            df = self.load_news_data()
            
            if df.empty:
                return []
            
            # 只筛选未发送的新闻，移除翻译条件限制
            df['is_sent'] = df['is_sent'].fillna(False)
            df['is_sent'] = df['is_sent'].astype(bool)
            
            unsent = df[df['is_sent'] == False].copy()
            
            if unsent.empty:
                logging.info("没有符合条件的未发送新闻")
                return []
            
            # 按爬取时间排序（最新的在前）
            unsent['crawl_time'] = pd.to_datetime(unsent['crawl_time'])
            unsent = unsent.sort_values('crawl_time', ascending=False)
            
            # 发送所有未发送的新闻，不限制数量
            
            logging.info(f"找到 {len(unsent)} 条未发送新闻")
            
            news_list = []
            for _, row in unsent.iterrows():
                news_list.append({
                    'id': row['id'],
                    'title': row['title'],
                    'title_cn': row['title_cn'] if pd.notna(row['title_cn']) else row['title'],  # 如果没有翻译就用原标题
                    'url': row['url'],
                    'hn_url': row['hn_url'],
                    'score': int(row['score']),
                    'comments': int(row['comments']),
                    'content_summary': row['content_summary'] if pd.notna(row['content_summary']) else '',
                    'content_summary_cn': row['content_summary_cn'] if pd.notna(row['content_summary_cn']) else '暂无内容摘要',
                    'crawl_time': row['crawl_time']
                })
            
            return news_list
            
        except Exception as e:
            logging.error(f"获取未发送新闻失败: {e}")
            return []
    
    def get_hn_frontpage(self):
        """获取HN首页所有新闻"""
        try:
            logging.info("🔍 开始获取HN首页新闻...")
            response = requests.get(
                self.base_url,
                headers=self.headers,
                proxies=self.proxies,
                timeout=self.request_timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []
            
            rows = soup.find_all('tr', class_='athing')
            
            # 获取首页所有新闻，不限制数量
            for i, row in enumerate(rows):
                try:
                    news_id = row.get('id')
                    if not news_id:
                        continue
                    
                    title_cell = row.find('span', class_='titleline')
                    if not title_cell:
                        continue
                    
                    title_link = title_cell.find('a')
                    if not title_link:
                        continue
                    
                    title = title_link.get_text().strip()
                    url = title_link.get('href', '')
                    
                    if url.startswith('item?'):
                        url = urljoin(self.base_url, url)
                    
                    # 获取分数和评论数
                    next_row = row.find_next_sibling('tr')
                    score = 0
                    comments = 0
                    
                    if next_row:
                        score_span = next_row.find('span', class_='score')
                        if score_span:
                            score_text = score_span.get_text()
                            score = int(score_text.split()[0]) if score_text else 0
                        
                        comments_link = next_row.find('a', string=lambda text: text and 'comment' in text)
                        if comments_link:
                            comments_text = comments_link.get_text()
                            comments = int(comments_text.split()[0]) if comments_text.split()[0].isdigit() else 0
                    
                    # 添加所有新闻，不过滤分数
                    news_items.append({
                        'id': news_id,
                        'title': title,
                        'url': url,
                        'score': score,
                        'comments': comments,
                        'hn_url': f"{self.base_url}/item?id={news_id}",
                        'rank': i + 1  # 保存原始排名
                    })
                    
                except Exception as e:
                    logging.error(f"解析新闻失败: {e}")
                    continue
            
            logging.info(f"获取到 {len(news_items)} 条新闻")
            return news_items
            
        except Exception as e:
            logging.error(f"获取HN首页失败: {e}")
            return []
    
    def get_article_content(self, url):
        """获取文章内容，改进错误处理"""
        try:
            if 'news.ycombinator.com' in url and '/item?' in url:
                return "这是一个HN讨论帖"
            
            # 添加更多请求头，避免403错误
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(
                url,
                headers=self.headers,
                proxies=self.proxies,
                timeout=self.request_timeout,
                allow_redirects=True
            )
            
            # 如果状态码不是200，返回简单描述
            if response.status_code != 200:
                logging.warning(f"HTTP {response.status_code} for {url}")
                return "无法获取文章内容"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除不需要的元素
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # 尝试找到主要内容
            content = ""
            for selector in ['article', 'main', '.content', '.post', '.entry']:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text()
                    break
            
            if not content:
                content = soup.get_text()
            
            # 清理内容
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if len(line) > 20 and not line.startswith(('http', 'www', '@')):
                    cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines[:8])  # 取前8行
            
        except requests.exceptions.RequestException as e:
            logging.warning(f"网络请求失败 {url}: {e}")
            return "网络请求失败，无法获取内容"
        except Exception as e:
            logging.error(f"获取文章内容失败 {url}: {e}")
            return "内容获取失败"
    
    def translate_text(self, text):
        """改进的翻译功能"""
        if not text or len(text.strip()) < 3:
            return text
        
        try:
            import re
            
            # 清理文本
            text = text.strip()
            text = re.sub(r'\s+', ' ', text)
            
            # 限制文本长度，避免API限制
            if len(text) > self.max_translation_length:
                text = text[:self.max_translation_length] + "..."
            
            # 检查是否已经是中文
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            if chinese_chars > len(text) * 0.3:
                return text
            
            # 构建翻译URL
            encoded_text = urllib.parse.quote(text)
            translate_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh&dt=t&q={encoded_text}"
            
            response = requests.get(
                translate_url,
                headers=self.headers,
                proxies=self.proxies,
                timeout=self.translation_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and len(result[0]) > 0:
                    translated = ""
                    for item in result[0]:
                        if item[0]:
                            translated += item[0]
                    
                    # 清理翻译结果
                    translated = translated.strip()
                    translated = re.sub(r'\s+', ' ', translated)
                    
                    # 简单的翻译质量检查
                    if len(translated) > 5 and translated != text:
                        return translated
            
            return text
            
        except Exception as e:
            logging.warning(f"翻译失败: {e}")
            return text
    
    def clean_and_summarize_content(self, content):
        """内容清理和摘要"""
        if not content or len(content) < 30:
            return "暂无内容摘要"
        
        import re
        
        # 移除HTML标签
        content = re.sub(r'<[^>]+>', '', content)
        
        # 分句
        sentences = re.split(r'[.!?]+\s+', content)
        good_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if (20 <= len(sentence) <= 120 and
                not sentence.startswith(('http', 'www', '@', '#')) and
                sentence.count(' ') >= 2):
                good_sentences.append(sentence)
        
        # 取前2句
        summary = '. '.join(good_sentences[:2])
        if summary and not summary.endswith('.'):
            summary += '.'
        
        return summary if summary else "暂无内容摘要"
    
    async def send_telegram_message(self, message, max_retries=None):
        """发送Telegram消息"""
        if max_retries is None:
            max_retries = self.message_max_retries
            
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    proxies=self.proxies,
                    timeout=self.telegram_timeout
                ) as client:
                    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                    data = {
                        'chat_id': self.chat_id,
                        'text': message,
                        'parse_mode': 'HTML',
                        'disable_web_page_preview': False
                    }
                    
                    response = await client.post(url, data=data)
                    response.raise_for_status()
                    
                    await asyncio.sleep(self.message_send_interval)
                    return True
                    
            except httpx.TimeoutException:
                logging.warning(f"⏰ 发送超时 (尝试 {attempt + 1}/{max_retries + 1})")
                if attempt < max_retries:
                    await asyncio.sleep(self.message_retry_interval)  # 超时后等待更长时间
                    
            except Exception as e:
                logging.error(f"❌ 发送失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                if attempt < max_retries:
                    await asyncio.sleep(self.message_send_interval)
                    
        return False
    
    def format_message(self, news, index, total):
        """商务风格的消息格式，移除翻译条件限制"""
        # 如果有中文翻译就用翻译，否则用原标题
        title = news.get('title_cn') if news.get('title_cn') and news.get('title_cn') != news['title'] else news['title']
        
        # 摘要处理：优先使用中文摘要，其次英文摘要，最后默认文本
        summary = news.get('content_summary_cn')
        if not summary or summary == '暂无内容摘要':
            summary = news.get('content_summary', '暂无内容摘要')
        if not summary:
            summary = "暂无内容摘要"
        
        # 限制摘要长度
        if len(summary) > 180:
            summary = summary[:180] + "..."
        
        # 商务化的分数等级描述
        if news['score'] > 500:
            popularity = "🔥 热门话题"
            score_level = "极高关注"
        elif news['score'] > 200:
            popularity = "⭐ 高度关注"
            score_level = "高关注度"
        elif news['score'] > 100:
            popularity = "📈 持续关注"
            score_level = "中等关注"
        else:
            popularity = "📊 新兴话题"
            score_level = "初期关注"
        
        # 讨论活跃度描述
        if news['comments'] > 100:
            discussion = "💬 讨论热烈"
        elif news['comments'] > 50:
            discussion = "💭 讨论活跃"
        elif news['comments'] > 10:
            discussion = "📝 有所讨论"
        else:
            discussion = "🔍 待深入讨论"
        
        # 时间格式化
        crawl_time = ""
        if 'crawl_time' in news:
            try:
                if isinstance(news['crawl_time'], str):
                    dt = datetime.fromisoformat(news['crawl_time'].replace('Z', '+00:00'))
                else:
                    dt = news['crawl_time']
                crawl_time = dt.strftime("%H:%M")
            except:
                crawl_time = ""
        
        # 商务风格的消息格式
        message = f"""<b>📰 Hacker News 科技资讯 #{index}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>🔥 {title}</b>

<b>📊 数据概览</b>
• {popularity} ({news['score']} 分)
• {discussion} ({news['comments']} 条评论)
• 发布时间: {crawl_time}

<b>📝 内容摘要</b>
{summary}

<b>🔗 相关链接</b>
• <a href="{news['url']}">查看原文</a>
• <a href="{news['hn_url']}">参与讨论</a>

<i>第 {index} 条，共 {total} 条资讯</i>"""
        
        return message
    
    async def send_batch_header(self, count):
        """简化的批次开始消息"""
        current_time = datetime.now().strftime("%H:%M")
        
        header = f"""📰 <b>HN科技资讯</b> ({count}条)

⏰ {current_time} | 🔥 news.ycombinator.com

━━━━━━━━━━━━━━━━━━━━"""
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=header,
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"发送批次消息失败: {e}")
    
    async def send_completion_message(self, success_count, total_count):
        """简化的完成消息"""
        next_time = (datetime.now() + timedelta(minutes=int(os.getenv('CHECK_INTERVAL_MINUTES', 1)))).strftime('%H:%M')
        
        completion_msg = f"""✅ <b>推送完成</b>

📊 成功: {success_count}/{total_count}
⏰ 下次: {next_time}

━━━━━━━━━━━━━━━━━━━━"""
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=completion_msg,
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"发送完成消息失败: {e}")
    
    async def crawl_and_send(self):
        """主要爬取和发送逻辑，优化去重"""
        logging.info("开始爬取...")
        
        # 获取新闻
        news_list = self.get_hn_frontpage()
        if not news_list:
            logging.warning("未获取到新闻")
            return
        
        # 加载现有数据，避免重复处理
        existing_df = self.load_news_data()
        # 修复数据类型问题：将ID统一转换为字符串进行比较
        existing_ids = set(str(id_val) for id_val in existing_df['id'].tolist()) if not existing_df.empty else set()
        
        # 处理新闻
        new_count = 0
        updated_count = 0
        processed_count = 0
        
        for news in news_list:
            try:
                processed_count += 1
                # 确保新闻ID也是字符串
                news_id = str(news['id'])
                
                # 如果新闻已存在，只更新分数和评论数
                if news_id in existing_ids:
                    # 通过save_news_to_csv来更新，它会正确处理现有记录
                    self.save_news_to_csv(news)
                    updated_count += 1
                    logging.info(f"更新现有新闻 ({processed_count}/{len(news_list)}): {news['title']}")
                    continue
                
                # 处理新新闻
                logging.info(f"处理新新闻 ({processed_count}/{len(news_list)}): {news['title']}")
                
                # 获取内容
                content = self.get_article_content(news['url'])
                
                # 翻译标题
                news['title_cn'] = self.translate_text(news['title'])
                
                # 处理摘要
                news['content_summary'] = self.clean_and_summarize_content(content)
                news['content_summary_cn'] = self.translate_text(news['content_summary'])
                
                # 保存到CSV
                if self.save_news_to_csv(news):
                    new_count += 1
                    existing_ids.add(news_id)  # 添加到已存在ID集合
                
                await asyncio.sleep(0.3)  # 避免请求过快
                
            except Exception as e:
                logging.error(f"处理新闻失败: {e}")
                continue
        
        # 分数和评论数的更新已经在save_news_to_csv中处理了
        if updated_count > 0:
            logging.info(f"更新 {updated_count} 条现有新闻的分数/评论数")
        
        if new_count > 0:
            logging.info(f"新增 {new_count} 条新闻")
        else:
            logging.info("没有新增新闻")
        
        # 获取未发送的新闻
        unsent_news = self.get_unsent_news_from_csv()
        
        if not unsent_news:
            logging.info("没有新闻需要发送")
            return
        
        logging.info(f"准备发送 {len(unsent_news)} 条新闻")
        
        # 发送新闻
        success_count = 0
        for i, news in enumerate(unsent_news, 1):
            try:
                message = self.format_message(news, i, len(unsent_news))
                success = await self.send_telegram_message(message)
                
                if success:
                    self.mark_news_as_sent(news['id'])
                    success_count += 1
                    logging.info(f"✅ 发送成功 ({i}/{len(unsent_news)}): {news['title']}")
                else:
                    logging.error(f"❌ 发送失败 ({i}/{len(unsent_news)}): {news['title']}")
                
                # 控制发送频率，避免API限制
                if i < len(unsent_news):  # 不是最后一条消息
                    await asyncio.sleep(self.request_interval)  # 避免请求过快
                
            except Exception as e:
                logging.error(f"❌ 处理新闻失败: {e}")
        
        # 发送完成消息
        if len(unsent_news) > 0:
            # 大批量发送时增加延迟
            delay = self.bulk_message_interval if len(unsent_news) > 20 else self.message_send_interval
            await asyncio.sleep(delay)
        
        if success_count > 0:
            try:
                await self.send_completion_message(success_count, len(unsent_news))
            except Exception as e:
                logging.warning(f"发送完成消息失败: {e}")
        
        logging.info(f"发送完成: {success_count}/{len(unsent_news)}")

    def test_network_connection(self):
        """测试网络连接"""
        try:
            # 测试HN网站连接
            response = requests.get(
                self.base_url,
                headers=self.headers,
                proxies=self.proxies,
                timeout=self.connection_test_timeout
            )
            
            if response.status_code == 200:
                logging.info("✅ HN网站连接正常")
            else:
                logging.warning(f"⚠️ HN网站连接异常: HTTP {response.status_code}")
            
            # 测试Telegram API连接
            if self.proxies:
                import httpx
                proxy_url = self.proxies.get('https', self.proxies.get('http'))
                
                async def test_telegram():
                    try:
                        async with httpx.AsyncClient(proxies=proxy_url, timeout=self.connection_test_timeout) as client:
                            response = await client.get(f"https://api.telegram.org/bot{self.bot_token}/getMe")
                            if response.status_code == 200:
                                result = response.json()
                                if result.get('ok'):
                                    logging.info("✅ Telegram API 连接正常")
                                    return True
                        return False
                    except Exception as e:
                        logging.warning(f"⚠️ Telegram API 连接失败: {e}")
                        return False
                
                # 运行异步测试
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果已经在事件循环中，创建新的任务
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, test_telegram())
                            return future.result()
                    else:
                        return asyncio.run(test_telegram())
                except Exception as e:
                    logging.error(f"❌ 异步测试失败: {e}")
                    return False
            else:
                # 直连模式测试 - 使用同步方式
                try:
                    # 简单测试Telegram API（使用requests）
                    telegram_response = requests.get(
                        f"https://api.telegram.org/bot{self.bot_token}/getMe",
                        proxies=self.proxies,
                        timeout=self.connection_test_timeout
                    )
                    
                    if telegram_response.status_code == 200:
                        result = telegram_response.json()
                        if result.get('ok'):
                            bot_info = result.get('result', {})
                            logging.info(f"✅ Telegram API连接正常 - Bot: {bot_info.get('username', 'Unknown')}")
                            return True
                    
                    logging.warning(f"⚠️ Telegram API连接异常: {telegram_response.status_code}")
                    return False
                except Exception as e:
                    logging.error(f"❌ Telegram API连接失败: {e}")
                    return False
                    
        except Exception as e:
            logging.error(f"❌ 网络连接测试失败: {e}")
            return False

def main():
    """主函数"""
    enable_web = os.getenv('ENABLE_WEB', 'false').lower() == 'true'
    
    if enable_web:
        logging.info("🌐 Web功能已启用")
        # Web功能代码...
    else:
        logging.info("🚫 Web功能已禁用")
    
    # 创建爬虫实例并测试连接
    crawler = HackerNewsCrawler()
    
    # 测试网络连接
    if not crawler.test_network_connection():
        logging.error("❌ 网络连接测试失败，请检查代理配置")
        return
    
    # 定义运行函数，使用同一个爬虫实例
    def run_crawler_instance():
        """运行爬虫实例"""
        try:
            asyncio.run(crawler.crawl_and_send())
        except Exception as e:
            logging.error(f"爬虫执行失败: {e}")
    
    # 立即执行一次
    logging.info("🚀 立即执行第一次爬取...")
    run_crawler_instance()
    
    # 设置定时任务
    interval_minutes = int(os.getenv('CHECK_INTERVAL_MINUTES', 5))
    schedule.every(interval_minutes).minutes.do(run_crawler_instance)
    logging.info(f"⏰ 定时任务: 每 {interval_minutes} 分钟执行一次")
    
    # 运行定时任务
    daemon_check_interval = int(os.getenv('DAEMON_CHECK_INTERVAL', 30))
    try:
        while True:
            schedule.run_pending()
            time.sleep(daemon_check_interval)
    except KeyboardInterrupt:
        logging.info("👋 程序被用户中断")
    except Exception as e:
        logging.error(f"❌ 定时任务执行失败: {e}")

if __name__ == "__main__":
    main() 
