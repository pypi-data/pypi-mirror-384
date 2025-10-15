"""
用户管理组件实现
- 实现ComponentInterface接口
- 提供统一的用户管理功能
- 支持用户CRUD操作和认证

主要功能：
- 用户管理
- 用户认证
- 用户信息管理
- 用户搜索和统计

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import time
from typing import Any, Dict, List, Optional
from framework.interfaces.component import (
    ComponentInterface,
    ComponentStatus,
    ComponentInfo,
    ComponentError,
    ComponentInitializationError,
)

from .models import (
    UserModel,
    UserCreate,
    UserUpdate,
    UserSearch,
    UserSearchResult,
    UserStats,
)
from .service import OptimizedUserService


class UserComponent(ComponentInterface):
    """
    用户管理组件

    提供统一的用户管理功能，支持用户CRUD操作、
    用户认证、用户信息管理、用户搜索和统计等特性。
    """

    def __init__(self, name: str = "user"):
        """
        初始化用户管理组件

        Args:
            name (str): 组件名称
        """
        self._name = name
        self._version = "0.1.0"
        self._description = "统一用户管理组件"
        self._dependencies = []  # 用户组件没有依赖
        self._status = ComponentStatus.UNINITIALIZED
        self._config = {}

        # 用户相关
        self._user_service = None
        self._startup_time = None
        self._stats = {
            "users_created": 0,
            "users_updated": 0,
            "users_deleted": 0,
            "users_searched": 0,
            "authentications": 0,
            "failed_authentications": 0,
        }

    @property
    def name(self) -> str:
        """获取组件名称"""
        return self._name

    @property
    def version(self) -> str:
        """获取组件版本"""
        return self._version

    @property
    def description(self) -> str:
        """获取组件描述"""
        return self._description

    @property
    def dependencies(self) -> List[str]:
        """获取组件依赖列表"""
        return self._dependencies.copy()

    def get_info(self) -> ComponentInfo:
        """
        获取组件信息

        Returns:
            ComponentInfo: 组件信息对象
        """
        return ComponentInfo(
            name=self._name,
            version=self._version,
            description=self._description,
            dependencies=self._dependencies,
            status=self._status,
            config=self._config.copy(),
            metadata={"component_type": "user_management"},
        )

    def get_status(self) -> ComponentStatus:
        """
        获取组件当前状态

        Returns:
            ComponentStatus: 组件当前状态
        """
        return self._status

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化组件

        Args:
            config (Dict[str, Any]): 组件配置参数

        Raises:
            ComponentInitializationError: 初始化失败时抛出异常
        """
        try:
            self._status = ComponentStatus.INITIALIZING

            # 更新配置
            self._config.update(config)

            # 获取数据库会话（必需）
            db_session = config.get('database_session')
            if not db_session:
                raise ValueError("database_session是必需的配置参数")

            # 初始化用户服务
            self._user_service = OptimizedUserService(session=db_session)

            self._status = ComponentStatus.INITIALIZED
            print(f"Component '{self._name}' initialized with database session")

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentInitializationError(
                self._name, f"Failed to initialize component: {e}"
            )

    def start(self) -> None:
        """
        启动组件

        Raises:
            ComponentError: 启动失败时抛出异常
        """
        try:
            self._status = ComponentStatus.STARTING
            self._startup_time = time.time()

            # 创建数据库表（如果使用数据库）
            if self._config.get('database_engine'):
                self._create_tables(self._config['database_engine'])

            # 启动用户服务
            if self._user_service:
                self._user_service.start()

            self._status = ComponentStatus.RUNNING
            print(f"Component '{self._name}' started")

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentError(self._name, f"Failed to start component: {e}")

    def _create_tables(self, engine) -> None:
        """
        创建数据库表
        
        Args:
            engine: SQLAlchemy引擎
        """
        try:
            from .models import UserTable
            from components.common.database.models import Base
            
            if UserTable is not None:
                # 只创建用户表
                Base.metadata.create_all(engine, tables=[UserTable.__table__], checkfirst=True)
                print(f"User tables created/verified")
        except Exception as e:
            print(f"Error creating user tables: {e}")

    def stop(self) -> None:
        """
        停止组件

        Raises:
            ComponentError: 停止失败时抛出异常
        """
        try:
            self._status = ComponentStatus.STOPPING

            # 停止用户服务
            if self._user_service:
                self._user_service.stop()

            self._status = ComponentStatus.STOPPED
            print(f"Component '{self._name}' stopped")

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentError(self._name, f"Failed to stop component: {e}")

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新组件配置

        Args:
            config (Dict[str, Any]): 新的配置参数
        """
        self._config.update(config)
        print(f"Component '{self._name}' config updated")

    def health_check(self) -> Dict[str, Any]:
        """
        组件健康检查

        Returns:
            Dict[str, Any]: 健康检查结果
        """
        health_status = {
            "status": (
                "healthy" if self._status == ComponentStatus.RUNNING else "unhealthy"
            ),
            "message": (
                "User component is running normally"
                if self._status == ComponentStatus.RUNNING
                else f"User component is {self._status.value}"
            ),
            "details": {
                "component_status": self._status.value,
                "user_service_available": self._user_service is not None,
                "uptime": time.time() - self._startup_time if self._startup_time else 0,
                "stats": self._stats.copy(),
            },
        }

        if self._status != ComponentStatus.RUNNING:
            health_status["status"] = "unhealthy"
            health_status["message"] = (
                f"User component is not running: {self._status.value}"
            )

        return health_status

    def get_metrics(self) -> Dict[str, Any]:
        """
        获取组件指标

        Returns:
            Dict[str, Any]: 组件指标数据
        """
        return {
            "component": {
                "name": self._name,
                "version": self._version,
                "status": self._status.value,
                "uptime": time.time() - self._startup_time if self._startup_time else 0,
            },
            "user_service": {
                "available": self._user_service is not None,
                "stats": self._stats.copy(),
            },
            "timestamp": time.time(),
        }

    def get_config(self) -> Dict[str, Any]:
        """
        获取组件配置

        Returns:
            Dict[str, Any]: 组件配置
        """
        return self._config.copy()

    # 用户服务方法
    def create_user(self, user_data: UserCreate) -> UserModel:
        """
        创建用户

        Args:
            user_data (UserCreate): 用户创建数据

        Returns:
            UserModel: 创建的用户对象
        """
        if not self._user_service:
            raise ComponentError(self._name, "User service not available")

        user = self._user_service.create_user(user_data)
        self._stats["users_created"] += 1
        return user

    def get_user(self, user_id: str) -> Optional[UserModel]:
        """
        获取用户信息

        Args:
            user_id (str): 用户ID

        Returns:
            Optional[UserModel]: 用户对象，如果不存在则返回None
        """
        if not self._user_service:
            raise ComponentError(self._name, "User service not available")

        return self._user_service.get_user(user_id)

    def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[UserModel]:
        """
        更新用户信息

        Args:
            user_id (str): 用户ID
            user_data (UserUpdate): 用户更新数据

        Returns:
            Optional[UserModel]: 更新后的用户对象，如果不存在则返回None
        """
        if not self._user_service:
            raise ComponentError(self._name, "User service not available")

        user = self._user_service.update_user(user_id, user_data)
        if user:
            self._stats["users_updated"] += 1
        return user

    def delete_user(self, user_id: str) -> bool:
        """
        删除用户

        Args:
            user_id (str): 用户ID

        Returns:
            bool: 删除是否成功
        """
        if not self._user_service:
            raise ComponentError(self._name, "User service not available")

        success = self._user_service.delete_user(user_id)
        if success:
            self._stats["users_deleted"] += 1
        return success

    def search_users(self, search_params: UserSearch) -> UserSearchResult:
        """
        搜索用户

        Args:
            search_params (UserSearch): 搜索参数

        Returns:
            UserSearchResult: 搜索结果
        """
        if not self._user_service:
            raise ComponentError(self._name, "User service not available")

        result = self._user_service.search_users(search_params)
        self._stats["users_searched"] += 1
        return result

    def get_user_stats(self) -> UserStats:
        """
        获取用户统计信息

        Returns:
            UserStats: 用户统计信息
        """
        if not self._user_service:
            raise ComponentError(self._name, "User service not available")

        return self._user_service.get_user_stats()


class UserService:
    """用户服务实现"""

    def __init__(self):
        """初始化用户服务"""
        self._users: Dict[str, UserModel] = {}
        self._running = False

    def start(self) -> None:
        """启动用户服务"""
        self._running = True
        print("User service started")

    def stop(self) -> None:
        """停止用户服务"""
        self._running = False
        print("User service stopped")

    def create_user(self, user_data: UserCreate) -> UserModel:
        """创建用户"""
        user_id = f"user_{len(self._users) + 1}"
        user = UserModel(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            is_active=True,
            created_at=time.time(),
            updated_at=time.time(),
        )
        self._users[user_id] = user
        return user

    def get_user(self, user_id: str) -> Optional[UserModel]:
        """获取用户"""
        return self._users.get(user_id)

    def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[UserModel]:
        """更新用户"""
        if user_id not in self._users:
            return None

        user = self._users[user_id]
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        user.updated_at = time.time()
        return user

    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False

    def search_users(self, search_params: UserSearch) -> UserSearchResult:
        """搜索用户"""
        # 简单的搜索实现
        results = []
        for user in self._users.values():
            if (
                search_params.username
                and search_params.username.lower() not in user.username.lower()
            ):
                continue
            if (
                search_params.email
                and search_params.email.lower() not in user.email.lower()
            ):
                continue
            results.append(user)

        return UserSearchResult(
            users=results,
            total=len(results),
            page=search_params.page,
            page_size=search_params.page_size,
        )

    def get_user_stats(self) -> UserStats:
        """获取用户统计信息"""
        total_users = len(self._users)
        active_users = sum(1 for user in self._users.values() if user.is_active)

        return UserStats(
            total_users=total_users,
            active_users=active_users,
            inactive_users=total_users - active_users,
        )
