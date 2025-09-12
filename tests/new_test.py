import requests
import json
import time

def test_backend():
    base_url = "http://localhost:8000"
    
    print("🧪 开始后端测试...")
    
    # 1. 测试根路径
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ 根路径测试: {response.status_code}")
        print(f"📄 响应: {response.json()}")
    except Exception as e:
        print(f"❌ 根路径测试失败: {e}")
        return
    
    # 2. 测试健康检查
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"✅ 健康检查: {response.status_code}")
        print(f"📄 响应: {response.json()}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return
    
    # 3. 测试聊天API（非流式）
    try:
        chat_data = {
            "message": "你好",
            "user_id": "test_user",
            "session_id": f"test_session_{int(time.time())}",
            "stream": False
        }
        
        print(f"📤 发送聊天请求: {chat_data}")
        response = requests.post(
            f"{base_url}/api/chat",
            json=chat_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ 聊天API测试: {response.status_code}")
        if response.status_code == 200:
            print(f"📄 响应: {response.json()}")
        else:
            print(f"❌ 错误响应: {response.text}")
    except Exception as e:
        print(f"❌ 聊天API测试失败: {e}")
    
    # 4. 测试流式聊天API
    try:
        chat_data = {
            "message": "你好",
            "user_id": "test_user", 
            "session_id": f"test_session_stream_{int(time.time())}",
            "stream": True
        }
        
        print(f"📤 发送流式聊天请求: {chat_data}")
        response = requests.post(
            f"{base_url}/api/chat",
            json=chat_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            stream=True
        )
        print(f"✅ 流式聊天API测试: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 开始接收流式数据:")
            for i, line in enumerate(response.iter_lines(decode_unicode=True)):
                if line:
                    print(f"  [{i}] {line}")
                if i > 10:  # 限制输出行数
                    print("  ... (更多数据)")
                    break
        else:
            print(f"❌ 流式错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 流式聊天API测试失败: {e}")

if __name__ == "__main__":
    test_backend()