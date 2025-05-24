#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hacker News 爬虫管理工具
用于启动、停止、检查爬虫进程状态
"""

import os
import sys
import subprocess
import signal
import time
from datetime import datetime
import logging
from dotenv import load_dotenv

# 加载配置
load_dotenv('config.env')

# 配置日志
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper()),
    format=os.getenv('LOG_FORMAT', '%(asctime)s - %(levelname)s - %(message)s')
)

def get_crawler_processes():
    """获取爬虫相关进程"""
    try:
        # 查找爬虫进程
        result = subprocess.run(
            ['ps', 'aux'], 
            capture_output=True, 
            text=True
        )
        
        processes = []
        for line in result.stdout.split('\n'):
            if ('hn_news_crawler.py' in line or 'run.py' in line) and 'grep' not in line:
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    command = ' '.join(parts[10:])
                    processes.append({'pid': pid, 'command': command})
        
        return processes
    except Exception as e:
        print(f"❌ 获取进程失败: {e}")
        return []

def show_status():
    """显示爬虫状态"""
    print("🔍 检查爬虫进程状态...")
    print("=" * 60)
    
    processes = get_crawler_processes()
    
    if not processes:
        print("✅ 没有运行中的爬虫进程")
    else:
        print(f"🔄 发现 {len(processes)} 个运行中的爬虫进程:")
        for proc in processes:
            print(f"  PID: {proc['pid']} | {proc['command']}")
    
    print()

def stop_crawler(self):
    """停止爬虫进程"""
    processes = get_crawler_processes()
    if not processes:
        print("❌ 没有找到运行中的爬虫进程")
        return False
    
    process_wait_time = int(os.getenv('PROCESS_WAIT_TIME', 2))
    process_stop_wait_time = int(os.getenv('PROCESS_STOP_WAIT_TIME', 3))
    
    for pid, cmd in processes:
        try:
            print(f"🛑 停止进程 {pid}: {cmd}")
            os.kill(pid, signal.SIGTERM)
            time.sleep(process_wait_time)  # 从配置文件读取等待时间
            
            # 检查进程是否已停止
            try:
                os.kill(pid, 0)  # 检查进程是否存在
                print(f"⚠️ 进程 {pid} 未响应SIGTERM，使用SIGKILL")
                os.kill(pid, signal.SIGKILL)
                time.sleep(process_stop_wait_time)  # 从配置文件读取停止等待时间
            except ProcessLookupError:
                print(f"✅ 进程 {pid} 已停止")
                
        except ProcessLookupError:
            print(f"⚠️ 进程 {pid} 不存在")
        except Exception as e:
            print(f"❌ 停止进程 {pid} 失败: {e}")
    
    return True

def start_daemon():
    """启动后台守护进程"""
    print("🚀 启动后台守护进程...")
    
    # 先停止现有进程
    stop_crawler()
    
    try:
        # 启动新的后台进程
        subprocess.Popen(
            [sys.executable, 'run.py'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        print("✅ 后台守护进程已启动")
        
        # 等待一下再检查状态
        time.sleep(3)
        show_status()
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def run_once():
    """运行一次"""
    print("⚡ 执行单次爬取...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'run_once.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 单次爬取完成")
        else:
            print(f"❌ 单次爬取失败: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 执行失败: {e}")

def show_logs():
    """显示最近的日志"""
    print("📋 最近的日志 (最后20行):")
    print("=" * 60)
    
    try:
        if os.path.exists('hn_crawler.log'):
            with open('hn_crawler.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    print(line.rstrip())
        else:
            print("❌ 日志文件不存在")
    except Exception as e:
        print(f"❌ 读取日志失败: {e}")

def main():
    """主菜单"""
    while True:
        print("\n" + "="*60)
        print("🤖 Hacker News 爬虫管理工具")
        print("="*60)
        print("1. 查看状态")
        print("2. 启动后台守护进程")
        print("3. 停止所有进程")
        print("4. 运行一次")
        print("5. 查看日志")
        print("0. 退出")
        print("-"*60)
        
        choice = input("请选择操作 (0-5): ").strip()
        
        if choice == '1':
            show_status()
        elif choice == '2':
            start_daemon()
        elif choice == '3':
            stop_all()
        elif choice == '4':
            run_once()
        elif choice == '5':
            show_logs()
        elif choice == '0':
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    main() 