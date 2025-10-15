安装指南
========

本页面介绍如何安装和配置Python模块化框架。

系统要求
--------

* Python 3.8 或更高版本
* pip 包管理器
* 操作系统：Windows、macOS、Linux

安装方法
--------

使用pip安装
~~~~~~~~~~~

推荐使用pip安装框架::

    pip install python-modular-framework

从源码安装
~~~~~~~~~~

如果您想从源码安装或参与开发::

    git clone https://github.com/your-org/python-modular-framework.git
    cd python-modular-framework
    pip install -e .

开发模式安装
~~~~~~~~~~~~

开发模式安装允许您修改源码并立即看到效果::

    pip install -e .[dev]

这将安装框架及其开发依赖。

验证安装
--------

安装完成后，您可以验证安装是否成功::

    python -c "from framework.core.application import Application; print('安装成功！')"

如果看到"安装成功！"消息，说明框架已正确安装。

配置环境
--------

环境变量
~~~~~~~~

您可以设置以下环境变量来配置框架:

* ``FRAMEWORK_DEBUG``: 启用调试模式 (true/false)
* ``FRAMEWORK_LOG_LEVEL``: 日志级别 (DEBUG/INFO/WARNING/ERROR)
* ``FRAMEWORK_CONFIG_PATH``: 配置文件路径

配置文件
~~~~~~~~

创建配置文件 ``config.yaml``::

    debug: true
    log_level: INFO
    components:
      database:
        host: localhost
        port: 5432
        name: myapp
      cache:
        type: redis
        host: localhost
        port: 6379

故障排除
--------

常见问题
~~~~~~~~

**问题**: ImportError: No module named 'framework'
**解决**: 确保已正确安装框架，检查Python路径

**问题**: 权限错误
**解决**: 使用 ``--user`` 标志安装到用户目录::

    pip install --user python-modular-framework

**问题**: 依赖冲突
**解决**: 使用虚拟环境::

    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # 或
    venv\Scripts\activate     # Windows
    pip install python-modular-framework

获取帮助
--------

如果您在安装过程中遇到问题:

* 查看 :doc:`troubleshooting/common_issues` 页面
* 在GitHub上提交问题: https://github.com/your-org/python-modular-framework/issues
* 查看项目文档: https://python-modular-framework.readthedocs.io

下一步
------

安装完成后，您可以:

* 查看 :doc:`quickstart` 开始使用框架
* 阅读 :doc:`concepts/overview` 了解核心概念
* 查看 :doc:`examples/basic_usage` 学习基本用法