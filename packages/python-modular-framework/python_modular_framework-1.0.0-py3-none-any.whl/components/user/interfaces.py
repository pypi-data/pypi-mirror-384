"""
用户服务接口定义
- 定义用户服务的标准接口
- 提供用户管理的抽象接口
- 支持依赖注入和接口实现

主要接口：
- UserServiceInterface: 用户服务接口
- UserRepositoryInterface: 用户仓储接口

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .models import (
    UserModel,
    UserCreate,
    UserUpdate,
    UserProfile,
    UserSearch,
    UserStats,
)


class UserServiceInterface(ABC):
    """
    用户服务接口

    定义用户管理的标准接口，包括用户CRUD操作、
    认证、授权等功能。
    """

    @abstractmethod
    def create_user(self, user_data: UserCreate) -> UserModel:
        """
        创建用户

        Args:
            user_data (UserCreate): 用户创建数据

        Returns:
            UserModel: 创建的用户对象

        Raises:
            UserError: 创建失败时抛出异常
        """

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[UserModel]:
        """
        根据ID获取用户

        Args:
            user_id (int): 用户ID

        Returns:
            Optional[UserModel]: 用户对象，如果不存在则返回None
        """

    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[UserModel]:
        """
        根据用户名获取用户

        Args:
            username (str): 用户名

        Returns:
            Optional[UserModel]: 用户对象，如果不存在则返回None
        """

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """
        根据邮箱获取用户

        Args:
            email (str): 邮箱地址

        Returns:
            Optional[UserModel]: 用户对象，如果不存在则返回None
        """

    @abstractmethod
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[UserModel]:
        """
        更新用户信息

        Args:
            user_id (int): 用户ID
            user_data (UserUpdate): 用户更新数据

        Returns:
            Optional[UserModel]: 更新后的用户对象，如果不存在则返回None

        Raises:
            UserError: 更新失败时抛出异常
        """

    @abstractmethod
    def delete_user(self, user_id: int) -> bool:
        """
        删除用户

        Args:
            user_id (int): 用户ID

        Returns:
            bool: 是否删除成功
        """

    @abstractmethod
    def list_users(
        self, search_params: Optional[UserSearch] = None
    ) -> List[UserProfile]:
        """
        获取用户列表

        Args:
            search_params (Optional[UserSearch]): 搜索参数

        Returns:
            List[UserProfile]: 用户列表
        """

    @abstractmethod
    def count_users(self, search_params: Optional[UserSearch] = None) -> int:
        """
        统计用户数量

        Args:
            search_params (Optional[UserSearch]): 搜索参数

        Returns:
            int: 用户数量
        """

    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> Optional[UserModel]:
        """
        用户认证

        Args:
            username (str): 用户名或邮箱
            password (str): 密码

        Returns:
            Optional[UserModel]: 认证成功的用户对象，如果认证失败则返回None
        """

    @abstractmethod
    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        验证密码

        Args:
            password (str): 明文密码
            password_hash (str): 密码哈希

        Returns:
            bool: 密码是否正确
        """

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """
        生成密码哈希

        Args:
            password (str): 明文密码

        Returns:
            str: 密码哈希
        """

    @abstractmethod
    def update_password(self, user_id: int, new_password: str) -> bool:
        """
        更新用户密码

        Args:
            user_id (int): 用户ID
            new_password (str): 新密码

        Returns:
            bool: 是否更新成功
        """

    @abstractmethod
    def activate_user(self, user_id: int) -> bool:
        """
        激活用户

        Args:
            user_id (int): 用户ID

        Returns:
            bool: 是否激活成功
        """

    @abstractmethod
    def deactivate_user(self, user_id: int) -> bool:
        """
        停用用户

        Args:
            user_id (int): 用户ID

        Returns:
            bool: 是否停用成功
        """

    @abstractmethod
    def verify_user(self, user_id: int) -> bool:
        """
        验证用户

        Args:
            user_id (int): 用户ID

        Returns:
            bool: 是否验证成功
        """

    @abstractmethod
    def update_last_login(self, user_id: int) -> bool:
        """
        更新最后登录时间

        Args:
            user_id (int): 用户ID

        Returns:
            bool: 是否更新成功
        """

    @abstractmethod
    def get_user_stats(self) -> UserStats:
        """
        获取用户统计信息

        Returns:
            UserStats: 用户统计信息
        """

    @abstractmethod
    def search_users(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> List[UserProfile]:
        """
        搜索用户

        Args:
            query (str): 搜索关键词
            limit (int): 返回数量限制
            offset (int): 偏移量

        Returns:
            List[UserProfile]: 搜索结果
        """


class UserRepositoryInterface(ABC):
    """
    用户仓储接口

    定义用户数据访问的标准接口。
    """

    @abstractmethod
    def create(self, user_data: UserCreate) -> UserModel:
        """
        创建用户

        Args:
            user_data (UserCreate): 用户创建数据

        Returns:
            UserModel: 创建的用户对象
        """

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[UserModel]:
        """
        根据ID获取用户

        Args:
            user_id (int): 用户ID

        Returns:
            Optional[UserModel]: 用户对象
        """

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[UserModel]:
        """
        根据用户名获取用户

        Args:
            username (str): 用户名

        Returns:
            Optional[UserModel]: 用户对象
        """

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[UserModel]:
        """
        根据邮箱获取用户

        Args:
            email (str): 邮箱地址

        Returns:
            Optional[UserModel]: 用户对象
        """

    @abstractmethod
    def update(self, user_id: int, user_data: UserUpdate) -> Optional[UserModel]:
        """
        更新用户

        Args:
            user_id (int): 用户ID
            user_data (UserUpdate): 用户更新数据

        Returns:
            Optional[UserModel]: 更新后的用户对象
        """

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """
        删除用户

        Args:
            user_id (int): 用户ID

        Returns:
            bool: 是否删除成功
        """

    @abstractmethod
    def list_all(self, limit: int = 20, offset: int = 0) -> List[UserModel]:
        """
        获取所有用户

        Args:
            limit (int): 返回数量限制
            offset (int): 偏移量

        Returns:
            List[UserModel]: 用户列表
        """

    @abstractmethod
    def count(self) -> int:
        """
        统计用户数量

        Returns:
            int: 用户数量
        """

    @abstractmethod
    def search(self, query: str, limit: int = 20, offset: int = 0) -> List[UserModel]:
        """
        搜索用户

        Args:
            query (str): 搜索关键词
            limit (int): 返回数量限制
            offset (int): 偏移量

        Returns:
            List[UserModel]: 搜索结果
        """


class UserError(Exception):
    """用户异常基类"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        初始化用户异常

        Args:
            message (str): 错误消息
            details (Optional[Dict[str, Any]]): 错误详情
        """
        self.details = details or {}
        super().__init__(message)


class UserNotFoundError(UserError):
    """用户未找到异常"""



class UserAlreadyExistsError(UserError):
    """用户已存在异常"""



class UserAuthenticationError(UserError):
    """用户认证异常"""



class UserValidationError(UserError):
    """用户验证异常"""



class UserPermissionError(UserError):
    """用户权限异常"""

