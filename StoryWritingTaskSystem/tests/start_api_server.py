"""
TATA Story Assistant API Server 启动脚本
在项目根目录运行此脚本来启动API服务器
"""
import sys
import os
from pathlib import Path

# 确保当前目录是项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    try:
        import uvicorn
        
        # 检查必要的文件是否存在
        server_main = project_root / "server" / "main.py"
        
        if not server_main.exists():
            print(f"❌ Error: {server_main} not found")
            return
        
        print("🔍 检查server/main.py内容...")
        
        # 直接导入并运行server/main.py
        # 添加server目录到sys.path
        server_dir = str(project_root / "server")
        if server_dir not in sys.path:
            sys.path.insert(0, server_dir)
        
        print(f"📁 Project root: {project_root}")
        print(f"📁 Server directory: {server_dir}")
        print("🚀 Starting TATA Story Assistant API Server...")
        
        # 直接运行server/main.py作为模块
        os.chdir(str(project_root))
        
        # 使用uvicorn运行app
        uvicorn.run(
            "server.main:app",  # 模块路径
            host="0.0.0.0", 
            port=8000, 
            reload=True,  # 启用热重载
            reload_dirs=[str(project_root)],  # 监控整个项目目录
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install fastapi uvicorn")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()