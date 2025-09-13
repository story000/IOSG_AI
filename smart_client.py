#!/usr/bin/env python3
"""
Smart Inoreader Client - OAuth认证脚本
用于获取和保存 Inoreader API 的访问令牌
"""

from inoreader_client import InoreaderClient, authenticate_with_browser
from token_manager import TokenManager
import sys

def main():
    """主要认证流程"""
    print("=== Inoreader OAuth 认证 ===")
    print()
    
    # 使用与 fetch_specific_feeds.py 相同的客户端凭据
    CLIENT_ID = "1000001559" 
    CLIENT_SECRET = "lDyl2_XuuueJYcFZOwNipRy79_TibMOH"
    
    # 创建客户端
    client = InoreaderClient(CLIENT_ID, CLIENT_SECRET)
    
    # 检查当前认证状态
    if client.is_authenticated():
        print("✅ 已经认证成功！")
        try:
            user_info = client.get_user_info()
            print(f"当前用户: {user_info.get('userName', 'Unknown')}")
            print(f"用户ID: {user_info.get('userId', 'Unknown')}")
            print()
            print("如果需要重新认证，请先运行: python clear_tokens.py")
            return
        except Exception as e:
            print(f"⚠️ 获取用户信息失败: {e}")
            print("令牌可能已失效，开始重新认证...")
    else:
        print("❌ 尚未认证，开始OAuth认证流程...")
    
    print()
    print("认证说明:")
    print("1. 即将打开浏览器进行认证")
    print("2. 请在浏览器中登录您的 Inoreader 账户")
    print("3. 授权应用访问您的 Inoreader 数据")
    print("4. 认证成功后会自动保存令牌")
    print()
    
    input("按 Enter 键开始认证...")
    
    try:
        # 开始浏览器认证
        token_data = authenticate_with_browser(client)
        
        print()
        print("🎉 认证成功！")
        print(f"访问令牌: {token_data['access_token'][:20]}...")
        print(f"刷新令牌: {token_data['refresh_token'][:20]}...")
        print(f"有效期: {token_data.get('expires_in', 3600)} 秒")
        
        # 测试认证是否工作
        print()
        print("正在测试认证...")
        try:
            user_info = client.get_user_info()
            print(f"✅ 认证测试成功！")
            print(f"用户名: {user_info.get('userName', 'Unknown')}")
            print(f"用户ID: {user_info.get('userId', 'Unknown')}")
        except Exception as e:
            print(f"❌ 认证测试失败: {e}")
            
        print()
        print("🚀 现在您可以运行其他脚本了:")
        print("  python fetch_specific_feeds.py  # 获取新闻")
        print("  python app.py                   # 启动Web界面")
        
    except Exception as e:
        print(f"❌ 认证失败: {e}")
        print()
        print("故障排除:")
        print("1. 确保您有有效的 Inoreader 账户")
        print("2. 检查网络连接")
        print("3. 确保浏览器允许弹出窗口")
        print("4. 如果问题持续，请联系管理员")
        sys.exit(1)

if __name__ == "__main__":
    main()