# HidenCloud 部署指南 - 24/7 永不斷線

## 📋 為什麼選擇 HidenCloud？

✅ 完全免費（真的永久免費）
✅ 24/7 永不斷線
✅ 資源豐富：3GB RAM、15GB 儲存、2 個資料庫
✅ 無需信用卡
✅ 同時支持 Discord 機器人 + Flask 網站
✅ 自動重啟機器人
⚠️ 只需每週點擊一次「更新」（很簡單）

---

## 🚀 第一步：建立 HidenCloud 帳戶

1. 前往 https://www.hidencloud.com/service/free-discord-hosting
2. 點擊「Sign Up」或「Create Account」
3. 填寫郵箱、用戶名、密碼
4. 驗證郵箱
5. ✅ 完成！

---

## 📦 第二步：準備代碼（已完成）

你的項目已經準備好了，需要的文件都在根目錄：

```
integrated_launcher.py    ← 主程序（同時啟動 Bot + Flask）
bot.py
web_app.py
web_models.py
models.py
commands.py
application_system.py
config.py
email_service.py
requirements.txt
web/
├── templates/
└── static/
```

**無需任何修改！** HidenCloud 可以直接運行你的代碼。

---

## 🔐 第三步：上傳代碼到 GitHub

如果你的代碼還沒有在 GitHub 上：

```bash
# 在你的本地電腦或 Replit 執行
cd /your/project/directory
git init
git add .
git commit -m "Prepare for HidenCloud deployment"
git remote add origin https://github.com/你的用戶名/grv-team-bot.git
git push -u origin main
```

如果已經有 GitHub，確保代碼已推送到 `main` 分支。

---

## 🎯 第四步：在 HidenCloud 建立服務

1. **登入 HidenCloud 儀表板**
2. **點擊「Create New Service」或「New Project」**
3. **選擇「Discord Bot」或「Python Application」**
4. **填寫基本信息**：
   - **Service Name**: `grv-team-bot`
   - **Description**: GRV 戰隊管理系統
   - **Runtime**: Python 3.11 或以上

---

## 📤 第五步：上傳代碼

### 方法 A：從 GitHub（推薦）
1. 在 HidenCloud 選擇「Deploy from GitHub」
2. 授權 GitHub 連接
3. 選擇你的倉庫：`grv-team-bot`
4. 分支選 `main`
5. **Main File / Entry Point**: `integrated_launcher.py`
6. 點擊「Deploy」

### 方法 B：手動上傳
1. 將整個項目壓縮成 `.zip` 文件
2. 在 HidenCloud 上傳這個 ZIP 檔案
3. 設定 **Start Command**: `python integrated_launcher.py`

---

## ⚙️ 第六步：設置環境變數

1. **進入服務設置**
2. **找到「Environment Variables」或「Config」**
3. **添加以下變數**：

```
DISCORD_TOKEN=你的_Discord_機器人_Token
FLASK_SECRET_KEY=生成的隨機密鑰
DATABASE_URL=sqlite:///grv_team.db
COMMAND_PREFIX=!
BOT_STATUS=使用 !help 獲取幫助
PORT=5000
```

### 如何獲取 Discord Token：
1. 前往 https://discord.com/developers/applications
2. 選擇你的應用
3. 點擊「Bot」
4. 點擊「Reset Token」
5. 複製 Token 值

### 生成隨機密鑰：
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🚀 第七步：啟動服務

1. 在 HidenCloud 儀表板點擊你的服務
2. 點擊「Start」或「Deploy」按鈕
3. 等待 1-2 分鐘，服務啟動
4. ✅ 完成！

---

## ✅ 驗證部署成功

### 檢查機器人狀態：
1. **進入你的 Discord 伺服器**
2. **查看機器人是否在線**（應該顯示綠色狀態）
3. **試試指令**：`!help`、`!ping`、`!info` 等
4. **查看 HidenCloud 日誌**：應該看到啟動信息

### 檢查網站：
1. HidenCloud 會給你一個公開 URL（例如：`https://your-service-xxxxx.hidencloud.com`）
2. **訪問這個 URL** 應該能看到登入頁面
3. ✅ 網站成功運行！

---

## 📊 監控和管理

### 查看實時日誌
```
HidenCloud 儀表板 → 你的服務 → Logs / Console
```

### 重啟服務
```
HidenCloud 儀表板 → 你的服務 → Restart
```

### 停止服務
```
HidenCloud 儀表板 → 你的服務 → Stop
```

---

## 🔄 每週維護（重要！）

HidenCloud 免費方案需要每週更新一次：

1. **登入 HidenCloud 儀表板**
2. **找到你的服務**
3. **點擊「Renew」或「Update」按鈕**
4. ✅ 完成！（只需 10 秒鐘）

**提示**：設置日曆提醒每週同一天更新。

---

## 📈 升級到付費方案（可選）

如果你想避免每週更新：

| 方案 | 價格 | 特點 |
|-----|------|------|
| 免費 | €0 | 每週更新一次 |
| 基礎 | €1.99/月 | 無需更新 |
| 高級 | €4.99/月 | 優先支持 + 更多資源 |

使用折扣碼 `CLOUDY10` 享受首月折扣。

---

## 📁 數據庫

HidenCloud 免費方案包含：
- **2 個 MySQL/PostgreSQL 資料庫**
- 你的應用現在用 SQLite（本地檔案）
- 如果需要，可以升級到 PostgreSQL

當前設置使用 SQLite，數據自動保存到 HidenCloud 文件系統。

---

## 🆘 故障排除

### 機器人無法啟動
```
檢查事項：
1. DISCORD_TOKEN 是否正確設置在環境變數中？
2. requirements.txt 是否完整？
3. Entry Point 是否指向 integrated_launcher.py？
4. 查看 HidenCloud 的錯誤日誌
```

### 網站無法訪問
```
檢查事項：
1. Flask 是否正常啟動？（檢查日誌）
2. HidenCloud 是否給了你公開 URL？
3. 嘗試重啟服務
4. 檢查防火牆設置
```

### 機器人在線但沒有反應
```
檢查事項：
1. 指令前綴是否正確？（默認 !）
2. Discord Intents 是否啟用？
3. 機器人是否有足夠權限？
4. 檢查日誌中的錯誤信息
```

### 服務被暫停
```
解決方案：
1. HidenCloud 免費方案需要每週更新
2. 進入儀表板點擊「Renew」
3. 服務立即恢復
```

---

## 💡 額外提示

### 1. 自動備份
```bash
# 定期下載你的數據庫
# 在 HidenCloud 文件瀏覽器中下載 grv_team.db
```

### 2. 從 GitHub 更新代碼
```bash
# 在本地修改代碼後
git add .
git commit -m "Update bot features"
git push origin main

# 在 HidenCloud 重新部署即可
```

### 3. 實時監控
- HidenCloud 提供 CPU、RAM、儲存空間的實時監控
- 免費方案有 3GB RAM，足以運行你的應用

### 4. UptimeRobot 保持喚醒（可選）
```
為了額外保障：
1. 註冊 UptimeRobot（免費）
2. 設置監控 HidenCloud 提供的公開 URL
3. 每 5 分鐘 ping 一次，確保服務不睡眠
```

---

## 📞 需要幫助？

- **HidenCloud 官方**：https://www.hidencloud.com
- **Discord.py 文檔**：https://discordpy.readthedocs.io
- **Flask 文檔**：https://flask.palletsprojects.com/
- **Python 文檔**：https://python.org/docs

---

## 🎉 完成！

現在你擁有：
- ✅ 24/7 永不斷線的 Discord 機器人
- ✅ 24/7 運行的 Flask 網站控制面板
- ✅ 完全免費（永久）
- ✅ 所有功能正常運行
- ✅ 無需信用卡

祝你部署成功！🚀

---

## 🔗 快速連結

- [HidenCloud 首頁](https://www.hidencloud.com)
- [HidenCloud 免費 Discord 託管](https://www.hidencloud.com/service/free-discord-hosting)
- [登入儀表板](https://www.hidencloud.com/dashboard)
- [官方文檔](https://docs.hidencloud.com/hidencloud)
