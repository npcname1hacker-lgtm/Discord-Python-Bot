"""
電子郵件服務 - 使用Resend發送驗證碼
"""

import os
import random
import string
import json
from datetime import datetime, timedelta
import requests

class EmailService:
    """電子郵件服務類"""
    
    def __init__(self):
        self.hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
        self.token = None
        
        # 嘗試獲取Replit identity token
        if os.environ.get('REPL_IDENTITY'):
            self.token = 'repl ' + os.environ.get('REPL_IDENTITY')
        elif os.environ.get('WEB_REPL_RENEWAL'):
            self.token = 'depl ' + os.environ.get('WEB_REPL_RENEWAL')
        
        self.connection_settings = None
        self.verification_codes = {}  # 存儲驗證碼 {email: {'code': '123456', 'expires': datetime}}
    
    def get_credentials(self):
        """獲取Resend API憑證"""
        if not self.hostname or not self.token:
            raise Exception("Resend連接未配置")
        
        url = f'https://{self.hostname}/api/v2/connection?include_secrets=true&connector_names=resend'
        
        response = requests.get(
            url,
            headers={
                'Accept': 'application/json',
                'X_REPLIT_TOKEN': self.token
            }
        )
        
        data = response.json()
        items = data.get('items', [])
        
        if not items:
            raise Exception("Resend未連接")
        
        self.connection_settings = items[0]
        settings = self.connection_settings.get('settings', {})
        
        if not settings.get('api_key'):
            raise Exception("Resend API密鑰未配置")
        
        return {
            'api_key': settings.get('api_key'),
            'from_email': settings.get('from_email', 'noreply@example.com')
        }
    
    def generate_verification_code(self, length=6):
        """生成驗證碼"""
        return ''.join(random.choices(string.digits, k=length))
    
    def send_verification_email(self, to_email, purpose='註冊'):
        """發送驗證碼郵件"""
        try:
            credentials = self.get_credentials()
            
            # 生成驗證碼
            code = self.generate_verification_code()
            
            # 存儲驗證碼（10分鐘有效期）
            self.verification_codes[to_email] = {
                'code': code,
                'expires': datetime.utcnow() + timedelta(minutes=10),
                'purpose': purpose
            }
            
            # 準備郵件內容
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 30px;
                        text-align: center;
                        border-radius: 10px 10px 0 0;
                    }}
                    .content {{
                        background: #f8f9fa;
                        padding: 30px;
                        border-radius: 0 0 10px 10px;
                    }}
                    .code-box {{
                        background: white;
                        border: 2px dashed #667eea;
                        border-radius: 8px;
                        padding: 20px;
                        text-align: center;
                        margin: 20px 0;
                    }}
                    .code {{
                        font-size: 32px;
                        font-weight: bold;
                        color: #667eea;
                        letter-spacing: 8px;
                        font-family: 'Courier New', monospace;
                    }}
                    .footer {{
                        text-align: center;
                        color: #666;
                        font-size: 12px;
                        margin-top: 20px;
                    }}
                    .warning {{
                        background: #fff3cd;
                        border-left: 4px solid #ffc107;
                        padding: 12px;
                        margin: 15px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🎮 ɢʀᴠ戰隊管理系統</h1>
                    <p>電子郵件驗證</p>
                </div>
                <div class="content">
                    <h2>您好！</h2>
                    <p>您正在進行<strong>{purpose}</strong>操作，請使用以下驗證碼完成驗證：</p>
                    
                    <div class="code-box">
                        <div class="code">{code}</div>
                        <p style="margin: 10px 0 0 0; color: #666;">驗證碼</p>
                    </div>
                    
                    <div class="warning">
                        <strong>⏰ 重要提示：</strong>
                        <ul style="margin: 5px 0;">
                            <li>此驗證碼將在 <strong>10分鐘</strong> 後失效</li>
                            <li>如果這不是您的操作，請忽略此郵件</li>
                            <li>請勿將驗證碼透露給他人</li>
                        </ul>
                    </div>
                    
                    <p style="margin-top: 20px;">如有任何問題，請聯繫戰隊管理員。</p>
                </div>
                <div class="footer">
                    <p>ɢʀᴠ戰隊管理系統 V1.00.8</p>
                    <p>創作者：ɢʀᴠ戰隊隊長殤嵐</p>
                </div>
            </body>
            </html>
            """
            
            # 發送郵件
            response = requests.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {credentials["api_key"]}',
                    'Content-Type': 'application/json'
                },
                json={
                    'from': credentials['from_email'],
                    'to': [to_email],
                    'subject': f'ɢʀᴠ戰隊 - 您的驗證碼是 {code}',
                    'html': html_content
                }
            )
            
            if response.status_code == 200:
                return True, f'驗證碼已發送到 {to_email}'
            else:
                return False, f'發送失敗：{response.text}'
                
        except Exception as e:
            return False, f'郵件服務錯誤：{str(e)}'
    
    def verify_code(self, email, code):
        """驗證驗證碼"""
        if email not in self.verification_codes:
            return False, '未找到驗證碼記錄'
        
        stored = self.verification_codes[email]
        
        # 檢查是否過期
        if datetime.utcnow() > stored['expires']:
            del self.verification_codes[email]
            return False, '驗證碼已過期，請重新獲取'
        
        # 驗證碼是否匹配
        if stored['code'] != code:
            return False, '驗證碼錯誤'
        
        # 驗證成功，刪除記錄
        del self.verification_codes[email]
        return True, '驗證成功'
    
    def send_password_reset_email(self, to_email, reset_token):
        """發送密碼重置郵件"""
        try:
            credentials = self.get_credentials()
            
            # 這裡應該是您的網站域名
            reset_url = f"http://0.0.0.0:5000/reset-password?token={reset_token}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        color: white;
                        padding: 30px;
                        text-align: center;
                        border-radius: 10px 10px 0 0;
                    }}
                    .content {{
                        background: #f8f9fa;
                        padding: 30px;
                        border-radius: 0 0 10px 10px;
                    }}
                    .button {{
                        display: inline-block;
                        background: #667eea;
                        color: white;
                        padding: 15px 30px;
                        text-decoration: none;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .footer {{
                        text-align: center;
                        color: #666;
                        font-size: 12px;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🔐 密碼重置請求</h1>
                </div>
                <div class="content">
                    <h2>您好！</h2>
                    <p>我們收到了您的密碼重置請求。點擊下方按鈕重置您的密碼：</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">重置密碼</a>
                    </div>
                    
                    <p style="margin-top: 20px;">如果按鈕無法點擊，請複製以下鏈接到瀏覽器：</p>
                    <p style="background: #e9ecef; padding: 10px; word-break: break-all; font-size: 12px;">
                        {reset_url}
                    </p>
                    
                    <p style="color: #dc3545; margin-top: 20px;">
                        <strong>⚠️ 此鏈接將在30分鐘後失效</strong>
                    </p>
                    
                    <p>如果這不是您的操作，請忽略此郵件，您的密碼不會被更改。</p>
                </div>
                <div class="footer">
                    <p>ɢʀᴠ戰隊管理系統 V1.00.8</p>
                </div>
            </body>
            </html>
            """
            
            response = requests.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {credentials["api_key"]}',
                    'Content-Type': 'application/json'
                },
                json={
                    'from': credentials['from_email'],
                    'to': [to_email],
                    'subject': 'ɢʀᴠ戰隊 - 密碼重置請求',
                    'html': html_content
                }
            )
            
            if response.status_code == 200:
                return True, '密碼重置郵件已發送'
            else:
                return False, f'發送失敗：{response.text}'
                
        except Exception as e:
            return False, f'郵件服務錯誤：{str(e)}'

# 延遲創建全局實例
email_service = None

def get_email_service():
    """獲取郵件服務實例（延遲初始化）"""
    global email_service
    if email_service is None:
        email_service = EmailService()
    return email_service
