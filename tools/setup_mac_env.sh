#!/usr/bin/env bash
set -euo pipefail

echo "[SETUP] macOS 环境初始化开始"

# 检查 Homebrew
if ! command -v brew >/dev/null 2>&1; then
  echo "[SETUP] 未发现 Homebrew，请先安装：https://brew.sh"
  exit 1
fi

PYVER="3.11"

echo "[SETUP] 安装 Python@${PYVER} (如已安装会跳过)"
brew list --versions python@${PYVER} >/dev/null 2>&1 || brew install python@${PYVER}

PYBIN="$(brew --prefix)/opt/python@${PYVER}/bin/python${PYVER}"
if [ ! -x "$PYBIN" ]; then
  echo "[SETUP] 未找到 Python 可执行文件: $PYBIN"
  exit 1
fi

echo "[SETUP] 创建虚拟环境 .venv"
"$PYBIN" -m venv .venv
source .venv/bin/activate

echo "[SETUP] 升级 pip"
pip install --upgrade pip wheel setuptools

echo "[SETUP] 安装项目依赖"
pip install -r python-desktop-translator/requirements.txt

echo "[SETUP] 安装 PyInstaller"
pip install pyinstaller

echo "[SETUP] 可选安装 DMG 工具 create-dmg"
brew list --versions create-dmg >/dev/null 2>&1 || brew install create-dmg || true

echo "[SETUP] 完成"
