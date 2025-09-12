"""
检查Metabase服务状态
"""

import requests
import time
import subprocess

def check_metabase_status():
    """检查Metabase状态"""
    print("🔍 检查Metabase服务状态...")
    
    # 检查容器状态
    try:
        result = subprocess.run(['docker', 'logs', 'tata-metabase', '--tail', '20'], 
                              capture_output=True, text=True, encoding='utf-8', errors='ignore')
        print("Metabase容器日志:")
        print(result.stdout)
        if result.stderr:
            print("错误信息:")
            print(result.stderr)
    except Exception as e:
        print(f"获取日志失败: {e}")
    
    # 尝试连接Metabase
    max_attempts = 10
    for i in range(max_attempts):
        try:
            print(f"尝试连接Metabase... ({i+1}/{max_attempts})")
            response = requests.get('http://localhost:3000', timeout=10)
            if response.status_code == 200:
                print("✅ Metabase服务正常运行!")
                print("🌐 访问地址: http://localhost:3000")
                return True
            else:
                print(f"响应状态码: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("连接被拒绝，Metabase可能还在启动中...")
        except Exception as e:
            print(f"连接错误: {e}")
        
        if i < max_attempts - 1:
            time.sleep(10)
    
    print("❌ Metabase服务未能正常启动")
    return False

def restart_metabase():
    """重启Metabase容器"""
    print("🔄 重启Metabase容器...")
    try:
        subprocess.run(['docker', 'restart', 'tata-metabase'], check=True)
        print("✅ Metabase容器已重启")
        time.sleep(30)
        return check_metabase_status()
    except Exception as e:
        print(f"❌ 重启失败: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Metabase状态检查工具")
    print("=" * 40)
    
    success = check_metabase_status()
    
    if not success:
        choice = input("Metabase启动失败，是否重启容器? (y/n): ").lower()
        if choice == 'y':
            restart_metabase()