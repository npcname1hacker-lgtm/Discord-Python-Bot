#!/data/data/com.termux/files/usr/bin/bash

# Termux 部署腳本 - GRV 戰隊管理系統
echo "🚀 正在初始化 Termux 環境..."

# 更新系統
pkg update && pkg upgrade -y

# 安裝必要套件與編譯工具
pkg update && pkg upgrade -y
pkg install python python-pip nodejs libffi openssl git sqlite clang make binutils -y

# 創建專案目錄
mkdir -p ~/grv_bot
cd ~/grv_bot

# 安裝 Python 依賴
pip install --upgrade pip
# 先安裝不需要編譯的
pip install flask flask-login flask-sqlalchemy discord.py requests python-dotenv gunicorn
# 嘗試安裝 bcrypt，如果失敗則安裝 pure-python 版本
pip install bcrypt || pip install py-bcrypt

echo "✅ 環境準備完成！"
echo "💡 啟動指令：python integrated_launcher.py"
