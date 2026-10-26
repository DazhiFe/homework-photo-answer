#!/usr/bin/env bash
# homework-photo-answer 环境安装（macOS / Linux）
set -e

PY=python3
command -v $PY >/dev/null 2>&1 || { echo "[!] 没检测到 python3，请先安装 Python 3.10+"; exit 1; }

echo "==> 创建虚拟环境 .venv"
$PY -m venv .venv

echo "==> 安装依赖"
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo
echo "[OK] 安装完成。以后这样运行："
echo "     .venv/bin/python cfg_XXX.py"
echo "     .venv/bin/python mkpdf.py out.pdf a.jpg b.jpg"
echo
echo "提示：macOS 若提示没有中文字体，安装 noto-cjk 或把字体放进 scripts/assets/ 即可。"
