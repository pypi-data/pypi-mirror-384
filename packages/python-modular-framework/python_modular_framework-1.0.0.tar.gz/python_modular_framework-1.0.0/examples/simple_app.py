"""
简单应用示例
- 演示如何使用框架创建简单的应用
- 展示组件注册和基本功能

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from framework import Application
from framework.interfaces.component import (
    ComponentInterface,
    ComponentStatus,
    ComponentInfo,
)
from typing import Dict, Any, List


class SimpleComponent(ComponentInterface):
    """简单组件示例"""

    def __init__(self, name: str):
        """
        初始化简单组件

        Args:
            name (str): 组件名称
        """
        self._name = name
        self._version = "1.0.0"
        self._description = f"Simple component: {name}"
        self._dependencies = []
        self._status = ComponentStatus.UNINITIALIZED
        self._config = {}

    @property
    def name(self) -> str:
        """获取组件名称"""
        return self._name

    @property
    def version(self) -> str:
        """获取组件版本"""
        return self._version

    @property
    def description(self) -> str:
        """获取组件描述"""
        return self._description

    @property
    def dependencies(self) -> List[str]:
        """获取组件依赖"""
        return self._dependencies

    def initialize(self, config: Dict[str, Any]) -> None:
        """初始化组件"""
        self._config = config
        self._status = ComponentStatus.INITIALIZED
        print(f"Component '{self._name}' initialized with config: {config}")

    def start(self) -> None:
        """启动组件"""
        self._status = ComponentStatus.RUNNING
        print(f"Component '{self._name}' started")

    def stop(self) -> None:
        """停止组件"""
        self._status = ComponentStatus.STOPPED
        print(f"Component '{self._name}' stopped")

    def get_status(self) -> ComponentStatus:
        """获取组件状态"""
        return self._status

    def get_info(self) -> ComponentInfo:
        """获取组件信息"""
        return ComponentInfo(
            name=self._name,
            version=self._version,
            description=self._description,
            dependencies=self._dependencies,
            status=self._status,
            config=self._config,
            metadata={},
        )

    def get_config(self) -> Dict[str, Any]:
        """获取组件配置"""
        return self._config

    def update_config(self, config: Dict[str, Any]) -> None:
        """更新组件配置"""
        self._config.update(config)

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": (
                "healthy" if self._status == ComponentStatus.RUNNING else "unhealthy"
            ),
            "message": f"Component {self._name} is {self._status.value}",
            "details": {"status": self._status.value, "config": self._config},
        }


def main():
    """主函数"""
    print("=== Python模块化框架简单示例 ===")

    # 创建应用
    app = Application(name="simple-app", version="1.0.0")
    print(f"Created application: {app.name} v{app.version}")

    # 创建组件
    component1 = SimpleComponent("component-1")
    component2 = SimpleComponent("component-2")

    # 注册组件
    app.register_component("comp1", component1)
    app.register_component("comp2", component2)
    print(f"Registered components: {app.list_components()}")

    # 配置应用
    config = {
        "comp1": {"setting1": "value1", "setting2": 42},
        "comp2": {"setting1": "value2", "setting2": 84},
        "app": {"debug": True, "log_level": "INFO"},
    }
    app.configure(config)
    print("Application configured")

    # 启动应用
    print("\nStarting application...")
    app.start()
    print(f"Application status: {app.get_status()}")

    # 健康检查
    health = app.health_check()
    print(f"\nHealth check: {health['overall']}")
    for comp_name, comp_health in health["components"].items():
        print(f"  {comp_name}: {comp_health['status']}")

    # 获取指标
    metrics = app.get_metrics()
    print(f"\nApplication metrics:")
    print(f"  Uptime: {metrics['application']['uptime']:.2f}s")
    print(f"  Components: {metrics['components']['total']}")

    # 停止应用
    print("\nStopping application...")
    app.stop()
    print(f"Application status: {app.get_status()}")

    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    main()
