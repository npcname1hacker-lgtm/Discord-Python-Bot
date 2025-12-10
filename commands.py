"""
Discord Bot - 指令處理模組
包含所有機器人指令的實現
"""

import discord
from discord.ext import commands
import asyncio
import random
import time
import logging
from models import DatabaseManager
from application_system import ApplicationListView

def setup_commands(bot):
    """設置所有機器人指令"""
    
    @bot.command(name='hello', aliases=['hi', '你好'])
    async def hello_command(ctx):
        """打招呼指令"""
        greetings = [
            f"👋 Hello {ctx.author.mention}！",
            f"🎉 嗨！{ctx.author.display_name}",
            f"✨ 哈囉 {ctx.author.mention}！很高興見到你！",
            f"🌟 Hi there, {ctx.author.display_name}！"
        ]
        
        embed = discord.Embed(
            title=random.choice(greetings),
            description="我是一個友善的Discord機器人！ 😊",
            color=0x00ff00
        )
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
    
    @bot.command(name='ping')
    async def ping_command(ctx):
        """檢查機器人延遲"""
        start_time = time.time()
        message = await ctx.send("🏓 Pinging...")
        end_time = time.time()
        
        # 計算延遲
        latency = round(bot.latency * 1000)  # WebSocket延遲
        response_time = round((end_time - start_time) * 1000)  # 回應時間
        
        embed = discord.Embed(title="🏓 Pong!", color=0x00ff00)
        embed.add_field(name="WebSocket延遲", value=f"{latency}ms", inline=True)
        embed.add_field(name="回應時間", value=f"{response_time}ms", inline=True)
        
        # 根據延遲設置顏色
        if latency < 100:
            embed.color = 0x00ff00  # 綠色 - 很好
        elif latency < 200:
            embed.color = 0xffff00  # 黃色 - 普通
        else:
            embed.color = 0xff0000  # 紅色 - 較差
        
        await message.edit(content="", embed=embed)
    
    @bot.command(name='info', aliases=['about', 'botinfo'])
    async def info_command(ctx):
        """顯示機器人資訊"""
        embed = discord.Embed(
            title="🤖 機器人資訊",
            description="一個用Python編寫的Discord機器人",
            color=0x0099ff
        )
        
        # 基本資訊
        embed.add_field(name="機器人名稱", value=bot.user.name, inline=True)
        embed.add_field(name="機器人ID", value=bot.user.id, inline=True)
        embed.add_field(name="伺服器數量", value=len(bot.guilds), inline=True)
        
        # 統計資訊
        total_members = sum(guild.member_count for guild in bot.guilds)
        embed.add_field(name="總用戶數", value=total_members, inline=True)
        embed.add_field(name="頻道數", value=len(list(bot.get_all_channels())), inline=True)
        embed.add_field(name="延遲", value=f"{round(bot.latency * 1000)}ms", inline=True)
        
        # 技術資訊
        embed.add_field(name="Python版本", value="3.8+", inline=True)
        embed.add_field(name="discord.py版本", value=discord.__version__, inline=True)
        embed.add_field(name="指令前綴", value="`!`", inline=True)
        
        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
        embed.set_footer(text=f"請求者: {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await ctx.send(embed=embed)
    
    @bot.command(name='serverinfo', aliases=['server', 'guildinfo'])
    async def serverinfo_command(ctx):
        """顯示伺服器資訊"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"🏰 {guild.name} 伺服器資訊",
            color=0x9932cc
        )
        
        # 基本資訊
        embed.add_field(name="伺服器名稱", value=guild.name, inline=True)
        embed.add_field(name="伺服器ID", value=guild.id, inline=True)
        embed.add_field(name="擁有者", value=guild.owner.mention if guild.owner else "未知", inline=True)
        
        # 統計資訊
        embed.add_field(name="成員數量", value=guild.member_count, inline=True)
        embed.add_field(name="頻道數量", value=len(guild.channels), inline=True)
        embed.add_field(name="角色數量", value=len(guild.roles), inline=True)
        
        # 其他資訊
        embed.add_field(name="創建時間", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="驗證等級", value=str(guild.verification_level).title(), inline=True)
        embed.add_field(name="加速等級", value=guild.premium_tier, inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.set_footer(text=f"請求者: {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await ctx.send(embed=embed)
    
    @bot.command(name='userinfo', aliases=['user', 'member'])
    async def userinfo_command(ctx, member: discord.Member = None):
        """顯示用戶資訊"""
        if member is None:
            member = ctx.author
        
        embed = discord.Embed(
            title=f"👤 {member.display_name} 的資訊",
            color=member.color if member.color != discord.Color.default() else 0x0099ff
        )
        
        # 基本資訊
        embed.add_field(name="用戶名稱", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="顯示名稱", value=member.display_name, inline=True)
        embed.add_field(name="用戶ID", value=member.id, inline=True)
        
        # 時間資訊
        embed.add_field(name="帳號創建", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="加入伺服器", value=member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "未知", inline=True)
        embed.add_field(name="狀態", value=str(member.status).title(), inline=True)
        
        # 角色資訊
        roles = [role.mention for role in member.roles[1:]]  # 排除@everyone角色
        if roles:
            embed.add_field(name=f"角色 ({len(roles)})", value=" ".join(roles), inline=False)
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.set_footer(text=f"請求者: {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await ctx.send(embed=embed)
    
    @bot.command(name='say', aliases=['echo'])
    async def say_command(ctx, *, message):
        """讓機器人說話"""
        # 刪除原始指令訊息
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        
        # 檢查訊息長度
        if len(message) > 2000:
            embed = discord.Embed(
                title="❌ 訊息太長",
                description="訊息不能超過2000個字符。",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        # 發送訊息
        await ctx.send(message)
    
    @bot.command(name='clear', aliases=['purge', 'clean'])
    @commands.has_permissions(manage_messages=True)
    async def clear_command(ctx, amount: int = 5):
        """清除訊息（需要管理訊息權限）"""
        if amount < 1:
            embed = discord.Embed(
                title="❌ 無效數量",
                description="清除數量必須大於0。",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        if amount > 100:
            embed = discord.Embed(
                title="❌ 數量太大",
                description="一次最多只能清除100條訊息。",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 包含指令本身
            
            embed = discord.Embed(
                title="✅ 清除完成",
                description=f"已清除 {len(deleted) - 1} 條訊息。",
                color=0x00ff00
            )
            
            # 發送確認訊息並在3秒後刪除
            confirmation = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await confirmation.delete()
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ 權限不足",
                description="機器人沒有刪除訊息的權限。",
                color=0xff0000
            )
            await ctx.send(embed=embed)
    
    @bot.command(name='help')
    async def help_command(ctx, command_name=None):
        """顯示幫助資訊"""
        if command_name:
            # 顯示特定指令的幫助
            command = bot.get_command(command_name)
            if command:
                embed = discord.Embed(
                    title=f"📖 指令: {command.name}",
                    description=command.help or "沒有描述",
                    color=0x0099ff
                )
                
                # 別名
                if command.aliases:
                    embed.add_field(name="別名", value=", ".join(command.aliases), inline=False)
                
                # 用法
                embed.add_field(name="用法", value=f"`!{command.name} {command.signature}`", inline=False)
                
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ 找不到指令",
                    description=f"指令 `{command_name}` 不存在。",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
        else:
            # 顯示所有指令 - 三個獨立菜單
            
            # ═══════════════════════════════════
            # 菜單 1: 基本指令與資訊
            # ═══════════════════════════════════
            embed1 = discord.Embed(
                title="📚 基本指令與資訊",
                description="系統與伺服器資訊查詢",
                color=0x0099ff
            )
            basic_commands = [
                "`!hello` - 打招呼",
                "`!ping` - 檢查連接延遲",
                "`!info` - 查看機器人資訊",
                "`!serverinfo` - 查看伺服器資訊",
                "`!userinfo [用戶]` - 查看用戶資訊"
            ]
            embed1.add_field(name="📖 指令列表", value="\n".join(basic_commands), inline=False)
            embed1.set_footer(text="菜單 1 / 3 | 使用 !help <指令名稱> 獲取詳細資訊")
            
            # ═══════════════════════════════════
            # 菜單 2: 通用工具
            # ═══════════════════════════════════
            embed2 = discord.Embed(
                title="🔧 通用工具",
                description="文字和訊息管理工具",
                color=0x00cc00
            )
            utility_commands = [
                "`!say <訊息>` - 讓機器人轉發訊息",
                "`!clear [數量]` - 批量清除訊息 (需要權限)"
            ]
            embed2.add_field(name="📖 指令列表", value="\n".join(utility_commands), inline=False)
            embed2.set_footer(text="菜單 2 / 3 | 使用 !help <指令名稱> 獲取詳細資訊")
            
            # ═══════════════════════════════════
            # 菜單 3: 隊長管理工具
            # ═══════════════════════════════════
            embed3 = discord.Embed(
                title="⚔️ 隊長管理工具",
                description="成員管理與申請審核",
                color=0xff6600
            )
            admin_commands = [
                "`!申請` - 查看待審核申請",
                "`!檢查成員` - 檢查未申請的成員",
                "`!要求申請 @成員` - 要求成員補交申請",
                "`!kick <成員> [原因]` - 踢出成員",
                "`!ban <成員> [原因]` - 封鎖成員",
                "`!timeout <成員> [分鐘] [原因]` - 禁言成員",
                "`!untimeout <成員>` - 解除禁言"
            ]
            embed3.add_field(name="📖 指令列表", value="\n".join(admin_commands), inline=False)
            embed3.set_footer(text="菜單 3 / 3 | 使用 !help <指令名稱> 獲取詳細資訊")
            
            await ctx.send(embed=embed1)
            await ctx.send(embed=embed2)
            await ctx.send(embed=embed3)
    
    @bot.command(name='申請', aliases=['applications'])
    @commands.has_permissions(manage_guild=True)
    async def applications_command(ctx):
        """查看所有待審核申請（管理員專用）"""
        db = DatabaseManager()
        applications = db.get_pending_applications()
        
        if not applications:
            embed = discord.Embed(
                title="📋 申請列表",
                description="目前沒有待審核的申請",
                color=0x0099ff
            )
            await ctx.send(embed=embed)
            return
        
        # 創建申請列表視圖
        view = ApplicationListView(applications, db, bot)
        embed = view.create_list_embed()
        
        await ctx.send(embed=embed, view=view)
    
    @bot.command(name='kick', aliases=['踢'])
    @commands.has_permissions(kick_members=True)
    async def kick_command(ctx, member: discord.Member, *, reason="未提供原因"):
        """踢出成員"""
        if member == ctx.author:
            embed = discord.Embed(
                title="❌ 無法執行",
                description="您不能踢出自己",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        if member.top_role >= ctx.author.top_role:
            embed = discord.Embed(
                title="❌ 權限不足",
                description="您無法踢出權限等於或高於您的成員",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # 私信通知被踢者
            try:
                embed_dm = discord.Embed(
                    title="⚠️ 您已被踢出戰隊",
                    description=f"您已被踢出 **{ctx.guild.name}** 戰隊\n\n**原因:** {reason}\n\n如有疑問，請聯繫戰隊管理員",
                    color=0xff0000
                )
                await member.send(embed=embed_dm)
            except:
                pass
            
            # 執行踢出
            await member.kick(reason=reason)
            
            # 確認訊息
            embed = discord.Embed(
                title="✅ 成員已踢出",
                description=f"**被踢出成員:** {member.mention}\n**執行者:** {ctx.author.mention}\n**原因:** {reason}",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ 權限不足",
                description="機器人沒有踢出成員的權限",
                color=0xff0000
            )
            await ctx.send(embed=embed)
    
    @bot.command(name='ban', aliases=['封鎖'])
    @commands.has_permissions(ban_members=True)
    async def ban_command(ctx, member: discord.Member, *, reason="未提供原因"):
        """封鎖成員"""
        if member == ctx.author:
            embed = discord.Embed(
                title="❌ 無法執行",
                description="您不能封鎖自己",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        if member.top_role >= ctx.author.top_role:
            embed = discord.Embed(
                title="❌ 權限不足",
                description="您無法封鎖權限等於或高於您的成員",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # 私信通知被封鎖者
            try:
                embed_dm = discord.Embed(
                    title="🚫 您已被封鎖",
                    description=f"您已被封鎖於 **{ctx.guild.name}** 戰隊\n\n**原因:** {reason}",
                    color=0xff0000
                )
                await member.send(embed=embed_dm)
            except:
                pass
            
            # 執行封鎖
            await member.ban(reason=reason)
            
            # 確認訊息
            embed = discord.Embed(
                title="🚫 成員已封鎖",
                description=f"**被封鎖成員:** {member.mention}\n**執行者:** {ctx.author.mention}\n**原因:** {reason}",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ 權限不足",
                description="機器人沒有封鎖成員的權限",
                color=0xff0000
            )
            await ctx.send(embed=embed)
    
    @bot.command(name='timeout', aliases=['禁言'])
    @commands.has_permissions(moderate_members=True)
    async def timeout_command(ctx, member: discord.Member, minutes: int = 10, *, reason="未提供原因"):
        """禁言成員"""
        if member == ctx.author:
            embed = discord.Embed(
                title="❌ 無法執行",
                description="您不能禁言自己",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        if member.top_role >= ctx.author.top_role:
            embed = discord.Embed(
                title="❌ 權限不足",
                description="您無法禁言權限等於或高於您的成員",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        if minutes <= 0 or minutes > 40320:  # Discord最大禁言時間28天
            embed = discord.Embed(
                title="❌ 無效時間",
                description="禁言時間必須在1-40320分鐘之間（最多28天）",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # 計算禁言結束時間
            from datetime import timedelta
            timeout_until = discord.utils.utcnow() + timedelta(minutes=minutes)
            
            # 執行禁言
            await member.timeout(timeout_until, reason=reason)
            
            # 私信通知被禁言者
            try:
                embed_dm = discord.Embed(
                    title="🔇 您已被禁言",
                    description=f"您在 **{ctx.guild.name}** 戰隊被禁言 {minutes} 分鐘\n\n**原因:** {reason}",
                    color=0xffaa00
                )
                await member.send(embed=embed_dm)
            except:
                pass
            
            # 確認訊息
            embed = discord.Embed(
                title="🔇 成員已禁言",
                description=f"**被禁言成員:** {member.mention}\n**禁言時長:** {minutes} 分鐘\n**執行者:** {ctx.author.mention}\n**原因:** {reason}",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ 權限不足",
                description="機器人沒有禁言成員的權限",
                color=0xff0000
            )
            await ctx.send(embed=embed)
    
    @bot.command(name='untimeout', aliases=['解除禁言'])
    @commands.has_permissions(moderate_members=True)
    async def untimeout_command(ctx, member: discord.Member):
        """解除禁言"""
        try:
            await member.timeout(None)
            
            embed = discord.Embed(
                title="✅ 禁言已解除",
                description=f"**成員:** {member.mention}\n**執行者:** {ctx.author.mention}",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ 權限不足",
                description="機器人沒有解除禁言的權限",
                color=0xff0000
            )
            await ctx.send(embed=embed)
    
    @bot.command(name='檢查成員', aliases=['check_members'])
    @commands.has_permissions(manage_guild=True)
    async def check_members_command(ctx):
        """檢查伺服器中未申請的成員"""
        db = DatabaseManager()
        
        # 獲取所有已申請的用戶ID
        session = db.get_session()
        try:
            approved_users = session.query(TeamApplication).filter_by(status='approved').all()
            approved_user_ids = set(app.user_id for app in approved_users)
        finally:
            session.close()
        
        # 檢查伺服器成員
        unchecked_members = []
        for member in ctx.guild.members:
            if (not member.bot and  # 不是機器人
                str(member.id) not in approved_user_ids and  # 沒有通過申請
                member != ctx.guild.owner):  # 不是伺服器擁有者
                unchecked_members.append(member)
        
        if not unchecked_members:
            embed = discord.Embed(
                title="✅ 檢查完成",
                description="所有成員都已通過申請流程",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
            return
        
        # 顯示未申請的成員
        embed = discord.Embed(
            title="⚠️ 未通過申請的成員",
            description=f"發現 {len(unchecked_members)} 位成員尚未完成申請流程：",
            color=0xffaa00
        )
        
        member_list = []
        for member in unchecked_members[:10]:  # 最多顯示10個
            member_list.append(f"• {member.display_name} ({member.mention})")
        
        embed.add_field(name="成員列表", value="\n".join(member_list), inline=False)
        
        if len(unchecked_members) > 10:
            embed.add_field(name="注意", value=f"還有 {len(unchecked_members) - 10} 位成員未顯示", inline=False)
        
        embed.add_field(name="建議操作", value="使用 `!要求申請 @成員` 要求特定成員補交申請", inline=False)
        
        await ctx.send(embed=embed)
    
    @bot.command(name='要求申請', aliases=['require_application'])
    @commands.has_permissions(manage_guild=True)
    async def require_application_command(ctx, member: discord.Member):
        """要求特定成員補交申請"""
        # 檢查該成員是否已有申請記錄
        db = DatabaseManager()
        session = db.get_session()
        try:
            existing_app = session.query(TeamApplication).filter_by(user_id=str(member.id)).first()
            if existing_app and existing_app.status == 'approved':
                embed = discord.Embed(
                    title="ℹ️ 成員已申請",
                    description=f"{member.display_name} 已經通過申請審核",
                    color=0x0099ff
                )
                await ctx.send(embed=embed)
                return
        finally:
            session.close()
        
        # 發送申請表單給該成員
        from application_system import ApplicationView
        
        embed = discord.Embed(
            title="📋 補交戰隊申請",
            description=f"Hi {member.display_name}！\n\n管理員要求您補交戰隊申請表。為了維護戰隊品質，請完成申請流程：",
            color=0xffaa00
        )
        embed.add_field(
            name="📋 申請流程",
            value="1️⃣ 填寫遊戲ID\n2️⃣ 上傳個人檔案照片（最多5張）\n3️⃣ 等待管理員審核",
            inline=False
        )
        embed.set_footer(text="請儘快完成申請，感謝配合！")
        
        view = ApplicationView(bot)
        
        try:
            await member.send(embed=embed, view=view)
            
            # 確認訊息
            confirm_embed = discord.Embed(
                title="✅ 申請要求已發送",
                description=f"已向 {member.mention} 發送申請表單",
                color=0x00ff00
            )
            await ctx.send(embed=confirm_embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ 無法發送私信",
                description=f"無法向 {member.mention} 發送私信，請手動通知該成員",
                color=0xff0000
            )
            await ctx.send(embed=embed)
