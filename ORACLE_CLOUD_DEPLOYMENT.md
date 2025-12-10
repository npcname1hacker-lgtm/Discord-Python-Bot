# Oracle Cloud Free Tier 部署指南

## 📋 前置要求
- Oracle Cloud Free Tier 帳戶（免費建立）
- SSH 客戶端（Windows 用 PuTTY，Mac/Linux 用終端）

---

## 🎯 第一步：建立 Oracle Cloud 帳戶

1. 前往 https://www.oracle.com/cloud/free/
2. 點擊「開始免費試用」
3. 填寫註冊信息（需要信用卡驗證，但不會扣費）
4. 驗證成功後登入控制台

---

## 🖥️ 第二步：建立 Compute VM 實例

1. 登入 Oracle Cloud 控制台
2. 選擇「Compute」→「Instances」
3. 點擊「建立實例」
4. 配置設定：
   - **映像**：Ubuntu 22.04（免費層支援）
   - **形狀**：Ampere（ARM）- A1 Compute（免費層 4 個核心、24GB 記憶體）
   - **網路**：保持預設設定
5. 下載 SSH 密鑰（`.key` 檔案）
6. 點擊「建立」

**💾 記下你的實例 IP 位址！**

---

## 🔑 第三步：SSH 連接到 VM

### Windows (PuTTY)
```bash
# 轉換密鑰格式（PPK）
puttygen.exe <your-key>.key -O private -o <your-key>.ppk

# 連接
puttygen 連接 ubuntu@<你的-IP>
```

### Mac/Linux
```bash
chmod 400 /path/to/your-key.key
ssh -i /path/to/your-key.key ubuntu@<你的-IP>
```

---

## 📦 第四步：安裝依賴

連接到 VM 後，執行以下命令：

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝 Python 和必要工具
sudo apt install -y python3.11 python3-pip python3-venv git

# 安裝 PostgreSQL（如果使用資料庫）
sudo apt install -y postgresql postgresql-contrib

# 安裝其他依賴
sudo apt install -y build-essential libssl-dev libffi-dev
```

---

## 🗄️ 第五步：配置 PostgreSQL

```bash
# 啟動 PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 建立資料庫和用戶
sudo -u postgres psql << EOF
CREATE DATABASE grv_team;
CREATE USER grv_user WITH PASSWORD 'your-secure-password';
ALTER ROLE grv_user SET client_encoding TO 'utf8';
ALTER ROLE grv_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE grv_user SET default_transaction_deferrable TO on;
ALTER ROLE grv_user SET default_transaction_read_committed TO on;
GRANT ALL PRIVILEGES ON DATABASE grv_team TO grv_user;
\q
EOF
```

---

## 📥 第六步：部署應用

```bash
# 建立應用目錄
mkdir -p /home/ubuntu/grv-team
cd /home/ubuntu/grv-team

# 克隆或複製代碼（假設上傳到 GitHub）
git clone https://your-github-repo.git .

# 建立虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝 Python 依賴
pip install -r requirements.txt

# 建立 .env 檔案
cat > .env << EOF
DATABASE_URL=postgresql://grv_user:your-secure-password@localhost/grv_team
DISCORD_TOKEN=your_discord_token
FLASK_SECRET_KEY=your_flask_secret_key
EOF

# 初始化資料庫
python3 -c "from web_models import get_web_database; get_web_database()"
```

---

## 🚀 第七步：使用 Systemd 設置持久服務

建立服務檔案：
```bash
sudo nano /etc/systemd/system/grv-team.service
```

貼上以下內容：
```ini
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

[Install]
WantedBy=multi-user.target
```

啟動服務：
```bash
sudo systemctl daemon-reload
sudo systemctl start grv-team
sudo systemctl enable grv-team

# 檢查狀態
sudo systemctl status grv-team

# 查看日誌
sudo journalctl -u grv-team -f
```

---

## 🌐 第八步：配置防火牆

```bash
# 允許 HTTP/HTTPS 流量
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

在 Oracle Cloud 控制台安全列表中也要開放這些埠。

---

## 🔐 第九步：配置 Nginx 反向代理（可選但推薦）

```bash
sudo apt install -y nginx

# 建立 Nginx 配置
sudo nano /etc/nginx/sites-available/grv-team
```

貼上：
```nginx
server {
    listen 80;
    server_name your-domain-or-ip;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

啟用：
```bash
sudo ln -s /etc/nginx/sites-available/grv-team /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

---

## ✅ 驗證部署

1. 訪問 `http://your-vm-ip` 檢查網站
2. 檢查 Discord 機器人是否在線
3. 監控日誌：
```bash
sudo journalctl -u grv-team -f
```

---

## 🆘 故障排除

### 機器人無法連接
```bash
# 檢查環境變數
cat /home/ubuntu/grv-team/.env

# 重啟服務
sudo systemctl restart grv-team
```

### 資料庫連接失敗
```bash
# 檢查 PostgreSQL 狀態
sudo systemctl status postgresql

# 測試連接
psql -h localhost -U grv_user -d grv_team
```

### 無法訪問網站
```bash
# 檢查 Nginx
sudo systemctl status nginx

# 檢查防火牆規則
sudo ufw status
```

---

## 📝 成本估算

使用 Oracle Cloud Free Tier：
- **VM (A1 Compute)**：永久免費（4 核心、24GB）
- **PostgreSQL**：可自行安裝在 VM 上（免費）
- **總成本**：💰 完全免費！

---

## 🎉 完成！

你現在有了：
- ✅ 24/7 永不斷線的伺服器
- ✅ 完全免費（永久）
- ✅ Discord 機器人永遠在線
- ✅ 網站控制面板隨時可訪問
