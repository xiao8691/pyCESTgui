@echo off
REM CEST图像处理GUI工具 - 启动脚本
REM 双击此文件启动应用（无需Python环境，只需虚拟环境）

cd /d "%~dp0"

REM 检查虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo 错误: 虚拟环境不存在！
    echo 请运行: python -m venv .venv
    echo 然后运行: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM 启动应用
echo 启动CEST图像处理GUI...
start "" ".venv\Scripts\python.exe" main.py

if %errorlevel% neq 0 (
    echo.
    echo 启动失败！错误代码: %errorlevel%
    pause
    exit /b %errorlevel%
)

exit /b 0
