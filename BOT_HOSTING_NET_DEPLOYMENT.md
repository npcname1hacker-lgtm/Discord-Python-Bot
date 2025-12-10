# Bot-Hosting.net 部署指南 - 24/7 永不斷線

## 📋 Bot-Hosting.net 是什麼？

✅ 完全免費（真的永久免費）
✅ 24/7 永不斷線
✅ 無需信用卡
✅ Python 完全支持
✅ 自動重啟機器人

---

## ⚠️ 重要注意

Bot-Hosting.net 主要用於**Discord 機器人**。

你的系統包含：
- ✅ Discord 機器人 → 可以部署
- ❌ Flask 網站 → Bot-Hosting.net 不支持

**解決方案：**
- 機器人部分：部署到 Bot-Hosting.net
- 網站部分：保留在 Replit 或其他地方

或者只部署機器人部分，網站功能暫停。

---

## 🚀 部署步驟

### 第 1 步：準備機器人代碼

在 Replit 中建立一個**簡化版的機器人**（不含網站）：

**bot_only.py**（新檔案）
```python
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} 已上線')
    print(f'已連接到 {len(bot.guilds)} 個伺服器')

bot.run(os.getenv('DISCORD_TOKEN'))
```

**requirements.txt**（簡化版）
```
discord.py==2.3.1
python-dotenv==1.0.0
```

### 第 2 步：上傳到 GitHub

```bash
cd /home/runner/workspace
git add bot_only.py requirements.txt
git commit -m "Bot-Hosting.net deployment"
git push origin main
```

### 第 3 步：在 Bot-Hosting.net 建立帳戶

1. 前往 https://bot-hosting.net
2. 點 **Sign Up** 或 **Register**
3. 填寫郵箱、用戶名、密碼
4. 驗證郵箱
5. ✅ 完成

### 第 4 步：建立新 Bot

1. 登入 Bot-Hosting.net 儀表板
2. 點 **New Bot** 或 **Create Bot**
3. 填寫資訊：
   - **Name**: `grv-team-bot`
   - **Prefix**: `!`
   - **Description**: GRV 戰隊管理機器人

### 第 5 步：上傳代碼

#### 方法 A：從 GitHub（推薦）
1. 在 Bot-Hosting.net 填入 GitHub 倉庫：
   ```
   https://github.com/npcname1hacker-lgtm/grv-team-bot.git
   ```
2. **Main File**: `bot_only.py` 或 `bot.py`
3. 點 **Deploy**

#### 方法 B：手動上傳
1. 下載你的代碼：`bot.py` 和 `requirements.txt`
2. 在 Bot-Hosting.net 上傳這兩個檔案
3. 設定 **Main File**: `bot.py`

### 第 6 步：設置環境變數

1. 進入 Bot 設置
2. 找 **Environment Variables**
3. 添加：
   ```
   DISCORD_TOKEN=你的_Discord_機器人_Token
   ```

### 第 7 步：啟動

1. 點 **Start** 或 **Deploy**
2. 等待 1-2 分鐘
3. ✅ 機器人上線！

---

## ✅ 驗證部署成功

1. **進入你的 Discord 伺服器**
2. **檢查機器人是否在線**（應該顯示綠色點）
3. **試試指令**：`!help` 或其他指令
4. **查看 Bot-Hosting.net 日誌** - 應該看到啟動信息

---

## 🌐 網站怎麼辦？

由於 Bot-Hosting.net 不支持 Flask 網站，你有幾個選擇：

### 選項 1：只用機器人（推薦）
- 部署機器人到 Bot-Hosting.net（24/7）
- 關閉 Replit 網站
- Discord 機器人功能完整

### 選項 2：機器人 + 網站分開
- **機器人**：Bot-Hosting.net（24/7）
- **網站**：保留在 Replit（會間歇性掉線）

### 選項 3：都部署到 Render
- 支持 Python Flask
- 需要 $7/月 才能 24/7 運行
- 兩個服務在同一地方

---

## 🆘 故障排除

### 機器人無法啟動
```
檢查事項：
1. DISCORD_TOKEN 是否正確？
2. requirements.txt 是否完整？
3. Main File 是否指向正確的 .py 檔案？
4. 查看 Bot-Hosting.net 的錯誤日誌
```

### 機器人在線但沒有反應
```
檢查事項：
1. 機器人是否有正確的 Intents？
2. 指令是否正確實現？
3. 檢查 Discord Developer Portal 的 Permissions
```

### GitHub 連接失敗
```
解決方案：
1. 檢查 GitHub 倉庫是否公開
2. 使用手動上傳代替
3. 確保代碼在 GitHub main 分支中
```

---

## 💡 額外提示

### 1. 自動重啟
Bot-Hosting.net 會自動重啟崩潰的機器人（無需額外配置）

### 2. 資源監控
進入 Bot 儀表板可以看到：
- CPU 使用率
- 記憶體使用量
- 運行時間

### 3. 備份代碼
在 GitHub 保持你的代碼同步，以便隨時重新部署

---

## 📞 需要幫助？

- **Bot-Hosting.net 官方**: https://bot-hosting.net
- **Discord.py 文檔**: https://discordpy.readthedocs.io
- **機器人常見問題**: https://bot-hosting.net/help

---

## 🎉 完成！

現在你有了：
- ✅ 24/7 永不斷線的 Discord 機器人
- ✅ 完全免費（永久）
- ✅ 自動重啟和監控
- ✅ 所有機器人功能正常

祝你部署成功！🚀
