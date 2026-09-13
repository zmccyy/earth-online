"""《地球Online》启动脚本 — 强制登录,无法退游。"""
import uvicorn

if __name__ == "__main__":
    print("=" * 46)
    print("  地球ONLINE · 服务器启动中…")
    print("  当前同时在线玩家: 8,086,000,000 人")
    print("  游戏地址: http://127.0.0.1:8899")
    print("=" * 46)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8899, log_level="warning")
