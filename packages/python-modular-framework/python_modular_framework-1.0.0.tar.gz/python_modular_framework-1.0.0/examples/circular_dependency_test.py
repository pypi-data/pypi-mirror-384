#!/usr/bin/env python3
"""
循环依赖检测测试示例

演示框架的循环依赖检测功能，包括：
- 创建具有循环依赖的组件
- 检测循环依赖
- 报告循环依赖路径

作者：开发团队
创建时间：2024-01-XX
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from framework.core.application import Application
from framework.core.dependency_resolver import DependencyResolver


def test_circular_dependency_detection():
    """测试循环依赖检测功能"""
    print("=== 循环依赖检测测试 ===\n")

    # 创建依赖解析器
    resolver = DependencyResolver()

    # 添加组件，创建循环依赖
    # A -> B -> C -> A (循环依赖)
    resolver.add_component("component_a", None, ["component_b"], True, {})
    resolver.add_component("component_b", None, ["component_c"], True, {})
    resolver.add_component("component_c", None, ["component_a"], True, {})

    print("添加的组件依赖关系:")
    print("  component_a -> component_b")
    print("  component_b -> component_c")
    print("  component_c -> component_a")
    print("  预期结果: 检测到循环依赖 A -> B -> C -> A\n")

    # 测试循环依赖检测
    try:
        cycle = resolver.detect_circular_dependency()
        print("❌ 循环依赖检测失败 - 应该抛出异常但没有")
    except Exception as e:
        print(f"✅ 循环依赖检测成功: {e}")

    print("\n" + "=" * 50 + "\n")

    # 测试更复杂的循环依赖
    resolver.clear()

    # 创建更复杂的循环依赖: A -> B -> D, A -> C -> D, D -> A
    resolver.add_component(
        "component_a", None, ["component_b", "component_c"], True, {}
    )
    resolver.add_component("component_b", None, ["component_d"], True, {})
    resolver.add_component("component_c", None, ["component_d"], True, {})
    resolver.add_component("component_d", None, ["component_a"], True, {})

    print("更复杂的循环依赖关系:")
    print("  component_a -> component_b, component_c")
    print("  component_b -> component_d")
    print("  component_c -> component_d")
    print("  component_d -> component_a")
    print("  预期结果: 检测到循环依赖\n")

    try:
        cycle = resolver.detect_circular_dependency()
        print("❌ 循环依赖检测失败 - 应该抛出异常但没有")
    except Exception as e:
        print(f"✅ 循环依赖检测成功: {e}")

    print("\n" + "=" * 50 + "\n")

    # 测试无循环依赖的情况
    resolver.clear()

    # 创建无循环依赖的组件
    resolver.add_component("component_a", None, [], True, {})
    resolver.add_component("component_b", None, ["component_a"], True, {})
    resolver.add_component(
        "component_c", None, ["component_a", "component_b"], True, {}
    )
    resolver.add_component("component_d", None, ["component_c"], True, {})

    print("无循环依赖的组件关系:")
    print("  component_a (无依赖)")
    print("  component_b -> component_a")
    print("  component_c -> component_a, component_b")
    print("  component_d -> component_c")
    print("  预期结果: 无循环依赖，可以正常解析\n")

    try:
        cycle = resolver.detect_circular_dependency()
        print(f"✅ 无循环依赖检测成功: {cycle}")

        # 测试拓扑排序
        startup_order = resolver.get_startup_order()
        shutdown_order = resolver.get_shutdown_order()

        print(f"启动顺序: {startup_order}")
        print(f"关闭顺序: {shutdown_order}")

        # 验证启动顺序是否正确
        expected_startup = ["component_a", "component_b", "component_c", "component_d"]
        if startup_order == expected_startup:
            print("✅ 启动顺序正确")
        else:
            print(f"❌ 启动顺序错误，期望: {expected_startup}")

    except Exception as e:
        print(f"❌ 无循环依赖检测失败: {e}")


def test_application_circular_dependency():
    """测试应用中的循环依赖检测"""
    print("\n=== 应用循环依赖检测测试 ===\n")

    # 创建应用实例
    app = Application(name="circular-dependency-test", version="1.0.0")

    # 创建具有循环依赖的组件配置
    config = {
        "app_name": "Circular Dependency Test",
        "debug": True,
        "components": {
            "circular_a": {
                "enabled": True,
                "path": "test.components.circular_a",
                "class": "CircularAComponent",
                "dependencies": ["circular_b"],
            },
            "circular_b": {
                "enabled": True,
                "path": "test.components.circular_b",
                "class": "CircularBComponent",
                "dependencies": ["circular_a"],
            },
        },
    }

    print("配置循环依赖组件:")
    print("  circular_a -> circular_b")
    print("  circular_b -> circular_a")
    print("  预期结果: 应用启动时检测到循环依赖\n")

    try:
        app.configure(config)
        print("配置成功，现在尝试启动应用...")
        app.start()
        print("❌ 启动成功 - 应该检测到循环依赖但没有")
    except Exception as e:
        print(f"✅ 循环依赖检测成功: {e}")


def main():
    """主函数"""
    print("=== Python模块化框架 - 循环依赖检测测试 ===\n")

    # 测试依赖解析器的循环依赖检测
    test_circular_dependency_detection()

    # 测试应用中的循环依赖检测
    test_application_circular_dependency()

    print("\n=== 测试完成 ===")
    return 0


if __name__ == "__main__":
    exit(main())
