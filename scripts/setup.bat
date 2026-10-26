@echo off
chcp 65001 >nul
echo ============================================
echo  homework-photo-answer  环境安装（Windows）
echo ============================================

where python >nul 2>nul
if errorlevel 1 (
  echo [!] 没有检测到 Python。
  echo     请先到 https://www.python.org/downloads/ 下载安装，
  echo     安装时务必勾选 "Add Python to PATH"，然后重新运行本脚本。
  pause
  exit /b 1
)

python -m venv .venv
if errorlevel 1 ( echo [!] 创建虚拟环境失败 & pause & exit /b 1 )

.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 ( echo [!] 依赖安装失败，检查网络后重试 & pause & exit /b 1 )

echo.
echo [OK] 安装完成。以后这样运行：
echo      .venv\Scripts\python.exe cfg_XXX.py
echo      .venv\Scripts\python.exe mkpdf.py out.pdf a.jpg b.jpg
echo.
pause
