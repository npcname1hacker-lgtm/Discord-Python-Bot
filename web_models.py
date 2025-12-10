"""
戰隊管理網站 - 擴展資料庫模型
包含用戶賬號、權限管理等
"""

import os
import bcrypt
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_login import UserMixin
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    """用戶權限等級"""
    HIGH = "high"      # 隊長 - 所有權限
    MEDIUM = "medium"  # 副隊長/幹部 - 基本功能
    LOW = "low"        # 警告狀態 - 準備封號

class WebUser(Base, UserMixin):
    """網站用戶模型"""
    __tablename__ = 'web_users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.MEDIUM)
    discord_id = Column(String(50))  # 關聯的Discord ID（隊長綁定）
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)  # 是否已通過隊長審核
    approval_status = Column(String(50), default="pending")  # pending/approved/rejected
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(50))  # 創建者用戶名
    
    def set_password(self, password):
        """設置密碼"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """驗證密碼"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def get_role_display(self):
        """獲取權限顯示名稱"""
        role_names = {
            UserRole.HIGH: "隊長",
            UserRole.MEDIUM: "副隊長/幹部", 
            UserRole.LOW: "受限用戶"
        }
        return role_names.get(self.role, "未知")

class BotCommand(Base):
    """自定義機器人指令"""
    __tablename__ = 'bot_commands'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    command_name = Column(String(50), nullable=False)
    command_aliases = Column(JSON)  # 指令別名
    description = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class PasswordReset(Base):
    """密碼重置驗證碼表"""
    __tablename__ = 'password_resets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    verification_code = Column(String(6), nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

class SystemSettings(Base):
    """系統設置"""
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text)
    description = Column(Text)
    updated_by = Column(String(50))
    updated_at = Column(DateTime, default=datetime.utcnow)

class VoiceState(Base):
    """語音狀態持久化表"""
    __tablename__ = 'voice_states'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)
    guild_id = Column(String(50), nullable=False)
    is_muted = Column(Boolean, default=False)  # 禁言
    is_deafened = Column(Boolean, default=False)  # 失聰
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class WelcomeSettings(Base):
    """歡迎設置"""
    __tablename__ = 'welcome_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(String(50), nullable=False, unique=True)
    channel_id = Column(String(50), nullable=False)
    message_template = Column(Text, default="歡迎 {username} 加入 {servername}！")
    auto_rename_enabled = Column(Boolean, default=True)
    rename_prefix = Column(String(50), default="ɢʀᴠ.")
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(50))

# 全局資料庫管理器實例
_web_db_instance = None

class WebDatabaseManager:
    """網站資料庫管理器"""
    
    def __init__(self):
        import os
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:////tmp/grv_team_web.db')
        
        # Ensure SQLite is used if database is not available
        if 'sqlite' not in self.database_url:
            if not self.database_url or 'ep-ancient-waterfall' in self.database_url:
                self.database_url = 'sqlite:////tmp/grv_team_web.db'
        
        # Configure SQLAlchemy for SQLite compatibility
        kwargs = {'check_same_thread': False} if 'sqlite' in self.database_url else {}
        self.engine = create_engine(self.database_url, connect_args=kwargs)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 創建所有表格
        Base.metadata.create_all(bind=self.engine)
        
        # 初始化預設用戶
        self.init_default_users()
    
    def get_session(self):
        """獲取資料庫會話"""
        return self.SessionLocal()
    
    def init_default_users(self):
        """初始化預設用戶賬號"""
        session = self.get_session()
        try:
            # 檢查是否已存在用戶
            existing_admin = session.query(WebUser).filter_by(username='admin0803').first()
            if existing_admin:
                return
            
            # 創建預設用戶
            users_data = [
                {
                    'username': 'admin0803',
                    'password': 'admin0803+0815',
                    'role': UserRole.HIGH,
                    'discord_id': '1266626578696245281',  # 隊長Discord ID
                    'is_approved': True,
                    'approval_status': 'approved',
                    'created_by': 'system'
                },
                {
                    'username': 'admin0815', 
                    'password': 'admin-fan.wei.lun',
                    'role': UserRole.MEDIUM,
                    'is_approved': True,
                    'approval_status': 'approved',
                    'created_by': 'system'
                },
                {
                    'username': 'admin3',
                    'password': 'admin1331914', 
                    'role': UserRole.MEDIUM,
                    'is_approved': True,
                    'approval_status': 'approved',
                    'created_by': 'system'
                }
            ]
            
            for user_data in users_data:
                user = WebUser(
                    username=user_data['username'],
                    role=user_data['role'],
                    discord_id=user_data.get('discord_id'),
                    is_approved=user_data.get('is_approved', True),
                    approval_status=user_data.get('approval_status', 'approved'),
                    created_by=user_data['created_by']
                )
                user.set_password(user_data['password'])
                session.add(user)
            
            try:
                session.commit()
                print("已創建預設管理員賬號")
            except Exception as e:
                # 如果插入失敗（如重複用戶名），回滾並忽略
                session.rollback()
                if "UNIQUE constraint failed" in str(e):
                    print("預設管理員賬號已存在，跳過創建")
                else:
                    print(f"初始化預設用戶出錯: {e}")
            
        finally:
            session.close()
    
    def get_user_by_username(self, username):
        """根據用戶名獲取用戶"""
        session = self.get_session()
        try:
            return session.query(WebUser).filter_by(username=username, is_active=True).first()
        finally:
            session.close()
    
    def get_user_by_id(self, user_id):
        """根據ID獲取用戶"""
        session = self.get_session()
        try:
            return session.query(WebUser).filter_by(id=user_id, is_active=True).first()
        finally:
            session.close()
    
    def create_user(self, username, password, role=UserRole.MEDIUM, created_by="admin", email=None, phone=None):
        """創建新用戶"""
        session = self.get_session()
        try:
            user = WebUser(
                username=username,
                role=role,
                created_by=created_by,
                email=email,
                phone=phone
            )
            user.set_password(password)
            session.add(user)
            session.commit()
            return user.id
        finally:
            session.close()
    
    def update_user_role(self, user_id, new_role):
        """更新用戶權限"""
        session = self.get_session()
        try:
            user = session.query(WebUser).filter_by(id=user_id).first()
            if user:
                user.role = new_role
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def change_user_password(self, user_id, new_password):
        """更改用戶密碼"""
        session = self.get_session()
        try:
            user = session.query(WebUser).filter_by(id=user_id).first()
            if user:
                user.set_password(new_password)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def get_all_users(self):
        """獲取所有用戶"""
        session = self.get_session()
        try:
            return session.query(WebUser).filter_by(is_active=True).all()
        finally:
            session.close()
    
    def add_custom_command(self, command_name, aliases, description, response_text, created_by):
        """添加自定義指令"""
        session = self.get_session()
        try:
            command = BotCommand(
                command_name=command_name,
                command_aliases=aliases,
                description=description,
                response_text=response_text,
                created_by=created_by
            )
            session.add(command)
            session.commit()
            return command.id
        finally:
            session.close()
    
    def get_custom_commands(self):
        """獲取所有自定義指令"""
        session = self.get_session()
        try:
            return session.query(BotCommand).filter_by(is_active=True).all()
        finally:
            session.close()
    
    def create_password_reset(self, username, code, expires_at):
        """創建密碼重置驗證碼"""
        session = self.get_session()
        try:
            reset = PasswordReset(username=username, verification_code=code, expires_at=expires_at)
            session.add(reset)
            session.commit()
            return reset.id
        finally:
            session.close()
    
    def verify_reset_code(self, username, code):
        """驗證重置碼"""
        session = self.get_session()
        try:
            reset = session.query(PasswordReset).filter_by(
                username=username, 
                verification_code=code, 
                is_used=False
            ).first()
            if reset and reset.expires_at > datetime.utcnow():
                return reset
            return None
        finally:
            session.close()
    
    def mark_reset_as_used(self, reset_id):
        """標記重置碼為已使用"""
        session = self.get_session()
        try:
            reset = session.query(PasswordReset).filter_by(id=reset_id).first()
            if reset:
                reset.is_used = True
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def get_admin_users(self):
        """獲取所有隊長級用戶"""
        session = self.get_session()
        try:
            return session.query(WebUser).filter_by(role=UserRole.HIGH, is_active=True).all()
        finally:
            session.close()

def get_web_database():
    """獲取網站資料庫管理器（延遲初始化）"""
    global _web_db_instance
    if _web_db_instance is None:
        _web_db_instance = WebDatabaseManager()
    return _web_db_instance