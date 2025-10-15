Python模块化框架 文档
=====================================

欢迎使用Python模块化框架！这是一个功能完整、性能优秀的Python模块化框架，支持组件化开发、依赖注入、中间件系统、插件机制等现代软件开发的核心特性。

.. toctree::
   :maxdepth: 2
   :caption: 快速开始

   quickstart
   installation

.. toctree::
   :maxdepth: 2
   :caption: 核心概念

   concepts/overview
   concepts/components
   concepts/middleware
   concepts/plugins

.. toctree::
   :maxdepth: 2
   :caption: API参考

   api/framework
   api/components
   api/middleware
   api/plugins

.. toctree::
   :maxdepth: 2
   :caption: 开发指南

   development/creating_components
   development/creating_middleware
   development/creating_plugins
   development/best_practices

.. toctree::
   :maxdepth: 2
   :caption: 示例和教程

   examples/basic_usage
   examples/advanced_usage
   examples/real_world_applications

.. toctree::
   :maxdepth: 2
   :caption: 故障排除

   troubleshooting/common_issues
   troubleshooting/performance
   troubleshooting/debugging

.. toctree::
   :maxdepth: 2
   :caption: 贡献指南

   contributing/guidelines
   contributing/development_setup
   contributing/code_style

特性
----

* **模块化设计**: 高度模块化的组件系统，支持组件复用和独立开发
* **依赖注入**: 完整的依赖注入容器，支持自动依赖解析和循环依赖检测
* **中间件系统**: 灵活的中间件链式调用，支持请求处理、认证、日志等功能
* **插件机制**: 动态插件加载和管理，支持插件生命周期控制
* **配置管理**: 灵活的配置管理系统，支持多种配置源和环境隔离
* **性能优化**: 优化的启动时间和内存使用，支持高并发处理
* **类型安全**: 完整的类型注解支持，提供更好的开发体验

快速开始
--------

安装框架::

    pip install python-modular-framework

创建简单应用::

    from framework.core.application import Application

    app = Application(name="my-app", version="1.0.0")
    app.configure({"debug": True})
    app.start()

更多信息请查看 :doc:`quickstart` 页面。

项目信息
--------

* **版本**: 1.0.0
* **许可证**: MIT
* **Python版本**: 3.8+
* **GitHub**: https://github.com/your-org/python-modular-framework

索引和表格
==========

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

