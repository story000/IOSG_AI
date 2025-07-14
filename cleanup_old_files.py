#!/usr/bin/env python3
"""
清理旧的时间戳格式文件
迁移到新的固定文件名系统后，清理旧的文件
"""

import os
import glob
from datetime import datetime

def cleanup_old_files():
    """清理旧的时间戳格式文件"""
    
    print("=== 清理旧文件 ===")
    
    # 要清理的文件模式
    file_patterns = [
        "crypto_feeds_unread_*.json",
        "classified_articles_*.json", 
        "formatted_report_*.txt",
        "classification_report_*.txt",
        "funding_articles_*.json",
        "funding_report_*.txt"
    ]
    
    total_deleted = 0
    total_size = 0
    
    for pattern in file_patterns:
        files = glob.glob(pattern)
        if files:
            print(f"\n📂 找到 {len(files)} 个 {pattern} 文件:")
            
            for file_path in files:
                try:
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    
                    # 显示文件信息
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    size_mb = file_size / 1024 / 1024
                    print(f"  - {file_path} ({size_mb:.2f} MB, {modified_time.strftime('%Y-%m-%d %H:%M')})")
                    
                except Exception as e:
                    print(f"  - {file_path} (获取信息失败: {e})")
            
            # 询问是否删除这类文件
            response = input(f"\n是否删除所有 {pattern} 文件? (y/n): ").strip().lower()
            if response == 'y':
                deleted_count = 0
                for file_path in files:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        total_deleted += 1
                    except Exception as e:
                        print(f"  ❌ 删除失败 {file_path}: {e}")
                
                print(f"  ✅ 已删除 {deleted_count} 个文件")
            else:
                print(f"  ⏭️ 跳过删除 {pattern}")
        else:
            print(f"\n📂 未找到 {pattern} 文件")
    
    print(f"\n=== 清理完成 ===")
    print(f"共删除 {total_deleted} 个文件")
    print(f"释放空间: {total_size / 1024 / 1024:.2f} MB")
    
    # 显示当前的新格式文件
    print(f"\n=== 当前的新格式文件 ===")
    new_files = [
        "latest_feeds.json",
        "historical_feeds.json", 
        "latest_classified.json",
        "historical_classified.json"
    ]
    
    for file_name in new_files:
        if os.path.exists(file_name):
            file_size = os.path.getsize(file_name)
            modified_time = datetime.fromtimestamp(os.path.getmtime(file_name))
            size_mb = file_size / 1024 / 1024
            print(f"✓ {file_name} ({size_mb:.2f} MB, {modified_time.strftime('%Y-%m-%d %H:%M')})")
        else:
            print(f"- {file_name} (不存在)")

def show_current_files():
    """显示当前所有相关文件"""
    print("=== 当前文件状态 ===")
    
    all_patterns = [
        "*.json",
        "*.txt"
    ]
    
    for pattern in all_patterns:
        files = glob.glob(pattern)
        if files:
            print(f"\n📂 {pattern} 文件:")
            for file_path in sorted(files):
                try:
                    file_size = os.path.getsize(file_path)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    size_mb = file_size / 1024 / 1024
                    print(f"  - {file_path} ({size_mb:.2f} MB, {modified_time.strftime('%Y-%m-%d %H:%M')})")
                except:
                    print(f"  - {file_path} (获取信息失败)")

def main():
    print("🧹 文件清理工具")
    print("=" * 50)
    
    while True:
        print("\n选择操作:")
        print("1. 显示当前文件状态")  
        print("2. 清理旧的时间戳文件")
        print("3. 退出")
        
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            show_current_files()
        elif choice == "2":
            cleanup_old_files()
        elif choice == "3":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    main()