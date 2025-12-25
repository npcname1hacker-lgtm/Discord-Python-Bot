"""
Discord Bot - 配置管理模組
管理機器人的所有配置和環境變數
"""

import os
from dotenv import load_dotenv

class Config:
    """機器人配置類別"""
    
    def __init__(self):
        """初始化配置"""
        # 只從 .env 檔案載入環境變數，不讀取系統環境變數
        load_dotenv(override=True)
        
        # 使用 os.environ.get 確保能讀取到 load_dotenv 載入的變數
        token = os.environ.get('DISCORD_TOKEN', '')
        # 過濾掉可能存在的引號和空格
        self.DISCORD_TOKEN = token.replace('"', '').replace("'", "").strip()
        self.COMMAND_PREFIX = os.environ.get('COMMAND_PREFIX', '!')
        self.BOT_STATUS = os.environ.get('BOT_STATUS', '使用 !help 獲取幫助')
        
        # 公告頻道設置
        self.ANNOUNCEMENT_CHANNEL_ID = 1410846655980503040  # ɢʀᴠ戰隊群公告頻道（永久預設）
        
        # 日誌設置
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # 驗證必要的配置
        self._validate_config()
    
    def _validate_config(self):
        """驗證配置是否正確"""
        if not self.DISCORD_TOKEN:
            raise ValueError(
                "未設置Discord機器人令牌。請在環境變數中設置 DISCORD_TOKEN 或在 .env 檔案中添加。"
            )
        
        if len(self.COMMAND_PREFIX) > 5:
            raise ValueError("指令前綴不能超過5個字符")
    
    def get_all_settings(self):
        """獲取所有配置設置（隱藏敏感資訊）"""
        return {
            'DISCORD_TOKEN': '***隱藏***' if self.DISCORD_TOKEN else '未設置',
            'COMMAND_PREFIX': self.COMMAND_PREFIX,
            'BOT_STATUS': self.BOT_STATUS,
            'LOG_LEVEL': self.LOG_LEVEL,
            'DEBUG': self.DEBUG
        }
