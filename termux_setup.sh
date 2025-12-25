#!/data/data/com.termux/files/usr/bin/bash

# Termux 部署腳本 - GRV 戰隊管理系統
echo "🚀 正在初始化 Termux 環境..."

# 更新系統
pkg update && pkg upgrade -y

# 安裝必要套件
pkg install python python-pip nodejs libffi openssl git sqlite -y

# 創建專案目錄
mkdir -p ~/grv_bot
cd ~/grv_bot

# 複製環境變數範本 (請記得修改)
if [ ! -f .env ]; then
    echo "⚠️ 請記得手動建立並配置 .env 文件"
fi

# 安裝 Python 依賴
pip install --upgrade pip
pip install flask flask-login flask-sqlalchemy discord-py requests python-dotenv bcrypt gunicorn py-bcrypt

echo "✅ 環境準備完成！"
echo "💡 啟動指令：python integrated_launcher.py"
