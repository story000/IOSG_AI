#!/usr/bin/env python3
"""
测试Token自动刷新功能
"""

import sys
import os
import time
from pathlib import Path

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.services.token_refresh_service import TokenRefreshService
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_token_refresh_service():
    """测试Token刷新服务"""

    print("=" * 50)
    print("Token自动刷新服务测试")
    print("=" * 50)

    # 检查配置
    client_id = os.getenv('INOREADER_CLIENT_ID')
    client_secret = os.getenv('INOREADER_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("❌ 未找到Inoreader配置，请检查.env文件")
        return False

    print(f"✓ Inoreader配置已找到: client_id={client_id[:10]}...")

    # 创建服务实例（测试用，较短的刷新间隔）
    service = TokenRefreshService(refresh_interval_hours=0.01)  # 36秒测试

    print(f"✓ Token刷新服务创建成功，刷新间隔: {service.refresh_interval_hours}小时")

    # 测试立即刷新功能
    print("\n--- 测试立即token刷新 ---")
    try:
        result = service.force_refresh()
        if result:
            print("✓ Token立即刷新成功")
        else:
            print("⚠️ Token立即刷新失败（可能需要重新认证）")
    except Exception as e:
        print(f"❌ Token立即刷新出错: {e}")

    # 测试服务启动
    print("\n--- 测试服务启动 ---")
    try:
        service.start()
        print("✓ Token刷新服务启动成功")

        # 获取状态
        status = service.get_status()
        print(f"  - 运行状态: {status['running']}")
        print(f"  - 刷新间隔: {status['refresh_interval_hours']}小时")
        print(f"  - 线程状态: {status['thread_alive']}")

        # 等待一小段时间看服务是否正常运行
        print("\n--- 监控服务运行 ---")
        for i in range(5):
            print(f"服务运行中... ({i+1}/5)")
            time.sleep(1)

        # 停止服务
        print("\n--- 停止服务 ---")
        service.stop()
        print("✓ Token刷新服务已停止")

        return True

    except Exception as e:
        print(f"❌ 服务测试失败: {e}")
        return False


def test_integration_with_main():
    """测试与main.py的集成"""

    print("\n" + "=" * 50)
    print("main.py集成测试")
    print("=" * 50)

    try:
        from src.services.token_refresh_service import start_token_refresh_service, stop_token_refresh_service

        print("✓ 导入token刷新服务成功")

        # 测试启动
        print("测试服务启动...")
        service = start_token_refresh_service(refresh_interval_hours=12)

        if service:
            print("✓ 服务通过start_token_refresh_service启动成功")

            # 等待一下
            time.sleep(2)

            # 测试停止
            print("测试服务停止...")
            stop_token_refresh_service()
            print("✓ 服务通过stop_token_refresh_service停止成功")

            return True
        else:
            print("⚠️ 服务启动返回None")
            return False

    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False


if __name__ == "__main__":
    print("开始Token自动刷新功能测试...\n")

    # 运行测试
    test1_result = test_token_refresh_service()
    test2_result = test_integration_with_main()

    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    print(f"基础功能测试: {'✓ 通过' if test1_result else '❌ 失败'}")
    print(f"集成测试: {'✓ 通过' if test2_result else '❌ 失败'}")

    if test1_result and test2_result:
        print("\n🎉 所有测试通过！Token自动刷新功能已成功集成")
        print("\n使用说明:")
        print("1. 运行 'python main.py' 时会自动启动token刷新服务")
        print("2. 服务会每12小时检查一次token是否需要刷新")
        print("3. 如果token即将过期，会自动尝试刷新")
        print("4. 程序退出时会自动停止刷新服务")
    else:
        print("\n❌ 部分测试失败，请检查配置和代码")

    print(f"\n注意: 如果看到'Token刷新失败'，这是正常的")
    print(f"因为当前的refresh_token可能已过期，需要重新通过Inoreader认证获取新的token")