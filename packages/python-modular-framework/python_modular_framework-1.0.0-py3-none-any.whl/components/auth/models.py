"""
权限认证数据模型
- 定义权限认证相关的数据模型
- 提供RBAC权限模型支持
- 支持JWT令牌管理

主要模型：
- PermissionModel: 权限模型（Pydantic）
- RoleModel: 角色模型（Pydantic）
- UserRoleModel: 用户角色关联模型（Pydantic）
- TokenModel: 令牌模型（Pydantic）
- PermissionTable: 权限表模型（SQLAlchemy）
- RoleTable: 角色表模型（SQLAlchemy）
- UserRoleTable: 用户角色关联表模型（SQLAlchemy）
- TokenTable: 令牌表模型（SQLAlchemy）

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Table,
    Index,
)
from sqlalchemy.orm import relationship

try:
    from components.common.database.models import BaseModel as DBBaseModel

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    DBBaseModel = None


class PermissionType(str, Enum):
    """权限类型枚举"""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class TokenType(str, Enum):
    """令牌类型枚举"""

    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"
    VERIFY = "verify"


class PermissionModel(BaseModel):
    """
    权限模型

    定义系统中的权限信息。
    """

    id: Optional[int] = Field(default=None, description="权限ID")
    name: str = Field(..., min_length=1, max_length=100, description="权限名称")
    code: str = Field(..., min_length=1, max_length=50, description="权限代码")
    description: Optional[str] = Field(
        default=None, max_length=500, description="权限描述"
    )
    resource: str = Field(..., min_length=1, max_length=100, description="资源名称")
    action: PermissionType = Field(..., description="权限动作")
    is_active: bool = Field(default=True, description="是否激活")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证权限代码"""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Permission code must contain only alphanumeric characters, underscores, and hyphens"
            )
        return v.lower()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """验证权限名称"""
        if not v.strip():
            raise ValueError("Permission name cannot be empty")
        return v.strip()

    class Config:
        """模型配置"""

        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class RoleModel(BaseModel):
    """
    角色模型

    定义系统中的角色信息。
    """

    id: Optional[int] = Field(default=None, description="角色ID")
    name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    code: str = Field(..., min_length=1, max_length=50, description="角色代码")
    description: Optional[str] = Field(
        default=None, max_length=500, description="角色描述"
    )
    is_system: bool = Field(default=False, description="是否系统角色")
    is_active: bool = Field(default=True, description="是否激活")
    permissions: List[int] = Field(default_factory=list, description="权限ID列表")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证角色代码"""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Role code must contain only alphanumeric characters, underscores, and hyphens"
            )
        return v.lower()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """验证角色名称"""
        if not v.strip():
            raise ValueError("Role name cannot be empty")
        return v.strip()

    class Config:
        """模型配置"""

        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserRoleModel(BaseModel):
    """
    用户角色关联模型

    定义用户和角色的关联关系。
    """

    id: Optional[int] = Field(default=None, description="关联ID")
    user_id: int = Field(..., description="用户ID")
    role_id: int = Field(..., description="角色ID")
    assigned_by: Optional[int] = Field(default=None, description="分配者ID")
    assigned_at: Optional[datetime] = Field(default=None, description="分配时间")
    expires_at: Optional[datetime] = Field(default=None, description="过期时间")
    is_active: bool = Field(default=True, description="是否激活")

    class Config:
        """模型配置"""

        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class TokenModel(BaseModel):
    """
    令牌模型

    定义JWT令牌信息。
    """

    id: Optional[int] = Field(default=None, description="令牌ID")
    user_id: int = Field(..., description="用户ID")
    token: str = Field(..., description="令牌字符串")
    token_type: TokenType = Field(..., description="令牌类型")
    expires_at: datetime = Field(..., description="过期时间")
    is_revoked: bool = Field(default=False, description="是否已撤销")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    revoked_at: Optional[datetime] = Field(default=None, description="撤销时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    class Config:
        """模型配置"""

        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class PermissionCreate(BaseModel):
    """
    权限创建模型

    用于创建新权限时的数据验证。
    """

    name: str = Field(..., min_length=1, max_length=100, description="权限名称")
    code: str = Field(..., min_length=1, max_length=50, description="权限代码")
    description: Optional[str] = Field(
        default=None, max_length=500, description="权限描述"
    )
    resource: str = Field(..., min_length=1, max_length=100, description="资源名称")
    action: PermissionType = Field(..., description="权限动作")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证权限代码"""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Permission code must contain only alphanumeric characters, underscores, and hyphens"
            )
        return v.lower()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """验证权限名称"""
        if not v.strip():
            raise ValueError("Permission name cannot be empty")
        return v.strip()


class RoleCreate(BaseModel):
    """
    角色创建模型

    用于创建新角色时的数据验证。
    """

    name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    code: str = Field(..., min_length=1, max_length=50, description="角色代码")
    description: Optional[str] = Field(
        default=None, max_length=500, description="角色描述"
    )
    permissions: List[int] = Field(default_factory=list, description="权限ID列表")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证角色代码"""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Role code must contain only alphanumeric characters, underscores, and hyphens"
            )
        return v.lower()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """验证角色名称"""
        if not v.strip():
            raise ValueError("Role name cannot be empty")
        return v.strip()


class TokenCreate(BaseModel):
    """
    令牌创建模型

    用于创建新令牌时的数据验证。
    """

    user_id: int = Field(..., description="用户ID")
    token_type: TokenType = Field(..., description="令牌类型")
    expires_in: int = Field(default=3600, ge=60, le=86400, description="过期时间（秒）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    @field_validator("expires_in")
    @classmethod
    def validate_expires_in(cls, v):
        """验证过期时间"""
        if v < 60:
            raise ValueError("Token expiration time must be at least 60 seconds")
        if v > 86400:
            raise ValueError("Token expiration time cannot exceed 24 hours")
        return v


class LoginRequest(BaseModel):
    """
    登录请求模型

    用于用户登录时的数据验证。
    """

    username: Optional[str] = Field(default=None, description="用户名")
    email: Optional[str] = Field(default=None, description="邮箱地址")
    password: str = Field(..., min_length=1, description="密码")
    remember_me: bool = Field(default=False, description="记住我")

    @field_validator("username", "email")
    @classmethod
    def validate_credentials(cls, v, info):
        """验证登录凭据"""
        if not v and not info.data.get("email"):
            raise ValueError("Either username or email must be provided")
        return v


class LoginResponse(BaseModel):
    """
    登录响应模型

    用于返回登录结果。
    """

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user_info: Dict[str, Any] = Field(..., description="用户信息")


class PermissionCheck(BaseModel):
    """
    权限检查模型

    用于权限检查请求。
    """

    user_id: int = Field(..., description="用户ID")
    resource: str = Field(..., description="资源名称")
    action: PermissionType = Field(..., description="权限动作")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")


class PermissionResult(BaseModel):
    """
    权限检查结果模型

    用于返回权限检查结果。
    """

    allowed: bool = Field(..., description="是否允许")
    reason: Optional[str] = Field(default=None, description="原因")
    permissions: List[str] = Field(default_factory=list, description="相关权限列表")
    roles: List[str] = Field(default_factory=list, description="相关角色列表")


# SQLAlchemy数据库表模型
if SQLALCHEMY_AVAILABLE:
    # 角色-权限关联表（多对多）
    role_permission_table = Table(
        "role_permissions",
        DBBaseModel.metadata,
        Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
        Column(
            "permission_id", Integer, ForeignKey("permissions.id"), primary_key=True
        ),
        Index("idx_role_permission", "role_id", "permission_id"),
    )

    class PermissionTable(DBBaseModel):
        """
        权限数据库表模型

        对应数据库中的permissions表。
        """

        __tablename__ = "permissions"

        # 基本信息
        name = Column(String(100), nullable=False, index=True)
        code = Column(String(50), unique=True, nullable=False, index=True)
        description = Column(Text, nullable=True)

        # 权限定义
        resource = Column(String(100), nullable=False, index=True)
        action = Column(String(20), nullable=False, index=True)

        # 状态
        is_active = Column(Boolean, nullable=False, default=True)

        # 关系
        roles = relationship(
            "RoleTable", secondary=role_permission_table, back_populates="permissions"
        )

        # 索引
        __table_args__ = (
            Index("idx_permission_code", "code"),
            Index("idx_permission_resource", "resource"),
            Index("idx_permission_action", "action"),
            Index("idx_permission_resource_action", "resource", "action"),
        )

        def to_pydantic(self) -> "PermissionModel":
            """
            转换为Pydantic模型

            Returns:
                PermissionModel: Pydantic权限模型
            """
            return PermissionModel(
                id=self.id,
                name=self.name,
                code=self.code,
                description=self.description,
                resource=self.resource,
                action=PermissionType(self.action),
                is_active=self.is_active,
                created_at=self.created_at,
                updated_at=self.updated_at,
            )

    class RoleTable(DBBaseModel):
        """
        角色数据库表模型

        对应数据库中的roles表。
        """

        __tablename__ = "roles"

        # 基本信息
        name = Column(String(100), nullable=False, index=True)
        code = Column(String(50), unique=True, nullable=False, index=True)
        description = Column(Text, nullable=True)

        # 状态
        is_system = Column(Boolean, nullable=False, default=False)
        is_active = Column(Boolean, nullable=False, default=True)

        # 关系
        permissions = relationship(
            "PermissionTable", secondary=role_permission_table, back_populates="roles"
        )
        user_roles = relationship("UserRoleTable", back_populates="role")

        # 索引
        __table_args__ = (
            Index("idx_role_code", "code"),
            Index("idx_role_system", "is_system"),
        )

        def to_pydantic(self) -> "RoleModel":
            """
            转换为Pydantic模型

            Returns:
                RoleModel: Pydantic角色模型
            """
            return RoleModel(
                id=self.id,
                name=self.name,
                code=self.code,
                description=self.description,
                is_system=self.is_system,
                is_active=self.is_active,
                permissions=[p.id for p in self.permissions],
                created_at=self.created_at,
                updated_at=self.updated_at,
            )

    class UserRoleTable(DBBaseModel):
        """
        用户角色关联数据库表模型

        对应数据库中的user_roles表。
        """

        __tablename__ = "user_roles"

        # 关联信息
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
        role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)

        # 分配信息
        assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
        assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
        expires_at = Column(DateTime, nullable=True)

        # 状态
        is_active = Column(Boolean, nullable=False, default=True)

        # 关系
        role = relationship("RoleTable", back_populates="user_roles")

        # 索引
        __table_args__ = (
            Index("idx_user_role_user", "user_id"),
            Index("idx_user_role_role", "role_id"),
            Index("idx_user_role_active", "is_active"),
            Index("idx_user_role_unique", "user_id", "role_id", unique=True),
        )

        def to_pydantic(self) -> "UserRoleModel":
            """
            转换为Pydantic模型

            Returns:
                UserRoleModel: Pydantic用户角色模型
            """
            return UserRoleModel(
                id=self.id,
                user_id=self.user_id,
                role_id=self.role_id,
                assigned_by=self.assigned_by,
                assigned_at=self.assigned_at,
                expires_at=self.expires_at,
                is_active=self.is_active,
            )

    class TokenTable(DBBaseModel):
        """
        令牌数据库表模型

        对应数据库中的tokens表。
        """

        __tablename__ = "tokens"

        # 关联信息
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

        # 令牌信息
        token = Column(String(500), unique=True, nullable=False, index=True)
        token_type = Column(String(20), nullable=False, index=True)

        # 时间信息
        expires_at = Column(DateTime, nullable=False, index=True)

        # 状态
        is_revoked = Column(Boolean, nullable=False, default=False)
        revoked_at = Column(DateTime, nullable=True)

        # 元数据
        metadata_json = Column(Text, nullable=True)

        # 索引
        __table_args__ = (
            Index("idx_token_user", "user_id"),
            Index("idx_token_type", "token_type"),
            Index("idx_token_expires", "expires_at"),
            Index("idx_token_revoked", "is_revoked"),
        )

        def to_pydantic(self) -> "TokenModel":
            """
            转换为Pydantic模型

            Returns:
                TokenModel: Pydantic令牌模型
            """
            return TokenModel(
                id=self.id,
                user_id=self.user_id,
                token=self.token,
                token_type=TokenType(self.token_type),
                expires_at=self.expires_at,
                is_revoked=self.is_revoked,
                created_at=self.created_at,
                revoked_at=self.revoked_at,
                metadata=eval(self.metadata_json) if self.metadata_json else {},
            )

else:
    PermissionTable = None
    RoleTable = None
    UserRoleTable = None
    TokenTable = None
    role_permission_table = None
