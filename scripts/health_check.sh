#!/bin/bash
# ================================
# Hacker News 爬虫健康检查脚本
# ================================

# 配置
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$PROJECT_DIR/hn_crawler.log"
LOCK_FILE="/tmp/hn_crawler.lock"
CONFIG_FILE="$PROJECT_DIR/config.env"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 检查进程状态
check_process() {
    log_info "检查爬虫进程状态..."
    
    local processes=$(ps aux | grep -E "(hn_news_crawler|run_daemon)" | grep -v grep)
    
    if [ -z "$processes" ]; then
        log_error "没有发现运行中的爬虫进程"
        return 1
    else
        log_info "发现运行中的进程:"
        echo "$processes" | while read line; do
            echo "  $line"
        done
        return 0
    fi
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."
    
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "配置文件不存在: $CONFIG_FILE"
        return 1
    fi
    
    # 检查必需配置
    local required_configs=("TELEGRAM_BOT_TOKEN" "TELEGRAM_CHAT_ID")
    local missing_configs=()
    
    for config in "${required_configs[@]}"; do
        if ! grep -q "^$config=" "$CONFIG_FILE" || grep -q "^$config=your_" "$CONFIG_FILE"; then
            missing_configs+=("$config")
        fi
    done
    
    if [ ${#missing_configs[@]} -gt 0 ]; then
        log_error "缺少必需配置: ${missing_configs[*]}"
        return 1
    else
        log_info "配置文件检查通过"
        return 0
    fi
}

# 检查网络连接
check_network() {
    log_info "检查网络连接..."
    
    # 检查 HN 网站
    if curl -s --max-time 10 https://news.ycombinator.com > /dev/null; then
        log_info "HN 网站连接正常"
    else
        log_error "无法连接到 HN 网站"
        return 1
    fi
    
    # 检查 Telegram API（如果有配置）
    if [ -f "$CONFIG_FILE" ]; then
        local bot_token=$(grep "^TELEGRAM_BOT_TOKEN=" "$CONFIG_FILE" | cut -d'=' -f2)
        if [ -n "$bot_token" ] && [ "$bot_token" != "your_bot_token_here" ]; then
            if curl -s --max-time 10 "https://api.telegram.org/bot$bot_token/getMe" > /dev/null; then
                log_info "Telegram API 连接正常"
            else
                log_warn "Telegram API 连接失败"
            fi
        fi
    fi
    
    return 0
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间..."
    
    local usage=$(df "$PROJECT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -gt 90 ]; then
        log_error "磁盘空间不足: ${usage}%"
        return 1
    elif [ "$usage" -gt 80 ]; then
        log_warn "磁盘空间紧张: ${usage}%"
    else
        log_info "磁盘空间充足: ${usage}%"
    fi
    
    return 0
}

# 检查日志文件
check_log_file() {
    log_info "检查日志文件..."
    
    if [ ! -f "$LOG_FILE" ]; then
        log_warn "日志文件不存在: $LOG_FILE"
        return 1
    fi
    
    # 检查日志文件大小
    local size=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null)
    local size_mb=$((size / 1024 / 1024))
    
    if [ "$size_mb" -gt 100 ]; then
        log_warn "日志文件过大: ${size_mb}MB"
    else
        log_info "日志文件大小正常: ${size_mb}MB"
    fi
    
    # 检查最近的错误
    local recent_errors=$(tail -100 "$LOG_FILE" | grep -i error | wc -l)
    if [ "$recent_errors" -gt 5 ]; then
        log_warn "最近发现 $recent_errors 个错误"
    else
        log_info "最近错误数量正常: $recent_errors"
    fi
    
    return 0
}

# 检查数据文件
check_data_files() {
    log_info "检查数据文件..."
    
    local data_dir="$PROJECT_DIR/data"
    if [ ! -d "$data_dir" ]; then
        log_error "数据目录不存在: $data_dir"
        return 1
    fi
    
    local today=$(date +%Y-%m-%d)
    local today_file="$data_dir/hn_news_$today.csv"
    
    if [ -f "$today_file" ]; then
        local lines=$(wc -l < "$today_file")
        log_info "今日数据文件存在，包含 $lines 行"
    else
        log_warn "今日数据文件不存在: $today_file"
    fi
    
    return 0
}

# 检查锁文件
check_lock_file() {
    log_info "检查锁文件..."
    
    if [ -f "$LOCK_FILE" ]; then
        local pid=$(cat "$LOCK_FILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            log_info "锁文件正常，进程 $pid 正在运行"
        else
            log_warn "锁文件存在但进程不存在，可能需要清理"
        fi
    else
        log_warn "锁文件不存在，可能没有守护进程运行"
    fi
    
    return 0
}

# 性能检查
check_performance() {
    log_info "检查系统性能..."
    
    # 检查内存使用
    local memory_usage=$(ps aux | grep -E "(hn_news_crawler|run_daemon)" | grep -v grep | awk '{sum += $4} END {print sum}')
    if [ -n "$memory_usage" ]; then
        log_info "爬虫进程内存使用: ${memory_usage}%"
    fi
    
    # 检查 CPU 使用
    local cpu_usage=$(ps aux | grep -E "(hn_news_crawler|run_daemon)" | grep -v grep | awk '{sum += $3} END {print sum}')
    if [ -n "$cpu_usage" ]; then
        log_info "爬虫进程 CPU 使用: ${cpu_usage}%"
    fi
    
    return 0
}

# 生成报告
generate_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local report_file="$PROJECT_DIR/health_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "================================"
        echo "Hacker News 爬虫健康检查报告"
        echo "时间: $timestamp"
        echo "================================"
        echo
        
        echo "进程状态:"
        ps aux | grep -E "(hn_news_crawler|run_daemon)" | grep -v grep || echo "  无运行进程"
        echo
        
        echo "磁盘使用:"
        df -h "$PROJECT_DIR"
        echo
        
        echo "最近日志 (最后10行):"
        if [ -f "$LOG_FILE" ]; then
            tail -10 "$LOG_FILE"
        else
            echo "  日志文件不存在"
        fi
        echo
        
        echo "数据文件:"
        ls -la "$PROJECT_DIR/data/" 2>/dev/null || echo "  数据目录不存在"
        
    } > "$report_file"
    
    log_info "健康检查报告已生成: $report_file"
}

# 主函数
main() {
    echo "================================"
    echo "Hacker News 爬虫健康检查"
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "================================"
    echo
    
    local exit_code=0
    
    # 执行各项检查
    check_config || exit_code=1
    echo
    
    check_process || exit_code=1
    echo
    
    check_network || exit_code=1
    echo
    
    check_disk_space || exit_code=1
    echo
    
    check_log_file || exit_code=1
    echo
    
    check_data_files || exit_code=1
    echo
    
    check_lock_file || exit_code=1
    echo
    
    check_performance || exit_code=1
    echo
    
    # 生成报告
    if [ "$1" = "--report" ]; then
        generate_report
    fi
    
    # 总结
    if [ $exit_code -eq 0 ]; then
        log_info "健康检查完成，所有项目正常"
    else
        log_error "健康检查发现问题，请查看上述输出"
    fi
    
    exit $exit_code
}

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  --report    生成详细的健康检查报告"
    echo "  --help      显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0                # 执行基本健康检查"
    echo "  $0 --report       # 执行检查并生成报告"
}

# 参数处理
case "$1" in
    --help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac 