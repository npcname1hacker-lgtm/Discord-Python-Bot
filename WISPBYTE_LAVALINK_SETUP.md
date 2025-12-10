# Wispbyte Lavalink 完整設置指南

## 🎵 Wispbyte + Lavalink + Discord.py 完整方案

**優勢**：
- ✅ 一個平台搞定：Wispbyte 支持 Python + Java
- ✅ 24/7 永不斷線機器人
- ✅ 完整音樂功能（YouTube、SoundCloud 等）
- ✅ 完全免費

---

## 📋 必需檔案檢查

確保你有：
```
✅ lavalink/Lavalink.jar
✅ lavalink/application.yml
✅ bot.py 或 integrated_launcher.py
✅ requirements.txt
```

---

## 🚀 部署步驟

### **第 1 步：在 Wispbyte 上建立 2 個服務器**

#### 服務器 1：Python 機器人
1. 進入 Wispbyte 儀表板
2. 點 **Create New Server** → 選擇 **Python**
3. 填寫資訊：
   - **Name**: `grv-bot`
   - **Startup Command**: `python integrated_launcher.py`
4. 點 **Create**

#### 服務器 2：Lavalink
1. 點 **Create New Server** → 選擇 **Java**
2. 填寫資訊：
   - **Name**: `grv-lavalink`
   - **Startup Command**: `java -jar Lavalink.jar`
3. 點 **Create**

---

### **第 2 步：上傳檔案到對應服務器**

#### Python 機器人服務器：上傳這些檔案
```
integrated_launcher.py
bot.py
web_app.py
web_models.py
models.py
commands.py
application_system.py
config.py
requirements.txt
web/
  ├── templates/
  ├── static/
```

#### Lavalink 服務器：上傳這些檔案
```
lavalink/
  ├── Lavalink.jar
  └── application.yml
```

---

### **第 3 步：更新 requirements.txt**

添加 Wavelink（Lavalink 的 Python 包裝）：

```txt
discord.py==2.3.1
python-dotenv==1.0.0
flask==3.0.0
flask-login==0.6.3
flask-sqlalchemy==3.1.1
sqlalchemy==2.0.23
bcrypt==4.1.2
requests==2.31.0
psycopg2-binary==2.9.9
discord-py==2.3.1
wavelink==3.3.2
```

---

### **第 4 步：設置 Lavalink 配置**

確保 `lavalink/application.yml` 包含：

```yaml
server:
  port: 2333
  address: 0.0.0.0

lavalink:
  server:
    password: "youshallnotpass"
    sources:
      youtube: true
      bandcamp: true
      soundcloud: true
      twitch: true
      vimeo: true
      http: true
      local: false
    filters:
      volume: true
      equalizer: true
      karaoke: true
      timescale: true
      tremolo: true
      vibrato: true
      distortion: true
      rotation: true
      channelmix: true
      lowpass: true

logging:
  level: INFO
  logback:
    rollingpolicy:
      max-size: 1GB
```

---

### **第 5 步：更新機器人代碼**

在 `bot.py` 頂部添加 Wavelink 初始化：

```python
import discord
from discord.ext import commands
import wavelink
import os

# ... 現有的 import ...

class GRVBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def setup_lavalink(self):
        """初始化 Lavalink 連接"""
        try:
            # 構建 Lavalink URI
            # 在 Wispbyte 上，使用內部 localhost 或獲得的子域
            lavalink_url = os.getenv('LAVALINK_URL', 'http://localhost:2333')
            lavalink_password = os.getenv('LAVALINK_PASSWORD', 'youshallnotpass')
            
            node = wavelink.Node(
                uri=lavalink_url,
                password=lavalink_password
            )
            
            await wavelink.Pool.connect(client=self.bot, nodes=[node])
            print(f"✅ Lavalink 已連接: {lavalink_url}")
            
        except Exception as e:
            print(f"⚠️ Lavalink 連接失敗: {e}")
            print("機器人會在無音樂功能的情況下繼續運行")

@bot.event
async def on_ready():
    print(f'✅ {bot.user} 已上線')
    # 初始化 Lavalink
    if not hasattr(on_ready, 'lavalink_setup'):
        await bot.cogs['GRVBot'].setup_lavalink()
        on_ready.lavalink_setup = True
```

---

### **第 6 步：添加音樂指令**

在 `commands.py` 或 `bot.py` 中添加：

```python
@bot.command(name='play')
async def play(ctx, *, query: str):
    """播放音樂
    
    用法: !play <歌名或 URL>
    例: !play 周杰倫
    """
    
    # 檢查用戶是否在語音頻道
    if not ctx.author.voice:
        return await ctx.send("❌ 請先加入語音頻道")
    
    # 連接到用戶的語音頻道
    if not ctx.voice_client:
        try:
            vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        except Exception as e:
            return await ctx.send(f"❌ 無法連接語音頻道: {e}")
    else:
        vc = ctx.voice_client
    
    # 搜索歌曲
    try:
        tracks = await wavelink.Playable.search(query)
        if not tracks:
            return await ctx.send("❌ 找不到符合的歌曲")
        
        track = tracks[0]
        await vc.play(track)
        await ctx.send(f"🎵 正在播放: **{track.title}**")
        
    except Exception as e:
        await ctx.send(f"❌ 播放失敗: {e}")

@bot.command(name='stop')
async def stop(ctx):
    """停止播放並斷開連接"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⏹️ 已停止播放並斷開連接")
    else:
        await ctx.send("❌ 機器人未連接語音頻道")

@bot.command(name='pause')
async def pause(ctx):
    """暫停播放"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        await ctx.voice_client.pause()
        await ctx.send("⏸️ 已暫停播放")
    else:
        await ctx.send("❌ 沒有正在播放的內容")

@bot.command(name='resume')
async def resume(ctx):
    """繼續播放"""
    if ctx.voice_client and ctx.voice_client.is_paused():
        await ctx.voice_client.resume()
        await ctx.send("▶️ 已繼續播放")
    else:
        await ctx.send("❌ 沒有暫停的內容")
```

---

### **第 7 步：設置環境變數**

在 Wispbyte **Python 服務器** 的設置中添加：

```
DISCORD_TOKEN=你的_Discord_Token
DATABASE_URL=你的_PostgreSQL_URL
LAVALINK_URL=http://localhost:2333
LAVALINK_PASSWORD=youshallnotpass
FLASK_SECRET_KEY=隨機密鑰
```

---

### **第 8 步：部署**

#### Python 服務器
1. 上傳所有 Python 檔案
2. 設置環境變數
3. 點 **Start** → 等待 1-2 分鐘

#### Lavalink 服務器
1. 上傳 `Lavalink.jar` 和 `application.yml`
2. 點 **Start** → 等待 1-2 分鐘
3. 查看日誌確認啟動成功

---

## ✅ 驗證部署

### 檢查 1：機器人是否在線
1. 進入你的 Discord 伺服器
2. 檢查機器人是否顯示綠色點

### 檢查 2：Lavalink 是否連接
1. 進入 Wispbyte Lavalink 服務器查看日誌
2. 尋找類似：`INFO [nodemanager.NodeManager] : Initializing nodemanager...`

### 檢查 3：音樂功能
1. 加入 Discord 語音頻道
2. 輸入: `!play 周杰倫`
3. 機器人應該加入你的語音頻道並播放音樂

---

## 🌐 Wispbyte 中的 Lavalink 連接方式

### 方案 A：同一 Wispbyte 帳戶（推薦）
```
LAVALINK_URL=http://localhost:2333
```

### 方案 B：不同主機名
如果 Lavalink 在不同的 Wispbyte 服務器：
```
LAVALINK_URL=http://lavalink-server-name.wispbyte.app:2333
```

### 方案 C：完整域名
```
LAVALINK_URL=http://your-lavalink-domain.com:2333
```

---

## 🆘 故障排除

### Lavalink 無法啟動
```
檢查事項：
1. Lavalink.jar 是否上傳？
2. application.yml 是否配置正確？
3. 查看 Wispbyte 日誌看具體錯誤
4. 確保 Java 已安裝
```

### 機器人無法連接 Lavalink
```
檢查事項：
1. LAVALINK_URL 是否正確？
2. LAVALINK_PASSWORD 是否匹配？
3. 兩個服務器是否都已啟動？
4. 查看機器人日誌的連接錯誤
```

### 音樂播放失敗
```
檢查事項：
1. 機器人是否有 SEND_MESSAGES 權限？
2. 用戶是否在語音頻道？
3. YouTube 或其他來源是否可訪問？
4. Lavalink 日誌是否有錯誤？
```

### 機器人卡頓
```
解決方案：
1. 檢查 Wispbyte 資源使用情況
2. 增加 Lavalink 記憶體配置
3. 考慮清理播放隊列
```

---

## 💡 額外功能

### 隊列系統
```python
@bot.command(name='queue')
async def queue(ctx):
    """顯示播放隊列"""
    if ctx.voice_client and ctx.voice_client.queue:
        songs = '\n'.join([f"{i+1}. {track.title}" 
                          for i, track in enumerate(ctx.voice_client.queue[:10])])
        await ctx.send(f"📋 隊列:\n{songs}")
    else:
        await ctx.send("📭 隊列為空")
```

### 跳過歌曲
```python
@bot.command(name='skip')
async def skip(ctx):
    """跳過當前歌曲"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        await ctx.voice_client.stop()
        await ctx.send("⏭️ 已跳過歌曲")
    else:
        await ctx.send("❌ 沒有正在播放的歌曲")
```

---

## 📚 資源

- **Wavelink 文檔**: https://wavelink.dev/
- **Lavalink 倉庫**: https://github.com/lavalink-devs/Lavalink
- **Wispbyte**: https://wispbyte.com
- **Discord.py**: https://discordpy.readthedocs.io

---

## 🎉 完成！

現在你有：
- ✅ 24/7 永不斷線的 Discord 機器人
- ✅ 完整的音樂播放功能
- ✅ Lavalink 支持所有主流音樂源
- ✅ 完全免費

祝你部署成功！🚀🎵
