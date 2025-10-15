#!/usr/bin/env python3
"""
分析插件示例

演示插件系统的功能，包括：
- 插件接口实现
- 插件生命周期管理
- 插件配置管理
- 插件与框架的集成

作者：开发团队
创建时间：2024-01-XX
"""

import time
import json
from typing import Dict, Any, List
from framework.core.plugin import BasePlugin, PluginInfo, PluginStatus


class AnalyticsPlugin(BasePlugin):
    """分析插件"""

    def __init__(self):
        """初始化分析插件"""
        info = PluginInfo(
            name="analytics",
            version="1.0.0",
            description="提供数据分析功能的插件",
            author="开发团队",
            dependencies=["notification"],  # 依赖通知插件
            optional_dependencies=["logging"],
            config_schema={
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": True},
                    "data_retention_days": {"type": "integer", "default": 30},
                    "metrics_interval": {"type": "integer", "default": 60},
                    "export_formats": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["json", "csv"],
                    },
                },
            },
            metadata={
                "category": "analytics",
                "tags": ["analytics", "metrics", "reporting"],
            },
        )
        super().__init__(info)

        self._events: List[Dict[str, Any]] = []
        self._metrics: Dict[str, Any] = {}
        self._start_time = time.time()

    def _on_initialize(self, config: Dict[str, Any]) -> None:
        """插件初始化回调"""
        print(f"[{self.info.name}] 初始化分析插件")

        # 验证配置
        if not config.get("enabled", True):
            print(f"[{self.info.name}] 分析插件已禁用")
            return

        data_retention_days = config.get("data_retention_days", 30)
        metrics_interval = config.get("metrics_interval", 60)
        export_formats = config.get("export_formats", ["json", "csv"])

        print(f"[{self.info.name}] 数据保留天数: {data_retention_days}")
        print(f"[{self.info.name}] 指标收集间隔: {metrics_interval}秒")
        print(f"[{self.info.name}] 支持的导出格式: {export_formats}")

    def _on_start(self) -> None:
        """插件启动回调"""
        print(f"[{self.info.name}] 启动分析插件")

        # 初始化指标
        self._metrics = {
            "events_total": 0,
            "events_by_type": {},
            "events_by_hour": {},
            "start_time": self._start_time,
            "last_updated": time.time(),
        }

        print(f"[{self.info.name}] 分析插件已启动")

    def _on_stop(self) -> None:
        """插件停止回调"""
        print(f"[{self.info.name}] 停止分析插件")

        # 保存最终指标
        self._update_metrics()
        print(f"[{self.info.name}] 分析插件已停止")

    def _on_config_update(self, config: Dict[str, Any]) -> None:
        """配置更新回调"""
        print(f"[{self.info.name}] 更新配置: {config}")

    def track_event(self, event_type: str, event_data: Dict[str, Any] = None) -> str:
        """
        跟踪事件

        Args:
            event_type (str): 事件类型
            event_data (Dict[str, Any]): 事件数据

        Returns:
            str: 事件ID
        """
        event_id = f"event_{int(time.time() * 1000000)}"
        current_time = time.time()

        event = {
            "id": event_id,
            "type": event_type,
            "data": event_data or {},
            "timestamp": current_time,
            "hour": int(current_time // 3600) * 3600,  # 按小时分组
        }

        self._events.append(event)

        # 更新指标
        self._metrics["events_total"] += 1
        self._metrics["events_by_type"][event_type] = (
            self._metrics["events_by_type"].get(event_type, 0) + 1
        )
        self._metrics["events_by_hour"][event["hour"]] = (
            self._metrics["events_by_hour"].get(event["hour"], 0) + 1
        )
        self._metrics["last_updated"] = current_time

        print(f"[{self.info.name}] 跟踪事件: {event_type} ({event_id})")

        return event_id

    def get_metrics(self) -> Dict[str, Any]:
        """
        获取指标数据

        Returns:
            Dict[str, Any]: 指标数据
        """
        self._update_metrics()
        return self._metrics.copy()

    def get_events(
        self, event_type: str = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取事件列表

        Args:
            event_type (str): 事件类型过滤
            limit (int): 限制数量

        Returns:
            List[Dict[str, Any]]: 事件列表
        """
        events = self._events.copy()

        if event_type:
            events = [e for e in events if e["type"] == event_type]

        # 按时间倒序排列
        events.sort(key=lambda x: x["timestamp"], reverse=True)

        return events[:limit]

    def export_data(self, format_type: str = "json") -> str:
        """
        导出数据

        Args:
            format_type (str): 导出格式

        Returns:
            str: 导出数据
        """
        if format_type == "json":
            data = {
                "events": self._events,
                "metrics": self._metrics,
                "export_time": time.time(),
            }
            return json.dumps(data, indent=2, ensure_ascii=False)

        elif format_type == "csv":
            # 简化的CSV导出
            csv_lines = ["event_id,type,timestamp,data"]
            for event in self._events:
                data_str = json.dumps(event["data"], ensure_ascii=False)
                csv_lines.append(
                    f"{event['id']},{event['type']},{event['timestamp']},\"{data_str}\""
                )
            return "\n".join(csv_lines)

        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def _update_metrics(self) -> None:
        """更新指标"""
        current_time = time.time()
        uptime = current_time - self._start_time

        self._metrics.update(
            {
                "uptime": uptime,
                "events_per_minute": (
                    (self._metrics["events_total"] / (uptime / 60)) if uptime > 0 else 0
                ),
                "last_updated": current_time,
            }
        )

    def health_check(self) -> Dict[str, Any]:
        """插件健康检查"""
        base_health = super().health_check()

        # 添加插件特定的健康检查
        self._update_metrics()
        base_health.update(
            {
                "metrics": self._metrics,
                "events_count": len(self._events),
                "uptime": time.time() - self._start_time,
            }
        )

        return base_health


# 插件入口点
def create_plugin():
    """创建插件实例"""
    return AnalyticsPlugin()
