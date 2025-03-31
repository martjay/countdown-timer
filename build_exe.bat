@echo off
chcp 65001 >nul
title 倒计时器打包

cd /d "%~dp0"

echo 正在清理旧的构建文件...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.spec del /q *.spec

echo 正在激活虚拟环境...
call venv\Scripts\activate

echo 正在构建可执行文件...
pyinstaller --name "倒计时器" --noconsole --icon=icon.ico ^
    --add-data "audio;audio" ^
    --add-data "icon.ico;." ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=PySide6.QtWidgets ^
    src\main.py

if %ERRORLEVEL% NEQ 0 (
    echo 构建失败，错误代码: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo 构建完成！
echo 可执行文件位于 dist\倒计时器\ 目录下

call venv\Scripts\deactivate
pause 