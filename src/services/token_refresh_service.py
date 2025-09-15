"""
Inoreader Token自动刷新服务
提供后台定期刷新token的功能
"""

import threading
import time
import os
from datetime import datetime, timedelta
from typing import Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class TokenRefreshService:
    """Inoreader Token自动刷新服务"""

    def __init__(self, refresh_interval_hours: int = 12):
        """
        初始化Token刷新服务

        Args:
            refresh_interval_hours: 刷新间隔时间（小时），默认12小时
        """
        self.refresh_interval_hours = refresh_interval_hours
        self.refresh_interval_seconds = refresh_interval_hours * 3600
        self.running = False
        self.refresh_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 延迟导入避免循环依赖
        self._inoreader_client = None
        self._token_manager = None

    def _get_inoreader_client(self):
        """延迟初始化Inoreader客户端"""
        if self._inoreader_client is None:
            try:
                # 导入并初始化Inoreader客户端
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from inoreader_client import InoreaderClient
                from token_manager import TokenManager

                # 从环境变量获取配置
                client_id = os.getenv('INOREADER_CLIENT_ID')
                client_secret = os.getenv('INOREADER_CLIENT_SECRET')

                if not client_id or not client_secret:
                    logger.warning("Inoreader客户端配置不完整，跳过token自动刷新")
                    return None

                self._inoreader_client = InoreaderClient(client_id, client_secret)
                self._token_manager = TokenManager()

                logger.info("Inoreader客户端初始化成功")

            except Exception as e:
                logger.error(f"初始化Inoreader客户端失败: {e}")
                return None

        return self._inoreader_client

    def _refresh_token_if_needed(self):
        """检查并刷新token"""
        try:
            client = self._get_inoreader_client()
            if not client:
                return False

            # 检查token是否需要刷新
            if hasattr(client, 'token_manager'):
                token_data = client.token_manager.load_tokens()

                if not token_data:
                    logger.warning("没有找到保存的token，需要手动认证")
                    return False

                if token_data.get('expired', True):
                    logger.info("Token已过期，尝试刷新...")

                    try:
                        # 执行token刷新
                        result = client.refresh_access_token()
                        if result:
                            logger.info("Token刷新成功")
                            return True
                        else:
                            logger.error("Token刷新失败")
                            return False

                    except Exception as e:
                        logger.error(f"Token刷新过程中出错: {e}")
                        return False
                else:
                    logger.debug("Token仍然有效，无需刷新")
                    return True

        except Exception as e:
            logger.error(f"检查token状态时出错: {e}")
            return False

    def _refresh_loop(self):
        """主刷新循环"""
        logger.info(f"Token自动刷新服务已启动，每{self.refresh_interval_hours}小时检查一次")

        # 启动时立即检查一次
        self._refresh_token_if_needed()

        while not self._stop_event.is_set():
            try:
                # 等待指定时间或停止信号
                if self._stop_event.wait(timeout=self.refresh_interval_seconds):
                    # 收到停止信号
                    break

                # 执行token刷新检查
                logger.info("开始定期token检查...")
                success = self._refresh_token_if_needed()

                if success:
                    logger.info("Token检查/刷新完成")
                else:
                    logger.warning("Token检查/刷新失败，将在下个周期重试")

            except Exception as e:
                logger.error(f"Token刷新循环中出现错误: {e}")
                # 出错后等待一段时间再继续
                if not self._stop_event.wait(timeout=300):  # 等待5分钟
                    continue
                else:
                    break

    def start(self):
        """启动token自动刷新服务"""
        if self.running:
            logger.warning("Token刷新服务已经在运行")
            return

        # 检查是否有必要的配置
        if not os.getenv('INOREADER_CLIENT_ID') or not os.getenv('INOREADER_CLIENT_SECRET'):
            logger.info("未配置Inoreader凭证，跳过token自动刷新服务")
            return

        self.running = True
        self._stop_event.clear()

        # 创建并启动后台线程
        self.refresh_thread = threading.Thread(
            target=self._refresh_loop,
            name="TokenRefreshService",
            daemon=True  # 设为守护线程，主进程结束时自动退出
        )
        self.refresh_thread.start()

        logger.info("Token自动刷新服务已启动")

    def stop(self):
        """停止token自动刷新服务"""
        if not self.running:
            return

        logger.info("正在停止Token自动刷新服务...")

        self.running = False
        self._stop_event.set()

        # 等待线程结束
        if self.refresh_thread and self.refresh_thread.is_alive():
            self.refresh_thread.join(timeout=5)

        logger.info("Token自动刷新服务已停止")

    def force_refresh(self):
        """立即强制刷新token"""
        logger.info("执行立即token刷新...")
        return self._refresh_token_if_needed()

    def get_status(self):
        """获取服务状态"""
        return {
            'running': self.running,
            'refresh_interval_hours': self.refresh_interval_hours,
            'thread_alive': self.refresh_thread.is_alive() if self.refresh_thread else False
        }


# 全局实例
_token_refresh_service: Optional[TokenRefreshService] = None


def get_token_refresh_service(refresh_interval_hours: int = 12) -> TokenRefreshService:
    """获取全局token刷新服务实例"""
    global _token_refresh_service

    if _token_refresh_service is None:
        _token_refresh_service = TokenRefreshService(refresh_interval_hours)

    return _token_refresh_service


def start_token_refresh_service(refresh_interval_hours: int = 12):
    """启动全局token刷新服务"""
    service = get_token_refresh_service(refresh_interval_hours)
    service.start()
    return service


def stop_token_refresh_service():
    """停止全局token刷新服务"""
    global _token_refresh_service

    if _token_refresh_service:
        _token_refresh_service.stop()