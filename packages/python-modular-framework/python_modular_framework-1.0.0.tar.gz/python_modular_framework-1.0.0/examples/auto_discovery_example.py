#!/usr/bin/env python3
"""
组件自动发现示例

演示框架的组件自动发现功能，包括：
- 自动扫描components目录
- 自动注册发现的组件
- 依赖关系解析
- 组件启动顺序优化

作者：开发团队
创建时间：2024-01-XX
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from framework.core.application import Application


def main():
    """主函数"""
    print("=== Python模块化框架 - 组件自动发现示例 ===\n")

    # 创建应用实例
    app = Application(name="auto-discovery-app", version="1.0.0")
    print(f"Created application: {app.name} v{app.version}")

    # 配置应用（不提供组件配置，让框架自动发现）
    config = {"app_name": "Auto Discovery Demo", "debug": True, "log_level": "INFO"}

    print("Configuring application...")
    app.configure(config)
    print("Application configured")

    # 手动触发组件发现
    print("\nDiscovering components...")
    discovered_components = app.discover_components()
    print(
        f"Discovered {len(discovered_components)} components: {discovered_components}"
    )

    # 显示组件注册表
    print("\nComponent Registry:")
    registry = app.get_component_registry()
    for component_name, metadata in registry.items():
        print(f"  {component_name}:")
        print(f"    Path: {metadata.get('path', 'N/A')}")
        print(f"    Class: {metadata.get('class', 'N/A')}")
        print(f"    Dependencies: {metadata.get('dependencies', [])}")
        print(f"    Enabled: {metadata.get('enabled', True)}")

    # 显示依赖关系图
    print("\nDependency Graph:")
    dependency_graph = app.get_dependency_graph()
    print(f"  Components: {dependency_graph['components']}")
    print(f"  Dependencies: {dependency_graph['dependencies']}")
    print(f"  Startup Order: {dependency_graph['startup_order']}")
    print(f"  Shutdown Order: {dependency_graph['shutdown_order']}")

    # 验证依赖关系
    validation = dependency_graph["validation"]
    if validation:
        print(f"  Validation Issues: {validation}")
    else:
        print("  Validation: All dependencies resolved successfully")

    # 启动应用
    print("\nStarting application...")
    try:
        app.start()
        print("Application started successfully")

        # 显示应用状态
        print(f"\nApplication status: {app.get_status()}")

        # 健康检查
        health = app.health_check()
        print(f"\nHealth check: {health['overall']}")
        for component_name, status in health["components"].items():
            print(f"  {component_name}: {status}")

        # 显示指标
        metrics = app.get_metrics()
        print(f"\nApplication metrics:")
        print(f"  Uptime: {metrics['application']['uptime']:.2f}s")
        print(f"  Components: {metrics['components']['total']}")
        print(f"  Registered: {metrics['components']['registered']}")

        # 停止应用
        print("\nStopping application...")
        app.stop()
        print("Application stopped")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    print("\n=== 示例完成 ===")
    return 0


if __name__ == "__main__":
    exit(main())
