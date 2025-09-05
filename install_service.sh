#!/bin/bash

# Django应用自启动服务安装脚本

set -e  # 遇到错误立即退出

echo "=== Django应用自启动服务安装脚本 ==="
echo

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
    echo "错误：请使用sudo运行此脚本"
    echo "使用方法: sudo bash install_service.sh"
    exit 1
fi

# 获取当前目录和用户信息
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER="${SUDO_USER:-$USER}"
SERVICE_NAME="django-evaluation"

echo "当前目录: $SCRIPT_DIR"
echo "运行用户: $CURRENT_USER"
echo "服务名称: $SERVICE_NAME"
echo

# 1. 给启动脚本添加执行权限
echo "1. 设置脚本权限..."
chmod +x "$SCRIPT_DIR/start_service.py"
chmod +x "$SCRIPT_DIR/start_production.py"

# 2. 创建systemd服务文件
echo "2. 创建systemd服务文件..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Django Evaluation System
After=network.target

[Service]
Type=exec
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=/usr/bin:/usr/local/bin
Environment=PYTHONPATH=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/start_service.py
Restart=always
RestartSec=10

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# 安全配置
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# 3. 重新加载systemd配置
echo "3. 重新加载systemd配置..."
systemctl daemon-reload

# 4. 启用服务（开机自启动）
echo "4. 启用开机自启动..."
systemctl enable "$SERVICE_NAME"

# 5. 启动服务
echo "5. 启动服务..."
systemctl start "$SERVICE_NAME"

# 6. 检查服务状态
echo "6. 检查服务状态..."
sleep 3
systemctl status "$SERVICE_NAME" --no-pager

echo
echo "=== 安装完成 ==="
echo
echo "服务管理命令："
echo "  查看状态: sudo systemctl status $SERVICE_NAME"
echo "  启动服务: sudo systemctl start $SERVICE_NAME"
echo "  停止服务: sudo systemctl stop $SERVICE_NAME"
echo "  重启服务: sudo systemctl restart $SERVICE_NAME"
echo "  查看日志: sudo journalctl -u $SERVICE_NAME -f"
echo "  禁用自启: sudo systemctl disable $SERVICE_NAME"
echo
# 获取公网IP地址
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "你的公网IP")
INTERNAL_IP=$(hostname -I | awk '{print $1}')

echo "访问地址:"
echo "  公网访问: http://$PUBLIC_IP:8003/"
echo "  内网访问: http://$INTERNAL_IP:8003/"
echo "管理后台:"
echo "  公网访问: http://$PUBLIC_IP:8003/admin/"
echo "  内网访问: http://$INTERNAL_IP:8003/admin/"
echo
