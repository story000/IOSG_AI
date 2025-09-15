#!/usr/bin/env python3
"""
重新获取Inoreader Token的辅助脚本
当refresh_token过期时可以使用此脚本重新认证
"""

import os
from dotenv import load_dotenv
from inoreader_client import InoreaderClient, authenticate_with_browser

load_dotenv()


def main():
    """重新获取Inoreader认证token"""

    print("=" * 60)
    print("Inoreader Token重新获取工具")
    print("=" * 60)

    # 获取配置
    client_id = os.getenv('INOREADER_CLIENT_ID')
    client_secret = os.getenv('INOREADER_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("❌ 错误: 未找到Inoreader配置")
        print("请确保在.env文件中设置了:")
        print("  INOREADER_CLIENT_ID=your_client_id")
        print("  INOREADER_CLIENT_SECRET=your_client_secret")
        return

    print(f"✓ 找到Inoreader配置")
    print(f"  Client ID: {client_id[:10]}...")

    try:
        # 创建客户端
        client = InoreaderClient(client_id, client_secret)

        print("\n正在启动浏览器进行OAuth认证...")
        print("请在浏览器中完成授权流程")

        # 进行认证
        token_data = authenticate_with_browser(client)

        print("\n✅ 认证成功!")
        print(f"Access Token: {token_data['access_token'][:20]}...")
        print(f"Refresh Token: {token_data['refresh_token'][:20]}...")
        print(f"过期时间: {token_data.get('expires_in', 'N/A')} 秒")

        print("\n🎉 新的token已保存到 inoreader_tokens.json")
        print("现在可以测试token自动刷新功能了!")

    except Exception as e:
        print(f"\n❌ 认证失败: {e}")
        print("请检查网络连接和Inoreader配置")


if __name__ == "__main__":
    main()