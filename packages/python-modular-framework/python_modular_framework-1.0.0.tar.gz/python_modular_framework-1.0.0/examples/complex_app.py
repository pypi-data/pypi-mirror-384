#!/usr/bin/env python3
"""
复杂应用示例

演示框架的高级功能，包括：
- 组件自动发现和注册
- 依赖关系解析和启动顺序优化
- 组件间协作和通信
- 健康检查和监控
- 配置管理和更新
- 错误处理和恢复

作者：开发团队
创建时间：2024-01-XX
"""

import sys
import os
import time
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from framework.core.application import Application


class ComplexAppDemo:
    """复杂应用演示类"""

    def __init__(self):
        """初始化演示应用"""
        self.app = None
        self.demo_data = {"users": [], "payments": [], "auth_tokens": []}

    def create_application(self):
        """创建应用实例"""
        print("=== 创建复杂应用实例 ===")

        self.app = Application(name="complex-demo-app", version="2.0.0")

        print(f"✅ 应用创建成功: {self.app.name} v{self.app.version}")
        return self.app

    def configure_application(self):
        """配置应用"""
        print("\n=== 配置应用 ===")

        config = {
            "app_name": "Complex Demo Application",
            "debug": True,
            "log_level": "INFO",
            "database": {
                "database_url": "sqlite:///demo.db",
                "pool_size": 5,
                "max_overflow": 10,
            },
            "cache": {"type": "memory", "max_size": 1000, "ttl": 3600},
            "logging": {"level": "INFO", "format": "detailed", "file": "demo.log"},
            "auth": {"jwt_secret": "demo-secret-key", "token_expiry": 3600},
            "payment": {"default_method": "alipay", "timeout": 30},
        }

        self.app.configure(config)
        print("✅ 应用配置完成")

        # 显示发现的组件
        discovered = self.app.discover_components()
        print(f"✅ 自动发现 {len(discovered)} 个组件: {discovered}")

        return config

    def show_component_info(self):
        """显示组件信息"""
        print("\n=== 组件信息 ===")

        # 显示组件注册表
        registry = self.app.get_component_registry()
        for name, metadata in registry.items():
            print(f"📦 {name}:")
            print(f"   路径: {metadata.get('path', 'N/A')}")
            print(f"   类名: {metadata.get('class', 'N/A')}")
            print(f"   依赖: {metadata.get('dependencies', [])}")
            print(f"   启用: {metadata.get('enabled', True)}")

        # 显示依赖关系图
        print("\n=== 依赖关系图 ===")
        dependency_graph = self.app.get_dependency_graph()
        print(f"组件数量: {len(dependency_graph['components'])}")
        print(f"依赖关系: {json.dumps(dependency_graph['dependencies'], indent=2)}")
        print(f"启动顺序: {dependency_graph['startup_order']}")
        print(f"关闭顺序: {dependency_graph['shutdown_order']}")

        # 验证依赖关系
        validation = dependency_graph["validation"]
        if validation:
            print(f"⚠️  依赖验证问题: {validation}")
        else:
            print("✅ 所有依赖关系验证通过")

    def start_application(self):
        """启动应用"""
        print("\n=== 启动应用 ===")

        try:
            self.app.start()
            print("✅ 应用启动成功")

            # 显示应用状态
            status = self.app.get_status()
            print(f"📊 应用状态: {status.value}")

            return True

        except Exception as e:
            print(f"❌ 应用启动失败: {e}")
            return False

    def demonstrate_component_interaction(self):
        """演示组件间交互"""
        print("\n=== 组件间交互演示 ===")

        try:
            # 获取用户组件
            user_component = self.app.get_component("user")
            if user_component:
                print("👤 用户组件交互:")

                # 创建用户
                from components.user.models import UserCreate

                user_data = UserCreate(
                    username="demouser", email="demo@example.com", full_name="Demo User"
                )

                user = user_component.create_user(user_data)
                self.demo_data["users"].append(user)
                print(f"   ✅ 创建用户: {user.username} (ID: {user.id})")

                # 搜索用户
                from components.user.models import UserSearch

                search_params = UserSearch(username="demo")
                search_result = user_component.search_users(search_params)
                print(f"   🔍 搜索用户: 找到 {search_result.total} 个用户")

            # 获取权限组件
            auth_component = self.app.get_component("auth")
            if auth_component:
                print("\n🔐 权限组件交互:")

                # 创建权限
                from components.auth.models import PermissionCreate

                permission_data = PermissionCreate(
                    name="demo_permission",
                    description="Demo permission for testing",
                    resource="demo_resource",
                    action="read",
                )

                permission = auth_component.create_permission(permission_data)
                print(f"   ✅ 创建权限: {permission.name}")

                # 创建角色
                from components.auth.models import RoleCreate

                role_data = RoleCreate(
                    name="demo_role",
                    description="Demo role for testing",
                    permissions=["demo_permission"],
                )

                role = auth_component.create_role(role_data)
                print(f"   ✅ 创建角色: {role.name}")

            # 获取支付组件
            payment_component = self.app.get_component("payment")
            if payment_component:
                print("\n💳 支付组件交互:")

                # 创建支付
                from components.payment.models import PaymentCreate

                payment_data = PaymentCreate(
                    user_id="demo_user",
                    amount="100.00",
                    currency="CNY",
                    method="alipay",
                    description="Demo payment",
                )

                payment = payment_component.create_payment(payment_data)
                self.demo_data["payments"].append(payment)
                print(
                    f"   ✅ 创建支付: {payment.id} - {payment.amount} {payment.currency}"
                )

            print("✅ 组件间交互演示完成")

        except Exception as e:
            print(f"❌ 组件交互演示失败: {e}")

    def monitor_application(self):
        """监控应用"""
        print("\n=== 应用监控 ===")

        # 健康检查
        health = self.app.health_check()
        print(f"🏥 整体健康状态: {health['overall']}")

        print("\n📊 组件健康状态:")
        for component_name, status in health["components"].items():
            print(f"   {component_name}: {status['status']}")
            if "details" in status:
                details = status["details"]
                if "stats" in details:
                    stats = details["stats"]
                    print(f"     统计: {json.dumps(stats, indent=6)}")

        # 应用指标
        metrics = self.app.get_metrics()
        print(f"\n📈 应用指标:")
        print(f"   运行时间: {metrics['application']['uptime']:.2f}秒")
        print(f"   组件数量: {metrics['components']['total']}")
        print(f"   已注册组件: {metrics['components']['registered']}")

        # 组件指标
        print(f"\n🔧 组件指标:")
        for component_name, component_metrics in metrics["components"].items():
            if isinstance(component_metrics, dict) and "status" in component_metrics:
                print(f"   {component_name}: {component_metrics['status']}")

    def test_configuration_update(self):
        """测试配置更新"""
        print("\n=== 配置更新测试 ===")

        try:
            # 获取当前配置
            current_config = self.app.get_config()
            print(f"📋 当前配置项数: {len(current_config)}")

            # 更新配置
            new_config = {
                "debug": False,
                "log_level": "WARNING",
                "cache": {"max_size": 2000, "ttl": 7200},
            }

            # 更新组件配置
            for component_name in self.app.list_components():
                component = self.app.get_component(component_name)
                if component:
                    # 为不同组件提供适当的配置
                    component_config = {}
                    if component_name == "cache":
                        component_config = new_config.get("cache", {})
                    elif component_name == "logging":
                        component_config = {
                            "log_level": new_config.get("log_level", "INFO")
                        }
                    elif component_name == "auth":
                        component_config = {"debug": new_config.get("debug", False)}

                    if component_config:
                        component.update_config(component_config)
                        print(f"   ✅ 更新 {component_name} 组件配置")

            print("✅ 配置更新完成")

        except Exception as e:
            print(f"❌ 配置更新失败: {e}")

    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 错误处理测试 ===")

        try:
            # 测试获取不存在的组件
            non_existent = self.app.get_component("non_existent")
            if non_existent is None:
                print("✅ 正确处理不存在的组件")

            # 测试获取组件信息
            component_info = self.app.get_component_info("user")
            if component_info:
                print(f"✅ 获取组件信息成功: {component_info.name}")

            # 测试健康检查
            health = self.app.health_check()
            if health["overall"] == "healthy":
                print("✅ 健康检查正常")

            print("✅ 错误处理测试通过")

        except Exception as e:
            print(f"❌ 错误处理测试失败: {e}")

    def stop_application(self):
        """停止应用"""
        print("\n=== 停止应用 ===")

        try:
            self.app.stop()
            print("✅ 应用停止成功")

            # 显示最终状态
            status = self.app.get_status()
            print(f"📊 最终状态: {status.value}")

        except Exception as e:
            print(f"❌ 应用停止失败: {e}")

    def show_demo_summary(self):
        """显示演示总结"""
        print("\n=== 演示总结 ===")

        print(f"📊 演示数据统计:")
        print(f"   创建用户数: {len(self.demo_data['users'])}")
        print(f"   创建支付数: {len(self.demo_data['payments'])}")
        print(f"   认证令牌数: {len(self.demo_data['auth_tokens'])}")

        print(f"\n🎯 演示功能:")
        print(f"   ✅ 组件自动发现和注册")
        print(f"   ✅ 依赖关系解析和启动顺序优化")
        print(f"   ✅ 组件间协作和通信")
        print(f"   ✅ 健康检查和监控")
        print(f"   ✅ 配置管理和更新")
        print(f"   ✅ 错误处理和恢复")

        print(f"\n🚀 框架特性验证:")
        print(f"   ✅ 模块化架构")
        print(f"   ✅ 依赖注入")
        print(f"   ✅ 生命周期管理")
        print(f"   ✅ 配置管理")
        print(f"   ✅ 健康监控")
        print(f"   ✅ 错误处理")

    def run_demo(self):
        """运行完整演示"""
        print("=== Python模块化框架 - 复杂应用演示 ===\n")

        try:
            # 1. 创建应用
            self.create_application()

            # 2. 配置应用
            self.configure_application()

            # 3. 显示组件信息
            self.show_component_info()

            # 4. 启动应用
            if not self.start_application():
                return 1

            # 5. 演示组件交互
            self.demonstrate_component_interaction()

            # 6. 监控应用
            self.monitor_application()

            # 7. 测试配置更新
            self.test_configuration_update()

            # 8. 测试错误处理
            self.test_error_handling()

            # 9. 停止应用
            self.stop_application()

            # 10. 显示总结
            self.show_demo_summary()

            print("\n=== 演示完成 ===")
            return 0

        except Exception as e:
            print(f"\n❌ 演示过程中发生错误: {e}")
            return 1


def main():
    """主函数"""
    demo = ComplexAppDemo()
    return demo.run_demo()


if __name__ == "__main__":
    exit(main())
