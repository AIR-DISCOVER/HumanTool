import sys
from api_client import api_call

def main():
    print("API 测试脚本，输入你的问题，按回车发送，输入 exit 退出。")
    while True:
        user_input = input("请输入你的问题: ")
        if user_input.strip().lower() == "exit":
            print("退出测试。")
            break
        try:
            result = api_call(user_input)
            print(f"API 返回: {result}\n")
        except Exception as e:
            print(f"调用失败: {e}\n")

if __name__ == "__main__":
    main()