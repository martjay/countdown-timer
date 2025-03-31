@echo off
chcp 65001 >nul
title 倒计时器启动
echo 正在启动倒计时器应用...

cd /d "%~dp0"
call venv\Scripts\activate
python src\main.py

if %ERRORLEVEL% NEQ 0 (
    echo 程序运行出错，错误代码: %ERRORLEVEL%
    pause 
)

call venv\Scripts\deactivate
exit 