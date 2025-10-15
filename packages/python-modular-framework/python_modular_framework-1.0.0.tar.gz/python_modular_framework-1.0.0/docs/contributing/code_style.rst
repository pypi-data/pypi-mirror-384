代码风格指南
============

本指南定义了Python模块化框架项目的代码风格和规范。

代码格式化
----------

Black 配置
~~~~~~~~~~

项目使用Black进行代码格式化，配置文件 ``pyproject.toml``::

    [tool.black]
    line-length = 88
    target-version = ['py38']
    include = '\.pyi?$'
    exclude = '''
    /(
        \.git
      | \.hg
      | \.mypy_cache
      | \.tox
      | \.venv
      | _build
      | buck-out
      | build
      | dist
    )/
    '''

运行格式化::

    black .

Flake8 配置
~~~~~~~~~~~

代码检查配置 ``.flake8``::

    [flake8]
    max-line-length = 88
    extend-ignore = E203, W503, E501
    exclude = 
        .git,
        __pycache__,
        .venv,
        _build,
        dist,
        *.egg-info

运行检查::

    flake8 .

MyPy 配置
~~~~~~~~~

类型检查配置 ``pyproject.toml``::

    [tool.mypy]
    python_version = "3.8"
    warn_return_any = true
    warn_unused_configs = true
    disallow_untyped_defs = true
    disallow_incomplete_defs = true
    check_untyped_defs = true
    disallow_untyped_decorators = true
    no_implicit_optional = true
    warn_redundant_casts = true
    warn_unused_ignores = true
    warn_no_return = true
    warn_unreachable = true
    strict_equality = true

运行类型检查::

    mypy .

命名规范
--------

文件命名
~~~~~~~~

* 使用小写字母和下划线
* 文件名应该描述其内容
* 测试文件以 ``test_`` 开头

示例::

    user_service.py
    database_config.py
    test_auth_component.py

类命名
~~~~~~

* 使用大驼峰命名法 (PascalCase)
* 类名应该描述其功能
* 接口类以 ``Interface`` 结尾

示例::

    class UserService:
        pass

    class ComponentInterface:
        pass

    class DatabaseConfig:
        pass

函数和变量命名
~~~~~~~~~~~~~~

* 使用小写字母和下划线
* 函数名应该是动词或动词短语
* 变量名应该描述其内容

示例::

    def get_user_by_id(user_id: int) -> User:
        pass

    def authenticate_user(username: str, password: str) -> bool:
        pass

    user_count = 0
    is_authenticated = False

常量命名
~~~~~~~~

* 使用大写字母和下划线
* 常量应该定义在模块顶部

示例::

    MAX_RETRY_COUNT = 3
    DEFAULT_TIMEOUT = 30
    API_VERSION = "v1"

文档规范
--------

文件头注释
~~~~~~~~~~

每个Python文件都应该有文件头注释::

    """
    组件名称模块

    该模块提供[功能描述]功能。
    包含以下主要类和函数：
    - ClassName: 类功能描述
    - function_name: 函数功能描述

    作者：开发团队
    创建时间：2024-01-XX
    最后修改：2024-01-XX
    """

类文档字符串
~~~~~~~~~~~~

使用Google风格的文档字符串::

    class UserService:
        """
        用户服务类
        
        提供用户管理相关的业务逻辑，包括用户创建、更新、删除和查询功能。
        
        Attributes:
            config: 配置对象
            logger: 日志记录器
        """
        
        def __init__(self, config: Config):
            """
            初始化用户服务
            
            Args:
                config: 配置对象，包含数据库连接等配置信息
            """
            pass

函数文档字符串
~~~~~~~~~~~~~~

::

    def create_user(self, username: str, email: str, password: str) -> User:
        """
        创建新用户
        
        根据提供的用户信息创建新用户，并返回用户对象。
        
        Args:
            username: 用户名，必须唯一
            email: 用户邮箱地址
            password: 用户密码，将自动加密存储
            
        Returns:
            User: 创建的用户对象
            
        Raises:
            ValueError: 当用户名或邮箱已存在时
            ValidationError: 当输入参数格式不正确时
            
        Example:
            >>> service = UserService(config)
            >>> user = service.create_user("john", "john@example.com", "password123")
            >>> print(user.username)
            john
        """
        pass

类型注解
--------

函数参数和返回值
~~~~~~~~~~~~~~~

::

    from typing import List, Dict, Optional, Union

    def get_users(
        self, 
        limit: int = 10, 
        offset: int = 0,
        filters: Optional[Dict[str, str]] = None
    ) -> List[User]:
        """
        获取用户列表
        
        Args:
            limit: 返回的最大用户数量
            offset: 跳过的用户数量
            filters: 可选的过滤条件
            
        Returns:
            用户对象列表
        """
        pass

变量类型注解
~~~~~~~~~~~~

::

    # 简单类型
    user_count: int = 0
    is_active: bool = True
    username: str = "admin"
    
    # 复杂类型
    users: List[User] = []
    config: Dict[str, Any] = {}
    optional_value: Optional[str] = None

导入规范
--------

导入顺序
~~~~~~~~

1. 标准库导入
2. 第三方库导入
3. 本地应用导入

每组之间用空行分隔::

    import os
    import sys
    from typing import Dict, List, Optional

    import requests
    import sqlalchemy

    from framework.core.config import Config
    from framework.interfaces.component import ComponentInterface

导入格式
~~~~~~~~

* 每行一个导入
* 使用绝对导入
* 避免使用 ``from module import *``

示例::

    # 好的做法
    from framework.core.application import Application
    from framework.core.config import Config
    
    # 避免的做法
    from framework.core import *
    from framework.core.application import Application, Config

异常处理
--------

异常类型
~~~~~~~~

使用具体的异常类型::

    # 好的做法
    if not username:
        raise ValueError("用户名不能为空")
    
    if user_exists:
        raise UserAlreadyExistsError(f"用户 {username} 已存在")
    
    # 避免的做法
    if not username:
        raise Exception("用户名不能为空")

异常处理
~~~~~~~~

::

    try:
        user = self.get_user_by_id(user_id)
    except UserNotFoundError:
        logger.warning(f"用户 {user_id} 不存在")
        return None
    except DatabaseError as e:
        logger.error(f"数据库错误: {e}")
        raise
    except Exception as e:
        logger.error(f"未知错误: {e}")
        raise

日志规范
--------

日志级别
~~~~~~~~

* **DEBUG**: 详细的调试信息
* **INFO**: 一般信息
* **WARNING**: 警告信息
* **ERROR**: 错误信息
* **CRITICAL**: 严重错误

日志格式
~~~~~~~~

::

    import logging

    logger = logging.getLogger(__name__)

    # 信息日志
    logger.info(f"用户 {username} 登录成功")
    
    # 警告日志
    logger.warning(f"用户 {username} 登录失败，密码错误")
    
    # 错误日志
    logger.error(f"数据库连接失败: {error}")
    
    # 调试日志
    logger.debug(f"处理请求: {request_data}")

测试规范
--------

测试文件结构
~~~~~~~~~~~~

::

    tests/
    ├── unit/                    # 单元测试
    │   ├── test_components/    # 组件测试
    │   ├── test_middleware/    # 中间件测试
    │   └── test_plugins/       # 插件测试
    ├── integration/            # 集成测试
    └── fixtures/               # 测试数据

测试命名
~~~~~~~~

* 测试文件以 ``test_`` 开头
* 测试函数以 ``test_`` 开头
* 测试类以 ``Test`` 开头

示例::

    class TestUserService:
        def test_create_user_success(self):
            """测试成功创建用户"""
            pass
        
        def test_create_user_duplicate_username(self):
            """测试创建重复用户名用户"""
            pass

测试结构
~~~~~~~~

使用AAA模式 (Arrange-Act-Assert)::

    def test_authenticate_user(self):
        """测试用户认证"""
        # Arrange - 准备测试数据
        username = "testuser"
        password = "password123"
        service = UserService(config)
        
        # Act - 执行被测试的操作
        result = service.authenticate_user(username, password)
        
        # Assert - 验证结果
        assert result is True

性能规范
--------

性能要求
~~~~~~~~

* 组件启动时间 < 0.5秒
* 内存使用 < 100MB
* 请求处理时间 < 100ms
* 支持并发请求 > 1000/秒

性能优化
~~~~~~~~

* 使用缓存减少重复计算
* 避免在循环中进行数据库查询
* 使用连接池管理数据库连接
* 合理使用异步编程

安全规范
--------

输入验证
~~~~~~~~

* 验证所有用户输入
* 使用白名单而不是黑名单
* 防止SQL注入和XSS攻击

敏感信息
~~~~~~~~

* 不在代码中硬编码密码
* 使用环境变量存储敏感配置
* 对敏感数据进行加密

代码审查
--------

审查要点
~~~~~~~~

* 代码是否符合风格规范
* 是否有适当的错误处理
* 是否有完整的测试覆盖
* 是否有安全漏洞
* 性能是否满足要求

审查流程
~~~~~~~~

1. 创建Pull Request
2. 自动运行CI检查
3. 代码审查
4. 修改和重新审查
5. 合并代码

工具配置
--------

预提交钩子
~~~~~~~~~~

安装pre-commit::

    pip install pre-commit
    pre-commit install

配置文件 ``.pre-commit-config.yaml``::

    repos:
    -   repo: https://github.com/psf/black
        rev: 22.3.0
        hooks:
        -   id: black
    -   repo: https://github.com/pycqa/flake8
        rev: 4.0.1
        hooks:
        -   id: flake8
    -   repo: https://github.com/pre-commit/mirrors-mypy
        rev: v0.950
        hooks:
        -   id: mypy

更多信息
--------

* :doc:`guidelines` - 贡献指南
* :doc:`development_setup` - 开发环境设置
* :doc:`../troubleshooting/common_issues` - 常见问题
