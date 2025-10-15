#!/usr/bin/env python3
"""
插件系统示例

演示框架的插件系统功能，包括：
- 插件加载和管理
- 插件生命周期管理
- 插件配置管理
- 插件依赖解析
- 插件与应用的集成

作者：开发团队
创建时间：2024-01-XX
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from framework.core.plugin import PluginManager, PluginStatus
from framework.core.application import Application


class PluginDemo:
    """插件演示类"""

    def __init__(self):
        self.app = Application(name="plugin-demo", version="1.0.0")
        self.plugin_manager = PluginManager(plugin_dirs=["example_plugins"])
        self.setup_application()

    def setup_application(self):
        """设置应用"""
        print("=== 设置应用 ===")

        # 配置应用
        config = {
            "app_name": "Plugin Demo Application",
            "debug": True,
            "log_level": "INFO",
        }

        self.app.configure(config)
        print("✅ 应用配置完成")

    def test_plugin_discovery(self):
        """测试插件发现"""
        print("\n=== 测试插件发现 ===")

        # 发现插件
        discovered_plugins = self.plugin_manager.discover_plugins()
        print(f"发现的插件数量: {len(discovered_plugins)}")

        for name, info in discovered_plugins.items():
            print(f"📦 插件: {name}")
            print(f"   版本: {info.version}")
            print(f"   描述: {info.description}")
            print(f"   作者: {info.author}")
            print(f"   依赖: {info.dependencies}")
            print(f"   可选依赖: {info.optional_dependencies}")
            print(f"   元数据: {info.metadata}")

        return discovered_plugins

    def test_plugin_loading(self, plugin_name: str, plugin_path: str):
        """测试插件加载"""
        print(f"\n=== 测试插件加载: {plugin_name} ===")

        # 加载插件
        success = self.plugin_manager.load_plugin(plugin_name, plugin_path)
        if success:
            print(f"✅ 插件 {plugin_name} 加载成功")

            # 获取插件信息
            plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
            if plugin_info:
                print(f"   插件信息: {plugin_info.name} v{plugin_info.version}")

            # 获取插件状态
            status = self.plugin_manager.get_plugin_status(plugin_name)
            print(f"   插件状态: {status.value if status else 'Unknown'}")

        else:
            print(f"❌ 插件 {plugin_name} 加载失败")

        return success

    def test_plugin_lifecycle(self, plugin_name: str):
        """测试插件生命周期"""
        print(f"\n=== 测试插件生命周期: {plugin_name} ===")

        # 初始化插件
        config = {
            "enabled": True,
            "max_notifications": 50,
            "notification_types": ["email", "sms"],
            "data_retention_days": 7,
            "metrics_interval": 30,
        }

        print("1. 初始化插件")
        success = self.plugin_manager.initialize_plugin(plugin_name, config)
        if success:
            print(f"   ✅ 插件 {plugin_name} 初始化成功")
        else:
            print(f"   ❌ 插件 {plugin_name} 初始化失败")
            return False

        # 启动插件
        print("2. 启动插件")
        success = self.plugin_manager.start_plugin(plugin_name)
        if success:
            print(f"   ✅ 插件 {plugin_name} 启动成功")
        else:
            print(f"   ❌ 插件 {plugin_name} 启动失败")
            return False

        # 获取插件实例并测试功能
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if plugin:
            print("3. 测试插件功能")
            self._test_plugin_functionality(plugin)

        # 健康检查
        print("4. 插件健康检查")
        health = self.plugin_manager.health_check()
        if plugin_name in health.get("plugins", {}):
            plugin_health = health["plugins"][plugin_name]
            print(f"   健康状态: {plugin_health.get('status', 'unknown')}")
            if "notifications" in plugin_health:
                print(f"   通知统计: {plugin_health['notifications']}")
            if "metrics" in plugin_health:
                print(f"   指标数据: {plugin_health['metrics']}")

        return True

    def _test_plugin_functionality(self, plugin):
        """测试插件功能"""
        plugin_name = plugin.info.name

        if plugin_name == "notification":
            # 测试通知插件功能
            print("   测试通知功能")

            # 发送通知
            notif_id1 = plugin.send_notification(
                "email", "user@example.com", "测试邮件通知"
            )
            notif_id2 = plugin.send_notification("sms", "+1234567890", "测试短信通知")
            notif_id3 = plugin.send_notification("push", "device123", "测试推送通知")

            print(f"   发送了3个通知: {notif_id1}, {notif_id2}, {notif_id3}")

            # 等待通知处理
            time.sleep(2)

            # 获取通知统计
            stats = plugin.get_notification_stats()
            print(f"   通知统计: {stats}")

            # 列出通知
            notifications = plugin.list_notifications()
            print(f"   通知列表: {len(notifications)} 个通知")

        elif plugin_name == "analytics":
            # 测试分析插件功能
            print("   测试分析功能")

            # 跟踪事件
            event_id1 = plugin.track_event(
                "user_login", {"user_id": "user123", "ip": "192.168.1.1"}
            )
            event_id2 = plugin.track_event(
                "page_view", {"page": "/dashboard", "duration": 30}
            )
            event_id3 = plugin.track_event("user_logout", {"user_id": "user123"})

            print(f"   跟踪了3个事件: {event_id1}, {event_id2}, {event_id3}")

            # 获取指标
            metrics = plugin.get_metrics()
            print(f"   指标数据: {metrics}")

            # 导出数据
            json_data = plugin.export_data("json")
            print(f"   导出JSON数据: {len(json_data)} 字符")

    def test_plugin_dependencies(self):
        """测试插件依赖"""
        print("\n=== 测试插件依赖 ===")

        # 加载分析插件（依赖通知插件）
        analytics_plugin = self.plugin_manager.get_plugin("analytics")
        if analytics_plugin:
            print("分析插件依赖:")
            for dep in analytics_plugin.info.dependencies:
                dep_plugin = self.plugin_manager.get_plugin(dep)
                if dep_plugin:
                    print(f"   ✅ {dep}: 已加载")
                else:
                    print(f"   ❌ {dep}: 未加载")

    def test_plugin_stop(self, plugin_name: str):
        """测试插件停止"""
        print(f"\n=== 测试插件停止: {plugin_name} ===")

        # 停止插件
        success = self.plugin_manager.stop_plugin(plugin_name)
        if success:
            print(f"✅ 插件 {plugin_name} 停止成功")
        else:
            print(f"❌ 插件 {plugin_name} 停止失败")

        # 获取插件状态
        status = self.plugin_manager.get_plugin_status(plugin_name)
        print(f"插件状态: {status.value if status else 'Unknown'}")

    def test_plugin_unload(self, plugin_name: str):
        """测试插件卸载"""
        print(f"\n=== 测试插件卸载: {plugin_name} ===")

        # 卸载插件
        success = self.plugin_manager.unload_plugin(plugin_name)
        if success:
            print(f"✅ 插件 {plugin_name} 卸载成功")
        else:
            print(f"❌ 插件 {plugin_name} 卸载失败")

        # 检查插件是否还存在
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if plugin:
            print(f"❌ 插件 {plugin_name} 仍然存在")
        else:
            print(f"✅ 插件 {plugin_name} 已完全移除")

    def show_plugin_status(self):
        """显示插件状态"""
        print("\n=== 插件状态 ===")

        plugins = self.plugin_manager.list_plugins()
        print(f"已加载插件数量: {len(plugins)}")

        for name in plugins:
            plugin = self.plugin_manager.get_plugin(name)
            status = self.plugin_manager.get_plugin_status(name)

            if plugin and status:
                print(f"📦 {name}:")
                print(f"   状态: {status.value}")
                print(f"   版本: {plugin.info.version}")
                print(f"   描述: {plugin.info.description}")

    def run_demo(self):
        """运行完整演示"""
        print("=== Python模块化框架 - 插件系统演示 ===\n")

        try:
            # 启动应用
            self.app.start()
            print("✅ 应用启动成功")

            # 测试插件发现
            discovered_plugins = self.test_plugin_discovery()

            if not discovered_plugins:
                print("❌ 没有发现任何插件")
                return 1

            # 测试通知插件
            notification_plugin_path = "example_plugins/notification_plugin.py"
            if self.test_plugin_loading("notification", notification_plugin_path):
                self.test_plugin_lifecycle("notification")

            # 测试分析插件
            analytics_plugin_path = "example_plugins/analytics_plugin.py"
            if self.test_plugin_loading("analytics", analytics_plugin_path):
                self.test_plugin_lifecycle("analytics")

            # 测试插件依赖
            self.test_plugin_dependencies()

            # 显示插件状态
            self.show_plugin_status()

            # 等待一段时间让插件运行
            print("\n=== 等待插件运行 ===")
            time.sleep(3)

            # 停止插件
            self.test_plugin_stop("analytics")
            self.test_plugin_stop("notification")

            # 卸载插件
            self.test_plugin_unload("analytics")
            self.test_plugin_unload("notification")

            # 停止应用
            self.app.stop()
            print("✅ 应用停止成功")

            print("\n=== 演示完成 ===")
            return 0

        except Exception as e:
            print(f"\n❌ 演示过程中发生错误: {e}")
            import traceback

            traceback.print_exc()
            return 1


def main():
    """主函数"""
    demo = PluginDemo()
    return demo.run_demo()


if __name__ == "__main__":
    exit(main())
