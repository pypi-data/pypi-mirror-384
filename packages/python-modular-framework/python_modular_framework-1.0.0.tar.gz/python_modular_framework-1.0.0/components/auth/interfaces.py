"""
权限认证服务接口定义
- 定义权限认证服务的标准接口
- 提供RBAC权限模型接口
- 支持JWT令牌管理接口

主要接口：
- AuthServiceInterface: 权限认证服务接口
- PermissionRepositoryInterface: 权限仓储接口

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .models import (
    PermissionModel,
    RoleModel,
    TokenModel,
    PermissionCreate,
    RoleCreate,
    TokenCreate,
    LoginRequest,
    LoginResponse,
    PermissionCheck,
    PermissionResult,
)


class AuthServiceInterface(ABC):
    """
    权限认证服务接口

    定义权限认证管理的标准接口，包括权限管理、
    角色管理、用户认证、令牌管理等功能。
    """

    # 权限管理
    @abstractmethod
    def create_permission(self, permission_data: PermissionCreate) -> PermissionModel:
        """
        创建权限

        Args:
            permission_data (PermissionCreate): 权限创建数据

        Returns:
            PermissionModel: 创建的权限对象

        Raises:
            AuthError: 创建失败时抛出异常
        """

    @abstractmethod
    def get_permission_by_id(self, permission_id: int) -> Optional[PermissionModel]:
        """
        根据ID获取权限

        Args:
            permission_id (int): 权限ID

        Returns:
            Optional[PermissionModel]: 权限对象，如果不存在则返回None
        """

    @abstractmethod
    def get_permission_by_code(self, code: str) -> Optional[PermissionModel]:
        """
        根据代码获取权限

        Args:
            code (str): 权限代码

        Returns:
            Optional[PermissionModel]: 权限对象，如果不存在则返回None
        """

    @abstractmethod
    def list_permissions(self, resource: Optional[str] = None) -> List[PermissionModel]:
        """
        获取权限列表

        Args:
            resource (Optional[str]): 资源名称过滤

        Returns:
            List[PermissionModel]: 权限列表
        """

    @abstractmethod
    def update_permission(
        self, permission_id: int, permission_data: Dict[str, Any]
    ) -> Optional[PermissionModel]:
        """
        更新权限

        Args:
            permission_id (int): 权限ID
            permission_data (Dict[str, Any]): 权限更新数据

        Returns:
            Optional[PermissionModel]: 更新后的权限对象，如果不存在则返回None
        """

    @abstractmethod
    def delete_permission(self, permission_id: int) -> bool:
        """
        删除权限

        Args:
            permission_id (int): 权限ID

        Returns:
            bool: 是否删除成功
        """

    # 角色管理
    @abstractmethod
    def create_role(self, role_data: RoleCreate) -> RoleModel:
        """
        创建角色

        Args:
            role_data (RoleCreate): 角色创建数据

        Returns:
            RoleModel: 创建的角色对象
        """

    @abstractmethod
    def get_role_by_id(self, role_id: int) -> Optional[RoleModel]:
        """
        根据ID获取角色

        Args:
            role_id (int): 角色ID

        Returns:
            Optional[RoleModel]: 角色对象，如果不存在则返回None
        """

    @abstractmethod
    def get_role_by_code(self, code: str) -> Optional[RoleModel]:
        """
        根据代码获取角色

        Args:
            code (str): 角色代码

        Returns:
            Optional[RoleModel]: 角色对象，如果不存在则返回None
        """

    @abstractmethod
    def list_roles(self) -> List[RoleModel]:
        """
        获取角色列表

        Returns:
            List[RoleModel]: 角色列表
        """

    @abstractmethod
    def update_role(
        self, role_id: int, role_data: Dict[str, Any]
    ) -> Optional[RoleModel]:
        """
        更新角色

        Args:
            role_id (int): 角色ID
            role_data (Dict[str, Any]): 角色更新数据

        Returns:
            Optional[RoleModel]: 更新后的角色对象，如果不存在则返回None
        """

    @abstractmethod
    def delete_role(self, role_id: int) -> bool:
        """
        删除角色

        Args:
            role_id (int): 角色ID

        Returns:
            bool: 是否删除成功
        """

    # 用户角色管理
    @abstractmethod
    def assign_role_to_user(
        self, user_id: int, role_id: int, assigned_by: Optional[int] = None
    ) -> bool:
        """
        为用户分配角色

        Args:
            user_id (int): 用户ID
            role_id (int): 角色ID
            assigned_by (Optional[int]): 分配者ID

        Returns:
            bool: 是否分配成功
        """

    @abstractmethod
    def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        """
        移除用户角色

        Args:
            user_id (int): 用户ID
            role_id (int): 角色ID

        Returns:
            bool: 是否移除成功
        """

    @abstractmethod
    def get_user_roles(self, user_id: int) -> List[RoleModel]:
        """
        获取用户角色列表

        Args:
            user_id (int): 用户ID

        Returns:
            List[RoleModel]: 用户角色列表
        """

    @abstractmethod
    def get_user_permissions(self, user_id: int) -> List[PermissionModel]:
        """
        获取用户权限列表

        Args:
            user_id (int): 用户ID

        Returns:
            List[PermissionModel]: 用户权限列表
        """

    # 权限检查
    @abstractmethod
    def check_permission(self, user_id: int, resource: str, action: str) -> bool:
        """
        检查用户权限

        Args:
            user_id (int): 用户ID
            resource (str): 资源名称
            action (str): 权限动作

        Returns:
            bool: 是否有权限
        """

    @abstractmethod
    def check_permissions(self, permission_check: PermissionCheck) -> PermissionResult:
        """
        检查用户权限（详细）

        Args:
            permission_check (PermissionCheck): 权限检查请求

        Returns:
            PermissionResult: 权限检查结果
        """

    # 认证管理
    @abstractmethod
    def authenticate_user(self, login_request: LoginRequest) -> Optional[LoginResponse]:
        """
        用户认证

        Args:
            login_request (LoginRequest): 登录请求

        Returns:
            Optional[LoginResponse]: 登录响应，如果认证失败则返回None
        """

    @abstractmethod
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证令牌

        Args:
            token (str): 令牌字符串

        Returns:
            Optional[Dict[str, Any]]: 令牌载荷，如果无效则返回None
        """

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> Optional[LoginResponse]:
        """
        刷新令牌

        Args:
            refresh_token (str): 刷新令牌

        Returns:
            Optional[LoginResponse]: 新的令牌响应，如果无效则返回None
        """

    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """
        撤销令牌

        Args:
            token (str): 令牌字符串

        Returns:
            bool: 是否撤销成功
        """

    # 令牌管理
    @abstractmethod
    def create_token(self, token_data: TokenCreate) -> TokenModel:
        """
        创建令牌

        Args:
            token_data (TokenCreate): 令牌创建数据

        Returns:
            TokenModel: 创建的令牌对象
        """

    @abstractmethod
    def get_token_by_string(self, token: str) -> Optional[TokenModel]:
        """
        根据令牌字符串获取令牌

        Args:
            token (str): 令牌字符串

        Returns:
            Optional[TokenModel]: 令牌对象，如果不存在则返回None
        """

    @abstractmethod
    def list_user_tokens(
        self, user_id: int, token_type: Optional[str] = None
    ) -> List[TokenModel]:
        """
        获取用户令牌列表

        Args:
            user_id (int): 用户ID
            token_type (Optional[str]): 令牌类型过滤

        Returns:
            List[TokenModel]: 令牌列表
        """

    @abstractmethod
    def revoke_user_tokens(self, user_id: int, token_type: Optional[str] = None) -> int:
        """
        撤销用户令牌

        Args:
            user_id (int): 用户ID
            token_type (Optional[str]): 令牌类型过滤

        Returns:
            int: 撤销的令牌数量
        """


class PermissionRepositoryInterface(ABC):
    """
    权限仓储接口

    定义权限数据访问的标准接口。
    """

    @abstractmethod
    def create_permission(self, permission_data: PermissionCreate) -> PermissionModel:
        """创建权限"""

    @abstractmethod
    def get_permission_by_id(self, permission_id: int) -> Optional[PermissionModel]:
        """根据ID获取权限"""

    @abstractmethod
    def get_permission_by_code(self, code: str) -> Optional[PermissionModel]:
        """根据代码获取权限"""

    @abstractmethod
    def list_permissions(self, resource: Optional[str] = None) -> List[PermissionModel]:
        """获取权限列表"""

    @abstractmethod
    def update_permission(
        self, permission_id: int, permission_data: Dict[str, Any]
    ) -> Optional[PermissionModel]:
        """更新权限"""

    @abstractmethod
    def delete_permission(self, permission_id: int) -> bool:
        """删除权限"""


class RoleRepositoryInterface(ABC):
    """
    角色仓储接口

    定义角色数据访问的标准接口。
    """

    @abstractmethod
    def create_role(self, role_data: RoleCreate) -> RoleModel:
        """创建角色"""

    @abstractmethod
    def get_role_by_id(self, role_id: int) -> Optional[RoleModel]:
        """根据ID获取角色"""

    @abstractmethod
    def get_role_by_code(self, code: str) -> Optional[RoleModel]:
        """根据代码获取角色"""

    @abstractmethod
    def list_roles(self) -> List[RoleModel]:
        """获取角色列表"""

    @abstractmethod
    def update_role(
        self, role_id: int, role_data: Dict[str, Any]
    ) -> Optional[RoleModel]:
        """更新角色"""

    @abstractmethod
    def delete_role(self, role_id: int) -> bool:
        """删除角色"""


class AuthError(Exception):
    """权限认证异常基类"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        初始化权限认证异常

        Args:
            message (str): 错误消息
            details (Optional[Dict[str, Any]]): 错误详情
        """
        self.details = details or {}
        super().__init__(message)


class PermissionNotFoundError(AuthError):
    """权限未找到异常"""


class RoleNotFoundError(AuthError):
    """角色未找到异常"""


class AuthenticationError(AuthError):
    """认证异常"""


class AuthorizationError(AuthError):
    """授权异常"""


class TokenError(AuthError):
    """令牌异常"""


class PermissionDeniedError(AuthError):
    """权限拒绝异常"""
