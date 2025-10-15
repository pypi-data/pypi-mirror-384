"""
用户服务实现（优化版）
- 继承BaseService基类
- 使用ExtendedBaseRepository
- 提供用户管理的核心业务逻辑
- 集成数据库存储和Argon2密码加密

主要功能：
- 用户认证
- 用户CRUD操作
- 密码管理
- 用户统计

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import Optional, List

try:
    from components.common.service import BaseService, ServiceConfig
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    from .repository import UserRepository
    from sqlalchemy.orm import Session
    ARGON2_AVAILABLE = True
    REPOSITORY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Import failed: {e}")
    ARGON2_AVAILABLE = False
    REPOSITORY_AVAILABLE = False
    BaseService = None
    ServiceConfig = None
    PasswordHasher = None
    UserRepository = None
    Session = None

from .models import (
    UserCreate,
    UserUpdate,
    UserProfile,
    UserStats,
)
from .interfaces import UserServiceInterface


class UserServiceConfig:
    """
    用户服务配置
    
    继承ServiceConfig，添加用户服务特定的配置项。
    """
    
    def __init__(self, **kwargs):
        """
        初始化用户服务配置
        
        Args:
            **kwargs: 配置参数
        """
        # 设置默认配置
        default_config = {
            'password_min_length': kwargs.get('password_min_length', 8),
            'password_require_special': kwargs.get('password_require_special', True),
            'max_failed_attempts': kwargs.get('max_failed_attempts', 5),
            'lockout_duration': kwargs.get('lockout_duration', 300),  # 5分钟
            'argon2_enabled': kwargs.get('argon2_enabled', True),
        }
        
        # 合并用户配置
        default_config.update(kwargs)
        super().__init__(**default_config)
    
    def _validate_config(self) -> None:
        """
        验证配置参数
        
        Raises:
            ValueError: 配置参数无效
        """
        if self._config['password_min_length'] < 6:
            raise ValueError("密码最小长度不能少于6个字符")
        
        if self._config['max_failed_attempts'] < 1:
            raise ValueError("最大失败尝试次数不能少于1次")


class OptimizedUserService(UserServiceInterface):
    """
    用户服务实现（优化版）
    
    继承BaseService，提供用户管理的核心业务逻辑，包括用户认证、
    用户CRUD操作、密码管理等功能。仅支持数据库存储。
    """

    def __init__(self, session: Session, config: Optional[UserServiceConfig] = None):
        """
        初始化用户服务
        
        Args:
            session (Session): 数据库会话
            config (Optional[UserServiceConfig]): 服务配置
        """
        # 初始化配置
        self._user_config = config or UserServiceConfig()
        
        # 初始化基类
        super().__init__(session, self._user_config)
        
        # 密码哈希器
        if ARGON2_AVAILABLE and self._user_config.get('argon2_enabled', True):
            self._password_hasher = PasswordHasher()
        else:
            self._password_hasher = None

    def _initialize_components(self) -> None:
        """初始化服务特定的组件"""
        self._repository = UserRepository(self._session)

    def _on_start(self) -> None:
        """服务启动时的钩子方法"""
        self._logger.info("用户服务启动，开始初始化数据库连接")

    def _on_stop(self) -> None:
        """服务停止时的钩子方法"""
        self._logger.info("用户服务停止，清理数据库连接")

    def hash_password(self, password: str) -> str:
        """
        哈希密码
        
        Args:
            password (str): 原始密码
        
        Returns:
            str: 哈希后的密码
        """
        self._log_operation("hash_password")
        
        if self._password_hasher:
            return self._password_hasher.hash(password)
        else:
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        验证密码
        
        Args:
            password (str): 原始密码
            password_hash (str): 哈希后的密码
        
        Returns:
            bool: 密码是否正确
        """
        try:
            if self._password_hasher:
                self._password_hasher.verify(password_hash, password)
                return True
            else:
                import hashlib
                return password_hash == hashlib.sha256(password.encode()).hexdigest()
        except (VerifyMismatchError, Exception):
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[UserProfile]:
        """
        用户认证
        
        Args:
            username (str): 用户名或邮箱
            password (str): 密码
        
        Returns:
            Optional[UserProfile]: 认证成功的用户档案，如果认证失败则返回None
        """
        self._log_operation("authenticate_user", username=username)
        
        try:
            # 尝试通过用户名查找
            user = self._repository.get_by_username(username)
            if not user:
                # 尝试通过邮箱查找
                user = self._repository.get_by_email(username)
            
            if user and self.verify_password(password, user.password_hash):
                # 更新最后登录时间
                self._repository.update_last_login(user.id)
                # 重置失败登录次数
                self._repository.reset_failed_login(user.id)
                return user.to_pydantic(UserProfile)
            elif user:
                # 增加失败登录次数
                self._repository.increment_failed_login(user.id)
            
            return None

        except Exception as e:
            self._handle_error(e, "authenticate_user", username=username)
            return None

    def create_user(self, user_data: UserCreate, password: str) -> UserProfile:
        """
        创建用户
        
        Args:
            user_data (UserCreate): 用户创建数据
            password (str): 密码
        
        Returns:
            UserProfile: 创建的用户档案
        
        Raises:
            ValueError: 用户名或邮箱已存在
        """
        self._log_operation("create_user", username=user_data.username, email=user_data.email)
        
        try:
            # 验证密码强度
            self._validate_password_strength(password)
            
            password_hash = self.hash_password(password)
            user = self._repository.create_user(
                username=user_data.username,
                email=user_data.email,
                password_hash=password_hash,
                first_name=user_data.full_name,
            )
            return user.to_pydantic(UserProfile)

        except Exception as e:
            self._handle_error(e, "create_user", username=user_data.username, email=user_data.email)
            raise

    def get_user_by_id(self, user_id: int) -> Optional[UserProfile]:
        """
        根据ID获取用户
        
        Args:
            user_id (int): 用户ID
        
        Returns:
            Optional[UserProfile]: 用户档案，如果不存在则返回None
        """
        user = self._repository.get_by_id(user_id)
        return user.to_pydantic(UserProfile) if user else None

    def get_user_by_username(self, username: str) -> Optional[UserProfile]:
        """
        根据用户名获取用户
        
        Args:
            username (str): 用户名
        
        Returns:
            Optional[UserProfile]: 用户档案，如果不存在则返回None
        """
        user = self._repository.get_by_username(username)
        return user.to_pydantic(UserProfile) if user else None

    def get_user_by_email(self, email: str) -> Optional[UserProfile]:
        """
        根据邮箱获取用户
        
        Args:
            email (str): 邮箱地址
        
        Returns:
            Optional[UserProfile]: 用户档案，如果不存在则返回None
        """
        user = self._repository.get_by_email(email)
        return user.to_pydantic(UserProfile) if user else None

    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[UserProfile]:
        """
        更新用户信息
        
        Args:
            user_id (int): 用户ID
            user_data (UserUpdate): 用户更新数据
        
        Returns:
            Optional[UserProfile]: 更新后的用户档案，如果用户不存在则返回None
        """
        self._log_operation("update_user", user_id=user_id)
        
        try:
            user = self._repository.get_by_id(user_id)
            if not user:
                return None
            
            # 更新用户信息
            update_data = {}
            if user_data.full_name is not None:
                update_data['first_name'] = user_data.full_name
            if user_data.phone is not None:
                update_data['phone'] = user_data.phone
            if user_data.status is not None:
                update_data['status'] = user_data.status.value
            if user_data.role is not None:
                update_data['role'] = user_data.role.value
            if user_data.is_verified is not None:
                update_data['is_verified'] = user_data.is_verified
            if user_data.is_active is not None:
                update_data['is_active'] = user_data.is_active
            
            updated_user = self._repository.update(user_id, update_data)
            return updated_user.to_pydantic(UserProfile) if updated_user else None

        except Exception as e:
            self._handle_error(e, "update_user", user_id=user_id)
            return None

    def delete_user(self, user_id: int) -> bool:
        """
        删除用户
        
        Args:
            user_id (int): 用户ID
        
        Returns:
            bool: 是否删除成功
        """
        self._log_operation("delete_user", user_id=user_id)
        
        try:
            return self._repository.delete(user_id)
        except Exception as e:
            self._handle_error(e, "delete_user", user_id=user_id)
            return False

    def search_users(self, query: str, limit: int = 20, offset: int = 0) -> List[UserProfile]:
        """
        搜索用户
        
        Args:
            query (str): 搜索关键词
            limit (int): 限制数量
            offset (int): 偏移量
        
        Returns:
            List[UserProfile]: 用户档案列表
        """
        self._log_operation("search_users", query=query, limit=limit, offset=offset)
        
        try:
            users = self._repository.search_users(query, limit, offset)
            return [user.to_pydantic(UserProfile) for user in users]
        except Exception as e:
            self._handle_error(e, "search_users", query=query)
            return []

    def get_user_stats(self) -> UserStats:
        """
        获取用户统计信息
        
        Returns:
            UserStats: 用户统计信息
        """
        try:
            total_users = self._repository.count()
            active_users = self._repository.count_active_users()
            inactive_users = self._repository.count_inactive_users()
            
            return UserStats(
                total_users=total_users,
                active_users=active_users,
                inactive_users=inactive_users,
            )
        except Exception as e:
            self._handle_error(e, "get_user_stats")
            return UserStats(
                total_users=0,
                active_users=0,
                inactive_users=0,
            )

    def activate_user(self, user_id: int) -> Optional[UserProfile]:
        """
        激活用户
        
        Args:
            user_id (int): 用户ID
        
        Returns:
            Optional[UserProfile]: 更新后的用户档案
        """
        self._log_operation("activate_user", user_id=user_id)
        
        try:
            updated_user = self._repository.activate_user(user_id)
            return updated_user.to_pydantic(UserProfile) if updated_user else None
        except Exception as e:
            self._handle_error(e, "activate_user", user_id=user_id)
            return None

    def deactivate_user(self, user_id: int) -> Optional[UserProfile]:
        """
        停用用户
        
        Args:
            user_id (int): 用户ID
        
        Returns:
            Optional[UserProfile]: 更新后的用户档案
        """
        self._log_operation("deactivate_user", user_id=user_id)
        
        try:
            updated_user = self._repository.deactivate_user(user_id)
            return updated_user.to_pydantic(UserProfile) if updated_user else None
        except Exception as e:
            self._handle_error(e, "deactivate_user", user_id=user_id)
            return None

    def verify_user(self, user_id: int) -> Optional[UserProfile]:
        """
        验证用户
        
        Args:
            user_id (int): 用户ID
        
        Returns:
            Optional[UserProfile]: 更新后的用户档案
        """
        self._log_operation("verify_user", user_id=user_id)
        
        try:
            updated_user = self._repository.verify_user(user_id)
            return updated_user.to_pydantic(UserProfile) if updated_user else None
        except Exception as e:
            self._handle_error(e, "verify_user", user_id=user_id)
            return None

    def update_password(self, user_id: int, new_password: str) -> bool:
        """
        更新用户密码
        
        Args:
            user_id (int): 用户ID
            new_password (str): 新密码
        
        Returns:
            bool: 是否更新成功
        """
        self._log_operation("update_password", user_id=user_id)
        
        try:
            # 验证密码强度
            self._validate_password_strength(new_password)
            
            password_hash = self.hash_password(new_password)
            updated_user = self._repository.update_password(user_id, password_hash)
            return updated_user is not None
        except Exception as e:
            self._handle_error(e, "update_password", user_id=user_id)
            return False

    def get_recent_users(self, days: int = 7, limit: int = 20) -> List[UserProfile]:
        """
        获取最近注册的用户
        
        Args:
            days (int): 天数
            limit (int): 限制数量
        
        Returns:
            List[UserProfile]: 用户档案列表
        """
        try:
            users = self._repository.get_recent_records(days, limit)
            return [user.to_pydantic(UserProfile) for user in users]
        except Exception as e:
            self._handle_error(e, "get_recent_users", days=days, limit=limit)
            return []

    def get_active_users(self, limit: int = 20, offset: int = 0) -> List[UserProfile]:
        """
        获取活跃用户列表
        
        Args:
            limit (int): 限制数量
            offset (int): 偏移量
        
        Returns:
            List[UserProfile]: 用户档案列表
        """
        try:
            users = self._repository.list_active_users(limit, offset)
            return [user.to_pydantic(UserProfile) for user in users]
        except Exception as e:
            self._handle_error(e, "get_active_users", limit=limit, offset=offset)
            return []

    def _validate_password_strength(self, password: str) -> None:
        """
        验证密码强度
        
        Args:
            password (str): 密码
        
        Raises:
            ValueError: 密码不符合要求
        """
        min_length = self._user_config.get('password_min_length', 8)
        
        if len(password) < min_length:
            raise ValueError(f"密码长度至少需要{min_length}个字符")
        
        if self._user_config.get('password_require_special', True):
            import re
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValueError("密码必须包含至少一个特殊字符")
        
        # 检查是否包含数字
        if not any(c.isdigit() for c in password):
            raise ValueError("密码必须包含至少一个数字")
        
        # 检查是否包含字母
        if not any(c.isalpha() for c in password):
            raise ValueError("密码必须包含至少一个字母")
