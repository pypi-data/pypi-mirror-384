# Python模块化框架

一个基于Python的模块化框架系统，支持组件复用和依赖注入。**现已支持PostgreSQL数据库集成！**

## 功能特性

- 🏗️ **模块化架构**: 分层设计，支持组件独立开发和部署
- 🔧 **依赖注入**: 内置依赖注入容器，支持松耦合设计
- ⚙️ **配置管理**: 灵活的配置系统，支持环境变量和配置文件
- 🔄 **生命周期管理**: 完整的组件生命周期管理
- 🗄️ **数据库集成**: PostgreSQL + SQLAlchemy ORM，自动建表
- 🔐 **密码安全**: Argon2加密，行业最佳实践
- 🧪 **测试友好**: 支持单元测试和集成测试
- 📚 **文档完整**: 完整的API文档和使用指南

## 🎉 新特性：数据库集成

User组件现已支持完整的PostgreSQL数据库集成！

**核心特性：**
- ✅ 自动创建数据库表结构
- ✅ Argon2密码加密（行业最佳实践）
- ✅ 事务自动管理
- ✅ 类型安全的Repository模式
- ✅ 失败登录追踪
- ✅ 用户搜索和统计

**5分钟快速开始：**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from components.user.component import UserComponent
from components.user.models import UserCreate

# 1. 连接数据库
engine = create_engine("postgresql://user:pass@localhost/myapp")
session = sessionmaker(bind=engine)()

# 2. 初始化组件
user_comp = UserComponent()
user_comp.initialize({
    'database_session': session,
    'database_engine': engine,
    'use_database': True,
})
user_comp.start()  # 自动创建users表！

# 3. 创建用户
user = user_comp._user_service.create_user(
    UserCreate(username="john", email="john@example.com"),
    password="SecurePassword123!"
)

# 4. 用户登录
auth_result = user_comp._user_service.authenticate_user("john", "SecurePassword123!")
if auth_result:
    print(f"登录成功！用户: {auth_result.username}")
```

📖 **详细文档：**
- [快速开始](plans/数据库集成快速开始.md) - 5分钟上手
- [使用指南](plans/数据库集成使用指南.md) - 完整说明
- [实施报告](plans/数据库集成实施进度报告.md) - 技术细节

🚀 **即将推出：**
- Auth组件数据库集成（权限、角色、令牌）
- Payment组件数据库集成（支付、退款）
- Redis缓存支持

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/example/python-modular-framework.git
cd python-modular-framework

# 安装依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .
```

### 基本使用

```python
from framework import Application
from components.user import UserService
from components.auth import AuthService

# 创建应用
app = Application()

# 注册组件
app.register_component('user', UserService())
app.register_component('auth', AuthService())

# 配置应用
app.configure({
    'database': {
        'url': 'sqlite:///app.db'
    }
})

# 启动应用
app.run()
```

## 项目结构

```
framework/
├── framework/                    # 框架层
│   ├── core/                    # 核心功能
│   └── interfaces/              # 接口定义
├── components/                  # 组件包层
│   ├── user/                    # 用户模块
│   ├── auth/                    # 权限模块
│   ├── payment/                 # 支付模块
│   └── common/                  # 通用组件
├── examples/                    # 示例应用
├── tests/                       # 测试文件
└── docs/                        # 文档
```

## 开发指南

### 代码规范

- 遵循PEP 8编码规范
- 使用类型注解
- 完整的文档字符串
- 单元测试覆盖率 > 80%

### 开发环境设置

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行代码格式化
black framework/ components/ tests/

# 运行代码检查
flake8 framework/ components/ tests/

# 运行类型检查
mypy framework/ components/

# 运行测试
pytest
```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目链接: [https://github.com/example/python-modular-framework](https://github.com/example/python-modular-framework)
- 问题反馈: [https://github.com/example/python-modular-framework/issues](https://github.com/example/python-modular-framework/issues)

## 更新日志

### v0.1.0 (开发中)
- 初始版本
- 基础框架结构
- 核心组件开发
