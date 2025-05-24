#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hacker News 爬虫 - 单次运行版本
只执行一次爬取和发送，不启动定时任务
"""

import asyncio
import logging
from hn_news_crawler import HackerNewsCrawler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hn_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def main():
    """单次运行主函数"""
    logging.info("🚀 开始单次爬取...")
    
    # 创建爬虫实例
    crawler = HackerNewsCrawler()
    
    # 测试网络连接
    if not crawler.test_network_connection():
        logging.error("❌ 网络连接测试失败，请检查代理配置")
        return
    
    # 执行一次爬取和发送
    try:
        asyncio.run(crawler.crawl_and_send())
        logging.info("✅ 单次爬取完成")
    except Exception as e:
        logging.error(f"❌ 爬虫执行失败: {e}")

if __name__ == "__main__":
    main() 