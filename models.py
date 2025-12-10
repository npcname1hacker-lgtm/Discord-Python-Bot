"""
Discord Bot - 資料庫模型
儲存戰隊申請和成員資料
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class TeamApplication(Base):
    """戰隊申請模型"""
    __tablename__ = 'team_applications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)  # Discord用戶ID
    username = Column(String(100), nullable=False)  # Discord用戶名
    display_name = Column(String(100), nullable=False)  # 顯示名稱
    game_id = Column(String(100), nullable=False)  # 遊戲ID
    avatar_url = Column(Text)  # 用戶頭像
    application_photos = Column(JSON)  # 申請照片URLs (最多5張)
    application_text = Column(Text)  # 申請說明文字
    status = Column(String(20), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(String(50))  # 審核者的Discord ID
    rejection_reason = Column(Text)  # 拒絕原因

class DatabaseManager:
    """資料庫管理器"""
    
    def __init__(self):
        import os
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:////tmp/grv_team_bot.db')
        
        # Ensure SQLite is used if database is not available
        if 'sqlite' not in self.database_url:
            if not self.database_url or 'ep-ancient-waterfall' in self.database_url:
                self.database_url = 'sqlite:////tmp/grv_team_bot.db'
        
        # Configure SQLAlchemy for SQLite compatibility
        kwargs = {'check_same_thread': False} if 'sqlite' in self.database_url else {}
        self.engine = create_engine(self.database_url, connect_args=kwargs)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 創建所有表格
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """獲取資料庫會話"""
        return self.SessionLocal()
    
    def add_application(self, user_id, username, display_name, game_id, avatar_url, photos, application_text=""):
        """添加新申請"""
        session = self.get_session()
        try:
            application = TeamApplication(
                user_id=user_id,
                username=username,
                display_name=display_name,
                game_id=game_id,
                avatar_url=avatar_url,
                application_photos=photos,
                application_text=application_text
            )
            session.add(application)
            session.commit()
            return application.id
        finally:
            session.close()
    
    def get_pending_applications(self):
        """獲取所有待審核申請"""
        session = self.get_session()
        try:
            return session.query(TeamApplication).filter_by(status='pending').all()
        finally:
            session.close()
    
    def get_application_by_id(self, app_id):
        """根據ID獲取申請"""
        session = self.get_session()
        try:
            return session.query(TeamApplication).filter_by(id=app_id).first()
        finally:
            session.close()
    
    def update_application_status(self, app_id, status, reviewed_by, rejection_reason=None):
        """更新申請狀態"""
        session = self.get_session()
        try:
            application = session.query(TeamApplication).filter_by(id=app_id).first()
            if application:
                application.status = status
                application.reviewed_by = reviewed_by
                application.reviewed_at = datetime.utcnow()
                if rejection_reason:
                    application.rejection_reason = rejection_reason
                session.commit()
                return True
            return False
        finally:
            session.close()

# 全局資料庫管理器實例
_bot_db_instance = None

def get_bot_database():
    """獲取機器人資料庫管理器（延遲初始化）"""
    global _bot_db_instance
    if _bot_db_instance is None:
        _bot_db_instance = DatabaseManager()
    return _bot_db_instance