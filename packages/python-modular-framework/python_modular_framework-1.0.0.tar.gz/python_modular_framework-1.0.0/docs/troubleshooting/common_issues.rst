常见问题故障排除
================

本页面列出了使用Python模块化框架时可能遇到的常见问题及其解决方案。

安装问题
--------

Python版本不兼容
~~~~~~~~~~~~~~~~

**问题**: 安装时提示Python版本不兼容

**错误信息**::
    ERROR: Package 'python-modular-framework' requires a different Python: 3.7.9 not in '>=3.8'

**解决方案**:
1. 检查Python版本::
    python --version

2. 升级到Python 3.8或更高版本
3. 使用虚拟环境隔离不同Python版本::
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    venv\Scripts\activate     # Windows

依赖冲突
~~~~~~~~

**问题**: 安装时出现依赖冲突

**错误信息**::
    ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following conflicts.

**解决方案**:
1. 使用虚拟环境::
    python -m venv venv
    source venv/bin/activate
    pip install python-modular-framework

2. 强制重新安装::
    pip install --force-reinstall python-modular-framework

3. 清理pip缓存::
    pip cache purge
    pip install python-modular-framework

权限错误
~~~~~~~~

**问题**: 安装时出现权限错误

**错误信息**::
    ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied

**解决方案**:
1. 使用用户安装::
    pip install --user python-modular-framework

2. 使用虚拟环境::
    python -m venv venv
    source venv/bin/activate
    pip install python-modular-framework

3. 检查文件权限::
    # Linux/macOS
    sudo chown -R $USER:$USER ~/.local/lib/python3.x/site-packages

启动问题
--------

组件初始化失败
~~~~~~~~~~~~~~

**问题**: 组件初始化时失败

**错误信息**::
    ComponentError: 组件 'database' 初始化失败: 连接数据库失败

**解决方案**:
1. 检查配置文件::
    # 确保配置文件存在且格式正确
    cat config.yaml

2. 验证数据库连接::
    # 测试数据库连接
    python -c "
    import sqlite3
    conn = sqlite3.connect('test.db')
    print('数据库连接成功')
    conn.close()
    "

3. 检查依赖组件::
    # 确保所有依赖组件都已正确注册
    app.get_component("database")

配置错误
~~~~~~~~

**问题**: 配置加载失败

**错误信息**::
    ConfigurationError: 配置文件格式错误

**解决方案**:
1. 验证YAML格式::
    # 使用在线YAML验证器或Python验证
    import yaml
    with open('config.yaml', 'r') as f:
        yaml.safe_load(f)

2. 检查配置路径::
    # 确保配置文件路径正确
    import os
    print(os.path.exists('config.yaml'))

3. 使用默认配置::
    # 如果配置文件有问题，使用默认配置
    app.configure({})

依赖解析失败
~~~~~~~~~~~~

**问题**: 组件依赖解析失败

**错误信息**::
    DependencyError: 无法解析组件依赖: 循环依赖检测到

**解决方案**:
1. 检查依赖关系::
    # 查看组件依赖声明
    class MyComponent(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.dependencies = ["other-component"]  # 检查依赖列表

2. 重新设计依赖关系::
    # 避免循环依赖，使用事件或回调机制
    class ComponentA(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.dependencies = []  # 移除循环依赖

3. 使用延迟加载::
    # 在需要时才获取依赖
    def some_method(self):
        other_component = self.get_dependency("other-component")

运行时问题
----------

内存泄漏
~~~~~~~~

**问题**: 应用运行时间长了出现内存泄漏

**症状**::
    - 内存使用持续增长
    - 应用响应变慢
    - 最终导致系统崩溃

**解决方案**:
1. 检查资源释放::
    # 确保在stop()方法中释放资源
    def stop(self) -> None:
        if self.connection:
            self.connection.close()
        if self.session:
            self.session.close()

2. 使用上下文管理器::
    # 使用with语句自动管理资源
    with self.get_connection() as conn:
        # 使用连接
        pass

3. 监控内存使用::
    # 使用memory_profiler监控内存
    from memory_profiler import profile
    
    @profile
    def memory_intensive_function(self):
        # 函数代码
        pass

性能问题
~~~~~~~~

**问题**: 应用性能不佳

**症状**::
    - 响应时间过长
    - 吞吐量低
    - CPU使用率高

**解决方案**:
1. 使用缓存::
    # 缓存频繁访问的数据
    from functools import lru_cache
    
    @lru_cache(maxsize=128)
    def expensive_calculation(self, param):
        # 计算逻辑
        return result

2. 异步处理::
    # 使用异步处理提高并发性能
    import asyncio
    
    async def async_operation(self):
        # 异步操作
        pass

3. 连接池::
    # 使用连接池管理数据库连接
    from sqlalchemy.pool import QueuePool
    
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20
    )

4. 性能分析::
    # 使用cProfile分析性能瓶颈
    import cProfile
    
    cProfile.run('your_function()')

异常处理
~~~~~~~~

**问题**: 未处理的异常导致应用崩溃

**错误信息**::
    Traceback (most recent call last):
      File "app.py", line 10, in <module>
        app.start()
    Exception: 未处理的异常

**解决方案**:
1. 添加异常处理::
    try:
        app.start()
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        # 处理异常

2. 使用中间件处理异常::
    class ErrorHandlingMiddleware(MiddlewareInterface):
        def process_error(self, error: Exception, request: Dict[str, Any]) -> Dict[str, Any]:
            logger.error(f"处理请求时发生错误: {error}")
            return {"error": "内部服务器错误", "status": 500}

3. 设置全局异常处理器::
    import sys
    import logging
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception

中间件问题
----------

中间件执行顺序
~~~~~~~~~~~~~~

**问题**: 中间件执行顺序不正确

**症状**::
    - 认证中间件在日志中间件之前执行
    - 缓存中间件没有生效

**解决方案**:
1. 检查注册顺序::
    # 按需要的顺序注册中间件
    manager.register(LoggingMiddleware("logging"))      # 1. 日志
    manager.register(AuthMiddleware("auth"))            # 2. 认证
    manager.register(CacheMiddleware("cache"))          # 3. 缓存

2. 使用优先级::
    # 如果中间件支持优先级，使用优先级控制顺序
    middleware = LoggingMiddleware("logging")
    middleware.priority = 100  # 高优先级先执行

中间件配置错误
~~~~~~~~~~~~~~

**问题**: 中间件配置不正确

**错误信息**::
    MiddlewareError: 中间件配置错误: 缺少必需参数

**解决方案**:
1. 检查配置格式::
    # 确保配置格式正确
    middleware_config = {
        "middleware": {
            "auth": {
                "token_header": "Authorization",
                "token_prefix": "Bearer"
            }
        }
    }

2. 验证配置参数::
    # 在中间件中验证配置
    def configure(self, config: Dict[str, Any]) -> None:
        required_params = ["token_header", "token_prefix"]
        for param in required_params:
            if param not in config:
                raise ValueError(f"缺少必需参数: {param}")

插件问题
--------

插件加载失败
~~~~~~~~~~~~

**问题**: 插件加载失败

**错误信息**::
    PluginLoadError: 插件加载失败: 模块导入错误

**解决方案**:
1. 检查插件路径::
    # 确保插件目录存在且可访问
    import os
    plugin_dir = "plugins"
    if not os.path.exists(plugin_dir):
        os.makedirs(plugin_dir)

2. 验证插件接口::
    # 确保插件实现了正确的接口
    from framework.interfaces.plugin import PluginInterface
    
    class MyPlugin(PluginInterface):
        def __init__(self):
            super().__init__()
            self.name = "my-plugin"
            self.version = "1.0.0"
            # 实现必需的方法

3. 检查依赖::
    # 确保插件依赖已安装
    pip install -r requirements.txt

插件依赖冲突
~~~~~~~~~~~~

**问题**: 插件依赖冲突

**错误信息**::
    PluginDependencyError: 插件依赖冲突: 版本不兼容

**解决方案**:
1. 检查依赖版本::
    # 在插件中声明兼容的依赖版本
    self.dependencies = ["database-plugin>=1.0.0,<2.0.0"]

2. 使用虚拟环境::
    # 为不同插件使用不同的虚拟环境
    python -m venv plugin_env
    source plugin_env/bin/activate
    pip install plugin-dependencies

3. 依赖隔离::
    # 使用依赖隔离机制
    manager = PluginManager(plugin_dirs=["plugins"], isolate_dependencies=True)

调试技巧
--------

日志配置
~~~~~~~~

**问题**: 日志信息不够详细

**解决方案**:
1. 设置详细日志::
    import logging
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )

2. 组件级别日志::
    # 为特定组件设置日志级别
    component_logger = logging.getLogger("component.database")
    component_logger.setLevel(logging.DEBUG)

3. 使用结构化日志::
    import json
    import logging
    
    class StructuredFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage()
            }
            return json.dumps(log_entry)

调试模式
~~~~~~~~

**问题**: 需要调试应用行为

**解决方案**:
1. 启用调试模式::
    app.configure({"debug": True})

2. 使用调试器::
    # 在代码中设置断点
    import pdb; pdb.set_trace()
    
    # 或使用ipdb
    import ipdb; ipdb.set_trace()

3. 性能分析::
    # 使用cProfile分析性能
    import cProfile
    import pstats
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 运行代码
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative').print_stats(10)

获取帮助
--------

如果以上解决方案都不能解决您的问题，请：

1. **查看日志**: 检查应用日志文件获取详细错误信息
2. **GitHub Issues**: 在GitHub上创建issue报告问题
3. **文档**: 查看完整的API文档和示例
4. **社区**: 参与社区讨论获取帮助

更多信息
--------

* :doc:`performance` - 性能问题故障排除
* :doc:`debugging` - 调试指南
* :doc:`../api/framework` - API参考
* :doc:`../examples/basic_usage` - 使用示例
