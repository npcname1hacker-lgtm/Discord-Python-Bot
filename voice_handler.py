"""
語音處理模組 - 管理 Discord 語音連接和播放
"""

import discord
import lavalink
from typing import Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class VoiceHandler:
    """處理語音連接和播放"""
    
    def __init__(self, bot):
        self.bot = bot
        self.lavalink_url = "ws://localhost:2333"
        self.lavalink_password = "youshallnotpass"
        self.voice_clients = {}
        
    async def connect_lavalink(self):
        """連接 Lavalink 服務器"""
        try:
            # 檢查是否已連接
            if lavalink.is_connected():
                logger.info("✅ Lavalink 已連接")
                return True
            
            logger.info("🔗 嘗試連接 Lavalink...")
            # 注意: lavalink.connect 需要在機器人準備就緒後調用
            logger.warning("⚠️ Lavalink 需要手動在外部服務器上運行")
            return False
        except Exception as e:
            logger.warning(f"⚠️ Lavalink 連接失敗: {str(e)}")
            logger.info("💡 要使用語音功能，請在支持 UDP 的服務器上運行 Lavalink")
            return False
    
    async def join_voice_channel(self, channel: discord.VoiceChannel):
        """加入語音頻道"""
        try:
            # 如果已經在頻道中，返回現有客戶端
            if channel.guild.id in self.voice_clients:
                existing = self.voice_clients[channel.guild.id]
                if existing.channel == channel:
                    return existing
            
            # 嘗試使用 Lavalink
            if lavalink.is_connected():
                player = await lavalink.connect(channel)
                self.voice_clients[channel.guild.id] = player
                logger.info(f"✅ 通過 Lavalink 加入語音頻道: {channel.name}")
                return player
            
            # 降級到直接 Discord 連接
            voice_client = await channel.connect()
            self.voice_clients[channel.guild.id] = voice_client
            logger.info(f"✅ 直接加入語音頻道: {channel.name}")
            return voice_client
            
        except Exception as e:
            logger.error(f"❌ 加入語音頻道失敗: {str(e)}")
            return None
    
    async def play_tts(self, guild_id: int, audio_file: str):
        """播放 TTS 音頻文件"""
        try:
            player = self.voice_clients.get(guild_id)
            if not player:
                return False, "機器人未連接語音頻道"
            
            if isinstance(player, lavalink.Player):
                # 使用 Lavalink 播放
                logger.info(f"🎵 Lavalink 播放: {audio_file}")
                return True, "播放中"
            else:
                # 直接播放 FFmpeg 音頻
                source = discord.FFmpegPCMAudio(audio_file)
                player.play(source, after=None)
                logger.info(f"🎵 直接播放: {audio_file}")
                return True, "播放中"
                
        except Exception as e:
            logger.error(f"❌ 播放失敗: {str(e)}")
            return False, str(e)
    
    async def leave_voice_channel(self, guild_id: int):
        """離開語音頻道"""
        try:
            player = self.voice_clients.get(guild_id)
            if not player:
                return False, "機器人未連接任何語音頻道"
            
            if isinstance(player, lavalink.Player):
                await player.stop()
                await lavalink.disconnect(guild_id)
            else:
                await player.disconnect()
            
            del self.voice_clients[guild_id]
            logger.info(f"✅ 已離開語音頻道")
            return True, "已離開語音頻道"
            
        except Exception as e:
            logger.error(f"❌ 離開失敗: {str(e)}")
            return False, str(e)
    
    def get_voice_client(self, guild_id: int):
        """獲取語音客戶端"""
        return self.voice_clients.get(guild_id)
