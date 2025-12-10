# Wispbyte 部署清單 ✅

## 📦 需要上傳的文件

### ✅ 核心Python文件（必須）
```
✓ integrated_launcher.py    (主程序)
✓ bot.py                     (Discord機器人)
✓ web_app.py                 (Flask網站)
✓ web_models.py              (網站數據庫模型)
✓ models.py                  (機器人數據庫模型)
✓ commands.py                (機器人指令)
✓ application_system.py      (申請系統)
✓ config.py                  (配置)
✓ email_service.py           (郵件服務)
✓ voice_handler.py           (語音處理)
✓ requirements.txt           (依賴包)
```

### ✅ 網站文件（必須）
```
web/
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── applications.html
│   ├── bot_control.html
│   ├── users.html
│   ├── settings.html
│   ├── welcome_settings.html
│   └── restricted.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

### ✅ 配置文件（可選但推薦）
```
✓ WISPBYTE_DEPLOYMENT.md    (部署指南)
✓ .env.example              (環境變數範例，如果有的話)
```

### ❌ 不需要上傳
```
✗ ORACLE_CLOUD_DEPLOYMENT.md
✗ setup-oracle.sh
✗ __pycache__/
✗ .replit
✗ .git/
✗ .gitignore
```

---

## 🚀 上傳步驟

### 第1步：下載所有文件
1. 在 Replit 按 **Files 圖示**
2. 選擇上面列出的所有文件
3. 下載（ZIP 或逐個下載）

### 第2步：在 Wispbyte 上傳
1. 登入 Wispbyte（https://wispbyte.com）
2. 建立新 Python 項目
3. **拖拉上傳**所有文件
4. 確保文件結構保持：
   ```
   grv-team-bot/
   ├── integrated_launcher.py
   ├── bot.py
   ├── requirements.txt
   └── web/
       ├── templates/
       └── static/
   ```

### 第3步：設置環境變數
在 Wispbyte 項目設置 → Environment Variables

```
DISCORD_TOKEN=你的Discord機器人Token
FLASK_SECRET_KEY=隨機密鑰（運行: python -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=sqlite:///grv_team.db
BOT_STATUS=使用 !help 獲取幫助
COMMAND_PREFIX=!
```

### 第4步：配置入口點
- **Entry Point**: `integrated_launcher.py`
- **Runtime**: Python 3.11+

### 第5步：部署
- 點擊「Deploy」或「Start」
- 等待 3-5 分鐘
- ✅ 完成！

---

## ✅ 驗證部署成功

1. **查看 Wispbyte 日誌** - 應該看到：
   ```
   Flask 網站已啟動 on 0.0.0.0:5000
   Discord 機器人已連接
   ```

2. **訪問你的網站**
   ```
   https://grv-team-bot-xxxxx.wispbyte.com
   ```

3. **檢查 Discord 機器人** - 應該在線

---

## 💡 如果遇到問題

**機器人無法連接**
- 檢查 DISCORD_TOKEN 是否正確
- 確認機器人已邀請到伺服器
- 查看 Wispbyte 日誌找錯誤信息

**網站無法訪問**
- 確認所有 web/templates 和 web/static 文件都上傳了
- 檢查 requirements.txt 是否完整
- 查看日誌中的 Python 錯誤

**數據庫錯誤**
- 確保 DATABASE_URL 設置為 `sqlite:///grv_team.db`
- 第一次啟動會自動創建數據庫

---

準備好了嗎？開始上傳吧！ 🚀
