"""
权限认证组件包
- 提供权限管理和认证功能
- 支持RBAC权限模型
- 提供JWT令牌管理
- 集成数据库存储和Redis缓存

主要组件：
- AuthComponent: 权限组件主类
- AuthService: 权限服务类
- PermissionModel: 权限数据模型
- AuthServiceInterface: 权限服务接口
- Repository: 数据访问层
- Cache: 缓存管理

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from .component import AuthComponent
from .service import AuthService
from .models import (
    PermissionModel,
    RoleModel,
    UserRoleModel,
    TokenModel,
    PermissionCreate,
    RoleCreate,
    TokenCreate,
    LoginRequest,
    LoginResponse,
    PermissionCheck,
    PermissionResult,
    PermissionType,
    TokenType,
    PermissionTable,
    RoleTable,
    UserRoleTable,
    TokenTable,
)
from .interfaces import (
    AuthServiceInterface,
    PermissionRepositoryInterface,
    RoleRepositoryInterface,
    AuthError,
    AuthenticationError,
    AuthorizationError,
)

# 尝试导入Repository和Cache（可能不可用）
try:
    from .repository import (
        PermissionRepository,
        RoleRepository,
        UserRoleRepository,
        TokenRepository,
    )
    from .cache import AuthCacheManager, create_cache_manager
    _repository_available = True
except ImportError:
    _repository_available = False
    PermissionRepository = None
    RoleRepository = None
    UserRoleRepository = None
    TokenRepository = None
    AuthCacheManager = None
    create_cache_manager = None

__version__ = "0.1.0"
__author__ = "开发团队"

__all__ = [
    # 组件
    "AuthComponent",
    # 服务
    "AuthService",
    # 接口
    "AuthServiceInterface",
    "PermissionRepositoryInterface",
    "RoleRepositoryInterface",
    # 异常
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    # 模型
    "PermissionModel",
    "RoleModel",
    "UserRoleModel",
    "TokenModel",
    "PermissionCreate",
    "RoleCreate",
    "TokenCreate",
    "LoginRequest",
    "LoginResponse",
    "PermissionCheck",
    "PermissionResult",
    "PermissionType",
    "TokenType",
    # 数据库表模型
    "PermissionTable",
    "RoleTable",
    "UserRoleTable",
    "TokenTable",
]

# 如果Repository可用，添加到导出列表
if _repository_available:
    __all__.extend([
        "PermissionRepository",
        "RoleRepository",
        "UserRoleRepository",
        "TokenRepository",
        "AuthCacheManager",
        "create_cache_manager",
    ])
