"""
用户数据模型
- 定义用户相关的数据模型
- 提供数据验证和序列化功能
- 支持用户创建、更新等操作

主要模型：
- UserModel: 用户基础模型（Pydantic）
- UserTable: 用户数据库表模型（SQLAlchemy）
- UserCreate: 用户创建模型
- UserUpdate: 用户更新模型

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, EmailStr
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, Text, Index, DateTime

try:
    from components.common.database.models import BaseModel as DBBaseModel
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    DBBaseModel = None


class UserStatus(str, Enum):
    """用户状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserRole(str, Enum):
    """用户角色枚举"""

    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    GUEST = "guest"


class UserModel(BaseModel):
    """
    用户基础模型

    定义用户的基本信息和属性。
    """

    id: str = Field(..., description="用户ID")
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(default=None, description="全名")
    is_active: bool = Field(default=True, description="是否激活")
    created_at: float = Field(..., description="创建时间")
    updated_at: float = Field(..., description="更新时间")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """验证用户名"""
        if not v.isalnum():
            raise ValueError("Username must contain only alphanumeric characters")
        return v.lower()

    class Config:
        """模型配置"""

        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserCreate(BaseModel):
    """
    用户创建模型

    用于创建新用户时的数据验证。
    """

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(default=None, description="全名")


class UserUpdate(BaseModel):
    """
    用户更新模型

    用于更新用户信息时的数据验证。
    """

    full_name: Optional[str] = Field(default=None, description="全名")
    email: Optional[str] = Field(default=None, description="邮箱地址")
    is_active: Optional[bool] = Field(default=None, description="是否激活")


class UserLogin(BaseModel):
    """
    用户登录模型

    用于用户登录时的数据验证。
    """

    username: Optional[str] = Field(default=None, description="用户名")
    email: Optional[EmailStr] = Field(default=None, description="邮箱地址")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(default=False, description="记住我")

    @field_validator("username", "email")
    @classmethod
    def validate_credentials(cls, v, info):
        """验证登录凭据"""
        if not v and not info.data.get("email"):
            raise ValueError("Either username or email must be provided")
        return v


class UserProfile(BaseModel):
    """
    用户档案模型

    用于返回用户公开信息。
    """

    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    first_name: Optional[str] = Field(default=None, description="名字")
    last_name: Optional[str] = Field(default=None, description="姓氏")
    phone: Optional[str] = Field(default=None, description="电话号码")
    avatar_url: Optional[str] = Field(default=None, description="头像URL")
    status: UserStatus = Field(..., description="用户状态")
    role: UserRole = Field(..., description="用户角色")
    is_verified: bool = Field(..., description="是否已验证")
    last_login: Optional[datetime] = Field(default=None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        """模型配置"""

        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserSearch(BaseModel):
    """
    用户搜索模型

    用于用户搜索时的查询参数。
    """

    username: Optional[str] = Field(default=None, description="用户名")
    email: Optional[str] = Field(default=None, description="邮箱地址")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")

    class Config:
        """模型配置"""

        json_encoders = {datetime: lambda v: v.isoformat()}


class UserSearchResult(BaseModel):
    """
    用户搜索结果模型

    用于返回用户搜索结果。
    """

    users: List[UserModel] = Field(..., description="用户列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")

    class Config:
        """模型配置"""

        from_attributes = True


class UserStats(BaseModel):
    """
    用户统计模型

    用于返回用户统计信息。
    """

    total_users: int = Field(..., description="总用户数")
    active_users: int = Field(..., description="活跃用户数")
    inactive_users: int = Field(..., description="非活跃用户数")

    class Config:
        """模型配置"""

        from_attributes = True


# SQLAlchemy数据库表模型
if SQLALCHEMY_AVAILABLE:
    class UserTable(DBBaseModel):
        """
        用户数据库表模型
        
        对应数据库中的users表。
        """
        
        __tablename__ = 'users'
        
        # 基本信息
        username = Column(String(50), unique=True, nullable=False, index=True)
        email = Column(String(255), unique=True, nullable=False, index=True)
        password_hash = Column(String(255), nullable=False)
        
        # 个人信息
        first_name = Column(String(50), nullable=True)
        last_name = Column(String(50), nullable=True)
        phone = Column(String(20), nullable=True)
        avatar_url = Column(String(500), nullable=True)
        
        # 状态信息
        status = Column(String(20), nullable=False, default=UserStatus.ACTIVE.value)
        role = Column(String(20), nullable=False, default=UserRole.USER.value)
        is_verified = Column(Boolean, nullable=False, default=False)
        is_active = Column(Boolean, nullable=False, default=True)
        
        # 认证信息
        last_login = Column(DateTime, nullable=True)
        failed_login_attempts = Column(Integer, nullable=False, default=0)
        locked_until = Column(DateTime, nullable=True)
        
        # 其他
        metadata_json = Column(Text, nullable=True)
        
        # 索引
        __table_args__ = (
            Index('idx_user_username', 'username'),
            Index('idx_user_email', 'email'),
            Index('idx_user_status', 'status'),
            Index('idx_user_created_at', 'created_at'),
        )
        
        def to_pydantic(self) -> 'UserProfile':
            """
            转换为Pydantic模型
            
            Returns:
                UserProfile: Pydantic用户档案模型
            """
            return UserProfile(
                id=self.id,
                username=self.username,
                email=self.email,
                first_name=self.first_name,
                last_name=self.last_name,
                phone=self.phone,
                avatar_url=self.avatar_url,
                status=UserStatus(self.status),
                role=UserRole(self.role),
                is_verified=self.is_verified,
                last_login=self.last_login,
                created_at=self.created_at,
            )
else:
    UserTable = None
