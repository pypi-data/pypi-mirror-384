"""
权限认证Repository实现
- 实现权限认证数据访问层
- 提供权限、角色、令牌CRUD操作
- 实现复杂的权限查询

主要类：
- PermissionRepository: 权限数据访问类
- RoleRepository: 角色数据访问类
- UserRoleRepository: 用户角色关联数据访问类
- TokenRepository: 令牌数据访问类

功能：
- 权限管理（CRUD、查询）
- 角色管理（CRUD、权限分配）
- 用户角色管理（分配、移除、查询）
- 令牌管理（创建、验证、撤销）

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

try:
    from components.common.database.repository import BaseRepository
    from .models import (
        PermissionTable, RoleTable, UserRoleTable, TokenTable
    )
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    BaseRepository = None
    PermissionTable = None
    RoleTable = None
    UserRoleTable = None
    TokenTable = None


if SQLALCHEMY_AVAILABLE:
    class PermissionRepository(BaseRepository[PermissionTable]):
        """
        权限Repository
        
        提供权限数据的访问和管理功能。
        """
        
        def __init__(self, session: Session):
            """
            初始化权限Repository
            
            Args:
                session (Session): 数据库会话
            """
            super().__init__(session, PermissionTable)
        
        def get_by_code(self, code: str) -> Optional[PermissionTable]:
            """
            根据代码获取权限
            
            Args:
                code (str): 权限代码
            
            Returns:
                Optional[PermissionTable]: 权限实例，如果不存在则返回None
            """
            return self.get_by_field('code', code)
        
        def get_by_resource_action(self, resource: str, action: str) -> Optional[PermissionTable]:
            """
            根据资源和动作获取权限
            
            Args:
                resource (str): 资源名称
                action (str): 权限动作
            
            Returns:
                Optional[PermissionTable]: 权限实例，如果不存在则返回None
            """
            stmt = select(self.model_class).where(
                and_(
                    self.model_class.resource == resource,
                    self.model_class.action == action
                )
            )
            result = self.session.execute(stmt)
            return result.scalar_one_or_none()
        
        def list_by_resource(self, resource: str) -> List[PermissionTable]:
            """
            获取指定资源的所有权限
            
            Args:
                resource (str): 资源名称
            
            Returns:
                List[PermissionTable]: 权限列表
            """
            return self.filter_by(resource=resource)
        
        def list_active_permissions(self) -> List[PermissionTable]:
            """
            获取所有活跃权限
            
            Returns:
                List[PermissionTable]: 活跃权限列表
            """
            return self.filter_by(is_active=True)

    class RoleRepository(BaseRepository[RoleTable]):
        """
        角色Repository
        
        提供角色数据的访问和管理功能。
        """
        
        def __init__(self, session: Session):
            """
            初始化角色Repository
            
            Args:
                session (Session): 数据库会话
            """
            super().__init__(session, RoleTable)
        
        def get_by_code(self, code: str) -> Optional[RoleTable]:
            """
            根据代码获取角色
            
            Args:
                code (str): 角色代码
            
            Returns:
                Optional[RoleTable]: 角色实例，如果不存在则返回None
            """
            return self.get_by_field('code', code)
        
        def list_system_roles(self) -> List[RoleTable]:
            """
            获取系统角色列表
            
            Returns:
                List[RoleTable]: 系统角色列表
            """
            return self.filter_by(is_system=True)
        
        def list_active_roles(self) -> List[RoleTable]:
            """
            获取活跃角色列表
            
            Returns:
                List[RoleTable]: 活跃角色列表
            """
            return self.filter_by(is_active=True)
        
        def assign_permission(self, role_id: int, permission_id: int) -> bool:
            """
            为角色分配权限
            
            Args:
                role_id (int): 角色ID
                permission_id (int): 权限ID
            
            Returns:
                bool: 是否分配成功
            """
            try:
                role = self.get_by_id(role_id)
                permission = PermissionRepository(self.session).get_by_id(permission_id)
                
                if role and permission:
                    role.permissions.append(permission)
                    self.session.commit()
                    return True
                return False
            except Exception:
                self.session.rollback()
                return False
        
        def remove_permission(self, role_id: int, permission_id: int) -> bool:
            """
            移除角色权限
            
            Args:
                role_id (int): 角色ID
                permission_id (int): 权限ID
            
            Returns:
                bool: 是否移除成功
            """
            try:
                role = self.get_by_id(role_id)
                permission = PermissionRepository(self.session).get_by_id(permission_id)
                
                if role and permission and permission in role.permissions:
                    role.permissions.remove(permission)
                    self.session.commit()
                    return True
                return False
            except Exception:
                self.session.rollback()
                return False
        
        def get_role_permissions(self, role_id: int) -> List[PermissionTable]:
            """
            获取角色的所有权限
            
            Args:
                role_id (int): 角色ID
            
            Returns:
                List[PermissionTable]: 权限列表
            """
            role = self.get_by_id(role_id)
            return role.permissions if role else []

    class UserRoleRepository(BaseRepository[UserRoleTable]):
        """
        用户角色Repository
        
        提供用户角色关联数据的访问和管理功能。
        """
        
        def __init__(self, session: Session):
            """
            初始化用户角色Repository
            
            Args:
                session (Session): 数据库会话
            """
            super().__init__(session, UserRoleTable)
        
        def assign_role_to_user(
            self, 
            user_id: int, 
            role_id: int, 
            assigned_by: Optional[int] = None
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
            try:
                # 检查是否已存在
                existing = self.get_by_user_role(user_id, role_id)
                if existing and existing.is_active:
                    return True  # 已经分配了
                
                data = {
                    'user_id': user_id,
                    'role_id': role_id,
                    'assigned_by': assigned_by,
                    'assigned_at': datetime.utcnow(),
                    'is_active': True,
                }
                
                self.create(data)
                return True
            except IntegrityError:
                # 唯一约束冲突，可能已存在
                return True
            except Exception:
                return False
        
        def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
            """
            移除用户角色
            
            Args:
                user_id (int): 用户ID
                role_id (int): 角色ID
            
            Returns:
                bool: 是否移除成功
            """
            user_role = self.get_by_user_role(user_id, role_id)
            if user_role:
                return self.update(user_role.id, {'is_active': False})
            return False
        
        def get_by_user_role(self, user_id: int, role_id: int) -> Optional[UserRoleTable]:
            """
            根据用户ID和角色ID获取关联
            
            Args:
                user_id (int): 用户ID
                role_id (int): 角色ID
            
            Returns:
                Optional[UserRoleTable]: 用户角色关联实例
            """
            stmt = select(self.model_class).where(
                and_(
                    self.model_class.user_id == user_id,
                    self.model_class.role_id == role_id
                )
            )
            result = self.session.execute(stmt)
            return result.scalar_one_or_none()
        
        def get_user_roles(self, user_id: int) -> List[RoleTable]:
            """
            获取用户的所有角色
            
            Args:
                user_id (int): 用户ID
            
            Returns:
                List[RoleTable]: 角色列表
            """
            stmt = select(RoleTable).join(UserRoleTable).where(
                and_(
                    UserRoleTable.user_id == user_id,
                    UserRoleTable.is_active == True
                )
            )
            result = self.session.execute(stmt)
            return list(result.scalars().all())
        
        def get_user_permissions(self, user_id: int) -> List[PermissionTable]:
            """
            获取用户的所有权限（通过角色）
            
            Args:
                user_id (int): 用户ID
            
            Returns:
                List[PermissionTable]: 权限列表
            """
            stmt = select(PermissionTable).join(
                RoleTable.permissions
            ).join(UserRoleTable).where(
                and_(
                    UserRoleTable.user_id == user_id,
                    UserRoleTable.is_active == True,
                    RoleTable.is_active == True,
                    PermissionTable.is_active == True
                )
            ).distinct()
            
            result = self.session.execute(stmt)
            return list(result.scalars().all())
        
        def check_user_permission(self, user_id: int, resource: str, action: str) -> bool:
            """
            检查用户是否有特定权限
            
            Args:
                user_id (int): 用户ID
                resource (str): 资源名称
                action (str): 权限动作
            
            Returns:
                bool: 是否有权限
            """
            stmt = select(PermissionTable).join(
                RoleTable.permissions
            ).join(UserRoleTable).where(
                and_(
                    UserRoleTable.user_id == user_id,
                    UserRoleTable.is_active == True,
                    RoleTable.is_active == True,
                    PermissionTable.is_active == True,
                    PermissionTable.resource == resource,
                    PermissionTable.action == action
                )
            )
            
            result = self.session.execute(stmt)
            return result.scalar_one_or_none() is not None

    class TokenRepository(BaseRepository[TokenTable]):
        """
        令牌Repository
        
        提供令牌数据的访问和管理功能。
        """
        
        def __init__(self, session: Session):
            """
            初始化令牌Repository
            
            Args:
                session (Session): 数据库会话
            """
            super().__init__(session, TokenTable)
        
        def get_by_token(self, token: str) -> Optional[TokenTable]:
            """
            根据令牌字符串获取令牌
            
            Args:
                token (str): 令牌字符串
            
            Returns:
                Optional[TokenTable]: 令牌实例，如果不存在则返回None
            """
            return self.get_by_field('token', token)
        
        def create_token(
            self,
            user_id: int,
            token: str,
            token_type: str,
            expires_at: datetime,
            metadata: Optional[Dict[str, Any]] = None
        ) -> TokenTable:
            """
            创建令牌
            
            Args:
                user_id (int): 用户ID
                token (str): 令牌字符串
                token_type (str): 令牌类型
                expires_at (datetime): 过期时间
                metadata (Optional[Dict[str, Any]]): 元数据
            
            Returns:
                TokenTable: 创建的令牌实例
            """
            data = {
                'user_id': user_id,
                'token': token,
                'token_type': token_type,
                'expires_at': expires_at,
                'metadata_json': str(metadata) if metadata else None,
            }
            return self.create(data)
        
        def list_user_tokens(
            self, 
            user_id: int, 
            token_type: Optional[str] = None
        ) -> List[TokenTable]:
            """
            获取用户的令牌列表
            
            Args:
                user_id (int): 用户ID
                token_type (Optional[str]): 令牌类型过滤
            
            Returns:
                List[TokenTable]: 令牌列表
            """
            filters = {'user_id': user_id}
            if token_type:
                filters['token_type'] = token_type
            return self.filter_by(**filters)
        
        def revoke_token(self, token: str) -> bool:
            """
            撤销令牌
            
            Args:
                token (str): 令牌字符串
            
            Returns:
                bool: 是否撤销成功
            """
            token_obj = self.get_by_token(token)
            if token_obj:
                return self.update(token_obj.id, {
                    'is_revoked': True,
                    'revoked_at': datetime.utcnow()
                })
            return False
        
        def revoke_user_tokens(
            self, 
            user_id: int, 
            token_type: Optional[str] = None
        ) -> int:
            """
            撤销用户的所有令牌
            
            Args:
                user_id (int): 用户ID
                token_type (Optional[str]): 令牌类型过滤
            
            Returns:
                int: 撤销的令牌数量
            """
            tokens = self.list_user_tokens(user_id, token_type)
            count = 0
            for token in tokens:
                if not token.is_revoked:
                    self.update(token.id, {
                        'is_revoked': True,
                        'revoked_at': datetime.utcnow()
                    })
                    count += 1
            return count
        
        def cleanup_expired_tokens(self) -> int:
            """
            清理过期令牌
            
            Returns:
                int: 清理的令牌数量
            """
            stmt = select(self.model_class).where(
                and_(
                    self.model_class.expires_at < datetime.utcnow(),
                    self.model_class.is_revoked == False
                )
            )
            result = self.session.execute(stmt)
            expired_tokens = list(result.scalars().all())
            
            count = 0
            for token in expired_tokens:
                self.update(token.id, {
                    'is_revoked': True,
                    'revoked_at': datetime.utcnow()
                })
                count += 1
            
            return count
        
        def is_token_valid(self, token: str) -> bool:
            """
            检查令牌是否有效
            
            Args:
                token (str): 令牌字符串
            
            Returns:
                bool: 令牌是否有效
            """
            token_obj = self.get_by_token(token)
            if not token_obj:
                return False
            
            return (
                not token_obj.is_revoked and
                token_obj.expires_at > datetime.utcnow()
            )
else:
    PermissionRepository = None
    RoleRepository = None
    UserRoleRepository = None
    TokenRepository = None
