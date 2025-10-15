"""
依赖解析器实现
- 提供组件依赖关系解析和循环依赖检测
- 支持拓扑排序算法确定组件启动顺序
- 实现组件自动发现功能

主要功能：
- 依赖关系管理
- 循环依赖检测
- 拓扑排序
- 组件自动发现

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import os
import importlib
from typing import Any, Dict, List, Set, Optional, Type
from dataclasses import dataclass
from framework.interfaces.component import ComponentInterface
from framework.interfaces.application import DependencyResolutionError


@dataclass
class ComponentDependency:
    """组件依赖信息"""

    name: str
    dependencies: List[str]
    component_type: Type[ComponentInterface]
    is_required: bool = True
    metadata: Dict[str, Any] = None


class DependencyResolver:
    """
    依赖解析器

    负责解析组件间的依赖关系，检测循环依赖，
    并提供拓扑排序来确定正确的组件启动顺序。
    """

    def __init__(self):
        """
        初始化依赖解析器

        创建内部存储结构和状态变量。
        """
        self._dependencies: Dict[str, List[str]] = {}
        self._components: Dict[str, ComponentDependency] = {}
        self._visited: Set[str] = set()
        self._recursion_stack: Set[str] = set()
        self._sorted_components: List[str] = []

    def add_component(
        self,
        name: str,
        component_type: Type[ComponentInterface],
        dependencies: List[str] = None,
        is_required: bool = True,
        metadata: Dict[str, Any] = None,
    ) -> None:
        """
        添加组件依赖信息

        Args:
            name (str): 组件名称
            component_type (Type[ComponentInterface]): 组件类型
            dependencies (List[str]): 依赖的组件名称列表
            is_required (bool): 是否为必需组件
            metadata (Dict[str, Any]): 组件元数据
        """
        dependencies = dependencies or []

        self._components[name] = ComponentDependency(
            name=name,
            dependencies=dependencies,
            component_type=component_type,
            is_required=is_required,
            metadata=metadata or {},
        )

        self._dependencies[name] = dependencies.copy()

    def remove_component(self, name: str) -> None:
        """
        移除组件依赖信息

        Args:
            name (str): 组件名称
        """
        if name in self._components:
            del self._components[name]
        if name in self._dependencies:
            del self._dependencies[name]

        # 从其他组件的依赖中移除
        for component_name, deps in self._dependencies.items():
            if name in deps:
                deps.remove(name)

    def get_component_dependencies(self, name: str) -> List[str]:
        """
        获取组件的依赖列表

        Args:
            name (str): 组件名称

        Returns:
            List[str]: 依赖的组件名称列表
        """
        return self._dependencies.get(name, []).copy()

    def get_dependents(self, name: str) -> List[str]:
        """
        获取依赖指定组件的组件列表

        Args:
            name (str): 组件名称

        Returns:
            List[str]: 依赖该组件的组件名称列表
        """
        dependents = []
        for component_name, deps in self._dependencies.items():
            if name in deps:
                dependents.append(component_name)
        return dependents

    def detect_circular_dependency(self) -> List[str]:
        """
        检测循环依赖

        使用深度优先搜索算法检测组件间的循环依赖关系。

        Returns:
            List[str]: 循环依赖路径，如果无循环依赖则返回空列表

        Raises:
            DependencyResolutionError: 发现循环依赖时抛出异常
        """
        self._visited.clear()
        self._recursion_stack.clear()

        for component in self._dependencies:
            if component not in self._visited:
                cycle = self._dfs_detect_cycle(component)
                if cycle:
                    cycle_str = " -> ".join(cycle)
                    raise DependencyResolutionError(
                        "circular_dependency",
                        f"Circular dependency detected: {cycle_str}",
                    )

        return []

    def _dfs_detect_cycle(self, component: str) -> List[str]:
        """
        深度优先搜索检测循环依赖

        Args:
            component (str): 当前组件名称

        Returns:
            List[str]: 循环路径，如果无循环则返回空列表
        """
        if component in self._recursion_stack:
            return [component]  # 发现循环

        if component in self._visited:
            return []  # 已访问过，无循环

        self._visited.add(component)
        self._recursion_stack.add(component)

        # 检查所有依赖
        for dependency in self._dependencies.get(component, []):
            cycle = self._dfs_detect_cycle(dependency)
            if cycle:
                return [component] + cycle

        self._recursion_stack.remove(component)
        return []

    def topological_sort(self) -> List[str]:
        """
        拓扑排序

        使用Kahn算法对组件进行拓扑排序，确定正确的启动顺序。

        Returns:
            List[str]: 按依赖顺序排序的组件名称列表

        Raises:
            DependencyResolutionError: 无法解析依赖关系时抛出异常
        """
        # 检测循环依赖
        self.detect_circular_dependency()

        # 计算入度（每个组件依赖多少个其他组件）
        in_degree = {
            component: len(deps) for component, deps in self._dependencies.items()
        }

        # 找到所有入度为0的组件（没有依赖的组件）
        queue = [component for component, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # 按组件名称排序，确保结果的一致性
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            # 减少依赖当前组件的其他组件的入度
            for component, deps in self._dependencies.items():
                if current in deps and component in in_degree:
                    in_degree[component] -= 1
                    if in_degree[component] == 0:
                        queue.append(component)

        # 检查是否所有组件都被处理
        if len(result) != len(self._dependencies):
            remaining = set(self._dependencies.keys()) - set(result)
            raise DependencyResolutionError(
                "dependency_resolution",
                f"Cannot resolve dependencies for components: {', '.join(remaining)}",
            )

        self._sorted_components = result
        return result.copy()

    def get_startup_order(self) -> List[str]:
        """
        获取组件启动顺序

        返回按依赖关系排序的组件启动顺序。

        Returns:
            List[str]: 组件启动顺序列表
        """
        if not self._sorted_components:
            self.topological_sort()
        return self._sorted_components.copy()

    def get_shutdown_order(self) -> List[str]:
        """
        获取组件关闭顺序

        返回与启动顺序相反的组件关闭顺序。

        Returns:
            List[str]: 组件关闭顺序列表
        """
        startup_order = self.get_startup_order()
        return list(reversed(startup_order))

    def validate_dependencies(self) -> Dict[str, List[str]]:
        """
        验证依赖关系

        检查所有依赖的组件是否都存在。

        Returns:
            Dict[str, List[str]]: 验证结果，键为组件名称，值为缺失的依赖列表
        """
        validation_result = {}

        for component, deps in self._dependencies.items():
            missing_deps = []
            for dep in deps:
                if dep not in self._dependencies:
                    missing_deps.append(dep)

            if missing_deps:
                validation_result[component] = missing_deps

        return validation_result

    def get_dependency_graph(self) -> Dict[str, Any]:
        """
        获取依赖关系图

        返回完整的依赖关系图信息。

        Returns:
            Dict[str, Any]: 依赖关系图数据
        """
        return {
            "components": list(self._dependencies.keys()),
            "dependencies": self._dependencies.copy(),
            "startup_order": self.get_startup_order(),
            "shutdown_order": self.get_shutdown_order(),
            "validation": self.validate_dependencies(),
        }

    def clear(self) -> None:
        """
        清空依赖解析器

        移除所有组件依赖信息。
        """
        self._dependencies.clear()
        self._components.clear()
        self._visited.clear()
        self._recursion_stack.clear()
        self._sorted_components.clear()


class ComponentDiscovery:
    """
    组件自动发现器

    负责自动发现和加载组件，支持基于配置的组件发现和自动扫描。
    """

    def __init__(self, base_path: str = "components"):
        """
        初始化组件发现器

        Args:
            base_path (str): 组件基础路径
        """
        self.base_path = base_path
        self._discovered_components: Dict[str, Type[ComponentInterface]] = {}
        self._component_registry: Dict[str, Dict[str, Any]] = {}

    def discover_components(
        self, component_configs: Dict[str, Any] = None
    ) -> Dict[str, Type[ComponentInterface]]:
        """
        发现组件

        根据配置自动发现和加载组件，如果没有配置则自动扫描components目录。

        Args:
            component_configs (Dict[str, Any]): 组件配置，如果为None则自动扫描

        Returns:
            Dict[str, Type[ComponentInterface]]: 发现的组件类型字典
        """
        discovered = {}

        if component_configs is None:
            # 自动扫描components目录
            component_configs = self._auto_scan_components()

        for component_name, config in component_configs.items():
            if not config.get("enabled", True):
                continue

            try:
                component_type = self._load_component(component_name, config)
                if component_type:
                    discovered[component_name] = component_type
                    self._discovered_components[component_name] = component_type
                    self._component_registry[component_name] = config
            except Exception as e:
                print(f"Failed to discover component '{component_name}': {e}")
                continue

        return discovered

    def _auto_scan_components(self) -> Dict[str, Dict[str, Any]]:
        """
        自动扫描components目录发现组件

        Returns:
            Dict[str, Dict[str, Any]]: 发现的组件配置字典
        """
        component_configs = {}

        try:
            # 扫描components目录
            components_dir = os.path.join(os.getcwd(), self.base_path)
            if not os.path.exists(components_dir):
                print(f"Components directory not found: {components_dir}")
                return component_configs

            # 递归遍历components目录下的所有子目录
            self._scan_directory_recursive(
                components_dir, self.base_path, component_configs
            )

        except Exception as e:
            print(f"Failed to auto-scan components: {e}")

        return component_configs

    def _scan_directory_recursive(
        self,
        directory: str,
        base_path: str,
        component_configs: Dict[str, Dict[str, Any]],
    ) -> None:
        """
        递归扫描目录查找组件

        Args:
            directory (str): 要扫描的目录
            base_path (str): 基础路径
            component_configs (Dict[str, Dict[str, Any]]): 组件配置字典
        """
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path) and not item.startswith("__"):
                    # 检查是否有component.py文件
                    component_file = os.path.join(item_path, "component.py")
                    if os.path.exists(component_file):
                        # 计算相对路径
                        rel_path = os.path.relpath(
                            item_path, os.path.join(os.getcwd(), self.base_path)
                        )
                        rel_path = rel_path.replace(os.sep, ".")

                        # 生成组件名称（使用目录名）
                        component_name = item

                        # 生成组件配置
                        component_config = {
                            "enabled": True,
                            "path": f"{base_path}.{rel_path}.component",
                            "class": f"{item.title()}Component",
                            "dependencies": [],
                        }

                        # 尝试从组件文件中获取依赖信息
                        try:
                            dependencies = self._extract_dependencies_from_file(
                                component_file
                            )
                            component_config["dependencies"] = dependencies
                        except Exception as e:
                            print(
                                f"Failed to extract dependencies from {component_file}: {e}"
                            )

                        component_configs[component_name] = component_config
                        print(f"Auto-discovered component: {component_name}")
                    else:
                        # 递归扫描子目录
                        self._scan_directory_recursive(
                            item_path, base_path, component_configs
                        )

        except Exception as e:
            print(f"Failed to scan directory {directory}: {e}")

    def _extract_dependencies_from_file(self, file_path: str) -> List[str]:
        """
        从组件文件中提取依赖信息

        Args:
            file_path (str): 组件文件路径

        Returns:
            List[str]: 依赖的组件名称列表
        """
        dependencies = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # 查找dependencies属性定义
                import re

                # 匹配 dependencies = [...] 或 dependencies: List[str] = [...]
                pattern = r"dependencies\s*[=:]\s*\[([^\]]*)\]"
                matches = re.findall(pattern, content)

                for match in matches:
                    # 解析依赖列表
                    dep_items = [item.strip().strip("\"'") for item in match.split(",")]
                    dependencies.extend([item for item in dep_items if item])

        except Exception as e:
            print(f"Failed to extract dependencies from {file_path}: {e}")

        return dependencies

    def _load_component(
        self, component_name: str, config: Dict[str, Any]
    ) -> Optional[Type[ComponentInterface]]:
        """
        加载单个组件

        Args:
            component_name (str): 组件名称
            config (Dict[str, Any]): 组件配置

        Returns:
            Optional[Type[ComponentInterface]]: 组件类型，如果加载失败则返回None
        """
        # 尝试从配置中获取组件路径
        component_path = config.get("path", f"{self.base_path}.{component_name}")
        component_class = config.get("class", f"{component_name.title()}Component")

        try:
            # 动态导入组件模块
            module = importlib.import_module(component_path)

            # 获取组件类
            if hasattr(module, component_class):
                component_type = getattr(module, component_class)

                # 验证是否为ComponentInterface的子类
                if issubclass(component_type, ComponentInterface):
                    return component_type
                else:
                    print(
                        f"Component '{component_name}' does not implement ComponentInterface"
                    )
                    return None
            else:
                print(
                    f"Component class '{component_class}' not found in module '{component_path}'"
                )
                return None

        except ImportError as e:
            print(f"Failed to import component module '{component_path}': {e}")
            return None
        except Exception as e:
            print(f"Failed to load component '{component_name}': {e}")
            return None

    def get_component_dependencies_from_config(
        self, component_name: str, config: Dict[str, Any]
    ) -> List[str]:
        """
        从配置中获取组件依赖

        Args:
            component_name (str): 组件名称
            config (Dict[str, Any]): 组件配置

        Returns:
            List[str]: 依赖的组件名称列表
        """
        # 从配置中获取依赖
        dependencies = config.get("dependencies", [])

        # 如果是字符串，转换为列表
        if isinstance(dependencies, str):
            dependencies = [dependencies]

        return dependencies

    def get_discovered_components(self) -> Dict[str, Type[ComponentInterface]]:
        """
        获取已发现的组件

        Returns:
            Dict[str, Type[ComponentInterface]]: 已发现的组件类型字典
        """
        return self._discovered_components.copy()

    def clear_discovered(self) -> None:
        """
        清空已发现的组件

        移除所有已发现的组件信息。
        """
        self._discovered_components.clear()
        self._component_registry.clear()

    def get_component_registry(self) -> Dict[str, Dict[str, Any]]:
        """
        获取组件注册表

        Returns:
            Dict[str, Dict[str, Any]]: 组件注册表
        """
        return self._component_registry.copy()

    def register_component_metadata(
        self, component_name: str, metadata: Dict[str, Any]
    ) -> None:
        """
        注册组件元数据

        Args:
            component_name (str): 组件名称
            metadata (Dict[str, Any]): 组件元数据
        """
        if component_name in self._component_registry:
            self._component_registry[component_name].update(metadata)
        else:
            self._component_registry[component_name] = metadata.copy()

    def get_component_metadata(self, component_name: str) -> Dict[str, Any]:
        """
        获取组件元数据

        Args:
            component_name (str): 组件名称

        Returns:
            Dict[str, Any]: 组件元数据
        """
        return self._component_registry.get(component_name, {}).copy()

    def list_available_components(self) -> List[str]:
        """
        列出所有可用的组件

        Returns:
            List[str]: 可用组件名称列表
        """
        return list(self._discovered_components.keys())

    def is_component_discovered(self, component_name: str) -> bool:
        """
        检查组件是否已被发现

        Args:
            component_name (str): 组件名称

        Returns:
            bool: 是否已被发现
        """
        return component_name in self._discovered_components
