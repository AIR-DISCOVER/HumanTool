#!/usr/bin/env python3
"""
系统服务启动脚本
用于systemd服务的Django应用启动
"""

import os
import sys
import logging
import signal
import django
from django.core.management import execute_from_command_line

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('django-service')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tata_evaluation.settings')

def signal_handler(signum, frame):
    """处理系统信号"""
    logger.info(f"接收到信号 {signum}，正在关闭服务...")
    sys.exit(0)

def main():
    """启动Django服务"""
    # 注册信号处理器
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("正在启动Django评估系统服务...")
    logger.info("工作目录: %s", os.getcwd())
    logger.info("Python路径: %s", sys.executable)
    
    try:
        # 检查Django配置
        django.setup()
        logger.info("Django配置检查通过")
        
        # 启动服务器
        logger.info("启动服务器，监听 0.0.0.0:8003")
        execute_from_command_line([
            'manage.py',
            'runserver',
            '0.0.0.0:8003',
            '--noreload'  # 禁用自动重载，适合生产环境
        ])
        
    except Exception as e:
        logger.error("启动失败: %s", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
