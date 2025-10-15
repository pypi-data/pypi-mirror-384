"""
用户管理组件包
- 提供用户管理功能
- 支持用户注册、登录、权限管理
- 提供用户数据模型和服务接口

主要组件：
- UserComponent: 用户组件主类
- UserService: 用户服务类
- UserModel: 用户数据模型
- UserServiceInterface: 用户服务接口

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from .component import UserComponent
from .service import OptimizedUserService
from .models import UserModel, UserCreate, UserUpdate, UserTable, UserProfile, UserStats, UserStatus, UserRole
from .interfaces import UserServiceInterface

try:
    from .repository import UserRepository
    REPOSITORY_AVAILABLE = True
except ImportError:
    UserRepository = None
    REPOSITORY_AVAILABLE = False

__version__ = "0.1.0"
__author__ = "开发团队"

__all__ = [
    "UserComponent",
    "OptimizedUserService",
    "UserModel",
    "UserCreate",
    "UserUpdate",
    "UserTable",
    "UserProfile",
    "UserStats",
    "UserStatus",
    "UserRole",
    "UserServiceInterface",
    "UserRepository",
]
