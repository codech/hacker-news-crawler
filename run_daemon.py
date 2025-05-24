#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hacker News 爬虫 - 守护进程版本（带文件锁）
确保只有一个实例运行，避免多进程竞争
"""

import os
import sys
import time
import fcntl
import asyncio
import logging
import schedule
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

class SingleInstanceDaemon:
    def __init__(self, lockfile):
        self.lockfile = lockfile
        self.lockfd = None
    
    def __enter__(self):
        try:
            self.lockfd = open(self.lockfile, 'w')
            fcntl.flock(self.lockfd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lockfd.write(str(os.getpid()))
            self.lockfd.flush()
            logging.info(f"🔒 获取文件锁成功: {self.lockfile}")
            return self
        except IOError:
            logging.error("❌ 另一个实例正在运行，退出")
            sys.exit(1)
    
    def __exit__(self, type, value, traceback):
        if self.lockfd:
            fcntl.flock(self.lockfd.fileno(), fcntl.LOCK_UN)
            self.lockfd.close()
            try:
                os.remove(self.lockfile)
            except:
                pass
            logging.info("🔓 释放文件锁")

def main():
    """主函数 - 带文件锁的守护进程"""
    lockfile = '/tmp/hn_crawler.lock'
    
    with SingleInstanceDaemon(lockfile):
        logging.info("🚀 启动Hacker News爬虫守护进程")
        
        # 创建爬虫实例
        crawler = HackerNewsCrawler()
        
        # 测试网络连接
        if not crawler.test_network_connection():
            logging.error("❌ 网络连接测试失败，请检查代理配置")
            return
        
        # 定义运行函数
        def run_crawler_instance():
            """运行爬虫实例"""
            try:
                logging.info("🔄 开始执行爬取任务...")
                asyncio.run(crawler.crawl_and_send())
                logging.info("✅ 爬取任务完成")
            except Exception as e:
                logging.error(f"❌ 爬虫执行失败: {e}")
        
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
                time.sleep(daemon_check_interval)  # 从配置文件读取检查间隔
        except KeyboardInterrupt:
            logging.info("👋 程序被用户中断")
        except Exception as e:
            logging.error(f"❌ 定时任务执行失败: {e}")
        finally:
            # 清理锁文件
            if os.path.exists(lockfile):
                os.remove(lockfile)
                logging.info("🧹 清理锁文件")

if __name__ == "__main__":
    main() 