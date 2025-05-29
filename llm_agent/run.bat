@echo off
:: 设置控制台编码为UTF-8
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: 设置控制台字体和颜色
color 0A
title 招生简章解析项目

echo ========================================
echo 招生简章解析项目运行脚本
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

:: 检查uv是否安装
uv --version >nul 2>&1
if errorlevel 1 (
    echo 警告: 未找到uv，正在安装...
    pip install uv
    if errorlevel 1 (
        echo 错误: uv安装失败
        pause
        exit /b 1
    )
)

:: 检查虚拟环境
if not exist ".venv" (
    echo 创建虚拟环境...
    uv venv
    if errorlevel 1 (
        echo 错误: 虚拟环境创建失败
        pause
        exit /b 1
    )
)

:: 激活虚拟环境
echo 激活虚拟环境...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo 错误: 虚拟环境激活失败
    pause
    exit /b 1
)

:: 安装依赖
echo 安装项目依赖...
uv pip install -e .
if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

:: 检查环境变量文件
if not exist ".env" (
    echo.
    echo 警告: 未找到.env文件
    echo 请复制.env.example为.env并配置相关参数:
    echo   - 数据库连接信息
    echo   - LLM API密钥
    echo   - 其他配置项
    echo.
    if exist ".env.example" (
        echo 是否现在复制.env.example为.env? (y/n)
        set /p choice="请选择: "
        if /i "!choice!"=="y" (
            copy ".env.example" ".env"
            echo .env文件已创建，请编辑配置后重新运行
            pause
            exit /b 0
        )
    )
    echo 请手动创建.env文件后重新运行
    pause
    exit /b 1
)

:: 显示菜单
:menu
echo.
echo ========================================
echo 请选择要执行的操作:
echo ========================================
echo 1. 初始化数据库
echo 2. 测试所有模块
echo 3. 完整流程 (爬取+分析+保存)
echo 4. 仅爬取招生简章
echo 5. 仅分析本地文档
echo 6. 查看数据库统计
echo 7. 列出学校信息
echo 8. 退出
echo ========================================
set /p choice="请输入选项 (1-8): "

if "%choice%"=="1" goto init_db
if "%choice%"=="2" goto test_modules
if "%choice%"=="3" goto full_process
if "%choice%"=="4" goto scrape_only
if "%choice%"=="5" goto analyze_only
if "%choice%"=="6" goto show_stats
if "%choice%"=="7" goto list_schools
if "%choice%"=="8" goto exit

echo 无效选项，请重新选择
goto menu

:init_db
echo.
echo 初始化数据库...
python scripts\init_db.py
if errorlevel 1 (
    echo 数据库初始化失败
    pause
)
goto menu

:test_modules
echo.
echo 测试所有模块...
python scripts\test_modules.py
if errorlevel 1 (
    echo 模块测试失败
    pause
)
goto menu

:full_process
echo.
echo 执行完整流程...
set /p url="请输入URL (回车使用默认): "
if "%url%"=="" (
    python scripts\run.py full
) else (
    python scripts\run.py full --url "%url%"
)
if errorlevel 1 (
    echo 完整流程执行失败
    pause
)
goto menu

:scrape_only
echo.
echo 仅爬取招生简章...
set /p url="请输入URL (回车使用默认): "
if "%url%"=="" (
    python scripts\run.py scrape
) else (
    python scripts\run.py scrape --url "%url%"
)
if errorlevel 1 (
    echo 爬取失败
    pause
)
goto menu

:analyze_only
echo.
echo 分析本地文档...
python scripts\run.py analyze
if errorlevel 1 (
    echo 分析失败
    pause
)
goto menu

:show_stats
echo.
echo 获取数据库统计信息...
python scripts\run.py stats
if errorlevel 1 (
    echo 获取统计信息失败
    pause
)
goto menu

:list_schools
echo.
echo 列出学校信息...
set /p limit="请输入显示数量 (回车使用默认10): "
if "%limit%"=="" (
    python scripts\run.py list
) else (
    python scripts\run.py list --limit %limit%
)
if errorlevel 1 (
    echo 获取学校列表失败
    pause
)
goto menu

:exit
echo.
echo 感谢使用！
pause
exit /b 0
