#!/usr/bin/env python
"""
生产环境启动脚本
用于公网访问的Django服务器
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tata_evaluation.settings')

def main():
    """启动生产环境服务器"""
    print("正在启动生产环境Django服务器...")
    print("注意：这是开发服务器，生产环境建议使用Gunicorn+Nginx")
    print("服务器将监听所有网络接口的8001端口")
    print("访问地址：http://你的服务器IP:8001/")
    print("管理后台：http://你的服务器IP:8001/admin/")
    print("按Ctrl+C停止服务器")
    print("-" * 50)
    
    # 启动服务器，监听所有网络接口
    execute_from_command_line([
        'manage.py', 
        'runserver', 
        '0.0.0.0:8001'
    ])

if __name__ == "__main__":
    main()
