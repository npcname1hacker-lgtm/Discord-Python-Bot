#!/bin/bash

# ɢʀᴠ Team Oracle Cloud 快速安裝腳本

set -e

echo "=========================================="
echo "ɢʀᴠ Team Oracle Cloud 部署腳本"
echo "=========================================="

# 檢查是否為 root
if [ "$EUID" -ne 0 ]; then 
    echo "請用 sudo 執行此腳本: sudo bash setup-oracle.sh"
    exit 1
fi

echo "[1/8] 更新系統..."
apt update && apt upgrade -y

echo "[2/8] 安裝 Python 和基礎工具..."
apt install -y python3.11 python3-pip python3-venv git build-essential libssl-dev libffi-dev

echo "[3/8] 安裝 PostgreSQL..."
apt install -y postgresql postgresql-contrib

echo "[4/8] 啟動 PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

echo "[5/8] 建立應用目錄..."
mkdir -p /home/ubuntu/grv-team
chown ubuntu:ubuntu /home/ubuntu/grv-team

echo "[6/8] 安裝 Python 虛擬環境和依賴..."
cd /home/ubuntu/grv-team
sudo -u ubuntu python3 -m venv venv
sudo -u ubuntu venv/bin/pip install --upgrade pip
# 用戶需要手動複製代碼和 requirements.txt
# 下面是範本
# sudo -u ubuntu venv/bin/pip install -r requirements.txt

echo "[7/8] 建立 Systemd 服務..."
cat > /etc/systemd/system/grv-team.service << 'EOF'
[Unit]
Description=ɢʀᴠ Team Bot and Web Service
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/grv-team
ExecStart=/home/ubuntu/grv-team/venv/bin/python integrated_launcher.py
Restart=always
RestartSec=10
Environment="PATH=/home/ubuntu/grv-team/venv/bin"

[Install]
WantedBy=multi-user.target
EOF

echo "[8/8] 配置防火牆..."
apt install -y ufw
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

systemctl daemon-reload

echo ""
echo "=========================================="
echo "✅ 基礎環境已安裝！"
echo "=========================================="
echo ""
echo "後續步驟："
echo "1. 將代碼上傳到 /home/ubuntu/grv-team"
echo "2. 建立 .env 檔案配置環境變數"
echo "3. 運行: source /home/ubuntu/grv-team/venv/bin/activate"
echo "4. 運行: pip install -r requirements.txt"
echo "5. 配置 PostgreSQL 資料庫"
echo "6. 運行: sudo systemctl start grv-team"
echo "7. 檢查: sudo systemctl status grv-team"
echo ""
echo "查看日誌: sudo journalctl -u grv-team -f"
