"""
Discord Bot - 戰隊申請系統
處理新成員申請、審核和通知功能
"""

import discord
from discord.ext import commands
import asyncio
import logging
from models import DatabaseManager, TeamApplication
from datetime import datetime

class ApplicationView(discord.ui.View):
    """申請表單視圖"""
    
    def __init__(self, bot):
        super().__init__(timeout=300)  # 5分鐘超時
        self.bot = bot
        self.db = DatabaseManager()
        
    @discord.ui.button(label='📝 填寫申請表', style=discord.ButtonStyle.green)
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """開啟申請表單"""
        modal = ApplicationModal(self.bot, self.db)
        await interaction.response.send_modal(modal)

class ApplicationModal(discord.ui.Modal):
    """申請表單彈窗"""
    
    def __init__(self, bot, db):
        super().__init__(title="🎮 ɢʀᴠ戰隊申請表")
        self.bot = bot
        self.db = db
        
    # 遊戲ID輸入框
    game_id = discord.ui.TextInput(
        label='遊戲ID',
        placeholder='請輸入您的遊戲ID...',
        required=True,
        max_length=100
    )
    
    # 申請說明
    application_text = discord.ui.TextInput(
        label='申請說明',
        placeholder='請簡單介紹您的遊戲經驗和為什麼想加入我們的戰隊...',
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1000
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """提交申請表單"""
        # 創建申請記錄
        app_id = self.db.add_application(
            user_id=str(interaction.user.id),
            username=interaction.user.name,
            display_name=interaction.user.display_name,
            game_id=self.game_id.value,
            avatar_url=interaction.user.avatar.url if interaction.user.avatar else None,
            photos=[],  # 稍後會更新照片
            application_text=self.application_text.value
        )
        
        # 提示用戶上傳照片
        embed = discord.Embed(
            title="✅ 申請表已提交！",
            description=f"申請編號: #{app_id}\n\n📸 **請上傳您的個人檔案和申請照片**\n最多可以上傳5張照片\n\n請在接下來的5分鐘內上傳照片，上傳完成後申請將自動提交給管理員審核。",
            color=0x00ff00
        )
        embed.set_footer(text="照片上傳完成後，您的申請將進入審核流程")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # 等待照片上傳
        await self.wait_for_photos(interaction, app_id)
    
    async def wait_for_photos(self, interaction, app_id):
        """等待用戶上傳照片"""
        photos = []
        
        def check_message(msg):
            return (msg.author.id == interaction.user.id and 
                   msg.channel == interaction.channel and 
                   len(msg.attachments) > 0)
        
        embed = discord.Embed(
            title="📸 照片上傳",
            description="請上傳您的個人檔案和申請照片（最多5張）\n\n上傳方式：直接將圖片拖拽到聊天框或點擊附件按鈕\n\n⏰ 5分鐘內完成上傳",
            color=0x0099ff
        )
        
        upload_msg = await interaction.followup.send(embed=embed, ephemeral=True)
        
        try:
            # 等待最多5張照片，5分鐘超時
            while len(photos) < 5:
                try:
                    message = await self.bot.wait_for('message', check=check_message, timeout=300)
                    
                    for attachment in message.attachments:
                        if attachment.content_type and attachment.content_type.startswith('image/'):
                            photos.append(attachment.url)
                            
                            # 更新進度
                            progress_embed = discord.Embed(
                                title="📸 照片上傳進度",
                                description=f"已上傳 {len(photos)}/5 張照片\n\n{chr(10).join([f'✅ 照片 {i+1}' for i in range(len(photos))])}\n\n繼續上傳或等待5分鐘自動提交申請",
                                color=0x00ff00
                            )
                            await upload_msg.edit(embed=progress_embed)
                            
                            if len(photos) >= 5:
                                break
                    
                    # 刪除用戶上傳的原始消息保持頻道整潔
                    try:
                        await message.delete()
                    except:
                        pass
                        
                except asyncio.TimeoutError:
                    break
        
        except Exception as e:
            logging.error(f"照片上傳過程發生錯誤: {e}")
        
        # 更新申請記錄中的照片
        session = self.db.get_session()
        try:
            application = session.query(TeamApplication).filter_by(id=app_id).first()
            if application:
                application.application_photos = photos
                session.commit()
        finally:
            session.close()
        
        # 通知申請完成
        final_embed = discord.Embed(
            title="🎉 申請提交完成！",
            description=f"申請編號: #{app_id}\n已上傳 {len(photos)} 張照片\n\n您的申請已提交給戰隊管理員審核，請耐心等待審核結果。\n\n審核結果將通過私信通知您。",
            color=0x00ff00
        )
        await upload_msg.edit(embed=final_embed)
        
        # 通知管理員有新申請
        await self.notify_admins(app_id, interaction.user)
    
    async def notify_admins(self, app_id, user):
        """通知管理員有新申請"""
        # 尋找"申請"頻道
        guild = self.bot.guilds[0]  # 假設機器人只在一個伺服器
        application_channel = discord.utils.get(guild.text_channels, name='申請')
        
        if application_channel:
            embed = discord.Embed(
                title="📋 新的戰隊申請",
                description=f"**申請者:** {user.mention}\n**申請編號:** #{app_id}\n**申請時間:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n使用 `!申請` 指令查看和處理申請。",
                color=0xffaa00
            )
            embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
            await application_channel.send(embed=embed)

class ApplicationListView(discord.ui.View):
    """申請列表視圖"""
    
    def __init__(self, applications, db, bot):
        super().__init__(timeout=300)
        self.applications = applications
        self.db = db
        self.bot = bot
        self.current_page = 0
        self.items_per_page = 5
        
        # 添加申請項目按鈕
        self.update_buttons()
    
    def update_buttons(self):
        """更新按鈕列表"""
        self.clear_items()
        
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_applications = self.applications[start_idx:end_idx]
        
        # 為每個申請添加按鈕
        for i, app in enumerate(page_applications):
            button = discord.ui.Button(
                label=f"{app.display_name}",
                style=discord.ButtonStyle.secondary,
                custom_id=f"app_{app.id}",
                row=i // 2
            )
            button.callback = self.create_application_callback(app)
            self.add_item(button)
        
        # 分頁按鈕
        if len(self.applications) > self.items_per_page:
            if self.current_page > 0:
                prev_button = discord.ui.Button(label="◀️ 上一頁", style=discord.ButtonStyle.primary, row=4)
                prev_button.callback = self.prev_page
                self.add_item(prev_button)
            
            if (self.current_page + 1) * self.items_per_page < len(self.applications):
                next_button = discord.ui.Button(label="▶️ 下一頁", style=discord.ButtonStyle.primary, row=4)
                next_button.callback = self.next_page
                self.add_item(next_button)
    
    def create_application_callback(self, application):
        """創建申請按鈕的回調函數"""
        async def callback(interaction):
            view = ApplicationDetailView(application, self.db, self.bot)
            
            embed = discord.Embed(
                title=f"📋 申請詳情 - #{application.id}",
                color=0x0099ff
            )
            embed.add_field(name="👤 申請者", value=f"<@{application.user_id}>", inline=True)
            embed.add_field(name="🎮 遊戲ID", value=application.game_id, inline=True)
            embed.add_field(name="📅 申請時間", value=application.created_at.strftime('%Y-%m-%d %H:%M:%S'), inline=True)
            
            if application.application_text:
                embed.add_field(name="📝 申請說明", value=application.application_text, inline=False)
            
            # 顯示照片數量
            photo_count = len(application.application_photos) if application.application_photos else 0
            embed.add_field(name="📸 照片數量", value=f"{photo_count} 張", inline=True)
            
            if application.avatar_url:
                embed.set_thumbnail(url=application.avatar_url)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        return callback
    
    async def prev_page(self, interaction):
        """上一頁"""
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        embed = self.create_list_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def next_page(self, interaction):
        """下一頁"""
        max_pages = (len(self.applications) - 1) // self.items_per_page
        self.current_page = min(max_pages, self.current_page + 1)
        self.update_buttons()
        embed = self.create_list_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    def create_list_embed(self):
        """創建列表嵌入式訊息"""
        embed = discord.Embed(
            title="📋 戰隊申請列表",
            description=f"共 {len(self.applications)} 份待審核申請",
            color=0x0099ff
        )
        
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_applications = self.applications[start_idx:end_idx]
        
        for app in page_applications:
            embed.add_field(
                name=f"#{app.id} - {app.display_name}",
                value=f"🎮 {app.game_id}\n📅 {app.created_at.strftime('%m-%d %H:%M')}",
                inline=True
            )
        
        if len(self.applications) > self.items_per_page:
            embed.set_footer(text=f"頁面 {self.current_page + 1}/{((len(self.applications) - 1) // self.items_per_page) + 1}")
        
        return embed

class ApplicationDetailView(discord.ui.View):
    """申請詳情和審核視圖"""
    
    def __init__(self, application, db, bot):
        super().__init__(timeout=300)
        self.application = application
        self.db = db
        self.bot = bot
    
    @discord.ui.button(label='🔍 查看照片', style=discord.ButtonStyle.secondary)
    async def view_photos(self, interaction: discord.Interaction, button: discord.ui.Button):
        """查看申請照片"""
        if not self.application.application_photos:
            embed = discord.Embed(
                title="❌ 沒有照片",
                description="此申請未上傳任何照片",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # 創建照片展示
        embeds = []
        for i, photo_url in enumerate(self.application.application_photos):
            embed = discord.Embed(
                title=f"📸 申請照片 {i+1}/{len(self.application.application_photos)}",
                color=0x0099ff
            )
            embed.set_image(url=photo_url)
            embed.set_footer(text=f"申請者: {self.application.display_name}")
            embeds.append(embed)
        
        # 發送第一張照片
        await interaction.response.send_message(embed=embeds[0], ephemeral=True)
        
        # 如果有多張照片，依序發送其他照片
        for embed in embeds[1:]:
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='✅ 接受', style=discord.ButtonStyle.green)
    async def approve_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        """接受申請"""
        # 檢查權限
        if not interaction.user.guild_permissions.manage_guild:
            embed = discord.Embed(
                title="❌ 權限不足",
                description="您沒有審核申請的權限",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # 更新申請狀態
        success = self.db.update_application_status(
            self.application.id, 
            'approved', 
            str(interaction.user.id)
        )
        
        if success:
            # 私信通知申請者
            try:
                user = await self.bot.fetch_user(int(self.application.user_id))
                embed = discord.Embed(
                    title="🎉 恭喜！您的戰隊申請已通過！",
                    description="歡迎加入 ɢʀᴠ 戰隊！\n\n請等待管理員邀請您進入戰隊伺服器。",
                    color=0x00ff00
                )
                await user.send(embed=embed)
            except:
                pass
            
            # 發送歡迎訊息到歡迎頻道
            await self.send_welcome_message(interaction.guild)
            
            # 確認訊息
            embed = discord.Embed(
                title="✅ 申請已接受",
                description=f"已接受 {self.application.display_name} 的申請\n已發送通知給申請者",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='❌ 拒絕', style=discord.ButtonStyle.red)
    async def reject_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        """拒絕申請"""
        # 檢查權限
        if not interaction.user.guild_permissions.manage_guild:
            embed = discord.Embed(
                title="❌ 權限不足",
                description="您沒有審核申請的權限",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # 顯示拒絕原因輸入框
        modal = RejectReasonModal(self.application, self.db, self.bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='🚪 關閉', style=discord.ButtonStyle.secondary)
    async def close_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        """關閉申請詳情"""
        await interaction.response.defer()
        await interaction.delete_original_response()
    
    async def send_welcome_message(self, guild):
        """發送歡迎訊息"""
        welcome_channel = discord.utils.get(guild.text_channels, name='歡迎')
        if welcome_channel:
            try:
                user = await self.bot.fetch_user(int(self.application.user_id))
                embed = discord.Embed(
                    title="🎉 歡迎新戰隊成員！",
                    description=f"歡迎 **{self.application.display_name}** 進入我們的戰隊~\n\n**ɢʀᴠ** 期待你的表演~ 🎮✨",
                    color=0x00ff00
                )
                embed.set_thumbnail(url=self.application.avatar_url)
                embed.add_field(name="🎮 遊戲ID", value=self.application.game_id, inline=True)
                embed.add_field(name="📅 加入時間", value=datetime.now().strftime('%Y-%m-%d'), inline=True)
                
                await welcome_channel.send(embed=embed)
            except Exception as e:
                logging.error(f"發送歡迎訊息失敗: {e}")

class RejectReasonModal(discord.ui.Modal):
    """拒絕原因輸入模態"""
    
    def __init__(self, application, db, bot):
        super().__init__(title="❌ 拒絕申請")
        self.application = application
        self.db = db
        self.bot = bot
    
    reason = discord.ui.TextInput(
        label='拒絕原因',
        placeholder='請輸入拒絕此申請的原因...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """提交拒絕原因"""
        # 更新申請狀態
        success = self.db.update_application_status(
            self.application.id,
            'rejected',
            str(interaction.user.id),
            self.reason.value
        )
        
        if success:
            # 私信通知申請者
            try:
                user = await self.bot.fetch_user(int(self.application.user_id))
                embed = discord.Embed(
                    title="😔 您的戰隊申請未通過審核",
                    description=f"很抱歉，您的申請未能通過審核。\n\n**拒絕原因：**\n{self.reason.value}\n\n歡迎您改善後重新申請！",
                    color=0xff0000
                )
                await user.send(embed=embed)
            except:
                pass
            
            # 確認訊息
            embed = discord.Embed(
                title="❌ 申請已拒絕",
                description=f"已拒絕 {self.application.display_name} 的申請\n已發送通知給申請者",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

def setup_application_system(bot):
    """設置申請系統事件處理"""
    db = DatabaseManager()
    
    @bot.event
    async def on_member_join(member):
        """新成員加入時顯示申請表單"""
        embed = discord.Embed(
            title="🎮 歡迎來到 ɢʀᴠ 戰隊！",
            description="歡迎您對我們戰隊感興趣！\n\n為了維護戰隊品質和團隊氛圍，我們需要所有新成員填寫申請表。\n\n請點擊下方按鈕開始申請流程：",
            color=0x0099ff
        )
        embed.add_field(
            name="📋 申請流程",
            value="1️⃣ 填寫遊戲ID\n2️⃣ 上傳個人檔案照片（最多5張）\n3️⃣ 等待管理員審核\n4️⃣ 接獲審核結果通知",
            inline=False
        )
        embed.set_footer(text="感謝您的理解與配合！")
        
        view = ApplicationView(bot)
        
        try:
            await member.send(embed=embed, view=view)
        except discord.Forbidden:
            # 如果無法私信，嘗試在系統頻道發送
            if member.guild.system_channel:
                await member.guild.system_channel.send(
                    f"{member.mention}, 請查看私信完成申請流程！",
                    embed=embed,
                    view=view
                )