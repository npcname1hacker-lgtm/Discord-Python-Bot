# Render 部署指南

## 部署步驟

### 第 1 步：準備 GitHub 倉庫

1. 將此專案推送到 GitHub
2. 確保以下檔案都在倉庫中：
   - `integrated_launcher.py`
   - `bot.py`
   - `web_app.py`
   - `web_models.py`
   - `models.py`
   - `commands.py`
   - `application_system.py`
   - `config.py`
   - `requirements.txt`
   - `web/` 資料夾（包含 templates 和 static）

### 第 2 步：在 Render 創建服務

1. 前往 [render.com](https://render.com) 註冊/登入
2. 點擊 **New +** → **Web Service**
3. 連接你的 GitHub 帳號，選擇你的倉庫
4. 設定以下參數：

| 設定項目 | 值 |
|---------|---|
| Name | grv-team-bot |
| Environment | Python 3 |
| Region | Singapore（或最近的區域）|
| Branch | main |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python integrated_launcher.py` |

### 第 3 步：設定環境變數

在 Render 的 **Environment** 頁面添加以下變數：

| Key | Value |
|-----|-------|
| `DISCORD_TOKEN` | 你的 Discord 機器人 Token |
| `DATABASE_URL` | PostgreSQL 連接字串（Render 提供）|
| `PYTHON_VERSION` | 3.11 |

### 第 4 步：創建 PostgreSQL 資料庫（可選）

1. 在 Render 點擊 **New +** → **PostgreSQL**
2. 選擇免費方案或付費方案
3. 創建後，複製 **Internal Database URL**
4. 將這個 URL 設為 `DATABASE_URL` 環境變數

### 第 5 步：部署

1. 點擊 **Create Web Service**
2. 等待 Render 建構和部署
3. 查看日誌確認機器人已連接

## 價格說明

| 方案 | 價格 | 說明 |
|-----|------|-----|
| Free | $0 | 15分鐘無活動會休眠 |
| Starter | $7/月 | 24/7 運行 |

## 注意事項

1. **免費方案限制**：15分鐘無活動會休眠，可用 UptimeRobot 保持喚醒
2. **資料庫**：Render PostgreSQL 免費方案有 90 天限制
3. **語音功能**：Render 支援 UDP，語音功能應該可以正常運作

## 環境變數範例

```
DISCORD_TOKEN=MTQxMDg0OTczMTY2MzM2NDEyNg.xxxxx.xxxxxxx
DATABASE_URL=postgresql://user:password@host:5432/database
```

## 常見問題

**Q: 機器人離線了？**
- 檢查 Render 日誌是否有錯誤
- 確認 DISCORD_TOKEN 正確
- 免費方案可能因閒置而休眠

**Q: 網站無法訪問？**
- 確認服務已啟動完成
- 查看日誌中 Flask 是否正常啟動

**Q: 資料庫連接失敗？**
- 確認 DATABASE_URL 格式正確
- 確認資料庫服務正在運行
