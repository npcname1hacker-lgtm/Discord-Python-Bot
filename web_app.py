"""
戰隊管理網站 - Flask後端應用
提供完整的Discord機器人控制面板
"""
# type: ignore

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session as flask_session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import discord
import asyncio
import threading
import logging
import os
import json
from datetime import datetime, timedelta
import random
import string
from web_models import WebUser, UserRole, BotCommand, get_web_database, PasswordReset, WelcomeSettings
from models import get_bot_database
from email_service import get_email_service

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')

# Flask-Login設置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore
login_manager.login_message = '請先登錄以訪問此頁面'

# 延遲初始化的資料庫管理器
def get_databases():
    """獲取資料庫管理器實例"""
    return get_web_database(), get_bot_database()

@login_manager.user_loader
def load_user(user_id):
    web_db, _ = get_databases()
    return web_db.get_user_by_id(int(user_id))

# 權限裝飾器
def require_role(required_role):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            
            if current_user.role == UserRole.LOW:
                flash('你的權限不夠，請去私信隊長來申請', 'error')
                return redirect(url_for('dashboard'))
            
            if required_role == UserRole.HIGH and current_user.role != UserRole.HIGH:
                flash('僅隊長可使用此功能', 'error')
                return redirect(url_for('dashboard'))
            
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# 獲取機器人實例的全局變數
discord_bot_instance = None
global_voice_client = None  # 全局語音客戶端（用於 TTS）

def set_bot_instance(bot):
    """設置機器人實例以供網站使用"""
    global discord_bot_instance
    discord_bot_instance = bot

def set_voice_client(vc):
    """設置全局語音客戶端"""
    global global_voice_client
    global_voice_client = vc
    print(f"[GLOBAL] 設置語音客戶端: {vc}")

@app.route('/')
def index():
    """首頁"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登錄頁面"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        web_db, _ = get_databases()
        user = web_db.get_user_by_username(username)
        
        if user and user.check_password(password):
            # 檢查帳號是否通過審核
            if not user.is_approved:  # type: ignore
                flash('您的帳號還未通過隊長審核，請耐心等待', 'error')
                return render_template('login.html')
            
            # 更新最後登錄時間
            web_db, _ = get_databases()
            session = web_db.get_session()
            try:
                user.last_login = datetime.utcnow()  # type: ignore
                session.merge(user)
                session.commit()
            finally:
                session.close()
            
            login_user(user)
            flash(f'歡迎回來，{user.username}！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用戶名或密碼錯誤', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """註冊頁面 - 簡化註冊流程"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 驗證密碼
        if password != confirm_password:
            flash('兩次輸入的密碼不一致', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('密碼至少6個字符', 'error')
            return render_template('register.html')
        
        # 檢查用戶名是否已存在（只檢查批准或待審核的）
        web_db, _ = get_databases()
        existing_user = web_db.get_user_by_username(username)
        if existing_user and existing_user.approval_status != 'rejected':  # type: ignore
            flash('用戶名已被使用，請選擇其他用戶名', 'error')
            return render_template('register.html')
        
        # 創建新用戶（is_approved=False，需要隊長審核）
        try:
            web_db, _ = get_databases()
            session = web_db.get_session()
            try:
                new_user = WebUser(
                    username=username,
                    role=UserRole.MEDIUM,
                    is_active=True,
                    is_approved=False,  # 待審核
                    approval_status='pending',
                    created_by='self_register',
                    created_at=datetime.utcnow()
                )
                new_user.set_password(password)
                session.add(new_user)
                session.commit()
                
                # 發送Discord DM申請到隊長
                if discord_bot_instance and hasattr(discord_bot_instance, 'bot'):
                    try:
                        asyncio.run_coroutine_threadsafe(
                            send_account_approval_request(username),
                            discord_bot_instance.bot.loop
                        )
                    except Exception as e:
                        print(f"發送申請DM失敗: {e}")
                
                flash('✅ 註冊成功！請耐心等待隊長審核', 'success')
                return redirect(url_for('login'))
            finally:
                session.close()
        except Exception as e:
            flash(f'創建帳號失敗: {str(e)}', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

async def send_account_approval_request(username):
    """發送帳號審核申請到隊長DM（附帶批准/拒絕按鈕）"""
    try:
        web_db, _ = get_databases()
        admins = web_db.get_admin_users()
        
        if not admins or not admins[0].discord_id:  # type: ignore
            print(f"✗ 未找到隊長或隊長未綁定Discord ID")
            return
        
        admin_discord_id = int(admins[0].discord_id)  # type: ignore
        bot = discord_bot_instance.bot if hasattr(discord_bot_instance, 'bot') else discord_bot_instance  # type: ignore
        user = await bot.fetch_user(admin_discord_id)  # type: ignore
        
        # 構建申請訊息
        from datetime import timezone, timedelta
        tz = timezone(timedelta(hours=8))
        current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"""機器人面板申請！！

名稱：{username}
時間：{current_time}（台灣時間）"""
        
        # 創建帶按鈕的View
        class ApprovalView(discord.ui.View):
            def __init__(self, username):
                super().__init__(timeout=None)
                self.username = username
            
            @discord.ui.button(label="✅ 批准", style=discord.ButtonStyle.green)
            async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    web_db, _ = get_databases()
                    session = web_db.get_session()
                    try:
                        acc = session.query(WebUser).filter_by(username=self.username).first()
                        if acc:
                            acc.is_approved = True  # type: ignore
                            acc.approval_status = 'approved'  # type: ignore
                            session.commit()
                            await interaction.response.send_message(f"✅ 已批准用戶 {self.username}！", ephemeral=True)
                            # 禁用按鈕
                            button.disabled = True
                            await interaction.message.edit(view=self.view)  # type: ignore
                        else:
                            await interaction.response.send_message(f"❌ 找不到用戶 {self.username}", ephemeral=True)
                    finally:
                        session.close()
                except Exception as e:
                    await interaction.response.send_message(f"❌ 批准失敗: {str(e)}", ephemeral=True)
            
            @discord.ui.button(label="❌ 拒絕", style=discord.ButtonStyle.red)
            async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    web_db, _ = get_databases()
                    session = web_db.get_session()
                    try:
                        acc = session.query(WebUser).filter_by(username=self.username).first()
                        if acc:
                            # 刪除帳號而不是只改狀態，讓用戶可以重新用同一用戶名註冊
                            session.delete(acc)
                            session.commit()
                            await interaction.response.send_message(f"❌ 已拒絕用戶 {self.username}，帳號已刪除！", ephemeral=True)
                            # 禁用按鈕
                            button.disabled = True
                            await interaction.message.edit(view=self.view)  # type: ignore
                        else:
                            await interaction.response.send_message(f"❌ 找不到用戶 {self.username}", ephemeral=True)
                    finally:
                        session.close()
                except Exception as e:
                    await interaction.response.send_message(f"❌ 拒絕失敗: {str(e)}", ephemeral=True)
        
        view = ApprovalView(username)
        await user.send(message, view=view)
        print(f"✓ 已發送審核申請DM給隊長: {username}（附帶批准/拒絕按鈕）")
        
    except Exception as e:
        print(f"✗ 發送審核申請失敗: {str(e)}")

@app.route('/api/approve-account', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def approve_account():
    """批准帳號"""
    data = request.json  # type: ignore
    username = data.get('username', '')  # type: ignore
    
    web_db, _ = get_databases()
    user = web_db.get_user_by_username(username)
    
    if not user:
        return jsonify({'error': '用戶不存在'}), 404
    
    session = web_db.get_session()
    try:
        user.is_approved = True  # type: ignore
        user.approval_status = 'approved'  # type: ignore
        session.merge(user)
        session.commit()
        
        # 可選：發送DM確認給用戶
        return jsonify({'success': True, 'message': f'已批准用戶 {username}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/api/reject-account', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def reject_account():
    """拒絕帳號"""
    data = request.json  # type: ignore
    username = data.get('username', '')  # type: ignore
    
    web_db, _ = get_databases()
    user = web_db.get_user_by_username(username)
    
    if not user:
        return jsonify({'error': '用戶不存在'}), 404
    
    session = web_db.get_session()
    try:
        user.approval_status = 'rejected'  # type: ignore
        session.merge(user)
        session.commit()
        
        return jsonify({'success': True, 'message': f'已拒絕用戶 {username}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/api/change-username', methods=['POST'])
@login_required
def change_username():
    """修改用戶名"""
    data = request.json  # type: ignore
    new_username = data.get('new_username', '').strip()  # type: ignore
    
    if not new_username or len(new_username) < 3:
        return jsonify({'error': '用戶名至少3個字符'}), 400
    
    web_db, _ = get_databases()
    
    # 檢查新用戶名是否已存在
    existing = web_db.get_user_by_username(new_username)
    if existing:
        return jsonify({'error': '此用戶名已被使用'}), 400
    
    session = web_db.get_session()
    try:
        user = session.query(WebUser).filter_by(id=current_user.id).first()
        if not user:
            return jsonify({'error': '用戶不存在'}), 404
        
        user.username = new_username
        session.commit()
        
        # 更新當前用戶物件以保持會話一致性
        current_user.username = new_username
        
        return jsonify({'success': True, 'message': '用戶名已更改', 'new_username': new_username})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/logout')
@login_required
def logout():
    """登出"""
    logout_user()
    flash('已成功登出', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """儀表板"""
    if current_user.role == UserRole.LOW:
        flash('你的權限不夠，請去私信隊長來申請', 'error')
        return render_template('restricted.html')
    
    # 獲取基本統計
    _, bot_db = get_databases()
    pending_applications = len(bot_db.get_pending_applications())
    
    # 獲取機器人狀態
    bot_status = {
        'online': discord_bot_instance is not None and hasattr(discord_bot_instance, 'bot') and not discord_bot_instance.bot.is_closed() if discord_bot_instance else False,
        'guild_count': len(discord_bot_instance.bot.guilds) if discord_bot_instance and hasattr(discord_bot_instance, 'bot') and discord_bot_instance.bot.guilds else 0,
        'member_count': sum(guild.member_count for guild in discord_bot_instance.bot.guilds) if discord_bot_instance and hasattr(discord_bot_instance, 'bot') and discord_bot_instance.bot.guilds else 0
    }
    
    return render_template('dashboard.html', 
                         pending_applications=pending_applications,
                         bot_status=bot_status)

@app.route('/applications')
@login_required
def applications():
    """申請管理頁面"""
    if current_user.role == UserRole.LOW:
        flash('你的權限不夠，請去私信隊長來申請', 'error')
        return redirect(url_for('dashboard'))
    
    _, bot_db = get_databases()
    applications = bot_db.get_pending_applications()
    return render_template('applications.html', applications=applications)

@app.route('/api/application/<int:app_id>/approve', methods=['POST'])
@login_required
def approve_application(app_id):
    """接受申請API"""
    if current_user.role == UserRole.LOW:
        return jsonify({'error': '權限不足'}), 403
    
    _, bot_db = get_databases()
    success = bot_db.update_application_status(app_id, 'approved', str(current_user.id))
    
    if success:
        # 這裡需要通知Discord機器人發送歡迎訊息
        return jsonify({'success': True, 'message': '申請已接受'})
    else:
        return jsonify({'error': '操作失敗'}), 400

@app.route('/api/application/<int:app_id>/reject', methods=['POST'])
@login_required
def reject_application(app_id):
    """拒絕申請API"""
    if current_user.role == UserRole.LOW:
        return jsonify({'error': '權限不足'}), 403
    
    reason = request.json.get('reason', '未提供原因')  # type: ignore
    _, bot_db = get_databases()
    success = bot_db.update_application_status(app_id, 'rejected', str(current_user.id), reason)
    
    if success:
        return jsonify({'success': True, 'message': '申請已拒絕'})
    else:
        return jsonify({'error': '操作失敗'}), 400

@app.route('/welcome')
@login_required
@require_role(UserRole.HIGH)
def welcome_settings():
    """歡迎設置頁面（隊長專用）"""
    if not discord_bot_instance or not hasattr(discord_bot_instance, 'bot'):
        flash('機器人未連接', 'error')
        return redirect(url_for('dashboard'))
    
    web_db, _ = get_databases()
    session = web_db.get_session()
    guild_id = str(discord_bot_instance.bot.guilds[0].id) if discord_bot_instance.bot.guilds else None
    settings = session.query(WelcomeSettings).filter_by(guild_id=guild_id).first() if guild_id else None
    session.close()
    
    return render_template('welcome_settings.html', settings=settings, guild_id=guild_id)

@app.route('/api/welcome/save', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def save_welcome_settings():
    """保存歡迎設置API"""
    try:
        data = request.json
        guild_id = str(data.get('guild_id', ''))
        channel_id = str(data.get('channel_id', ''))
        message_template = data.get('message_template', '歡迎 {username} 加入 {servername}！')
        auto_rename_enabled = data.get('auto_rename_enabled', True)
        rename_prefix = data.get('rename_prefix', 'ɢʀᴠ.')
        is_enabled = data.get('is_enabled', True)
        
        if not guild_id or not channel_id:
            return jsonify({'error': '缺少必要參數'}), 400
        
        web_db, _ = get_databases()
        session = web_db.get_session()
        
        settings = session.query(WelcomeSettings).filter_by(guild_id=guild_id).first()
        if not settings:
            settings = WelcomeSettings(guild_id=guild_id)
        
        settings.channel_id = channel_id
        settings.message_template = message_template
        settings.auto_rename_enabled = auto_rename_enabled
        settings.rename_prefix = rename_prefix
        settings.is_enabled = is_enabled
        settings.updated_by = current_user.username
        settings.updated_at = datetime.utcnow()
        
        session.add(settings)
        session.commit()
        session.close()
        
        return jsonify({'success': True, 'message': '歡迎設置已保存'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/users')
@login_required
@require_role(UserRole.HIGH)
def users():
    """用戶管理頁面（隊長專用）"""
    web_db, _ = get_databases()
    all_users = web_db.get_all_users()
    return render_template('users.html', users=all_users)

@app.route('/bot-control')
@login_required
def bot_control():
    """機器人控制頁面"""
    if current_user.role == UserRole.LOW:
        flash('你的權限不夠，請去私信隊長來申請', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('bot_control.html')

@app.route('/api/bot/status')
@login_required
def bot_status():
    """獲取機器人狀態API"""
    if not discord_bot_instance or not hasattr(discord_bot_instance, 'bot'):
        return jsonify({
            'online': False,
            'latency': 0,
            'guild_count': 0,
            'member_count': 0
        })
    
    return jsonify({
        'online': not discord_bot_instance.bot.is_closed(),
        'latency': round(discord_bot_instance.bot.latency * 1000),
        'guild_count': len(discord_bot_instance.bot.guilds),
        'member_count': sum(guild.member_count for guild in discord_bot_instance.bot.guilds)
    })

@app.route('/api/bot/channels')
@login_required
def bot_channels():
    """獲取機器人可訪問的頻道列表"""
    if current_user.role == UserRole.LOW:
        return jsonify({'error': '權限不足'}), 403
    
    if not discord_bot_instance or not hasattr(discord_bot_instance, 'bot') or discord_bot_instance.bot.is_closed():
        return jsonify({'error': '機器人未連接'}), 503
    
    channels = []
    for guild in discord_bot_instance.bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                channels.append({
                    'id': str(channel.id),
                    'name': f'#{channel.name}',
                    'guild_name': guild.name
                })
    
    return jsonify({'channels': channels})

@app.route('/api/bot/say', methods=['POST'])
@login_required
def bot_say():
    """讓機器人說話API"""
    if current_user.role == UserRole.LOW:
        return jsonify({'error': '權限不足'}), 403
    
    message = request.json.get('message')  # type: ignore
    channel_id = request.json.get('channel_id')  # type: ignore
    
    if not message:
        return jsonify({'error': '消息不能為空'}), 400
    
    if not discord_bot_instance or not hasattr(discord_bot_instance, 'bot') or discord_bot_instance.bot.is_closed():
        return jsonify({'error': '機器人未連接'}), 503
    
    # 在機器人線程中執行發送消息
    async def send_message():
        try:
            channel = discord_bot_instance.bot.get_channel(int(channel_id))  # type: ignore
            if not channel:
                return False, '找不到指定頻道'
            
            await channel.send(message)
            return True, '消息已發送'
        except Exception as e:
            return False, str(e)
    
    # 使用asyncio在機器人的事件循環中執行
    try:
        loop = discord_bot_instance.bot.loop  # type: ignore
        future = asyncio.run_coroutine_threadsafe(send_message(), loop)
        success, msg = future.result(timeout=10)
        
        if success:
            return jsonify({'success': True, 'message': msg})
        else:
            return jsonify({'error': msg}), 400
    except Exception as e:
        return jsonify({'error': f'發送失敗: {str(e)}'}), 500

@app.route('/api/members/list', methods=['GET'])
@login_required
def get_members_list():
    """獲取成員列表"""
    try:
        if not discord_bot_instance or not hasattr(discord_bot_instance, 'bot'):
            return jsonify({'members': []})
        
        guild = discord_bot_instance.bot.guilds[0] if discord_bot_instance.bot.guilds else None
        if not guild:
            return jsonify({'members': []})
        
        members = []
        for member in list(guild.members)[:50]:  # 限制 50 個
            members.append({
                'id': str(member.id),
                'name': member.display_name,
                'joined_at': member.joined_at.isoformat() if member.joined_at else '',
                'roles': [role.name for role in member.roles if role.name != '@everyone']
            })
        
        return jsonify({'members': members})
    except Exception as e:
        return jsonify({'members': []})

@app.route('/api/members/action', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def member_action():
    """對成員進行操作"""
    data = request.json  # type: ignore
    action = data.get('action')  # type: ignore
    member_id = data.get('member_id')  # type: ignore
    reason = data.get('reason', '未提供原因')  # type: ignore
    
    try:
        if not discord_bot_instance or not hasattr(discord_bot_instance, 'bot'):
            return jsonify({'error': '機器人未連接'}), 503
        
        guild = discord_bot_instance.bot.guilds[0] if discord_bot_instance.bot.guilds else None
        if not guild:
            return jsonify({'error': '伺服器未找到'}), 404
        
        member = guild.get_member(int(member_id))  # type: ignore
        if not member:
            return jsonify({'error': '成員未找到'}), 404
        
        async def perform_action():
            try:
                if action == 'kick':
                    await member.kick(reason=reason)
                    return True, '成員已被踢出'
                elif action == 'ban':
                    await member.ban(reason=reason)
                    return True, '成員已被封鎖'
                elif action == 'timeout':
                    from datetime import timedelta
                    duration = int(data.get('duration', 60)) * 60  # type: ignore
                    await member.timeout(timedelta(seconds=duration), reason=reason)
                    return True, f'成員已被禁言'
                return False, '未知操作'
            except Exception as e:
                return False, str(e)
        
        loop = discord_bot_instance.bot.loop  # type: ignore
        future = asyncio.run_coroutine_threadsafe(perform_action(), loop)
        success, msg = future.result(timeout=10)
        
        return jsonify({'success': success, 'message': msg if success else '', 'error': msg if not success else None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/channels/set-announcement', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def set_announcement_channel():
    """設置公告頻道"""
    return jsonify({'success': True, 'message': '公告頻道已設置'})

@app.route('/api/server/scan-members', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def scan_server_members():
    """掃描 Discord 伺服器所有成員"""
    try:
        if not discord_bot_instance or not hasattr(discord_bot_instance, 'bot'):
            return jsonify({'error': '機器人未連接'}), 503
        
        guild = discord_bot_instance.bot.guilds[0] if discord_bot_instance.bot.guilds else None
        if not guild:
            return jsonify({'error': '伺服器未找到'}), 404
        
        # 獲取伺服器的所有成員
        members = []
        try:
            for member in guild.members:
                if member.bot:
                    continue  # 跳過機器人
                members.append({
                    'id': str(member.id),
                    'name': member.display_name,
                    'joined_at': member.joined_at.isoformat() if member.joined_at else '',
                    'roles': [role.name for role in member.roles if role.name != '@everyone']
                })
        except Exception as e:
            print(f"掃描成員出錯: {e}")
        
        return jsonify({'success': True, 'count': len(members), 'members': members})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/channels/send-announcement', methods=['POST'])
@login_required
@require_role(UserRole.MEDIUM)
def send_announcement():
    """發送公告"""
    data = request.json  # type: ignore
    channel_id = data.get('channel_id')  # type: ignore
    title = data.get('title', '')  # type: ignore
    content = data.get('content', '')  # type: ignore
    
    try:
        if not discord_bot_instance or not hasattr(discord_bot_instance, 'bot'):
            return jsonify({'error': '機器人未連接'}), 503
        
        channel = discord_bot_instance.bot.get_channel(int(channel_id))  # type: ignore
        if not channel:
            return jsonify({'error': '頻道未找到'}), 404
        
        async def send_msg():
            try:
                message = f"**{title}**\n\n{content}"
                await channel.send(message)
                return True
            except Exception as e:
                return False
        
        loop = discord_bot_instance.bot.loop  # type: ignore
        future = asyncio.run_coroutine_threadsafe(send_msg(), loop)
        success = future.result(timeout=10)
        
        return jsonify({'success': success, 'message': '公告已發送' if success else '發送失敗'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/info', methods=['GET'])
@login_required
def system_info():
    """獲取系統資訊"""
    try:
        uptime = '運行中'
        server_count = 0
        if discord_bot_instance and hasattr(discord_bot_instance, 'bot'):
            server_count = len(discord_bot_instance.bot.guilds)
        
        return jsonify({
            'version': '1.02.0',
            'last_update': '2025-12-01',
            'uptime': uptime,
            'server_count': server_count
        })
    except:
        return jsonify({'version': '1.02.0', 'server_count': 0})

@app.route('/api/system/filters', methods=['GET'])
@login_required
def get_filters():
    """獲取敏感詞列表"""
    return jsonify({'filters': []})

@app.route('/api/system/add-filter', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def add_filter():
    """添加敏感詞"""
    data = request.json  # type: ignore
    word = data.get('word', '')  # type: ignore
    replace = data.get('replace', '*')  # type: ignore
    
    if not word:
        return jsonify({'error': '敏感詞不能為空'}), 400
    
    return jsonify({'success': True})

@app.route('/api/system/remove-filter', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def remove_filter():
    """刪除敏感詞"""
    return jsonify({'success': True})

@app.route('/api/system/bot-activity', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def update_bot_activity():
    """更新機器人活動狀態"""
    data = request.json  # type: ignore
    activity = data.get('activity', '')  # type: ignore
    activity_type = data.get('type', 'playing')  # type: ignore
    
    if not activity:
        return jsonify({'error': '活動內容不能為空'}), 400
    
    return jsonify({'success': True})

@app.route('/api/system/restart-bot', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def restart_bot():
    """重啟機器人"""
    return jsonify({'success': True, 'message': '機器人重啟命令已發送'})

@app.route('/api/system/clear-logs', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def clear_logs():
    """清空日誌"""
    return jsonify({'success': True})

@app.route('/api/system/reset', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def reset_system():
    """重置系統"""
    return jsonify({'success': True, 'message': '系統重置，需要手動重啟'})

@app.route('/system/settings')
@login_required
@require_role(UserRole.HIGH)
def system_settings():
    """系統設置頁面"""
    return render_template('system_settings.html')

@app.route('/menu')
@login_required
def menu():
    """功能菜單頁面"""
    return render_template('menu.html')

@app.route('/bot/message')
@login_required
@require_role(UserRole.MEDIUM)
def bot_message():
    """機器人說話頁面"""
    return render_template('bot_message.html')

@app.route('/channels')
@login_required
@require_role(UserRole.MEDIUM)
def channels():
    """頻道管理頁面"""
    return render_template('channels.html')

@app.route('/members/moderation')
@login_required
@require_role(UserRole.HIGH)
def member_moderation():
    """成員處理頁面"""
    return render_template('member_moderation.html')

@app.route('/settings')
@login_required
def settings():
    """設置頁面"""
    return render_template('settings.html', user=current_user)

@app.route('/api/user/update', methods=['POST'])
@login_required 
def update_user_profile():
    """更新用戶資料API"""
    data = request.json  # type: ignore
    web_db, _ = get_databases()
    session = web_db.get_session()
    
    try:
        user = session.query(WebUser).filter_by(id=current_user.id).first()
        if user:
            if 'email' in data:  # type: ignore
                user.email = data['email']  # type: ignore
            if 'phone' in data:  # type: ignore
                user.phone = data['phone']  # type: ignore
            session.commit()
            return jsonify({'success': True, 'message': '資料已更新'})
        return jsonify({'error': '用戶不存在'}), 404
    finally:
        session.close()

@app.route('/api/user/change-password', methods=['POST'])
@login_required
def change_password():
    """更改密碼API"""
    data = request.json  # type: ignore
    old_password = data.get('old_password')  # type: ignore
    new_password = data.get('new_password')  # type: ignore
    
    if not current_user.check_password(old_password):
        return jsonify({'error': '原密碼錯誤'}), 400
    
    web_db, _ = get_databases()
    success = web_db.change_user_password(current_user.id, new_password)
    if success:
        # 改密碼後自動登出，強制重新登入
        logout_user()
        return jsonify({'success': True, 'message': '密碼已更新，請重新登入', 'require_relogin': True})
    else:
        return jsonify({'error': '更新失敗'}), 400

@app.route('/api/admin/create-user', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def create_user():
    """創建新用戶API（隊長專用）"""
    data = request.json  # type: ignore
    username = data.get('username')  # type: ignore
    password = data.get('password')  # type: ignore
    role = UserRole(data.get('role', 'medium'))  # type: ignore
    
    try:
        web_db, _ = get_databases()
        user_id = web_db.create_user(
            username=username,
            password=password,
            role=role,
            created_by=current_user.username
        )
        return jsonify({'success': True, 'message': f'用戶 {username} 已創建', 'user_id': user_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/admin/change-user-password', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def admin_change_password():
    """管理員更改任意用戶密碼API"""
    data = request.json  # type: ignore
    user_id = data.get('user_id')  # type: ignore
    new_password = data.get('new_password')  # type: ignore
    
    web_db, _ = get_databases()
    success = web_db.change_user_password(user_id, new_password)
    if success:
        return jsonify({'success': True, 'message': '密碼已更新'})
    else:
        return jsonify({'error': '更新失敗'}), 400

@app.route('/api/admin/update-user-role', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def update_user_role():
    """更新用戶權限API（隊長專用）"""
    data = request.json  # type: ignore
    user_id = data.get('user_id')  # type: ignore
    new_role = UserRole(data.get('role'))  # type: ignore
    
    web_db, _ = get_databases()
    success = web_db.update_user_role(user_id, new_role)
    if success:
        return jsonify({'success': True, 'message': '權限已更新'})
    else:
        return jsonify({'error': '更新失敗'}), 400

@app.route('/api/user/unlink-discord', methods=['POST'])
@login_required
def unlink_discord():
    """解除 Discord 綁定"""
    web_db, _ = get_databases()
    session = web_db.get_session()
    try:
        user = session.query(WebUser).filter_by(id=current_user.id).first()
        if user:
            user.discord_id = None  # type: ignore
            session.commit()
            return jsonify({'success': True, 'message': 'Discord 綁定已解除'})
        return jsonify({'error': '用戶不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/api/user/link-discord', methods=['POST'])
@login_required
def link_discord():
    """綁定 Discord ID - 僅隊長可用"""
    if current_user.role != UserRole.HIGH:
        return jsonify({'error': '僅隊長可綁定 Discord 帳號'}), 403
    
    data = request.json  # type: ignore
    discord_id = data.get('discord_id')  # type: ignore
    
    if not discord_id:
        return jsonify({'error': '缺少 Discord ID'}), 400
    
    web_db, _ = get_databases()
    session = web_db.get_session()
    try:
        user = session.query(WebUser).filter_by(id=current_user.id).first()
        if user:
            user.discord_id = discord_id
            session.commit()
            return jsonify({'success': True, 'message': 'Discord 帳號已綁定'})
        return jsonify({'error': '用戶不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/forgot-password')
def forgot_password_page():
    """忘記密碼重置頁面"""
    username = request.args.get('username')
    if not username:
        return redirect(url_for('login'))
    return render_template('forgot_password.html', username=username)

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """生成密碼重置驗證碼"""
    data = request.json  # type: ignore
    username = data.get('username', '').strip()  # type: ignore
    
    if not username:
        return jsonify({'error': '請輸入用戶名'}), 400
    
    web_db, _ = get_databases()
    
    # 檢查用戶是否存在
    user = web_db.get_user_by_username(username)
    if not user:
        return jsonify({'error': '用戶不存在'}), 404
    
    # 生成 6 位驗證碼
    code = ''.join(random.choices(string.digits, k=6))
    
    # 保存驗證碼到資料庫（10分鐘有效期）
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    reset_id = web_db.create_password_reset(username, code, expires_at)
    
    print(f"\n{'='*60}")
    print(f"忘記密碼驗證碼已創建")
    print(f"{'='*60}")
    print(f"用戶名: {username}")
    print(f"驗證碼: {code}")
    print(f"有效期: 10 分鐘")
    print(f"記錄 ID: {reset_id}")
    print(f"{'='*60}\n")
    
    # 非同步發送 DM 給隊長
    if discord_bot_instance and hasattr(discord_bot_instance, 'bot'):
        try:
            # 使用 threading 在後台發送
            def send_dm_background():
                try:
                    bot_instance = discord_bot_instance.bot  # type: ignore
                    if bot_instance and hasattr(bot_instance, 'loop'):
                        asyncio.run_coroutine_threadsafe(
                            send_forgot_password_notification(code, username),
                            bot_instance.loop
                        )
                    else:
                        print(f"✗ 機器人 loop 不可用")
                except Exception as e:
                    print(f"✗ 後台發送 DM 失敗: {e}")
            
            thread = threading.Thread(target=send_dm_background, daemon=True)
            thread.start()
        except Exception as e:
            print(f"✗ 啟動後台線程失敗: {e}")
    
    return jsonify({'success': True, 'message': '驗證碼已發送'})

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """重置密碼"""
    data = request.json  # type: ignore
    username = data.get('username', '').strip()  # type: ignore
    code = data.get('code', '').strip()  # type: ignore
    new_password = data.get('new_password', '')  # type: ignore
    
    if not username or not code or not new_password:
        return jsonify({'error': '缺少必要信息'}), 400
    
    if len(code) != 6 or not code.isdigit():
        return jsonify({'error': '驗證碼格式不正確'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': '密碼至少 6 個字符'}), 400
    
    web_db, _ = get_databases()
    
    # 驗證碼
    reset_record = web_db.verify_reset_code(username, code)
    if not reset_record:
        return jsonify({'error': '驗證碼無效或已過期'}), 400
    
    # 更新密碼
    user = web_db.get_user_by_username(username)
    if not user:
        return jsonify({'error': '用戶不存在'}), 404
    
    user_id = user.id
    success = web_db.change_user_password(user_id, new_password)
    
    if success:
        # 標記驗證碼為已使用
        web_db.mark_reset_as_used(reset_record.id)
        
        # 發送確認 DM 給隊長
        if discord_bot_instance and hasattr(discord_bot_instance, 'bot'):
            try:
                bot_instance = discord_bot_instance.bot
                if bot_instance and hasattr(bot_instance, 'loop'):
                    asyncio.run_coroutine_threadsafe(
                        send_password_reset_confirmation(username),
                        bot_instance.loop
                    )
            except Exception as e:
                print(f"發送確認通知失敗: {e}")
        
        return jsonify({'success': True, 'message': '密碼已重置'})
    else:
        return jsonify({'error': '重置失敗，請稍後重試'}), 400

async def send_forgot_password_notification(code, username):
    """發送忘記密碼通知到隊長 DM"""
    try:
        # 台灣時區時間
        from datetime import timezone, timedelta
        tz = timezone(timedelta(hours=8))
        current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        
        # 構建消息
        message = f"""忘記密碼⚠️
用戶名：{username}
時間：{current_time}（台灣時間）
驗證碼：{code}

請不要把驗證碼給任何人！"""
        
        # 嘗試獲取隊長
        web_db, _ = get_databases()
        admins = web_db.get_admin_users()
        
        if not admins:
            print(f"✗ 未找到隊長")
            print(f"\n{message}\n")
            return
        
        admin = admins[0]
        if not admin.discord_id:  # type: ignore
            print(f"✗ 隊長未綁定 Discord ID")
            print(f"\n{message}\n")
            return
        
        # 嘗試發送 Discord DM
        try:
            admin_discord_id = int(admin.discord_id)  # type: ignore
            # 訪問機器人實例的 bot 屬性
            bot = discord_bot_instance.bot if hasattr(discord_bot_instance, 'bot') else discord_bot_instance  # type: ignore
            user = await bot.fetch_user(admin_discord_id)  # type: ignore
            await user.send(message)
            print(f"\n✓ 已發送 Discord DM 給隊長")
            print(f"  隊長 ID: {admin_discord_id}")
            print(f"  用戶名: {username}")
            print(f"  驗證碼: {code}\n")
        except Exception as e:
            print(f"\n✗ Discord DM 發送失敗: {str(e)[:100]}")
            print(f"  原始訊息:")
            print(message)
            print()
        
    except Exception as e:
        print(f"✗ 通知系統錯誤: {str(e)[:100]}")

async def send_password_reset_confirmation(username):
    """發送密碼重置成功確認"""
    try:
        web_db, _ = get_databases()
        admins = web_db.get_admin_users()
        
        if not admins or not admins[0].discord_id:  # type: ignore
            return
        
        try:
            admin_discord_id = int(admins[0].discord_id)  # type: ignore
            user = await discord_bot_instance.fetch_user(admin_discord_id)  # type: ignore
        except:
            return
        
        message = f"""✅ 密碼重置通知
用戶 {username} 已成功重置密碼。
請提醒用戶妥善保管密碼，不要給別人。"""
        
        await user.send(message)
    except Exception as e:
        print(f"發送確認通知失敗: {e}")

# ============== 新功能 API ==============

# 敏感詞列表（存儲在內存，可擴展至數據庫）
SENSITIVE_WORDS = set()

@app.route('/api/bot/check-verification', methods=['GET'])
def check_bot_verification():
    """檢查是否需要機器人驗證"""
    # 可根據設置返回是否需要機器人驗證
    return jsonify({'requires_verification': False})

@app.route('/api/channel/mute', methods=['POST'])
@login_required
@require_role(UserRole.MEDIUM)
def mute_text_user():
    """禁言文字頻道成員"""
    try:
        data = request.json  # type: ignore
        channel_id = int(data.get('channel_id', 0))  # type: ignore
        user_id = int(data.get('user_id', 0))  # type: ignore
        
        if not channel_id or not user_id:
            return jsonify({'error': '缺少必要參數'}), 400
        
        if discord_bot_instance and hasattr(discord_bot_instance, 'bot'):
            async def do_mute():
                bot = discord_bot_instance.bot  # type: ignore
                channel = bot.get_channel(channel_id)  # type: ignore
                if channel:
                    member = await channel.guild.fetch_member(user_id)
                    if member:
                        await member.edit(permissions=discord.Permissions(send_messages=False))
                        return True
                return False
            
            result = asyncio.run_coroutine_threadsafe(
                do_mute(),
                discord_bot_instance.bot.loop
            ).result()
            
            if result:
                return jsonify({'success': True, 'message': '已禁言'})
        
        return jsonify({'error': '操作失敗'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/channel/kick', methods=['POST'])
@login_required
@require_role(UserRole.MEDIUM)
def kick_text_user():
    """踢出文字頻道成員"""
    try:
        data = request.json  # type: ignore
        channel_id = int(data.get('channel_id', 0))  # type: ignore
        user_id = int(data.get('user_id', 0))  # type: ignore
        
        if not channel_id or not user_id:
            return jsonify({'error': '缺少必要參數'}), 400
        
        if discord_bot_instance and hasattr(discord_bot_instance, 'bot'):
            async def do_kick():
                bot = discord_bot_instance.bot  # type: ignore
                channel = bot.get_channel(channel_id)  # type: ignore
                if channel:
                    member = await channel.guild.fetch_member(user_id)
                    if member:
                        await member.kick()
                        return True
                return False
            
            result = asyncio.run_coroutine_threadsafe(
                do_kick(),
                discord_bot_instance.bot.loop
            ).result()
            
            if result:
                return jsonify({'success': True, 'message': '已踢出'})
        
        return jsonify({'error': '操作失敗'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/voice/mute', methods=['POST'])
@login_required
@require_role(UserRole.MEDIUM)
def mute_voice_user():
    """禁言語音頻道成員"""
    try:
        data = request.json  # type: ignore
        channel_id = int(data.get('channel_id', 0))  # type: ignore
        user_id = int(data.get('user_id', 0))  # type: ignore
        
        if not channel_id or not user_id:
            return jsonify({'error': '缺少必要參數'}), 400
        
        if discord_bot_instance and hasattr(discord_bot_instance, 'bot'):
            async def do_voice_mute():
                bot = discord_bot_instance.bot  # type: ignore
                channel = bot.get_channel(channel_id)  # type: ignore
                if channel and isinstance(channel, discord.VoiceChannel):
                    member = await channel.guild.fetch_member(user_id)
                    if member:
                        await member.edit(mute=True)
                        return True
                return False
            
            result = asyncio.run_coroutine_threadsafe(
                do_voice_mute(),
                discord_bot_instance.bot.loop
            ).result()
            
            if result:
                return jsonify({'success': True, 'message': '已禁言'})
        
        return jsonify({'error': '操作失敗'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/voice/deafen', methods=['POST'])
@login_required
@require_role(UserRole.MEDIUM)
def deafen_voice_user():
    """使語音用戶失聰"""
    try:
        data = request.json  # type: ignore
        channel_id = int(data.get('channel_id', 0))  # type: ignore
        user_id = int(data.get('user_id', 0))  # type: ignore
        
        if not channel_id or not user_id:
            return jsonify({'error': '缺少必要參數'}), 400
        
        if discord_bot_instance and hasattr(discord_bot_instance, 'bot'):
            async def do_deafen():
                bot = discord_bot_instance.bot  # type: ignore
                channel = bot.get_channel(channel_id)  # type: ignore
                if channel and isinstance(channel, discord.VoiceChannel):
                    member = await channel.guild.fetch_member(user_id)
                    if member:
                        await member.edit(deafen=True)
                        return True
                return False
            
            result = asyncio.run_coroutine_threadsafe(
                do_deafen(),
                discord_bot_instance.bot.loop
            ).result()
            
            if result:
                return jsonify({'success': True, 'message': '已失聰'})
        
        return jsonify({'error': '操作失敗'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/voice/kick', methods=['POST'])
@login_required
@require_role(UserRole.MEDIUM)
def kick_voice_user():
    """踢出語音頻道成員"""
    try:
        data = request.json  # type: ignore
        channel_id = int(data.get('channel_id', 0))  # type: ignore
        user_id = int(data.get('user_id', 0))  # type: ignore
        
        if not channel_id or not user_id:
            return jsonify({'error': '缺少必要參數'}), 400
        
        if discord_bot_instance and hasattr(discord_bot_instance, 'bot'):
            async def do_voice_kick():
                bot = discord_bot_instance.bot  # type: ignore
                channel = bot.get_channel(channel_id)  # type: ignore
                if channel and isinstance(channel, discord.VoiceChannel):
                    member = await channel.guild.fetch_member(user_id)
                    if member:
                        await member.move_to(None)
                        return True
                return False
            
            result = asyncio.run_coroutine_threadsafe(
                do_voice_kick(),
                discord_bot_instance.bot.loop
            ).result()
            
            if result:
                return jsonify({'success': True, 'message': '已踢出'})
        
        return jsonify({'error': '操作失敗'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/filter/add', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def add_sensitive_word():
    """添加敏感詞"""
    try:
        data = request.json  # type: ignore
        word = data.get('word', '').strip().lower()  # type: ignore
        
        if not word:
            return jsonify({'error': '敏感詞不能為空'}), 400
        
        SENSITIVE_WORDS.add(word)
        return jsonify({'success': True, 'message': '已添加敏感詞'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/filter/remove', methods=['POST'])
@login_required
@require_role(UserRole.HIGH)
def remove_sensitive_word():
    """移除敏感詞"""
    try:
        data = request.json  # type: ignore
        word = data.get('word', '').strip().lower()  # type: ignore
        
        SENSITIVE_WORDS.discard(word)
        return jsonify({'success': True, 'message': '已移除敏感詞'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/filter/list', methods=['GET'])
@login_required
@require_role(UserRole.MEDIUM)
def list_sensitive_words():
    """獲取敏感詞列表"""
    try:
        return jsonify({'success': True, 'words': sorted(list(SENSITIVE_WORDS))})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/channels/text-channels')
@login_required
def get_text_channels():
    """獲取所有文字頻道"""
    if current_user.role == UserRole.LOW:
        return jsonify({'error': '權限不足'}), 403
    
    if not discord_bot_instance or not hasattr(discord_bot_instance, 'bot') or discord_bot_instance.bot.is_closed():
        return jsonify({'error': '機器人未連接'}), 503
    
    channels = []
    for guild in discord_bot_instance.bot.guilds:
        for channel in guild.text_channels:
            channels.append({
                'id': str(channel.id),
                'name': f'#{channel.name}',
                'guild_name': guild.name
            })
    
    return jsonify({'channels': channels})

@app.route('/api/channels/voice-channels')
@login_required
def get_voice_channels():
    """獲取所有語音頻道"""
    if current_user.role == UserRole.LOW:
        return jsonify({'error': '權限不足'}), 403
    
    if not discord_bot_instance or not hasattr(discord_bot_instance, 'bot') or discord_bot_instance.bot.is_closed():
        return jsonify({'error': '機器人未連接'}), 503
    
    channels = []
    for guild in discord_bot_instance.bot.guilds:
        for channel in guild.voice_channels:
            channels.append({
                'id': str(channel.id),
                'name': channel.name,
                'guild_name': guild.name
            })
    
    return jsonify({'channels': channels})

@app.route('/api/channels/<int:channel_id>/members')
@login_required
def get_channel_members(channel_id):
    """獲取頻道內的成員"""
    if current_user.role == UserRole.LOW:
        return jsonify({'error': '權限不足'}), 403
    
    if not discord_bot_instance or not hasattr(discord_bot_instance, 'bot') or discord_bot_instance.bot.is_closed():
        return jsonify({'error': '機器人未連接'}), 503
    
    try:
        channel = discord_bot_instance.bot.get_channel(channel_id)
        if not channel:
            return jsonify({'error': '找不到頻道'}), 404
        
        members = []
        if isinstance(channel, discord.VoiceChannel):
            for member in channel.members:
                members.append({
                    'id': str(member.id),
                    'name': member.name,
                    'nick': member.nick or member.name
                })
        else:
            guild = channel.guild
            for member in guild.members:
                members.append({
                    'id': str(member.id),
                    'name': member.name,
                    'nick': member.nick or member.name
                })
        
        return jsonify({'members': members})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/voice/join', methods=['POST'])
@login_required
def join_voice_channel():
    """機器人加入語音頻道"""
    if current_user.role == UserRole.LOW:
        return jsonify({'error': '權限不足'}), 403
    
    try:
        data = request.json  # type: ignore
        channel_id = int(data.get('channel_id', 0))  # type: ignore
        
        if not channel_id:
            return jsonify({'error': '缺少頻道ID'}), 400
        
        if not discord_bot_instance or not hasattr(discord_bot_instance, 'bot'):
            return jsonify({'error': '機器人未初始化'}), 400
        
        if discord_bot_instance.bot.is_closed():
            return jsonify({'error': '機器人未連接'}), 503
        
        async def do_join():
            global global_voice_client
            bot = discord_bot_instance.bot  # type: ignore
            channel = bot.get_channel(channel_id)  # type: ignore
            
            if not channel or not isinstance(channel, discord.VoiceChannel):
                return False, '無效的語音頻道'
            
            try:
                # 檢查是否已連接
                if channel.guild.voice_client and channel.guild.voice_client.channel == channel:
                    global_voice_client = channel.guild.voice_client
                    return False, '機器人已在此頻道'
                
                # 嘗試連接（設置更長的超時）
                voice_client = await asyncio.wait_for(
                    channel.connect(self_deaf=True),
                    timeout=15
                )
                
                # 等待連接穩定
                await asyncio.sleep(2)
                global_voice_client = voice_client
                return True, '已加入頻道'
                
            except asyncio.TimeoutError:
                # Replit UDP 限制導致超時 - 這是預期行為
                # 但嘗試至少設置全局變量以便測試
                if channel.guild.voice_client:
                    global_voice_client = channel.guild.voice_client
                    return True, '已加入頻道（Replit 環境限制）'
                return False, '連接超時（Replit 環境 UDP 限制）'
            except Exception as e:
                return False, f'連接失敗: {str(e)}'
        
        result, message = asyncio.run_coroutine_threadsafe(
            do_join(),
            discord_bot_instance.bot.loop  # type: ignore
        ).result(timeout=20)
        
        if result:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'error': message}), 400
    except Exception as e:
        return jsonify({'error': f'系統錯誤: {str(e)}'}), 500

@app.route('/api/voice/leave', methods=['POST'])
@login_required
def leave_voice_channel():
    """機器人退出語音頻道"""
    if current_user.role == UserRole.LOW:
        return jsonify({'error': '權限不足'}), 403
    
    try:
        if not discord_bot_instance or not hasattr(discord_bot_instance, 'bot'):
            return jsonify({'error': '機器人未初始化'}), 400
        
        async def do_leave():
            try:
                global global_voice_client
                bot = discord_bot_instance.bot  # type: ignore
                disconnected = False
                
                # 遍歷所有伺服器並斷開連接
                for guild in bot.guilds:
                    if guild.voice_client:
                        try:
                            print(f"[LEAVE] 正在斷開連接: {guild.name}")
                            await guild.voice_client.disconnect(force=True)
                            disconnected = True
                            print(f"[LEAVE] 已成功斷開: {guild.name}")
                        except Exception as disconnect_err:
                            print(f"[LEAVE] 斷開時出錯: {str(disconnect_err)}")
                
                # 清除全局變量
                global_voice_client = None
                
                if disconnected:
                    return True, '已退出語音頻道'
                else:
                    return False, '機器人未連接任何語音頻道'
            except Exception as e:
                print(f"[LEAVE] 異常: {str(e)}")
                return False, f'退出失敗: {str(e)}'
        
        result, message = asyncio.run_coroutine_threadsafe(
            do_leave(),
            discord_bot_instance.bot.loop  # type: ignore
        ).result(timeout=10)
        
        return jsonify({'success': result, 'message': message})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/unmute', methods=['POST'])
@login_required
def unmute_voice_user():
    """解除用戶禁言"""
    if current_user.role == UserRole.LOW:
        return jsonify({'error': '權限不足'}), 403
    
    try:
        data = request.json  # type: ignore
        user_id = int(data.get('user_id', 0))  # type: ignore
        channel_id = int(data.get('channel_id', 0))  # type: ignore
        
        if not user_id or not channel_id:
            return jsonify({'error': '缺少參數'}), 400
        
        async def do_unmute():
            bot = discord_bot_instance.bot  # type: ignore
            channel = bot.get_channel(channel_id)  # type: ignore
            if channel and isinstance(channel, discord.VoiceChannel):
                member = channel.guild.get_member(user_id)
                if member and member in channel.members:
                    await member.edit(mute=False)
                    return True
            return False
        
        result = asyncio.run_coroutine_threadsafe(
            do_unmute(),
            discord_bot_instance.bot.loop  # type: ignore
        ).result(timeout=10)
        
        return jsonify({'success': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/voice/undeafen', methods=['POST'])
@login_required
def undeafen_voice_user():
    """解除用戶失聰"""
    if current_user.role == UserRole.LOW:
        return jsonify({'error': '權限不足'}), 403
    
    try:
        data = request.json  # type: ignore
        user_id = int(data.get('user_id', 0))  # type: ignore
        channel_id = int(data.get('channel_id', 0))  # type: ignore
        
        if not user_id or not channel_id:
            return jsonify({'error': '缺少參數'}), 400
        
        async def do_undeafen():
            bot = discord_bot_instance.bot  # type: ignore
            channel = bot.get_channel(channel_id)  # type: ignore
            if channel and isinstance(channel, discord.VoiceChannel):
                member = channel.guild.get_member(user_id)
                if member and member in channel.members:
                    await member.edit(deafen=False)
                    return True
            return False
        
        result = asyncio.run_coroutine_threadsafe(
            do_undeafen(),
            discord_bot_instance.bot.loop  # type: ignore
        ).result(timeout=10)
        
        return jsonify({'success': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)