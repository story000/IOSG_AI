import json
import os
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self, token_file="inoreader_tokens.json"):
        self.token_file = token_file
    
    def save_tokens(self, access_token, refresh_token, expires_in=3600):
        """保存令牌到文件"""
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        token_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': expires_at.isoformat(),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print(f"✓ 令牌已保存到 {self.token_file}")
    
    def load_tokens(self):
        """从文件加载令牌"""
        if not os.path.exists(self.token_file):
            return None
        
        try:
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
            
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            
            # 检查是否过期（提前5分钟刷新）
            if datetime.now() >= expires_at - timedelta(minutes=5):
                print("⚠️ 访问令牌即将过期，需要刷新")
                return {
                    'access_token': None,
                    'refresh_token': token_data['refresh_token'],
                    'expired': True
                }
            
            print("✓ 从缓存加载有效令牌")
            return {
                'access_token': token_data['access_token'],
                'refresh_token': token_data['refresh_token'],
                'expired': False
            }
            
        except Exception as e:
            print(f"⚠️ 读取令牌文件失败: {e}")
            return None
    
    def clear_tokens(self):
        """清除保存的令牌"""
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            print("✓ 令牌文件已清除")
    
    def is_token_valid(self):
        """检查令牌是否有效"""
        token_data = self.load_tokens()
        return token_data is not None and not token_data.get('expired', True)