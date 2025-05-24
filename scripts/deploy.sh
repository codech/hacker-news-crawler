#!/bin/bash
# ================================
# Hacker News 爬虫自动化部署脚本
# ================================

set -e  # 遇到错误立即退出

# 配置
PROJECT_NAME="hacker-news-crawler"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_VERSION="3.8"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="hn-crawler"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 错误处理
error_exit() {
    log_error "$1"
    exit 1
}

# 检查系统要求
check_requirements() {
    log_step "检查系统要求..."
    
    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        log_info "检测到 Linux 系统"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        log_info "检测到 macOS 系统"
    else
        error_exit "不支持的操作系统: $OSTYPE"
    fi
    
    # 检查 Python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        local python_version=$(python3 --version | cut -d' ' -f2)
        log_info "Python 版本: $python_version"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        local python_version=$(python --version | cut -d' ' -f2)
        log_info "Python 版本: $python_version"
    else
        error_exit "未找到 Python，请先安装 Python $PYTHON_VERSION+"
    fi
    
    # 检查 pip
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        error_exit "未找到 pip，请先安装 pip"
    fi
    
    # 检查 curl
    if ! command -v curl &> /dev/null; then
        error_exit "未找到 curl，请先安装 curl"
    fi
    
    log_info "系统要求检查通过"
}

# 创建虚拟环境
setup_virtualenv() {
    log_step "设置 Python 虚拟环境..."
    
    if [ -d "$VENV_DIR" ]; then
        log_warn "虚拟环境已存在，跳过创建"
    else
        log_info "创建虚拟环境: $VENV_DIR"
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 升级 pip
    log_info "升级 pip..."
    pip install --upgrade pip
    
    log_info "虚拟环境设置完成"
}

# 安装依赖
install_dependencies() {
    log_step "安装项目依赖..."
    
    if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
        error_exit "requirements.txt 文件不存在"
    fi
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 安装依赖
    log_info "安装 Python 依赖包..."
    pip install -r "$PROJECT_DIR/requirements.txt"
    
    log_info "依赖安装完成"
}

# 配置文件设置
setup_config() {
    log_step "设置配置文件..."
    
    local config_file="$PROJECT_DIR/config.env"
    local config_example="$PROJECT_DIR/config.env.example"
    
    if [ ! -f "$config_example" ]; then
        error_exit "配置模板文件不存在: $config_example"
    fi
    
    if [ ! -f "$config_file" ]; then
        log_info "复制配置模板..."
        cp "$config_example" "$config_file"
        log_warn "请编辑 $config_file 文件，填入正确的配置信息"
        
        # 提示用户配置必需项
        echo
        echo "必需配置项："
        echo "  TELEGRAM_BOT_TOKEN=your_bot_token_here"
        echo "  TELEGRAM_CHAT_ID=your_chat_id_here"
        echo
        read -p "是否现在编辑配置文件？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} "$config_file"
        fi
    else
        log_info "配置文件已存在: $config_file"
    fi
}

# 创建数据目录
setup_directories() {
    log_step "创建必要目录..."
    
    local dirs=("data" "logs" "backup")
    
    for dir in "${dirs[@]}"; do
        local dir_path="$PROJECT_DIR/$dir"
        if [ ! -d "$dir_path" ]; then
            log_info "创建目录: $dir_path"
            mkdir -p "$dir_path"
        fi
    done
    
    log_info "目录创建完成"
}

# 测试安装
test_installation() {
    log_step "测试安装..."
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 测试导入
    log_info "测试 Python 模块导入..."
    $PYTHON_CMD -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
try:
    from hn_news_crawler import HackerNewsCrawler
    print('✓ 模块导入成功')
except ImportError as e:
    print(f'✗ 模块导入失败: {e}')
    sys.exit(1)
"
    
    # 测试配置
    log_info "测试配置文件..."
    if [ -f "$PROJECT_DIR/config.env" ]; then
        if grep -q "your_bot_token_here" "$PROJECT_DIR/config.env"; then
            log_warn "配置文件包含默认值，请完成配置"
        else
            log_info "配置文件检查通过"
        fi
    fi
    
    log_info "安装测试完成"
}

# 创建 systemd 服务（仅 Linux）
create_systemd_service() {
    if [ "$OS" != "linux" ]; then
        log_info "非 Linux 系统，跳过 systemd 服务创建"
        return
    fi
    
    log_step "创建 systemd 服务..."
    
    local service_file="/etc/systemd/system/$SERVICE_NAME.service"
    local user=$(whoami)
    
    # 检查是否有 sudo 权限
    if ! sudo -n true 2>/dev/null; then
        log_warn "需要 sudo 权限创建系统服务，跳过此步骤"
        return
    fi
    
    log_info "创建服务文件: $service_file"
    
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=Hacker News Crawler
After=network.target
Wants=network.target

[Service]
Type=simple
User=$user
Group=$user
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python $PROJECT_DIR/run_daemon.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载 systemd
    sudo systemctl daemon-reload
    
    # 启用服务
    sudo systemctl enable "$SERVICE_NAME"
    
    log_info "systemd 服务创建完成"
    log_info "使用以下命令管理服务："
    echo "  启动: sudo systemctl start $SERVICE_NAME"
    echo "  停止: sudo systemctl stop $SERVICE_NAME"
    echo "  状态: sudo systemctl status $SERVICE_NAME"
    echo "  日志: sudo journalctl -u $SERVICE_NAME -f"
}

# 创建启动脚本
create_startup_scripts() {
    log_step "创建启动脚本..."
    
    # 创建启动脚本
    local start_script="$PROJECT_DIR/start.sh"
    cat > "$start_script" << EOF
#!/bin/bash
# Hacker News 爬虫启动脚本

PROJECT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="\$PROJECT_DIR/venv"

# 激活虚拟环境
source "\$VENV_DIR/bin/activate"

# 切换到项目目录
cd "\$PROJECT_DIR"

# 启动守护进程
echo "启动 Hacker News 爬虫..."
nohup python run_daemon.py > /dev/null 2>&1 &

echo "爬虫已在后台启动"
echo "查看状态: python manage_crawler.py"
echo "查看日志: tail -f hn_crawler.log"
EOF
    
    chmod +x "$start_script"
    
    # 创建停止脚本
    local stop_script="$PROJECT_DIR/stop.sh"
    cat > "$stop_script" << EOF
#!/bin/bash
# Hacker News 爬虫停止脚本

echo "停止 Hacker News 爬虫..."
pkill -f "run_daemon.py"
pkill -f "hn_news_crawler.py"

# 清理锁文件
rm -f /tmp/hn_crawler.lock

echo "爬虫已停止"
EOF
    
    chmod +x "$stop_script"
    
    log_info "启动脚本创建完成:"
    echo "  启动: $start_script"
    echo "  停止: $stop_script"
}

# 设置日志轮转
setup_log_rotation() {
    log_step "设置日志轮转..."
    
    if [ "$OS" == "linux" ] && command -v logrotate &> /dev/null; then
        local logrotate_config="/etc/logrotate.d/$SERVICE_NAME"
        
        if sudo -n true 2>/dev/null; then
            sudo tee "$logrotate_config" > /dev/null << EOF
$PROJECT_DIR/hn_crawler.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 $(whoami) $(whoami)
}
EOF
            log_info "日志轮转配置完成: $logrotate_config"
        else
            log_warn "需要 sudo 权限设置日志轮转，跳过此步骤"
        fi
    else
        log_info "创建手动日志轮转脚本..."
        cat > "$PROJECT_DIR/rotate_logs.sh" << 'EOF'
#!/bin/bash
# 手动日志轮转脚本

LOG_FILE="hn_crawler.log"
MAX_SIZE=10485760  # 10MB

if [ -f "$LOG_FILE" ]; then
    size=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null)
    if [ "$size" -gt "$MAX_SIZE" ]; then
        mv "$LOG_FILE" "$LOG_FILE.$(date +%Y%m%d_%H%M%S)"
        touch "$LOG_FILE"
        echo "日志文件已轮转"
    fi
fi
EOF
        chmod +x "$PROJECT_DIR/rotate_logs.sh"
        log_info "手动日志轮转脚本: $PROJECT_DIR/rotate_logs.sh"
    fi
}

# 显示部署总结
show_summary() {
    log_step "部署总结"
    
    echo
    echo "================================"
    echo "🎉 Hacker News 爬虫部署完成！"
    echo "================================"
    echo
    echo "项目目录: $PROJECT_DIR"
    echo "虚拟环境: $VENV_DIR"
    echo "配置文件: $PROJECT_DIR/config.env"
    echo
    echo "快速开始："
    echo "  1. 编辑配置文件: nano $PROJECT_DIR/config.env"
    echo "  2. 测试运行: $PROJECT_DIR/start.sh"
    echo "  3. 查看状态: python $PROJECT_DIR/manage_crawler.py"
    echo "  4. 查看日志: tail -f $PROJECT_DIR/hn_crawler.log"
    echo
    echo "管理命令："
    echo "  启动: $PROJECT_DIR/start.sh"
    echo "  停止: $PROJECT_DIR/stop.sh"
    echo "  健康检查: $PROJECT_DIR/scripts/health_check.sh"
    
    if [ "$OS" == "linux" ] && [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
        echo
        echo "系统服务："
        echo "  启动: sudo systemctl start $SERVICE_NAME"
        echo "  停止: sudo systemctl stop $SERVICE_NAME"
        echo "  状态: sudo systemctl status $SERVICE_NAME"
    fi
    
    echo
    echo "文档："
    echo "  README: $PROJECT_DIR/README.md"
    echo "  API 文档: $PROJECT_DIR/docs/API.md"
    echo "  故障排除: $PROJECT_DIR/docs/TROUBLESHOOTING.md"
    echo
}

# 主函数
main() {
    echo "================================"
    echo "🚀 Hacker News 爬虫自动化部署"
    echo "================================"
    echo
    
    # 检查是否在项目目录中
    if [ ! -f "$PROJECT_DIR/hn_news_crawler.py" ]; then
        error_exit "请在项目根目录中运行此脚本"
    fi
    
    # 执行部署步骤
    check_requirements
    setup_virtualenv
    install_dependencies
    setup_config
    setup_directories
    test_installation
    create_systemd_service
    create_startup_scripts
    setup_log_rotation
    show_summary
    
    echo "🎉 部署完成！"
}

# 显示帮助
show_help() {
    echo "Hacker News 爬虫自动化部署脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  --help      显示此帮助信息"
    echo "  --no-service 跳过系统服务创建"
    echo
    echo "此脚本将自动完成以下步骤："
    echo "  1. 检查系统要求"
    echo "  2. 创建 Python 虚拟环境"
    echo "  3. 安装项目依赖"
    echo "  4. 设置配置文件"
    echo "  5. 创建必要目录"
    echo "  6. 测试安装"
    echo "  7. 创建系统服务（Linux）"
    echo "  8. 创建启动脚本"
    echo "  9. 设置日志轮转"
}

# 参数处理
case "$1" in
    --help)
        show_help
        exit 0
        ;;
    --no-service)
        SKIP_SERVICE=true
        main
        ;;
    *)
        main
        ;;
esac 