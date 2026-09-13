@echo off
chcp 65001 >nul
title 地球Online 服务器
echo ==============================================
echo   地球ONLINE 服务器启动中...
echo   游戏地址: http://127.0.0.1:8899
echo   (关闭本窗口即全服停机维护)
echo ==============================================
python run.py
pause
