"""
权限认证服务实现
- 继承BaseService基类
- 使用ExtendedBaseRepository
- 提供权限认证的核心业务逻辑
- 支持JWT令牌生成和验证
- 集成数据库存储和Redis缓存

主要功能：
- 用户认证
- 权限检查
- 令牌管理
- 角色权限管理
- 缓存优化

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import jwt
import secrets
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

try:
    from components.common.service import BaseService, ServiceConfig
    from .repository import (
        PermissionRepository, RoleRepository, 
        UserRoleRepository, TokenRepository
    )
    from .cache import AuthCacheManager, create_cache_manager
    from sqlalchemy.orm import Session
    REPOSITORY_AVAILABLE = True
except ImportError:
    REPOSITORY_AVAILABLE = False
    BaseService = None
    ServiceConfig = None
    PermissionRepository = None
    RoleRepository = None
    UserRoleRepository = None
    TokenRepository = None
    AuthCacheManager = None
    create_cache_manager = None
    Session = None

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
    TokenType,
    PermissionType,
)
from .interfaces import (
    AuthServiceInterface,
    AuthError,
)


class AuthServiceConfig(ServiceConfig):
    """
    权限认证服务配置
    
    继承ServiceConfig，添加权限认证特定的配置项。
    """
    
    def __init__(self, **kwargs):
        """
        初始化权限认证服务配置
        
        Args:
            **kwargs: 配置参数
        """
        # 设置默认配置
        default_config = {
            'jwt_secret': kwargs.get('jwt_secret', 'default_secret_key'),
            'jwt_algorithm': kwargs.get('jwt_algorithm', 'HS256'),
            'token_expiry': kwargs.get('token_expiry', 3600),
            'refresh_token_expiry': kwargs.get('refresh_token_expiry', 86400 * 7),
            'cache_enabled': kwargs.get('cache_enabled', True),
            'cache_ttl': kwargs.get('cache_ttl', 300),
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
        required_keys = ['jwt_secret']
        missing_keys = []
        for key in required_keys:
            if key not in self._config or not self._config[key]:
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"缺少必需的配置项: {', '.join(missing_keys)}")
        
        # 验证JWT密钥长度
        if len(self._config['jwt_secret']) < 32:
            raise ValueError("JWT密钥长度至少需要32个字符")


class AuthService(BaseService, AuthServiceInterface):
    """
    权限认证服务

    继承BaseService，提供权限认证的核心业务逻辑，包括用户认证、
    权限检查、令牌管理等功能。支持数据库存储和Redis缓存。
    """

    def __init__(
        self,
        session: Session,
        config: Optional[AuthServiceConfig] = None,
        cache_manager: Optional[AuthCacheManager] = None,
    ):
        """
        初始化权限认证服务

        Args:
            session (Session): 数据库会话
            config (Optional[AuthServiceConfig]): 服务配置
            cache_manager (Optional[AuthCacheManager]): 缓存管理器
        """
        # 初始化配置
        self._auth_config = config or AuthServiceConfig()
        
        # 初始化基类
        super().__init__(session, self._auth_config)
        
        # 缓存管理器
        self._cache_manager = cache_manager or create_cache_manager()
        
        # 初始化默认权限和角色
        self._initialize_default_data()

    def _initialize_components(self) -> None:
        """初始化服务特定的组件"""
        # 数据库相关
        self._permission_repo = PermissionRepository(self._session)
        self._role_repo = RoleRepository(self._session)
        self._user_role_repo = UserRoleRepository(self._session)
        self._token_repo = TokenRepository(self._session)

    def _initialize_default_data(self) -> None:
        """初始化默认权限和角色"""
        try:
            # 创建默认权限
            default_permissions = [
                PermissionCreate(
                    name="用户管理",
                    code="user_manage",
                    description="管理用户信息",
                    resource="user",
                    action=PermissionType.WRITE,
                ),
                PermissionCreate(
                    name="用户查看",
                    code="user_read",
                    description="查看用户信息",
                    resource="user",
                    action=PermissionType.READ,
                ),
                PermissionCreate(
                    name="权限管理",
                    code="permission_manage",
                    description="管理权限信息",
                    resource="permission",
                    action=PermissionType.ADMIN,
                ),
                PermissionCreate(
                    name="角色管理",
                    code="role_manage",
                    description="管理角色信息",
                    resource="role",
                    action=PermissionType.ADMIN,
                ),
            ]

            for perm_data in default_permissions:
                self.create_permission(perm_data)

            # 创建默认角色
            default_roles = [
                RoleCreate(
                    name="管理员",
                    code="admin",
                    description="系统管理员",
                    permissions=[1, 2, 3, 4],  # 所有权限
                ),
                RoleCreate(
                    name="普通用户",
                    code="user",
                    description="普通用户",
                    permissions=[2],  # 只有查看权限
                ),
            ]

            for role_data in default_roles:
                self.create_role(role_data)
                
        except Exception as e:
            self._logger.warning(f"初始化默认数据时出现警告: {e}")

    def _on_start(self) -> None:
        """服务启动时的钩子方法"""
        self._logger.info("权限认证服务启动，开始初始化缓存和数据库连接")

    def _on_stop(self) -> None:
        """服务停止时的钩子方法"""
        self._logger.info("权限认证服务停止，清理缓存和数据库连接")

    # 权限管理
    def create_permission(self, permission_data: PermissionCreate) -> PermissionModel:
        """创建权限"""
        self._log_operation("create_permission", code=permission_data.code)
        
        try:
            # 检查权限代码是否已存在
            existing = self._permission_repo.get_by_code(permission_data.code)
            if existing:
                raise AuthError(f"权限代码 '{permission_data.code}' 已存在")

            # 创建权限
            permission_table = self._permission_repo.create({
                'name': permission_data.name,
                'code': permission_data.code,
                'description': permission_data.description,
                'resource': permission_data.resource,
                'action': permission_data.action.value,
            })

            return permission_table.to_pydantic(PermissionModel)

        except Exception as e:
            self._handle_error(e, "create_permission", code=permission_data.code)
            raise

    def get_permission_by_id(self, permission_id: int) -> Optional[PermissionModel]:
        """根据ID获取权限"""
        permission_table = self._permission_repo.get_by_id(permission_id)
        return permission_table.to_pydantic(PermissionModel) if permission_table else None

    def get_permission_by_code(self, code: str) -> Optional[PermissionModel]:
        """根据代码获取权限"""
        permission_table = self._permission_repo.get_by_code(code)
        return permission_table.to_pydantic(PermissionModel) if permission_table else None

    def list_permissions(self, resource: Optional[str] = None) -> List[PermissionModel]:
        """获取权限列表"""
        if resource:
            permission_tables = self._permission_repo.list_by_resource(resource)
        else:
            permission_tables = self._permission_repo.list_all()
        
        return [perm.to_pydantic(PermissionModel) for perm in permission_tables]

    def update_permission(
        self, permission_id: int, permission_data: Dict[str, Any]
    ) -> Optional[PermissionModel]:
        """更新权限"""
        self._log_operation("update_permission", permission_id=permission_id)
        
        try:
            updated_permission = self._permission_repo.update(permission_id, permission_data)
            return updated_permission.to_pydantic(PermissionModel) if updated_permission else None
        except Exception as e:
            self._handle_error(e, "update_permission", permission_id=permission_id)
            raise

    def delete_permission(self, permission_id: int) -> bool:
        """删除权限"""
        self._log_operation("delete_permission", permission_id=permission_id)
        return self._permission_repo.delete(permission_id)

    # 角色管理
    def create_role(self, role_data: RoleCreate) -> RoleModel:
        """创建角色"""
        self._log_operation("create_role", code=role_data.code)
        
        try:
            # 检查角色代码是否已存在
            existing = self._role_repo.get_by_code(role_data.code)
            if existing:
                raise AuthError(f"角色代码 '{role_data.code}' 已存在")

            # 创建角色
            role_table = self._role_repo.create({
                'name': role_data.name,
                'code': role_data.code,
                'description': role_data.description,
                'permissions': role_data.permissions,
            })

            return role_table.to_pydantic(RoleModel)

        except Exception as e:
            self._handle_error(e, "create_role", code=role_data.code)
            raise

    def get_role_by_id(self, role_id: int) -> Optional[RoleModel]:
        """根据ID获取角色"""
        role_table = self._role_repo.get_by_id(role_id)
        return role_table.to_pydantic(RoleModel) if role_table else None

    def get_role_by_code(self, code: str) -> Optional[RoleModel]:
        """根据代码获取角色"""
        role_table = self._role_repo.get_by_code(code)
        return role_table.to_pydantic(RoleModel) if role_table else None

    def list_roles(self) -> List[RoleModel]:
        """获取角色列表"""
        role_tables = self._role_repo.list_all()
        return [role.to_pydantic(RoleModel) for role in role_tables]

    def update_role(
        self, role_id: int, role_data: Dict[str, Any]
    ) -> Optional[RoleModel]:
        """更新角色"""
        self._log_operation("update_role", role_id=role_id)
        
        try:
            updated_role = self._role_repo.update(role_id, role_data)
            return updated_role.to_pydantic(RoleModel) if updated_role else None
        except Exception as e:
            self._handle_error(e, "update_role", role_id=role_id)
            raise

    def delete_role(self, role_id: int) -> bool:
        """删除角色"""
        self._log_operation("delete_role", role_id=role_id)
        return self._role_repo.delete(role_id)

    # 用户角色管理
    def assign_role_to_user(
        self, user_id: int, role_id: int, assigned_by: Optional[int] = None
    ) -> bool:
        """为用户分配角色"""
        self._log_operation("assign_role_to_user", user_id=user_id, role_id=role_id)
        
        try:
            return self._user_role_repo.assign_role_to_user(user_id, role_id, assigned_by)
        except Exception as e:
            self._handle_error(e, "assign_role_to_user", user_id=user_id, role_id=role_id)
            return False

    def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        """移除用户角色"""
        self._log_operation("remove_role_from_user", user_id=user_id, role_id=role_id)
        
        try:
            return self._user_role_repo.remove_role_from_user(user_id, role_id)
        except Exception as e:
            self._handle_error(e, "remove_role_from_user", user_id=user_id, role_id=role_id)
            return False

    def get_user_roles(self, user_id: int) -> List[RoleModel]:
        """获取用户角色列表"""
        # 先检查缓存
        if self._auth_config.get('cache_enabled', True):
            cached_roles = self._cache_manager.get_user_roles(user_id)
            if cached_roles:
                return [RoleModel(**role) for role in cached_roles]

        # 使用数据库获取角色
        role_tables = self._user_role_repo.get_user_roles(user_id)
        roles = [role.to_pydantic(RoleModel) for role in role_tables]

        # 缓存结果
        if roles and self._auth_config.get('cache_enabled', True):
            cache_data = [role.model_dump() for role in roles]
            self._cache_manager.cache_user_roles(user_id, cache_data)

        return roles

    def get_user_permissions(self, user_id: int) -> List[PermissionModel]:
        """获取用户权限列表"""
        # 先检查缓存
        if self._auth_config.get('cache_enabled', True):
            cached_permissions = self._cache_manager.get_user_permissions(user_id)
            if cached_permissions:
                return [PermissionModel(**perm) for perm in cached_permissions]

        # 使用数据库获取权限
        permission_tables = self._user_role_repo.get_user_permissions(user_id)
        permissions = [perm.to_pydantic(PermissionModel) for perm in permission_tables]

        # 缓存结果
        if permissions and self._auth_config.get('cache_enabled', True):
            cache_data = [perm.model_dump() for perm in permissions]
            self._cache_manager.cache_user_permissions(user_id, cache_data)

        return permissions

    # 权限检查
    def check_permission(self, user_id: int, resource: str, action: str) -> bool:
        """检查用户权限"""
        # 先检查缓存
        if self._auth_config.get('cache_enabled', True):
            cached_result = self._cache_manager.get_permission_check(user_id, resource, action)
            if cached_result is not None:
                return cached_result

        # 使用数据库检查权限
        has_permission = self._user_role_repo.check_user_permission(user_id, resource, action)

        # 缓存结果
        if self._auth_config.get('cache_enabled', True):
            self._cache_manager.cache_permission_check(user_id, resource, action, has_permission)
        
        return has_permission

    def check_permissions(self, permission_check: PermissionCheck) -> PermissionResult:
        """检查用户权限（详细）"""
        permissions = self.get_user_permissions(permission_check.user_id)
        roles = self.get_user_roles(permission_check.user_id)

        allowed = False
        relevant_permissions = []
        relevant_roles = []

        for permission in permissions:
            if permission.resource == permission_check.resource:
                relevant_permissions.append(permission.code)
                if permission.action.value == permission_check.action.value:
                    allowed = True

        for role in roles:
            for perm_id in role.permissions:
                permission = self.get_permission_by_id(perm_id)
                if permission and permission.resource == permission_check.resource:
                    relevant_roles.append(role.code)
                    break

        return PermissionResult(
            allowed=allowed,
            reason=None if allowed else "Insufficient permissions",
            permissions=relevant_permissions,
            roles=relevant_roles,
        )

    # 认证管理
    def authenticate_user(self, login_request: LoginRequest) -> Optional[LoginResponse]:
        """用户认证"""
        self._log_operation("authenticate_user", username=login_request.username)
        
        try:
            # 这里应该与用户组件集成，验证用户名/邮箱和密码
            # 为了演示，我们使用简单的验证逻辑

            # 模拟用户验证（实际应用中应该查询用户数据库）
            if not self._validate_user_credentials(login_request):
                return None

            # 获取用户ID（实际应用中应该从用户数据库获取）
            user_id = self._get_user_id_by_credentials(login_request)
            if not user_id:
                return None

            # 生成令牌
            access_token = self._generate_access_token(user_id)
            refresh_token = self._generate_refresh_token(user_id)

            # 存储令牌
            self._store_token(access_token, user_id, TokenType.ACCESS)
            self._store_token(refresh_token, user_id, TokenType.REFRESH)

            # 获取用户信息
            user_info = self._get_user_info(user_id)

            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=self._auth_config.get('token_expiry'),
                user_info=user_info,
            )

        except Exception as e:
            self._handle_error(e, "authenticate_user", username=login_request.username)
            return None

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token, 
                self._auth_config.get('jwt_secret'), 
                algorithms=[self._auth_config.get('jwt_algorithm')]
            )

            # 检查令牌是否被撤销
            token_obj = self._token_repo.get_by_token(token)
            if token_obj and token_obj.is_revoked:
                return None

            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def refresh_token(self, refresh_token: str) -> Optional[LoginResponse]:
        """刷新令牌"""
        payload = self.verify_token(refresh_token)
        if not payload:
            return None

        user_id = payload.get("user_id")
        if not user_id:
            return None

        # 生成新的访问令牌
        access_token = self._generate_access_token(user_id)

        # 存储新令牌
        self._store_token(access_token, user_id, TokenType.ACCESS)

        # 获取用户信息
        user_info = self._get_user_info(user_id)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # 刷新令牌保持不变
            token_type="Bearer",
            expires_in=self._auth_config.get('token_expiry'),
            user_info=user_info,
        )

    def revoke_token(self, token: str) -> bool:
        """撤销令牌"""
        return self._token_repo.revoke_token(token)

    # 令牌管理
    def create_token(self, token_data: TokenCreate) -> TokenModel:
        """创建令牌"""
        token_string = self._generate_token_string()
        expires_at = datetime.utcnow() + timedelta(seconds=token_data.expires_in)

        token_table = self._token_repo.create_token(
            user_id=token_data.user_id,
            token=token_string,
            token_type=token_data.token_type.value,
            expires_at=expires_at,
        )

        return token_table.to_pydantic(TokenModel)

    def get_token_by_string(self, token: str) -> Optional[TokenModel]:
        """根据令牌字符串获取令牌"""
        token_table = self._token_repo.get_by_token(token)
        return token_table.to_pydantic(TokenModel) if token_table else None

    def list_user_tokens(
        self, user_id: int, token_type: Optional[str] = None
    ) -> List[TokenModel]:
        """获取用户令牌列表"""
        token_tables = self._token_repo.list_user_tokens(user_id, token_type)
        return [token.to_pydantic(TokenModel) for token in token_tables]

    def revoke_user_tokens(self, user_id: int, token_type: Optional[str] = None) -> int:
        """撤销用户令牌"""
        return self._token_repo.revoke_user_tokens(user_id, token_type)

    # 私有方法
    def _validate_user_credentials(self, login_request: LoginRequest) -> bool:
        """验证用户凭据"""
        # 这里应该与用户组件集成
        # 为了演示，我们使用简单的验证逻辑
        username = login_request.username or login_request.email
        return username and login_request.password

    def _get_user_id_by_credentials(self, login_request: LoginRequest) -> Optional[int]:
        """根据凭据获取用户ID"""
        # 这里应该与用户组件集成
        # 为了演示，我们返回一个固定的用户ID
        return 1

    def _get_user_info(self, user_id: int) -> Dict[str, Any]:
        """获取用户信息"""
        # 这里应该与用户组件集成
        # 为了演示，我们返回模拟的用户信息
        return {
            "id": user_id,
            "username": "demo_user",
            "email": "demo@example.com",
            "roles": [role.code for role in self.get_user_roles(user_id)],
        }

    def _generate_access_token(self, user_id: int) -> str:
        """生成访问令牌"""
        payload = {
            "user_id": user_id,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(seconds=self._auth_config.get('token_expiry')),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self._auth_config.get('jwt_secret'), algorithm=self._auth_config.get('jwt_algorithm'))

    def _generate_refresh_token(self, user_id: int) -> str:
        """生成刷新令牌"""
        payload = {
            "user_id": user_id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(seconds=self._auth_config.get('refresh_token_expiry')),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self._auth_config.get('jwt_secret'), algorithm=self._auth_config.get('jwt_algorithm'))

    def _generate_token_string(self) -> str:
        """生成令牌字符串"""
        return secrets.token_urlsafe(32)

    def _store_token(self, token: str, user_id: int, token_type: TokenType) -> None:
        """存储令牌"""
        expires_in = (
            self._auth_config.get('token_expiry')
            if token_type == TokenType.ACCESS
            else self._auth_config.get('refresh_token_expiry')
        )
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        self._token_repo.create_token(
            user_id=user_id,
            token=token,
            token_type=token_type.value,
            expires_at=expires_at,
        )
