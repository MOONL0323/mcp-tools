"""
开发环境启动脚本
"""
import os
import sys

# 确保工作目录正确
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

print(f"工作目录: {os.getcwd()}")
print(f"Python路径: {sys.path[:3]}")
print("=" * 50)

# 启动uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
