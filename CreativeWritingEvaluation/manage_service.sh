#!/bin/bash

# Django服务管理脚本

SERVICE_NAME="django-evaluation"

show_usage() {
    echo "Django评估系统服务管理脚本"
    echo
    echo "使用方法: $0 [命令]"
    echo
    echo "可用命令:"
    echo "  install   - 安装并启动服务"
    echo "  start     - 启动服务"
    echo "  stop      - 停止服务"
    echo "  restart   - 重启服务"
    echo "  status    - 查看服务状态"
    echo "  logs      - 查看服务日志"
    echo "  enable    - 启用开机自启动"
    echo "  disable   - 禁用开机自启动"
    echo "  uninstall - 卸载服务"
    echo
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "错误：此操作需要root权限"
        echo "请使用: sudo $0 $1"
        exit 1
    fi
}

case "$1" in
    install)
        check_root
        echo "安装Django服务..."
        bash "$(dirname "$0")/install_service.sh"
        ;;
    start)
        check_root
        echo "启动服务..."
        systemctl start "$SERVICE_NAME"
        systemctl status "$SERVICE_NAME" --no-pager
        ;;
    stop)
        check_root
        echo "停止服务..."
        systemctl stop "$SERVICE_NAME"
        ;;
    restart)
        check_root
        echo "重启服务..."
        systemctl restart "$SERVICE_NAME"
        systemctl status "$SERVICE_NAME" --no-pager
        ;;
    status)
        echo "服务状态:"
        systemctl status "$SERVICE_NAME" --no-pager
        echo
        echo "服务是否启用开机自启动:"
        systemctl is-enabled "$SERVICE_NAME" 2>/dev/null && echo "已启用" || echo "未启用"
        ;;
    logs)
        echo "查看服务日志 (按Ctrl+C退出):"
        journalctl -u "$SERVICE_NAME" -f
        ;;
    enable)
        check_root
        echo "启用开机自启动..."
        systemctl enable "$SERVICE_NAME"
        echo "开机自启动已启用"
        ;;
    disable)
        check_root
        echo "禁用开机自启动..."
        systemctl disable "$SERVICE_NAME"
        echo "开机自启动已禁用"
        ;;
    uninstall)
        check_root
        echo "卸载Django服务..."
        systemctl stop "$SERVICE_NAME" 2>/dev/null || true
        systemctl disable "$SERVICE_NAME" 2>/dev/null || true
        rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
        systemctl daemon-reload
        echo "服务已卸载"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
