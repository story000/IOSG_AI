#!/usr/bin/env python3
"""
清除保存的令牌 - 用于重新认证
"""

from token_manager import TokenManager

def main():
    token_manager = TokenManager()
    
    print("=== 清除令牌工具 ===")
    
    if token_manager.is_token_valid():
        print("发现有效令牌")
        confirm = input("确定要清除吗？(y/n): ").lower()
        if confirm == 'y':
            token_manager.clear_tokens()
            print("✓ 令牌已清除，下次运行将重新认证")
        else:
            print("取消操作")
    else:
        print("未找到有效令牌文件")

if __name__ == "__main__":
    main()