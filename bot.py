"""
Discord Bot - 核心機器人類別
包含機器人的主要功能和事件處理
"""

import discord
from discord.ext import commands
import logging
import os
from config import Config
from commands import setup_commands
from application_system import setup_application_system
from web_models import WelcomeSettings

class DiscordBot:
    def __init__(self):
        """初始化Discord機器人"""
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        self.voice_clients = {}
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        intents.voice_states = True
        intents.members = True
        
        self.bot = commands.Bot(
            command_prefix=self.config.COMMAND_PREFIX,
            intents=intents,
            help_command=None
        )
        
        self.setup_events()
        setup_commands(self.bot)
        setup_application_system(self.bot)
    
    def setup_events(self):
        """設置機器人事件處理器"""
        
        @self.bot.event
        async def on_ready():
            """機器人準備就緒時觸發"""
            self.logger.info(f'機器人 {self.bot.user} 已成功登入!')
            self.logger.info(f'機器人ID: {self.bot.user.id if self.bot.user else "未知"}')
            self.logger.info(f'已連接到 {len(self.bot.guilds)} 個伺服器')
            
            activity = discord.Game(name=self.config.BOT_STATUS)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            
            for guild in self.bot.guilds:
                self.logger.info(f'已連接伺服器: {guild.name} (ID: {guild.id})')
        
        @self.bot.event
        async def on_guild_join(guild):
            """機器人加入新伺服器時觸發"""
            self.logger.info(f'機器人已加入新伺服器: {guild.name} (ID: {guild.id})')
            
            channel = guild.system_channel
            if not channel:
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).send_messages:
                        channel = ch
                        break
            
            if channel:
                embed = discord.Embed(
                    title="👋 Hello! 感謝邀請我到這個伺服器！",
                    description=f"使用 `{self.config.COMMAND_PREFIX}help` 查看可用指令",
                    color=0x00ff00
                )
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    self.logger.warning(f'無法在 {guild.name} 的 {channel.name} 頻道發送歡迎訊息')
        
        @self.bot.event
        async def on_guild_remove(guild):
            """機器人離開伺服器時觸發"""
            self.logger.info(f'機器人已離開伺服器: {guild.name} (ID: {guild.id})')
        
        @self.bot.event
        async def on_member_join(member):
            """新成員加入伺服器時觸發"""
            try:
                from web_models import get_web_database
                web_db = get_web_database()
                
                session = web_db.get_session()
                welcome_settings = session.query(WelcomeSettings).filter_by(
                    guild_id=str(member.guild.id),
                    is_enabled=True
                ).first()
                session.close()
                
                if not welcome_settings:
                    return
                
                if welcome_settings.auto_rename_enabled:
                    try:
                        new_name = f"{welcome_settings.rename_prefix}{member.name}"
                        await member.edit(nick=new_name)
                        self.logger.info(f"已將成員 {member.name} 改名為 {new_name}")
                    except discord.Forbidden:
                        self.logger.warning(f"無法改名成員 {member.name}，權限不足")
                    except Exception as e:
                        self.logger.warning(f"改名失敗: {e}")
                
                try:
                    channel = self.bot.get_channel(int(welcome_settings.channel_id))
                    if channel:
                        message = welcome_settings.message_template.format(
                            username=member.name,
                            servername=member.guild.name
                        )
                        await channel.send(message)
                        self.logger.info(f"已發送歡迎訊息給 {member.name}")
                except Exception as e:
                    self.logger.warning(f"發送歡迎訊息失敗: {e}")
            
            except Exception as e:
                self.logger.error(f"成員加入事件處理失敗: {e}")
        
        @self.bot.event
        async def on_message(message):
            """收到訊息時觸發"""
            if message.author == self.bot.user:
                return
            
            if self.config.DEBUG:
                self.logger.debug(f'收到訊息 - 使用者: {message.author}, 內容: {message.content}')
            
            try:
                from web_app import SENSITIVE_WORDS
                content_lower = message.content.lower()
                for word in SENSITIVE_WORDS:
                    if word in content_lower:
                        await message.delete()
                        await message.author.send(f"⚠️ 訊息包含不允許的詞彙: {word}")
                        return
            except Exception as e:
                self.logger.debug(f'敏感詞過濾錯誤: {e}')
            
            if self.bot.user and self.bot.user.mentioned_in(message) and not message.mention_everyone:
                embed = discord.Embed(
                    title="👋 嗨！我是Discord機器人",
                    description=f"使用 `{self.config.COMMAND_PREFIX}help` 查看我能做什麼！",
                    color=0x0099ff
                )
                await message.channel.send(embed=embed)
            
            await self.bot.process_commands(message)
        
        @self.bot.event
        async def on_command_error(ctx, error):
            """指令錯誤處理"""
            if isinstance(error, commands.CommandNotFound):
                embed = discord.Embed(
                    title="❌ 找不到指令",
                    description=f"指令 `{ctx.invoked_with}` 不存在。使用 `{self.config.COMMAND_PREFIX}help` 查看可用指令。",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
            
            elif isinstance(error, commands.MissingRequiredArgument):
                embed = discord.Embed(
                    title="❌ 缺少必要參數",
                    description=f"指令 `{ctx.command}` 缺少必要參數。使用 `{self.config.COMMAND_PREFIX}help {ctx.command}` 查看用法。",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
            
            elif isinstance(error, commands.MissingPermissions):
                embed = discord.Embed(
                    title="❌ 權限不足",
                    description="您沒有執行此指令的權限。",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
            
            elif isinstance(error, commands.BotMissingPermissions):
                embed = discord.Embed(
                    title="❌ 機器人權限不足",
                    description="機器人沒有執行此操作的權限。",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
            
            else:
                self.logger.error(f'指令錯誤: {error}', exc_info=True)
                embed = discord.Embed(
                    title="❌ 發生錯誤",
                    description="執行指令時發生未預期的錯誤，請稍後再試。",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
        
        @self.bot.event
        async def on_voice_state_update(member, before, after):
            """機器人加入語音頻道時觸發"""
            try:
                if member == self.bot.user and after.channel and not before.channel:
                    self.logger.info(f'機器人已加入語音頻道: {after.channel.name}')
            except Exception as e:
                self.logger.warning(f'語音狀態更新事件出錯: {str(e)}')
    
    async def start_bot(self):
        """啟動機器人"""
        try:
            if not self.config.DISCORD_TOKEN:
                raise ValueError("未設置Discord機器人令牌。請檢查環境變數 DISCORD_TOKEN。")
            
            await self.bot.start(self.config.DISCORD_TOKEN)
        except discord.LoginFailure:
            self.logger.error("Discord登入失敗。請檢查機器人令牌是否正確。")
            raise
        except Exception as e:
            self.logger.error(f"啟動機器人時發生錯誤: {e}")
            raise
        finally:
            if not self.bot.is_closed():
                await self.bot.close()
