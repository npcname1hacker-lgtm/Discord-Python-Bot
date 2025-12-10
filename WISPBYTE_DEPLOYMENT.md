# Wispbyte 部署指南 - 24/7 永不斷線

## 📋 為什麼選擇 Wispbyte？

✅ 完全免費（真的永久免費）
✅ 24/7 永不斷線
✅ 無需更新/續期
✅ 無需信用卡
✅ 國小生也能用
✅ Python 完全支持

---

## 🚀 第一步：建立 Wispbyte 帳戶

1. 前往 https://wispbyte.com
2. 點擊「Sign Up」
3. 填寫信息（郵箱、用戶名、密碼）
4. 驗證郵箱
5. 完成！

---

## 📦 第二步：準備應用代碼

### 方案 A：使用當前 Replit 代碼（推薦）

1. **下載代碼**
   ```bash
   # 在 Replit 中下載整個項目
   # 或在本地 clone 你的代碼
   ```

2. **保留必要文件**
   ```
   integrated_launcher.py    ← 主程序
   bot.py
   web_app.py
   web_models.py
   models.py
   commands.py
   application_system.py
   config.py
   email_service.py
   web/
   ├── templates/
   └── static/
   requirements.txt
   .env.example
   ```

3. **刪除不需要的文件**
   ```bash
   rm -f ORACLE_CLOUD_DEPLOYMENT.md
   rm -f setup-oracle.sh
   rm -f *.md  # 只保留 WISPBYTE_DEPLOYMENT.md
   ```

---

## 🐍 第三步：建立 requirements.txt

確保 `requirements.txt` 包含所有依賴：

```
Flask==2.3.0
Flask-Login==0.6.2
Flask-SQLAlchemy==3.0.5
discord.py==2.3.1
SQLAlchemy==2.0.19
psycopg2-binary==2.9.6
bcrypt==4.0.1
python-dotenv==1.0.0
requests==2.31.0
lavalink==2.9.0
pynacl==1.5.0
werkzeug==2.3.0
```

---

## 🗄️ 第四步：建立 Wispbyte 實例

### 在 Wispbyte 控制台：

1. **建立新項目**
   - 點擊「New Project」
   - 選擇「Python」
   - 命名（例：grv-team-bot）

2. **配置選項**
   - **Runtime**: Python 3.11+
   - **Entry Point**: `integrated_launcher.py`
   - **Memory**: 選擇默認（足夠）
   - **CPU**: 選擇默認（足夠）

3. **上傳代碼**
   - 方法 A: 拖拉上傳檔案
   - 方法 B: 使用 Wispbyte CLI
     ```bash
     npm install -g wispbyte
     wispbyte login
     wispbyte upload
     ```

---

## 🔐 第五步：配置環境變數

### 在 Wispbyte 項目設置中：

1. **點擊「Environment Variables」**
2. **添加以下變數**

```
DISCORD_TOKEN=你的_Discord_機器人_Token
FLASK_SECRET_KEY=你的_隨機_Secret_Key
DATABASE_URL=sqlite:///grv_team.db
COMMAND_PREFIX=!
BOT_STATUS=使用 !help 獲取幫助
```

### 如何獲取 Discord Token：

1. 前往 https://discord.com/developers/applications
2. 選擇你的應用
3. 點擊「Bot」
4. 點擊「Reset Token」
5. 複製 Token 值
6. **絕對不要分享這個 Token！**

### 生成隨機密鑰：

```bash
# 在任何 Python 環境執行
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📁 第六步：配置數據庫

### SQLite（推薦用於 Wispbyte）

Wispbyte 提供持久存儲，SQLite 就夠用了。

**在 `web_models.py` 確保有：**
```python
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///grv_team.db')
```

數據庫文件會自動保存在 Wispbyte 的文件系統中。

---

## ⚙️ 第七步：建立 startup.sh（可選但推薦）

在項目根目錄建立 `startup.sh`：

```bash
#!/bin/bash
# 安裝依賴
pip install -r requirements.txt

# 初始化數據庫
python3 -c "from web_models import get_web_database; get_web_database()"

# 啟動應用
python3 integrated_launcher.py
```

在 Wispbyte 項目設置中：
- **Entry Point**: `bash startup.sh`

---

## ✅ 第八步：部署和驗證

1. **點擊「Deploy」或「Start」**
2. **等待應用啟動**（3-5 分鐘）
3. **檢查日誌** - Wispbyte 會顯示啟動日誌
4. **驗證運行**
   ```bash
   # 訪問網站（Wispbyte 會給你一個公開 URL）
   https://your-project-xxxxx.wispbyte.com
   
   # 檢查 Discord 機器人是否在線
   在 Discord 伺服器看機器人狀態
   ```

---

## 📊 監控和管理

### 查看日誌
```
Wispbyte 控制台 → 項目 → Logs
```

### 重啟應用
```
Wispbyte 控制台 → 項目 → Restart
```

### 更新代碼
```
1. 更新本地代碼
2. 在 Wispbyte 上刪除舊項目
3. 上傳新代碼
4. 重新部署
```

---

## 🆘 故障排除

### 機器人無法連接
```
檢查事項：
1. DISCORD_TOKEN 是否正確？
2. 檢查日誌中的錯誤信息
3. 確認機器人已邀請到伺服器
4. 檢查 Discord Intents 是否啟用
```

### 應用無法啟動
```
檢查事項：
1. requirements.txt 是否完整？
2. integrated_launcher.py 是否存在？
3. 查看詳細的啟動日誌
4. 檢查所有文件是否上傳
```

### 數據遺失
```
Wispbyte 文件系統是持久的
SQLite 數據庫會被保存
無需擔心重啟時數據遺失
```

---

## 🎉 完成！

你現在有了：
- ✅ 24/7 永不斷線的 Discord 機器人
- ✅ 完整的網站控制面板
- ✅ 完全免費（永久）
- ✅ 無需信用卡
- ✅ 數據自動保存

---

## 💡 額外提示

### 1. 自動備份（可選）
```bash
# 定期下載 grv_team.db 備份
# 在 Wispbyte 文件瀏覽器中下載
```

### 2. 自動更新代碼
```
# 如果代碼在 GitHub
# 可以在 Wispbyte 設置中配置 GitHub 自動部署
```

### 3. 監控健康狀態
```
# 在 Discord 中設置健康檢查指令
# 定期驗證機器人是否在線
```

---

## 📞 需要幫助？

- **Wispbyte 官方文檔**: https://wispbyte.com/docs
- **Discord.py 文檔**: https://discordpy.readthedocs.io
- **Python 文檔**: https://python.org/docs

祝你部署成功！🚀
