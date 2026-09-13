"""FastAPI 入口:API 路由 + 前端静态托管。"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import router

app = FastAPI(title="地球Online", docs_url=None, redoc_url=None)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.include_router(router)


# 静态前端放在最后挂载,避免拦截 /api
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
