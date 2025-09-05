#!/usr/bin/env python
"""
创建超级用户脚本
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tata_evaluation.settings')
django.setup()

from django.contrib.auth.models import User

def create_superuser():
    """创建超级用户"""
    
    username = 'admin'
    email = 'admin@example.com'
    password = 'admin123'
    
    # 检查用户是否已存在
    if User.objects.filter(username=username).exists():
        print(f"用户 '{username}' 已存在")
        user = User.objects.get(username=username)
        if not user.is_superuser:
            user.is_superuser = True
            user.is_staff = True
            user.save()
            print(f"已将用户 '{username}' 设置为超级用户")
        else:
            print(f"用户 '{username}' 已经是超级用户")
    else:
        # 创建新的超级用户
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"成功创建超级用户: {username}")
        print(f"密码: {password}")
    
    print(f"\n可以使用以下信息登录管理后台:")
    print(f"用户名: {username}")
    print(f"密码: {password}")
    print(f"管理后台地址: http://localhost:8000/admin/")

if __name__ == "__main__":
    create_superuser()
