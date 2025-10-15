"""
循环依赖测试组件 A

该组件用于测试框架的循环依赖检测功能。
与 CircularBComponent 形成循环依赖关系。

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import Dict, Any
from framework.interfaces.component import ComponentInterface, ComponentStatus, ComponentInfo


class CircularAComponent(ComponentInterface):
    """
    循环依赖测试组件 A
    
    该组件依赖 CircularBComponent，形成循环依赖关系用于测试。
    """

    def __init__(self, name: str = "circular_a"):
        """
        初始化组件A
        
        参数:
            name: 组件名称
        """
        self._name = name
        self._version = "1.0.0"
        self._description = "循环依赖测试组件A"
        self._status = ComponentStatus.UNINITIALIZED
        self._config = {}
        self._dependency_b = None

    @property
    def name(self) -> str:
        """
        获取组件名称
        
        返回:
            str: 组件名称
        """
        return self._name

    @property
    def version(self) -> str:
        """
        获取组件版本
        
        返回:
            str: 组件版本号
        """
        return self._version

    @property
    def description(self) -> str:
        """
        获取组件描述
        
        返回:
            str: 组件描述信息
        """
        return self._description

    @property
    def dependencies(self) -> list:
        """
        获取组件依赖列表
        
        返回:
            list: 依赖的组件名称列表
        """
        return ["circular_b"]

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化组件
        
        参数:
            config: 组件配置参数
        """
        self._config = config
        self._status = ComponentStatus.INITIALIZED
        print(f"组件 {self._name} 已初始化")

    def start(self) -> None:
        """
        启动组件
        
        启动组件A，设置状态为运行中。
        """
        self._status = ComponentStatus.RUNNING
        print(f"组件 {self._name} 已启动")

    def stop(self) -> None:
        """
        停止组件
        
        停止组件A，设置状态为已停止。
        """
        self._status = ComponentStatus.STOPPED
        print(f"组件 {self._name} 已停止")

    def get_status(self) -> ComponentStatus:
        """
        获取组件状态
        
        返回:
            ComponentStatus: 组件当前状态
        """
        return self._status

    def get_info(self) -> ComponentInfo:
        """
        获取组件详细信息
        
        返回:
            ComponentInfo: 组件信息对象
        """
        return ComponentInfo(
            name=self._name,
            version=self._version,
            description=self._description,
            dependencies=self.dependencies,
            status=self._status,
            config=self._config,
            metadata={"type": "test_component"}
        )

    def get_config(self) -> Dict[str, Any]:
        """
        获取组件当前配置
        
        返回:
            Dict[str, Any]: 组件配置字典
        """
        return self._config

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新组件配置
        
        参数:
            config: 新的配置参数
        """
        self._config.update(config)

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        返回:
            Dict[str, Any]: 健康检查结果
        """
        is_healthy = self._status == ComponentStatus.RUNNING
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "message": f"组件 {self._name} 状态: {self._status.value}",
            "details": {"status": self._status.value}
        }

    def set_dependency_b(self, component_b):
        """
        设置对组件B的依赖
        
        参数:
            component_b: CircularBComponent 实例
        """
        self._dependency_b = component_b
