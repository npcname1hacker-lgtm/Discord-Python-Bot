"""
語音處理模組 - 管理 Discord 語音連接和播放
"""

import discord
from typing import Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class VoiceHandler:
    """處理語音連接和播放"""
    
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
    
    async def join_voice_channel(self, channel: discord.VoiceChannel):
        """加入語音頻道"""
        try:
            if channel.guild.id in self.voice_clients:
                existing = self.voice_clients[channel.guild.id]
                if existing.channel == channel:
                    return existing
            
            voice_client = await channel.connect()
            self.voice_clients[channel.guild.id] = voice_client
            logger.info(f"✅ 加入語音頻道: {channel.name}")
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
            
            source = discord.FFmpegPCMAudio(audio_file)
            player.play(source, after=None)
            logger.info(f"🎵 播放: {audio_file}")
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
