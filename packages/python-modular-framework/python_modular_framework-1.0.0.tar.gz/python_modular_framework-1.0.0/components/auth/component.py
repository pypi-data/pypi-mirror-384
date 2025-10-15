"""
权限认证组件实现
- 实现ComponentInterface接口
- 提供统一的权限认证管理功能
- 支持RBAC权限模型和JWT令牌管理

主要功能：
- 权限管理
- 角色管理
- 用户认证
- 令牌管理
- 权限检查

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import asyncio
import threading
import time
import secrets
from typing import Any, Dict, List, Optional
from framework.interfaces.component import (
    ComponentInterface,
    ComponentStatus,
    ComponentInfo,
    ComponentError,
    ComponentInitializationError,
)
from .models import (
    PermissionModel,
    RoleModel,
    PermissionCreate,
    RoleCreate,
    LoginRequest,
    LoginResponse,
)
from .interfaces import AuthServiceInterface
from .service import AuthService


class AuthComponent(ComponentInterface):
    """
    权限认证组件

    提供统一的权限认证管理功能，支持RBAC权限模型、
    JWT令牌管理、用户认证等特性。
    """

    def __init__(self, name: str = "auth"):
        """
        初始化权限认证组件

        Args:
            name (str): 组件名称
        """
        self._name = name
        self._version = "0.1.0"
        self._description = "统一权限认证管理组件"
        self._dependencies = ["user"]  # 权限组件依赖用户组件
        self._status = ComponentStatus.UNINITIALIZED
        self._config = {}

        # 权限认证相关
        self._auth_service = None
        self._jwt_secret = None
        self._jwt_algorithm = "HS256"
        self._token_expiry = 3600  # 1小时
        self._refresh_token_expiry = 86400 * 7  # 7天

        # 统计信息
        self._stats = {
            "authentications": 0,
            "permission_checks": 0,
            "token_creations": 0,
            "token_revocations": 0,
            "failed_authentications": 0,
            "permission_denials": 0,
        }
        self._start_time = None

        # 清理任务
        self._cleanup_task = None
        self._shutdown_event = threading.Event()

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
        """获取组件依赖"""
        return self._dependencies

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化权限认证组件

        Args:
            config (Dict[str, Any]): 组件配置参数

        Raises:
            ComponentInitializationError: 初始化失败时抛出异常
        """
        try:
            self._status = ComponentStatus.INITIALIZING

            # 更新配置
            self._config = config or {}

            # 设置JWT配置
            self._jwt_secret = self._config.get("jwt_secret", self._generate_secret())
            self._jwt_algorithm = self._config.get("jwt_algorithm", "HS256")
            self._token_expiry = self._config.get("token_expiry", 3600)
            self._refresh_token_expiry = self._config.get(
                "refresh_token_expiry", 86400 * 7
            )

            # 获取数据库配置（必需）
            db_session = self._config.get('database_session')
            if not db_session:
                raise ValueError("database_session是必需的配置参数")
            
            # 创建缓存管理器
            cache_manager = None
            if self._config.get('redis_url'):
                from .cache import create_cache_manager
                cache_manager = create_cache_manager(redis_url=self._config['redis_url'])

            # 创建权限认证服务
            self._auth_service = AuthService(
                jwt_secret=self._jwt_secret,
                session=db_session,
                jwt_algorithm=self._jwt_algorithm,
                token_expiry=self._token_expiry,
                refresh_token_expiry=self._refresh_token_expiry,
                cache_manager=cache_manager,
            )

            self._status = ComponentStatus.INITIALIZED
            self._start_time = time.time()

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentInitializationError(
                self._name, f"Failed to initialize auth component: {e}"
            )

    def start(self) -> None:
        """
        启动权限认证组件

        Raises:
            ComponentError: 启动失败时抛出异常
        """
        if self._status != ComponentStatus.INITIALIZED:
            raise ComponentError(
                self._name, f"Cannot start component in status {self._status}"
            )

        try:
            self._status = ComponentStatus.STARTING

            # 创建数据库表
            if self._config.get('database_engine'):
                self._create_tables(self._config['database_engine'])

            # 启动清理任务
            self._start_cleanup_task()

            self._status = ComponentStatus.RUNNING

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentError(self._name, f"Failed to start auth component: {e}")
    
    def _create_tables(self, engine) -> None:
        """
        创建数据库表
        
        Args:
            engine: SQLAlchemy引擎实例
        """
        try:
            from .models import PermissionTable, RoleTable, UserRoleTable, TokenTable, role_permission_table
            from components.common.database.models import Base
            
            if PermissionTable is not None:
                Base.metadata.create_all(engine, tables=[
                    PermissionTable.__table__,
                    RoleTable.__table__,
                    UserRoleTable.__table__,
                    TokenTable.__table__,
                    role_permission_table,
                ], checkfirst=True)
                print(f"Auth tables created/verified")
        except Exception as e:
            print(f"Error creating auth tables: {e}")

    def stop(self) -> None:
        """
        停止权限认证组件

        Raises:
            ComponentError: 停止失败时抛出异常
        """
        if self._status not in [ComponentStatus.RUNNING, ComponentStatus.STARTING]:
            return

        try:
            self._status = ComponentStatus.STOPPING

            # 停止清理任务
            if self._cleanup_task:
                self._shutdown_event.set()
                self._cleanup_task.cancel()
                try:
                    asyncio.get_event_loop().run_until_complete(self._cleanup_task)
                except asyncio.CancelledError:
                    pass
                self._cleanup_task = None

            self._status = ComponentStatus.STOPPED

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentError(self._name, f"Failed to stop auth component: {e}")

    def get_status(self) -> ComponentStatus:
        """获取组件状态"""
        return self._status

    def get_info(self) -> ComponentInfo:
        """获取组件信息"""
        return ComponentInfo(
            name=self._name,
            version=self._version,
            description=self._description,
            dependencies=self._dependencies,
            status=self._status,
            config=self._config,
            metadata={
                "jwt_algorithm": self._jwt_algorithm,
                "token_expiry": self._token_expiry,
                "refresh_token_expiry": self._refresh_token_expiry,
                "stats": self._stats.copy(),
                "uptime": time.time() - self._start_time if self._start_time else 0,
            },
        )

    def get_config(self) -> Dict[str, Any]:
        """获取组件配置"""
        return self._config.copy()

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新组件配置

        Args:
            config (Dict[str, Any]): 新的配置参数
        """
        if self._status == ComponentStatus.RUNNING:
            # 运行时更新配置需要重新初始化
            self.stop()

        self._config.update(config)

        if self._status in [ComponentStatus.INITIALIZED, ComponentStatus.STOPPED]:
            self.initialize(self._config)

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 健康检查结果
        """
        health_status = {
            "status": "healthy",
            "message": "Auth component is running normally",
            "details": {
                "component_status": self._status.value,
                "jwt_algorithm": self._jwt_algorithm,
                "auth_service_available": self._auth_service is not None,
                "stats": self._stats.copy(),
            },
        }

        if self._status != ComponentStatus.RUNNING:
            health_status["status"] = "unhealthy"
            health_status["message"] = f"Component is not running: {self._status.value}"

        return health_status

    def _generate_secret(self) -> str:
        """生成JWT密钥"""
        return secrets.token_urlsafe(32)

    def _start_cleanup_task(self) -> None:
        """启动清理任务"""
        # 检查是否禁用清理任务
        cleanup_interval = self._config.get("cleanup_interval", 3600)
        if cleanup_interval <= 0:
            return

        # 检查是否有运行的事件循环
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 没有运行的事件循环，跳过异步任务
            print("No running event loop, skipping async cleanup task")
            return

        async def cleanup_worker():
            while not self._shutdown_event.is_set():
                try:
                    await asyncio.sleep(cleanup_interval)
                    self._cleanup_expired_tokens()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"Error in auth cleanup worker: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_worker())

    def _cleanup_expired_tokens(self) -> None:
        """清理过期令牌"""
        if self._auth_service:
            try:
                # 这里可以添加清理过期令牌的逻辑
                pass
            except Exception as e:
                print(f"Error cleaning up expired tokens: {e}")

    # 权限认证服务代理方法
    def get_auth_service(self) -> Optional[AuthServiceInterface]:
        """
        获取权限认证服务

        Returns:
            Optional[AuthServiceInterface]: 权限认证服务实例
        """
        return self._auth_service

    def authenticate_user(self, login_request: LoginRequest) -> Optional[LoginResponse]:
        """
        用户认证

        Args:
            login_request (LoginRequest): 登录请求

        Returns:
            Optional[LoginResponse]: 登录响应，如果认证失败则返回None
        """
        if not self._auth_service:
            return None

        try:
            result = self._auth_service.authenticate_user(login_request)
            if result:
                self._stats["authentications"] += 1
            else:
                self._stats["failed_authentications"] += 1
            return result
        except Exception as e:
            self._stats["failed_authentications"] += 1
            return None

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
        if not self._auth_service:
            return False

        try:
            result = self._auth_service.check_permission(user_id, resource, action)
            self._stats["permission_checks"] += 1
            if not result:
                self._stats["permission_denials"] += 1
            return result
        except Exception as e:
            self._stats["permission_denials"] += 1
            return False

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证令牌

        Args:
            token (str): 令牌字符串

        Returns:
            Optional[Dict[str, Any]]: 令牌载荷，如果无效则返回None
        """
        if not self._auth_service:
            return None

        try:
            return self._auth_service.verify_token(token)
        except Exception as e:
            return None

    def create_permission(
        self, permission_data: PermissionCreate
    ) -> Optional[PermissionModel]:
        """
        创建权限

        Args:
            permission_data (PermissionCreate): 权限创建数据

        Returns:
            Optional[PermissionModel]: 创建的权限对象
        """
        if not self._auth_service:
            return None

        try:
            return self._auth_service.create_permission(permission_data)
        except Exception as e:
            return None

    def create_role(self, role_data: RoleCreate) -> Optional[RoleModel]:
        """
        创建角色

        Args:
            role_data (RoleCreate): 角色创建数据

        Returns:
            Optional[RoleModel]: 创建的角色对象
        """
        if not self._auth_service:
            return None

        try:
            return self._auth_service.create_role(role_data)
        except Exception as e:
            return None

    def get_stats(self) -> Dict[str, Any]:
        """
        获取权限认证统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self._stats.copy()
        stats["uptime"] = time.time() - self._start_time if self._start_time else 0
        return stats

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "authentications": 0,
            "permission_checks": 0,
            "token_creations": 0,
            "token_revocations": 0,
            "failed_authentications": 0,
            "permission_denials": 0,
        }
