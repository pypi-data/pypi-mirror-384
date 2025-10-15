调试指南
========

本页面提供Python模块化框架的调试技巧和工具使用指南。

调试环境设置
------------

日志配置
~~~~~~~~

配置详细日志::

    import logging
    import sys

    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # 创建文件处理器
    file_handler = logging.FileHandler('debug.log')
    file_handler.setLevel(logging.DEBUG)

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 添加处理器
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

组件级别日志::

    # 为特定组件设置详细日志
    component_logger = logging.getLogger("component.database")
    component_logger.setLevel(logging.DEBUG)

    # 为框架核心设置日志
    framework_logger = logging.getLogger("framework.core")
    framework_logger.setLevel(logging.DEBUG)

调试模式
~~~~~~~~

启用调试模式::

    from framework.core.application import Application

    app = Application("debug-app", "1.0.0")
    
    # 启用调试模式
    app.configure({
        "debug": True,
        "log_level": "DEBUG",
        "enable_tracing": True
    })

使用环境变量::

    import os

    # 设置环境变量启用调试
    os.environ["FRAMEWORK_DEBUG"] = "true"
    os.environ["FRAMEWORK_LOG_LEVEL"] = "DEBUG"

调试工具
--------

Python调试器
~~~~~~~~~~~~

使用pdb调试器::

    import pdb

    def problematic_function():
        """有问题的函数"""
        data = []
        for i in range(10):
            # 设置断点
            pdb.set_trace()
            data.append(i * 2)
        return data

    # 运行调试
    result = problematic_function()

使用ipdb调试器::

    import ipdb

    def debug_function():
        """调试函数"""
        value = 42
        # 设置断点
        ipdb.set_trace()
        result = value * 2
        return result

    # 运行调试
    result = debug_function()

VS Code调试配置
~~~~~~~~~~~~~~~

创建调试配置文件 ``.vscode/launch.json``::

    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Current File",
                "type": "python",
                "request": "launch",
                "program": "${file}",
                "console": "integratedTerminal",
                "cwd": "${workspaceFolder}",
                "env": {
                    "FRAMEWORK_DEBUG": "true"
                }
            },
            {
                "name": "Python: Framework App",
                "type": "python",
                "request": "launch",
                "module": "framework.core.application",
                "args": ["--debug"],
                "console": "integratedTerminal",
                "cwd": "${workspaceFolder}",
                "env": {
                    "FRAMEWORK_DEBUG": "true",
                    "FRAMEWORK_LOG_LEVEL": "DEBUG"
                }
            },
            {
                "name": "Python: Tests",
                "type": "python",
                "request": "launch",
                "module": "pytest",
                "args": ["tests/", "-v", "-s"],
                "console": "integratedTerminal",
                "cwd": "${workspaceFolder}"
            }
        ]
    }

PyCharm调试配置
~~~~~~~~~~~~~~~

1. 创建运行配置
2. 设置脚本路径
3. 添加环境变量
4. 设置断点
5. 启动调试

组件调试
--------

组件生命周期调试
~~~~~~~~~~~~~~~~

.. code-block:: python

    """
    组件生命周期调试示例
    """

    from framework.interfaces.component import ComponentInterface
    from framework.core.config import Config
    from typing import Dict, Any
    import logging

    class DebugComponent(ComponentInterface):
        """调试组件"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.logger = logging.getLogger(f"debug.component.{name}")
            self.debug_enabled = config.get(f"components.{name}.debug", False)
        
        def initialize(self) -> None:
            """初始化组件"""
            self.logger.info(f"开始初始化组件: {self.name}")
            
            if self.debug_enabled:
                self.logger.debug(f"组件配置: {self.config.to_dict()}")
                self.logger.debug(f"组件依赖: {self.dependencies}")
            
            try:
                # 初始化逻辑
                self._do_initialization()
                self.logger.info(f"组件初始化完成: {self.name}")
            except Exception as e:
                self.logger.error(f"组件初始化失败: {e}")
                raise
        
        def start(self) -> None:
            """启动组件"""
            self.logger.info(f"开始启动组件: {self.name}")
            
            if self.debug_enabled:
                self.logger.debug("检查依赖组件状态")
                for dep_name in self.dependencies:
                    try:
                        dep_component = self.get_dependency(dep_name)
                        health = dep_component.get_health_status()
                        self.logger.debug(f"依赖组件 {dep_name} 状态: {health}")
                    except Exception as e:
                        self.logger.warning(f"无法获取依赖组件 {dep_name} 状态: {e}")
            
            try:
                # 启动逻辑
                self._do_start()
                self.logger.info(f"组件启动完成: {self.name}")
            except Exception as e:
                self.logger.error(f"组件启动失败: {e}")
                raise
        
        def stop(self) -> None:
            """停止组件"""
            self.logger.info(f"开始停止组件: {self.name}")
            
            try:
                # 停止逻辑
                self._do_stop()
                self.logger.info(f"组件停止完成: {self.name}")
            except Exception as e:
                self.logger.error(f"组件停止失败: {e}")
                raise
        
        def get_health_status(self) -> Dict[str, Any]:
            """获取健康状态"""
            status = {
                "status": "healthy",
                "component_name": self.name,
                "debug_enabled": self.debug_enabled
            }
            
            if self.debug_enabled:
                status["config"] = self.config.to_dict()
                status["dependencies"] = self.dependencies
            
            return status
        
        def _do_initialization(self):
            """实际初始化逻辑"""
            pass
        
        def _do_start(self):
            """实际启动逻辑"""
            pass
        
        def _do_stop(self):
            """实际停止逻辑"""
            pass

依赖注入调试
~~~~~~~~~~~~

.. code-block:: python

    """
    依赖注入调试示例
    """

    from framework.core.container import Container
    import logging

    class DebugContainer(Container):
        """调试容器"""
        
        def __init__(self):
            super().__init__()
            self.logger = logging.getLogger("debug.container")
        
        def register_singleton(self, name: str, service_class):
            """注册单例服务"""
            self.logger.debug(f"注册单例服务: {name} -> {service_class}")
            super().register_singleton(name, service_class)
        
        def register_transient(self, name: str, service_class):
            """注册瞬态服务"""
            self.logger.debug(f"注册瞬态服务: {name} -> {service_class}")
            super().register_transient(name, service_class)
        
        def get(self, name: str):
            """获取服务"""
            self.logger.debug(f"获取服务: {name}")
            try:
                service = super().get(name)
                self.logger.debug(f"成功获取服务: {name} -> {type(service)}")
                return service
            except Exception as e:
                self.logger.error(f"获取服务失败: {name} - {e}")
                raise
        
        def resolve_dependencies(self, service_class):
            """解析依赖"""
            self.logger.debug(f"解析依赖: {service_class}")
            try:
                dependencies = super().resolve_dependencies(service_class)
                self.logger.debug(f"依赖解析成功: {service_class} -> {dependencies}")
                return dependencies
            except Exception as e:
                self.logger.error(f"依赖解析失败: {service_class} - {e}")
                raise

中间件调试
----------

中间件执行调试
~~~~~~~~~~~~~~

.. code-block:: python

    """
    中间件执行调试示例
    """

    from framework.core.middleware import MiddlewareInterface
    from typing import Dict, Any
    import logging
    import time

    class DebugMiddleware(MiddlewareInterface):
        """调试中间件"""
        
        def __init__(self, name: str):
            super().__init__(name)
            self.logger = logging.getLogger(f"debug.middleware.{name}")
            self.request_count = 0
            self.total_time = 0.0
        
        def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
            """处理请求"""
            self.request_count += 1
            start_time = time.time()
            
            self.logger.debug(f"开始处理请求 #{self.request_count}")
            self.logger.debug(f"请求数据: {request}")
            
            try:
                # 处理请求
                processed_request = self._process_request_internal(request)
                
                processing_time = time.time() - start_time
                self.total_time += processing_time
                
                self.logger.debug(f"请求处理完成，耗时: {processing_time:.3f}秒")
                
                return processed_request
            except Exception as e:
                self.logger.error(f"请求处理失败: {e}")
                raise
        
        def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
            """处理响应"""
            start_time = time.time()
            
            self.logger.debug(f"开始处理响应")
            self.logger.debug(f"响应数据: {response}")
            
            try:
                # 处理响应
                processed_response = self._process_response_internal(response)
                
                processing_time = time.time() - start_time
                self.logger.debug(f"响应处理完成，耗时: {processing_time:.3f}秒")
                
                return processed_response
            except Exception as e:
                self.logger.error(f"响应处理失败: {e}")
                raise
        
        def process_error(self, error: Exception, request: Dict[str, Any]) -> Dict[str, Any]:
            """处理错误"""
            self.logger.error(f"处理错误: {error}")
            self.logger.debug(f"错误请求: {request}")
            
            try:
                # 处理错误
                error_response = self._process_error_internal(error, request)
                
                self.logger.debug(f"错误处理完成: {error_response}")
                
                return error_response
            except Exception as e:
                self.logger.error(f"错误处理失败: {e}")
                raise
        
        def _process_request_internal(self, request: Dict[str, Any]) -> Dict[str, Any]:
            """内部请求处理"""
            # 添加调试信息
            request["_debug_middleware"] = self.name
            request["_debug_timestamp"] = time.time()
            return request
        
        def _process_response_internal(self, response: Dict[str, Any]) -> Dict[str, Any]:
            """内部响应处理"""
            # 添加调试信息
            response["_debug_middleware"] = self.name
            response["_debug_timestamp"] = time.time()
            return response
        
        def _process_error_internal(self, error: Exception, request: Dict[str, Any]) -> Dict[str, Any]:
            """内部错误处理"""
            return {
                "error": str(error),
                "status": 500,
                "debug_middleware": self.name,
                "debug_timestamp": time.time()
            }

插件调试
--------

插件加载调试
~~~~~~~~~~~~

.. code-block:: python

    """
    插件加载调试示例
    """

    from framework.core.plugin import PluginManager
    import logging

    class DebugPluginManager(PluginManager):
        """调试插件管理器"""
        
        def __init__(self, plugin_dirs):
            super().__init__(plugin_dirs)
            self.logger = logging.getLogger("debug.plugin_manager")
        
        def discover_plugins(self):
            """发现插件"""
            self.logger.debug(f"开始发现插件，搜索目录: {self.plugin_dirs}")
            
            try:
                plugins = super().discover_plugins()
                self.logger.info(f"发现 {len(plugins)} 个插件")
                
                for plugin in plugins:
                    self.logger.debug(f"发现插件: {plugin.name} v{plugin.version}")
                    self.logger.debug(f"插件描述: {plugin.description}")
                    self.logger.debug(f"插件依赖: {plugin.dependencies}")
                
                return plugins
            except Exception as e:
                self.logger.error(f"插件发现失败: {e}")
                raise
        
        def load_plugin(self, plugin_info):
            """加载插件"""
            self.logger.debug(f"开始加载插件: {plugin_info.name}")
            
            try:
                super().load_plugin(plugin_info)
                self.logger.info(f"插件加载成功: {plugin_info.name}")
            except Exception as e:
                self.logger.error(f"插件加载失败: {plugin_info.name} - {e}")
                raise
        
        def start_plugin(self, plugin_name: str):
            """启动插件"""
            self.logger.debug(f"开始启动插件: {plugin_name}")
            
            try:
                super().start_plugin(plugin_name)
                self.logger.info(f"插件启动成功: {plugin_name}")
            except Exception as e:
                self.logger.error(f"插件启动失败: {plugin_name} - {e}")
                raise
        
        def stop_plugin(self, plugin_name: str):
            """停止插件"""
            self.logger.debug(f"开始停止插件: {plugin_name}")
            
            try:
                super().stop_plugin(plugin_name)
                self.logger.info(f"插件停止成功: {plugin_name}")
            except Exception as e:
                self.logger.error(f"插件停止失败: {plugin_name} - {e}")
                raise

性能调试
--------

性能分析
~~~~~~~~

.. code-block:: python

    """
    性能分析调试示例
    """

    import cProfile
    import pstats
    import time
    from framework.core.application import Application

    class PerformanceDebugger:
        """性能调试器"""
        
        def __init__(self):
            self.profiler = cProfile.Profile()
            self.start_time = None
            self.end_time = None
        
        def start_profiling(self):
            """开始性能分析"""
            self.start_time = time.time()
            self.profiler.enable()
        
        def stop_profiling(self):
            """停止性能分析"""
            self.profiler.disable()
            self.end_time = time.time()
        
        def analyze_results(self, top_functions=20):
            """分析结果"""
            duration = self.end_time - self.start_time
            print(f"总执行时间: {duration:.3f}秒")
            
            stats = pstats.Stats(self.profiler)
            stats.sort_stats('cumulative')
            stats.print_stats(top_functions)
        
        def profile_application_startup(self):
            """分析应用启动性能"""
            print("开始分析应用启动性能...")
            
            self.start_profiling()
            
            app = Application("performance-debug-app", "1.0.0")
            app.start()
            
            self.stop_profiling()
            
            print("应用启动性能分析结果:")
            self.analyze_results()
            
            app.stop()

    # 使用示例
    if __name__ == "__main__":
        debugger = PerformanceDebugger()
        debugger.profile_application_startup()

内存调试
~~~~~~~~

.. code-block:: python

    """
    内存调试示例
    """

    import tracemalloc
    import gc
    from framework.core.application import Application

    class MemoryDebugger:
        """内存调试器"""
        
        def __init__(self):
            self.snapshots = []
        
        def start_tracing(self):
            """开始内存跟踪"""
            tracemalloc.start()
            print("内存跟踪已开始")
        
        def take_snapshot(self, label):
            """拍摄内存快照"""
            snapshot = tracemalloc.take_snapshot()
            self.snapshots.append((label, snapshot))
            print(f"内存快照已拍摄: {label}")
        
        def compare_snapshots(self, label1, label2):
            """比较内存快照"""
            snapshot1 = next(s for l, s in self.snapshots if l == label1)
            snapshot2 = next(s for l, s in self.snapshots if l == label2)
            
            top_stats = snapshot2.compare_to(snapshot1, 'lineno')
            
            print(f"内存变化 ({label1} -> {label2}):")
            for stat in top_stats[:10]:
                print(stat)
        
        def get_memory_usage(self):
            """获取当前内存使用"""
            current, peak = tracemalloc.get_traced_memory()
            print(f"当前内存使用: {current / 1024 / 1024:.1f}MB")
            print(f"峰值内存使用: {peak / 1024 / 1024:.1f}MB")
        
        def stop_tracing(self):
            """停止内存跟踪"""
            tracemalloc.stop()
            print("内存跟踪已停止")
        
        def debug_application_memory(self):
            """调试应用内存使用"""
            self.start_tracing()
            
            # 拍摄初始快照
            self.take_snapshot("初始状态")
            
            # 创建应用
            app = Application("memory-debug-app", "1.0.0")
            self.take_snapshot("应用创建后")
            
            # 启动应用
            app.start()
            self.take_snapshot("应用启动后")
            
            # 停止应用
            app.stop()
            self.take_snapshot("应用停止后")
            
            # 强制垃圾回收
            gc.collect()
            self.take_snapshot("垃圾回收后")
            
            # 比较快照
            self.compare_snapshots("初始状态", "应用创建后")
            self.compare_snapshots("应用启动后", "应用停止后")
            self.compare_snapshots("应用停止后", "垃圾回收后")
            
            self.get_memory_usage()
            self.stop_tracing()

    # 使用示例
    if __name__ == "__main__":
        debugger = MemoryDebugger()
        debugger.debug_application_memory()

调试最佳实践
------------

1. **分层调试**: 从应用层到组件层逐步调试
2. **日志记录**: 使用详细的日志记录执行流程
3. **断点调试**: 在关键位置设置断点
4. **性能监控**: 定期监控性能指标
5. **内存分析**: 定期检查内存使用情况

调试工具推荐
------------

* **IDE调试器**: VS Code, PyCharm
* **命令行调试器**: pdb, ipdb
* **性能分析**: cProfile, line_profiler
* **内存分析**: memory_profiler, tracemalloc
* **日志分析**: 结构化日志, ELK Stack

更多信息
--------

* :doc:`common_issues` - 常见问题故障排除
* :doc:`performance` - 性能问题故障排除
* :doc:`../examples/advanced_usage` - 高级使用示例
