"""
用户Repository实现
- 实现用户数据访问层
- 提供用户CRUD操作
- 实现用户查询和搜索

主要类：
- UserRepository: 用户数据访问类

功能：
- 用户创建、查询、更新、删除
- 按用户名、邮箱查询
- 用户搜索
- 用户统计

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

try:
    from components.common.database.repository import BaseRepository, DuplicateRecordError
    from .models import UserTable
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    BaseRepository = None
    UserTable = None


if SQLALCHEMY_AVAILABLE:
    class UserRepository(BaseRepository[UserTable]):
        """
        用户Repository
        
        提供用户数据的访问和管理功能。
        """
        
        def __init__(self, session: Session):
            """
            初始化用户Repository
            
            Args:
                session (Session): 数据库会话
            """
            super().__init__(session, UserTable)
        
        def get_by_username(self, username: str) -> Optional[UserTable]:
            """
            根据用户名获取用户
            
            Args:
                username (str): 用户名
            
            Returns:
                Optional[UserTable]: 用户实例，如果不存在则返回None
            """
            return self.get_by_field('username', username.lower())
        
        def get_by_email(self, email: str) -> Optional[UserTable]:
            """
            根据邮箱获取用户
            
            Args:
                email (str): 邮箱地址
            
            Returns:
                Optional[UserTable]: 用户实例，如果不存在则返回None
            """
            return self.get_by_field('email', email.lower())
        
        def create_user(
            self,
            username: str,
            email: str,
            password_hash: str,
            **kwargs
        ) -> UserTable:
            """
            创建用户
            
            Args:
                username (str): 用户名
                email (str): 邮箱地址
                password_hash (str): 密码哈希
                **kwargs: 其他用户属性
            
            Returns:
                UserTable: 创建的用户实例
            
            Raises:
                DuplicateRecordError: 用户名或邮箱已存在
            """
            # 检查用户名是否已存在
            if self.get_by_username(username):
                raise DuplicateRecordError(
                    f"Username '{username}' already exists",
                    {"field": "username", "value": username}
                )
            
            # 检查邮箱是否已存在
            if self.get_by_email(email):
                raise DuplicateRecordError(
                    f"Email '{email}' already exists",
                    {"field": "email", "value": email}
                )
            
            data = {
                'username': username.lower(),
                'email': email.lower(),
                'password_hash': password_hash,
                **kwargs
            }
            
            try:
                return self.create(data)
            except IntegrityError as e:
                raise DuplicateRecordError(
                    "User already exists",
                    {"error": str(e)}
                )
        
        def search_users(
            self,
            query: str,
            limit: int = 20,
            offset: int = 0
        ) -> List[UserTable]:
            """
            搜索用户
            
            Args:
                query (str): 搜索关键词
                limit (int): 返回数量限制
                offset (int): 偏移量
            
            Returns:
                List[UserTable]: 搜索结果
            """
            search_term = f"%{query.lower()}%"
            stmt = select(self.model_class).where(
                or_(
                    self.model_class.username.like(search_term),
                    self.model_class.email.like(search_term),
                    self.model_class.first_name.like(search_term),
                    self.model_class.last_name.like(search_term)
                )
            ).offset(offset).limit(limit)
            
            result = self.session.execute(stmt)
            return list(result.scalars().all())
        
        def list_active_users(
            self,
            limit: Optional[int] = None,
            offset: Optional[int] = None
        ) -> List[UserTable]:
            """
            获取活跃用户列表
            
            Args:
                limit (Optional[int]): 限制数量
                offset (Optional[int]): 偏移量
            
            Returns:
                List[UserTable]: 活跃用户列表
            """
            return self.filter_by(is_active=True)
        
        def count_by_status(self, status: str) -> int:
            """
            按状态统计用户数量
            
            Args:
                status (str): 用户状态
            
            Returns:
                int: 用户数量
            """
            return self.count(status=status)
        
        def count_active_users(self) -> int:
            """
            统计活跃用户数量
            
            Returns:
                int: 活跃用户数量
            """
            return self.count(is_active=True)
        
        def count_inactive_users(self) -> int:
            """
            统计非活跃用户数量
            
            Returns:
                int: 非活跃用户数量
            """
            return self.count(is_active=False)
        
        def update_last_login(self, user_id: int) -> Optional[UserTable]:
            """
            更新最后登录时间
            
            Args:
                user_id (int): 用户ID
            
            Returns:
                Optional[UserTable]: 更新后的用户实例
            """
            from datetime import datetime
            return self.update(user_id, {'last_login': datetime.utcnow()})
        
        def update_password(self, user_id: int, password_hash: str) -> Optional[UserTable]:
            """
            更新用户密码
            
            Args:
                user_id (int): 用户ID
                password_hash (str): 新密码哈希
            
            Returns:
                Optional[UserTable]: 更新后的用户实例
            """
            return self.update(user_id, {'password_hash': password_hash})
        
        def activate_user(self, user_id: int) -> Optional[UserTable]:
            """
            激活用户
            
            Args:
                user_id (int): 用户ID
            
            Returns:
                Optional[UserTable]: 更新后的用户实例
            """
            return self.update(user_id, {'is_active': True})
        
        def deactivate_user(self, user_id: int) -> Optional[UserTable]:
            """
            停用用户
            
            Args:
                user_id (int): 用户ID
            
            Returns:
                Optional[UserTable]: 更新后的用户实例
            """
            return self.update(user_id, {'is_active': False})
        
        def verify_user(self, user_id: int) -> Optional[UserTable]:
            """
            验证用户
            
            Args:
                user_id (int): 用户ID
            
            Returns:
                Optional[UserTable]: 更新后的用户实例
            """
            return self.update(user_id, {'is_verified': True})
        
        def increment_failed_login(self, user_id: int) -> Optional[UserTable]:
            """
            增加失败登录次数
            
            Args:
                user_id (int): 用户ID
            
            Returns:
                Optional[UserTable]: 更新后的用户实例
            """
            user = self.get_by_id(user_id)
            if user:
                new_count = user.failed_login_attempts + 1
                return self.update(user_id, {'failed_login_attempts': new_count})
            return None
        
        def reset_failed_login(self, user_id: int) -> Optional[UserTable]:
            """
            重置失败登录次数
            
            Args:
                user_id (int): 用户ID
            
            Returns:
                Optional[UserTable]: 更新后的用户实例
            """
            return self.update(user_id, {'failed_login_attempts': 0})
else:
    UserRepository = None

