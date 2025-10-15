# Python模块化框架使用指南

## 概述

Python模块化框架是一个分层的模块化框架系统，支持组件复用和依赖注入。本指南将帮助您快速上手并构建自己的应用程序。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行简单示例

```bash
python examples/simple_app.py
```

### 3. 运行复杂示例

```bash
python examples/complex_app.py
```

## 核心概念

### 应用 (Application)

应用是框架的核心，负责管理组件的生命周期和依赖关系。

```python
from framework import Application

# 创建应用
app = Application(name="my-app", version="1.0.0")

# 配置应用
config = {
    "app": {"debug": True},
    "components": {
        "logging": {
            "enabled": True,
            "config": {"level": "INFO"}
        }
    }
}
app.configure(config)

# 启动应用
app.start()

# 停止应用
app.stop()
```

### 组件 (Component)

组件是框架的基本构建块，实现特定功能。

```python
from framework.interfaces.component import ComponentInterface, ComponentStatus, ComponentInfo
from typing import Dict, Any, List

class MyComponent(ComponentInterface):
    def __init__(self, name: str):
        self._name = name
        self._status = ComponentStatus.UNINITIALIZED
        self._dependencies = []
    
    def initialize(self, config: Dict[str, Any]) -> None:
        self._status = ComponentStatus.INITIALIZED
    
    def start(self) -> None:
        self._status = ComponentStatus.RUNNING
    
    def stop(self) -> None:
        self._status = ComponentStatus.STOPPED
    
    def get_status(self) -> ComponentStatus:
        return self._status
    
    def get_info(self) -> ComponentInfo:
        return ComponentInfo(
            name=self._name,
            version="1.0.0",
            description="My custom component",
            dependencies=self._dependencies,
            status=self._status,
            config={},
            metadata={}
        )
```

### 依赖注入

框架支持自动依赖注入，组件可以通过构造函数参数声明依赖。

```python
class AuthComponent(ComponentInterface):
    def __init__(self, user_service: UserServiceInterface, cache_service: CacheServiceInterface):
        self.user_service = user_service
        self.cache_service = cache_service
```

## 配置系统

### 应用配置

应用配置支持多层级结构：

```python
config = {
    "app": {
        "name": "my-app",
        "version": "1.0.0",
        "debug": True
    },
    "components": {
        "logging": {
            "enabled": True,
            "path": "components.common.logging.component",
            "class": "LoggingComponent",
            "dependencies": [],
            "config": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "cache": {
            "enabled": True,
            "path": "components.common.cache.component",
            "class": "CacheComponent",
            "dependencies": ["logging"],
            "config": {
                "strategy": "memory",
                "max_size": 1000,
                "ttl": 3600
            }
        }
    }
}
```

### 组件自动发现

框架支持基于配置的组件自动发现：

```python
# 配置中的组件会自动被发现和注册
components = {
    "auth": {
        "enabled": True,
        "path": "components.auth.component",
        "class": "AuthComponent",
        "dependencies": ["logging", "cache"],
        "config": {
            "jwt_secret": "your-secret-key",
            "token_expiry": 86400
        }
    }
}
```

## 依赖管理

### 依赖声明

组件可以在配置中声明依赖关系：

```python
"auth": {
    "dependencies": ["logging", "cache", "database"]
}
```

### 循环依赖检测

框架会自动检测循环依赖并抛出异常：

```python
try:
    app.start()
except DependencyResolutionError as e:
    print(f"循环依赖检测: {e}")
```

### 拓扑排序

框架使用拓扑排序算法确定组件的正确启动顺序：

```python
# 获取启动顺序
startup_order = app.get_startup_order()
print(f"启动顺序: {' -> '.join(startup_order)}")

# 获取关闭顺序
shutdown_order = app.get_shutdown_order()
print(f"关闭顺序: {' -> '.join(shutdown_order)}")
```

## 内置组件

### 日志组件 (LoggingComponent)

提供统一的日志管理功能。

```python
from components.common.logging.component import LoggingComponent

logging_component = LoggingComponent("logging")
app.register_component("logging", logging_component)
```

### 缓存组件 (CacheComponent)

提供多种缓存策略支持。

```python
from components.common.cache.component import CacheComponent

cache_component = CacheComponent("cache")
app.register_component("cache", cache_component)

# 使用缓存
cache_component.set("key", "value", ttl=60)
value = cache_component.get("key")
```

### 数据库组件 (DatabaseComponent)

提供数据库连接和操作功能。

```python
from components.common.database.component import DatabaseComponent

db_component = DatabaseComponent("database")
app.register_component("database", db_component)
```

### 权限组件 (AuthComponent)

提供完整的权限认证功能。

```python
from components.auth.component import AuthComponent

auth_component = AuthComponent("auth")
app.register_component("auth", auth_component)

# 创建权限
permission = auth_component.create_permission({
    "name": "user.read",
    "description": "读取用户信息",
    "permission_type": "READ"
})

# 生成JWT令牌
token = auth_component.generate_token({
    "user_id": "user123",
    "username": "testuser",
    "roles": ["admin"]
})
```

### 支付组件 (PaymentComponent)

提供多种支付方式支持。

```python
from components.payment.component import PaymentComponent

payment_component = PaymentComponent("payment")
app.register_component("payment", payment_component)

# 创建支付订单
payment = payment_component.create_payment({
    "user_id": "user123",
    "amount": Decimal("99.99"),
    "currency": "CNY",
    "method": "ALIPAY",
    "payment_type": "PURCHASE"
})
```

## 健康检查和监控

### 应用健康检查

```python
health = app.health_check()
print(f"应用健康状态: {health['overall']}")

for comp_name, comp_health in health['components'].items():
    print(f"  {comp_name}: {comp_health['status']}")
```

### 应用指标

```python
metrics = app.get_metrics()
print(f"运行时间: {metrics['application']['uptime']:.2f}秒")
print(f"组件数量: {metrics['components']['total']}")
```

### 依赖关系图

```python
dependency_graph = app.get_dependency_graph()
print(f"组件列表: {dependency_graph['components']}")
print(f"依赖关系: {dependency_graph['dependencies']}")
print(f"启动顺序: {dependency_graph['startup_order']}")
```

## 错误处理

### 异常类型

框架定义了多种异常类型：

- `ApplicationError`: 应用异常基类
- `ApplicationConfigurationError`: 配置错误
- `ApplicationStartError`: 启动错误
- `ApplicationStopError`: 停止错误
- `ComponentRegistrationError`: 组件注册错误
- `ComponentNotFoundError`: 组件未找到错误
- `DependencyResolutionError`: 依赖解析错误

### 错误处理示例

```python
try:
    app.start()
except ApplicationStartError as e:
    print(f"应用启动失败: {e}")
except DependencyResolutionError as e:
    print(f"依赖解析失败: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 最佳实践

### 1. 组件设计

- 保持组件职责单一
- 通过接口定义依赖关系
- 实现完整的生命周期方法
- 提供详细的健康检查

### 2. 配置管理

- 使用环境变量覆盖默认配置
- 为不同环境提供不同配置
- 验证配置参数的有效性

### 3. 错误处理

- 实现优雅的错误恢复机制
- 记录详细的错误日志
- 提供有意义的错误消息

### 4. 性能优化

- 合理设置组件启动顺序
- 使用缓存减少重复计算
- 监控应用性能指标

## 示例应用

### 简单应用 (simple_app.py)

演示基本的框架使用方法，包括：
- 创建应用和组件
- 注册和配置组件
- 启动和停止应用
- 健康检查和指标获取

### 复杂应用 (complex_app.py)

演示高级功能，包括：
- 组件自动发现
- 依赖关系解析
- 循环依赖检测
- 完整的业务组件集成
- 错误处理和恢复

### 集成测试 (integration_test.py)

测试所有组件的集成功能，包括：
- 组件间依赖注入
- 完整的业务流程
- 性能测试
- 健康检查

## 故障排除

### 常见问题

1. **组件启动失败**
   - 检查组件依赖是否正确
   - 验证配置参数
   - 查看错误日志

2. **循环依赖错误**
   - 检查组件依赖关系
   - 重新设计组件架构
   - 使用事件驱动模式

3. **配置错误**
   - 验证配置文件格式
   - 检查必需配置项
   - 确认组件路径正确

### 调试技巧

1. **启用调试模式**
   ```python
   config = {
       "app": {"debug": True, "log_level": "DEBUG"}
   }
   ```

2. **查看依赖关系图**
   ```python
   dependency_graph = app.get_dependency_graph()
   print(json.dumps(dependency_graph, indent=2))
   ```

3. **监控组件状态**
   ```python
   for name in app.list_components():
       component = app.get_component(name)
       print(f"{name}: {component.get_status()}")
   ```

## 扩展开发

### 创建自定义组件

1. 实现 `ComponentInterface` 接口
2. 定义组件配置结构
3. 实现生命周期方法
4. 提供健康检查功能

### 创建自定义服务

1. 定义服务接口
2. 实现服务类
3. 注册到依赖注入容器
4. 在组件中使用服务

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。

## 支持

如果您遇到问题或有建议，请：

1. 查看文档和示例
2. 搜索已知问题
3. 创建 Issue
4. 联系开发团队

