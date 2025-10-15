#!/usr/bin/env python3
"""
通知插件示例

演示插件系统的功能，包括：
- 插件接口实现
- 插件生命周期管理
- 插件配置管理
- 插件与框架的集成

作者：开发团队
创建时间：2024-01-XX
"""

import time
import threading
from typing import Dict, Any, List
from framework.core.plugin import BasePlugin, PluginInfo, PluginStatus


class NotificationPlugin(BasePlugin):
    """通知插件"""

    def __init__(self):
        """初始化通知插件"""
        info = PluginInfo(
            name="notification",
            version="1.0.0",
            description="提供通知功能的插件",
            author="开发团队",
            dependencies=[],
            optional_dependencies=["logging"],
            config_schema={
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": True},
                    "max_notifications": {"type": "integer", "default": 100},
                    "notification_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["email", "sms", "push"],
                    },
                },
            },
            metadata={
                "category": "communication",
                "tags": ["notification", "messaging", "alert"],
            },
        )
        super().__init__(info)

        self._notifications: List[Dict[str, Any]] = []
        self._notification_thread = None
        self._running = False

    def _on_initialize(self, config: Dict[str, Any]) -> None:
        """插件初始化回调"""
        print(f"[{self.info.name}] 初始化通知插件")

        # 验证配置
        if not config.get("enabled", True):
            print(f"[{self.info.name}] 通知插件已禁用")
            return

        max_notifications = config.get("max_notifications", 100)
        notification_types = config.get("notification_types", ["email", "sms", "push"])

        print(f"[{self.info.name}] 最大通知数: {max_notifications}")
        print(f"[{self.info.name}] 支持的通知类型: {notification_types}")

    def _on_start(self) -> None:
        """插件启动回调"""
        print(f"[{self.info.name}] 启动通知插件")

        # 启动通知处理线程
        self._running = True
        self._notification_thread = threading.Thread(target=self._process_notifications)
        self._notification_thread.daemon = True
        self._notification_thread.start()

        print(f"[{self.info.name}] 通知处理线程已启动")

    def _on_stop(self) -> None:
        """插件停止回调"""
        print(f"[{self.info.name}] 停止通知插件")

        # 停止通知处理线程
        self._running = False
        if self._notification_thread and self._notification_thread.is_alive():
            self._notification_thread.join(timeout=5)

        print(f"[{self.info.name}] 通知插件已停止")

    def _on_config_update(self, config: Dict[str, Any]) -> None:
        """配置更新回调"""
        print(f"[{self.info.name}] 更新配置: {config}")

    def _process_notifications(self) -> None:
        """处理通知的后台线程"""
        while self._running:
            try:
                # 处理待发送的通知
                notifications_to_send = [
                    n for n in self._notifications if n.get("status") == "pending"
                ]

                for notification in notifications_to_send:
                    self._send_notification(notification)

                time.sleep(1)  # 每秒检查一次

            except Exception as e:
                print(f"[{self.info.name}] 通知处理线程错误: {e}")
                time.sleep(5)  # 出错时等待5秒再重试

    def _send_notification(self, notification: Dict[str, Any]) -> None:
        """发送通知"""
        try:
            notification_type = notification.get("type", "email")
            recipient = notification.get("recipient", "")
            message = notification.get("message", "")

            # 模拟发送通知
            print(
                f"[{self.info.name}] 发送{notification_type}通知给 {recipient}: {message}"
            )

            # 更新通知状态
            notification["status"] = "sent"
            notification["sent_at"] = time.time()

        except Exception as e:
            print(f"[{self.info.name}] 发送通知失败: {e}")
            notification["status"] = "failed"
            notification["error"] = str(e)

    def send_notification(
        self,
        notification_type: str,
        recipient: str,
        message: str,
        priority: str = "normal",
    ) -> str:
        """
        发送通知

        Args:
            notification_type (str): 通知类型
            recipient (str): 接收者
            message (str): 消息内容
            priority (str): 优先级

        Returns:
            str: 通知ID
        """
        notification_id = f"notif_{int(time.time() * 1000000)}"

        notification = {
            "id": notification_id,
            "type": notification_type,
            "recipient": recipient,
            "message": message,
            "priority": priority,
            "status": "pending",
            "created_at": time.time(),
        }

        self._notifications.append(notification)
        print(f"[{self.info.name}] 创建通知: {notification_id}")

        return notification_id

    def get_notification(self, notification_id: str) -> Dict[str, Any]:
        """
        获取通知信息

        Args:
            notification_id (str): 通知ID

        Returns:
            Dict[str, Any]: 通知信息
        """
        for notification in self._notifications:
            if notification["id"] == notification_id:
                return notification.copy()
        return {}

    def list_notifications(self, status: str = None) -> List[Dict[str, Any]]:
        """
        列出通知

        Args:
            status (str): 状态过滤

        Returns:
            List[Dict[str, Any]]: 通知列表
        """
        if status:
            return [n for n in self._notifications if n.get("status") == status]
        return [n.copy() for n in self._notifications]

    def get_notification_stats(self) -> Dict[str, Any]:
        """
        获取通知统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        total = len(self._notifications)
        pending = len([n for n in self._notifications if n.get("status") == "pending"])
        sent = len([n for n in self._notifications if n.get("status") == "sent"])
        failed = len([n for n in self._notifications if n.get("status") == "failed"])

        return {
            "total": total,
            "pending": pending,
            "sent": sent,
            "failed": failed,
            "success_rate": (sent / total * 100) if total > 0 else 0,
        }

    def health_check(self) -> Dict[str, Any]:
        """插件健康检查"""
        base_health = super().health_check()

        # 添加插件特定的健康检查
        base_health.update(
            {
                "notifications": self.get_notification_stats(),
                "thread_running": self._notification_thread
                and self._notification_thread.is_alive(),
                "running": self._running,
            }
        )

        return base_health


# 插件入口点
def create_plugin():
    """创建插件实例"""
    return NotificationPlugin()
