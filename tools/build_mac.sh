#!/usr/bin/env bash
set -euo pipefail

APP_NAME="小铠同学"
SPEC_FILE="pyinstaller.spec"
ICON_ICNS=""

echo "[BUILD] 启动 macOS 打包"

# 兼容用户虚拟环境目录名为 venv 或 .venv 的情况（优先使用 venv）
VENV_DIR=""
if [ -d "venv" ]; then
  VENV_DIR="venv"
elif [ -d ".venv" ]; then
  VENV_DIR=".venv"
else
  echo "[BUILD] 未发现 venv 或 .venv，请先运行 tools/setup_mac_env.sh 创建虚拟环境"
  exit 1
fi
echo "[BUILD] 使用虚拟环境: $VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "[BUILD] 使用 PyInstaller spec 构建 .app"
pyinstaller "$SPEC_FILE" --clean

echo "[BUILD] 构建完成，产物位于 dist/$APP_NAME.app"

# 可选代码签名（占位示例，如需启用请填充证书名称）
SIGN_IDENTITY=""
if [ -n "$SIGN_IDENTITY" ]; then
  echo "[SIGN] 使用证书签名: $SIGN_IDENTITY"
  codesign --deep --force --verify --verbose \
    --sign "$SIGN_IDENTITY" \
    "dist/$APP_NAME.app"
fi

# 可选生成 DMG
if command -v create-dmg >/dev/null 2>&1; then
  echo "[DMG] 生成 DMG 包"
  rm -f "$APP_NAME.dmg" || true
  create-dmg \
    --volname "$APP_NAME 安装" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --app-drop-link 425 180 \
    "$APP_NAME.dmg" \
    "dist/$APP_NAME.app"
  echo "[DMG] 输出: $APP_NAME.dmg"
else
  echo "[DMG] 未安装 create-dmg，跳过 DMG 生成。可运行 brew install create-dmg 后重试。"
fi

echo "[BUILD] 完成"
