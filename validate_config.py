#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证脚本
用于验证config.env中的所有配置项是否正确加载
"""

import os
import sys

def load_config():
    """加载配置文件"""
    try:
        # 尝试加载python-dotenv
        try:
            from dotenv import load_dotenv
            load_dotenv('config.env')
            print("✅ 使用python-dotenv加载配置")
        except ImportError:
            print("⚠️ python-dotenv未安装，使用手动解析")
            # 手动解析配置文件
            if os.path.exists('config.env'):
                with open('config.env', 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
            else:
                print("❌ config.env文件不存在")
                return False
        
        return True
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return False

def validate_config():
    """验证配置项"""
    print("\n🔍 验证配置项...")
    
    # 必需配置
    required_configs = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID'
    ]
    
    # 网络配置
    network_configs = [
        'BASE_URL',
        'REQUEST_TIMEOUT',
        'CONNECTION_TEST_TIMEOUT',
        'TRANSLATION_TIMEOUT',
        'TELEGRAM_TIMEOUT',
        'MAX_RETRIES',
        'REQUEST_INTERVAL',
        'USER_AGENT'
    ]
    
    # 消息配置
    message_configs = [
        'MESSAGE_SEND_INTERVAL',
        'MESSAGE_RETRY_INTERVAL',
        'BULK_MESSAGE_INTERVAL',
        'MESSAGE_MAX_RETRIES'
    ]
    
    # 数据存储配置
    storage_configs = [
        'DATA_DIR',
        'CSV_ENCODING',
        'CSV_COLUMNS'
    ]
    
    # 日志配置
    log_configs = [
        'LOG_LEVEL',
        'LOG_FILE',
        'LOG_FORMAT'
    ]
    
    # 功能开关
    feature_configs = [
        'ENABLE_TRANSLATION',
        'ENABLE_CONTENT_SUMMARY',
        'ENABLE_PROXY',
        'ENABLE_WEB'
    ]
    
    # 进程管理配置
    process_configs = [
        'DAEMON_CHECK_INTERVAL',
        'PROCESS_WAIT_TIME',
        'PROCESS_STOP_WAIT_TIME'
    ]
    
    all_configs = {
        '必需配置': required_configs,
        '网络配置': network_configs,
        '消息配置': message_configs,
        '存储配置': storage_configs,
        '日志配置': log_configs,
        '功能开关': feature_configs,
        '进程管理': process_configs
    }
    
    total_configs = 0
    loaded_configs = 0
    
    for category, configs in all_configs.items():
        print(f"\n📋 {category}:")
        for config in configs:
            total_configs += 1
            value = os.getenv(config)
            if value is not None:
                loaded_configs += 1
                # 隐藏敏感信息
                if 'TOKEN' in config or 'SECRET' in config:
                    display_value = value[:10] + "..." if len(value) > 10 else "***"
                else:
                    display_value = value
                print(f"  ✅ {config} = {display_value}")
            else:
                print(f"  ❌ {config} = 未设置")
    
    print(f"\n📊 配置统计:")
    print(f"  总配置项: {total_configs}")
    print(f"  已加载: {loaded_configs}")
    print(f"  成功率: {loaded_configs/total_configs*100:.1f}%")
    
    return loaded_configs == total_configs

def test_config_types():
    """测试配置类型转换"""
    print("\n🧪 测试配置类型转换...")
    
    type_tests = [
        ('REQUEST_TIMEOUT', int, 15),
        ('MESSAGE_SEND_INTERVAL', float, 1.0),
        ('ENABLE_PROXY', bool, False),
        ('MAX_RETRIES', int, 3)
    ]
    
    all_passed = True
    
    for config_name, expected_type, default_value in type_tests:
        try:
            raw_value = os.getenv(config_name, str(default_value))
            
            if expected_type == bool:
                converted_value = raw_value.lower() == 'true'
            else:
                converted_value = expected_type(raw_value)
            
            print(f"  ✅ {config_name}: {raw_value} -> {converted_value} ({expected_type.__name__})")
        except Exception as e:
            print(f"  ❌ {config_name}: 转换失败 - {e}")
            all_passed = False
    
    return all_passed

def main():
    """主函数"""
    print("🔧 Hacker News 爬虫配置验证")
    print("=" * 50)
    
    # 加载配置
    if not load_config():
        sys.exit(1)
    
    # 验证配置
    config_valid = validate_config()
    
    # 测试类型转换
    types_valid = test_config_types()
    
    print("\n" + "=" * 50)
    if config_valid and types_valid:
        print("🎉 所有配置验证通过！")
        sys.exit(0)
    else:
        print("❌ 配置验证失败，请检查config.env文件")
        sys.exit(1)

if __name__ == "__main__":
    main() 