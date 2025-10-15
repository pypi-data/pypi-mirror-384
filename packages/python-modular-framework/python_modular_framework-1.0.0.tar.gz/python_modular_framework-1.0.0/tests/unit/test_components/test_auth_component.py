"""
认证组件测试

测试components.auth.component模块的功能。

测试内容：
- 认证组件生命周期
- 认证服务功能
- 用户管理
- 权限管理
- 错误处理

作者：开发团队
创建时间：2025-01-12
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from framework.core.config import Config
from components.auth.component import AuthComponent
from components.auth.service import AuthService
from components.auth.models import User, Role, Permission


class TestAuthComponent:
    """认证组件测试"""
    
    def test_auth_component_initialization(self):
        """测试认证组件初始化"""
        config = Config()
        component = AuthComponent("auth", config)
        
        assert component.name == "auth"
        assert component.config == config
        assert component._service is None
    
    def test_auth_component_initialize(self):
        """测试认证组件初始化"""
        config = Config()
        component = AuthComponent("auth", config)
        
        component.initialize()
        
        assert component._service is not None
        assert isinstance(component._service, AuthService)
    
    def test_auth_component_start(self):
        """测试认证组件启动"""
        config = Config()
        component = AuthComponent("auth", config)
        
        component.initialize()
        component.start()
        
        # 组件应该正常启动
        assert component._service is not None
    
    def test_auth_component_stop(self):
        """测试认证组件停止"""
        config = Config()
        component = AuthComponent("auth", config)
        
        component.initialize()
        component.start()
        component.stop()
        
        # 组件应该正常停止
        assert component._service is not None  # 服务实例应该保留
    
    def test_auth_component_get_health_status(self):
        """测试认证组件健康状态"""
        config = Config()
        component = AuthComponent("auth", config)
        
        component.initialize()
        
        health = component.get_health_status()
        
        assert health["status"] == "healthy"
        assert health["component_name"] == "auth"
        assert "service_status" in health
    
    def test_auth_component_get_service(self):
        """测试获取认证服务"""
        config = Config()
        component = AuthComponent("auth", config)
        
        component.initialize()
        
        service = component.get_service()
        
        assert service is not None
        assert isinstance(service, AuthService)
    
    def test_auth_component_get_service_not_initialized(self):
        """测试未初始化时获取服务"""
        config = Config()
        component = AuthComponent("auth", config)
        
        with pytest.raises(RuntimeError, match="Component not initialized"):
            component.get_service()
    
    def test_auth_component_with_config(self):
        """测试使用配置的认证组件"""
        config = Config()
        config.set("components.auth.secret_key", "test_secret")
        config.set("components.auth.token_expiry", 3600)
        
        component = AuthComponent("auth", config)
        component.initialize()
        
        # 配置应该传递给服务
        assert component._service is not None


class TestAuthService:
    """认证服务测试"""
    
    def test_auth_service_initialization(self):
        """测试认证服务初始化"""
        service = AuthService()
        
        assert service is not None
        assert service._users == {}
        assert service._roles == {}
        assert service._permissions == {}
    
    def test_register_user(self):
        """测试注册用户"""
        service = AuthService()
        
        user = service.register_user("testuser", "test@example.com", "password123")
        
        assert isinstance(user, User)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.id in service._users
    
    def test_register_user_duplicate_username(self):
        """测试注册重复用户名"""
        service = AuthService()
        
        # 注册第一个用户
        service.register_user("testuser", "test1@example.com", "password123")
        
        # 尝试注册重复用户名
        with pytest.raises(ValueError, match="Username already exists"):
            service.register_user("testuser", "test2@example.com", "password123")
    
    def test_register_user_duplicate_email(self):
        """测试注册重复邮箱"""
        service = AuthService()
        
        # 注册第一个用户
        service.register_user("user1", "test@example.com", "password123")
        
        # 尝试注册重复邮箱
        with pytest.raises(ValueError, match="Email already exists"):
            service.register_user("user2", "test@example.com", "password123")
    
    def test_authenticate_user(self):
        """测试用户认证"""
        service = AuthService()
        
        # 注册用户
        user = service.register_user("testuser", "test@example.com", "password123")
        
        # 认证成功
        authenticated_user = service.authenticate("testuser", "password123")
        
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        assert authenticated_user.username == "testuser"
    
    def test_authenticate_user_wrong_password(self):
        """测试错误密码认证"""
        service = AuthService()
        
        # 注册用户
        service.register_user("testuser", "test@example.com", "password123")
        
        # 使用错误密码认证
        with pytest.raises(ValueError, match="Invalid credentials"):
            service.authenticate("testuser", "wrongpassword")
    
    def test_authenticate_user_not_found(self):
        """测试不存在的用户认证"""
        service = AuthService()
        
        # 尝试认证不存在的用户
        with pytest.raises(ValueError, match="User not found"):
            service.authenticate("nonexistent", "password123")
    
    def test_get_user_by_id(self):
        """测试通过ID获取用户"""
        service = AuthService()
        
        # 注册用户
        user = service.register_user("testuser", "test@example.com", "password123")
        
        # 通过ID获取用户
        retrieved_user = service.get_user_by_id(user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.username == "testuser"
    
    def test_get_user_by_username(self):
        """测试通过用户名获取用户"""
        service = AuthService()
        
        # 注册用户
        user = service.register_user("testuser", "test@example.com", "password123")
        
        # 通过用户名获取用户
        retrieved_user = service.get_user_by_username("testuser")
        
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        assert retrieved_user.id == user.id
    
    def test_get_user_by_email(self):
        """测试通过邮箱获取用户"""
        service = AuthService()
        
        # 注册用户
        user = service.register_user("testuser", "test@example.com", "password123")
        
        # 通过邮箱获取用户
        retrieved_user = service.get_user_by_email("test@example.com")
        
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.id == user.id
    
    def test_create_role(self):
        """测试创建角色"""
        service = AuthService()
        
        role = service.create_role("admin", "Administrator role")
        
        assert isinstance(role, Role)
        assert role.name == "admin"
        assert role.description == "Administrator role"
        assert role.id in service._roles
    
    def test_create_role_duplicate(self):
        """测试创建重复角色"""
        service = AuthService()
        
        # 创建第一个角色
        service.create_role("admin", "Administrator role")
        
        # 尝试创建重复角色
        with pytest.raises(ValueError, match="Role already exists"):
            service.create_role("admin", "Another admin role")
    
    def test_create_permission(self):
        """测试创建权限"""
        service = AuthService()
        
        permission = service.create_permission("read_users", "Read user data")
        
        assert isinstance(permission, Permission)
        assert permission.name == "read_users"
        assert permission.description == "Read user data"
        assert permission.id in service._permissions
    
    def test_create_permission_duplicate(self):
        """测试创建重复权限"""
        service = AuthService()
        
        # 创建第一个权限
        service.create_permission("read_users", "Read user data")
        
        # 尝试创建重复权限
        with pytest.raises(ValueError, match="Permission already exists"):
            service.create_permission("read_users", "Another read permission")
    
    def test_assign_role_to_user(self):
        """测试为用户分配角色"""
        service = AuthService()
        
        # 创建用户和角色
        user = service.register_user("testuser", "test@example.com", "password123")
        role = service.create_role("admin", "Administrator role")
        
        # 分配角色
        service.assign_role_to_user(user.id, role.id)
        
        # 检查用户是否有角色
        user_roles = service.get_user_roles(user.id)
        assert len(user_roles) == 1
        assert user_roles[0].id == role.id
    
    def test_assign_permission_to_role(self):
        """测试为角色分配权限"""
        service = AuthService()
        
        # 创建角色和权限
        role = service.create_role("admin", "Administrator role")
        permission = service.create_permission("read_users", "Read user data")
        
        # 分配权限
        service.assign_permission_to_role(role.id, permission.id)
        
        # 检查角色是否有权限
        role_permissions = service.get_role_permissions(role.id)
        assert len(role_permissions) == 1
        assert role_permissions[0].id == permission.id
    
    def test_check_user_permission(self):
        """测试检查用户权限"""
        service = AuthService()
        
        # 创建用户、角色和权限
        user = service.register_user("testuser", "test@example.com", "password123")
        role = service.create_role("admin", "Administrator role")
        permission = service.create_permission("read_users", "Read user data")
        
        # 分配角色和权限
        service.assign_role_to_user(user.id, role.id)
        service.assign_permission_to_role(role.id, permission.id)
        
        # 检查权限
        has_permission = service.check_user_permission(user.id, "read_users")
        assert has_permission is True
        
        # 检查不存在的权限
        has_permission = service.check_user_permission(user.id, "write_users")
        assert has_permission is False
    
    def test_update_user(self):
        """测试更新用户"""
        service = AuthService()
        
        # 注册用户
        user = service.register_user("testuser", "test@example.com", "password123")
        
        # 更新用户信息
        updated_user = service.update_user(user.id, email="newemail@example.com")
        
        assert updated_user.email == "newemail@example.com"
        assert updated_user.username == "testuser"  # 用户名不应该改变
    
    def test_delete_user(self):
        """测试删除用户"""
        service = AuthService()
        
        # 注册用户
        user = service.register_user("testuser", "test@example.com", "password123")
        
        # 删除用户
        service.delete_user(user.id)
        
        # 用户应该不存在
        with pytest.raises(ValueError, match="User not found"):
            service.get_user_by_id(user.id)
    
    def test_list_users(self):
        """测试列出用户"""
        service = AuthService()
        
        # 注册多个用户
        user1 = service.register_user("user1", "user1@example.com", "password123")
        user2 = service.register_user("user2", "user2@example.com", "password123")
        
        # 列出用户
        users = service.list_users()
        
        assert len(users) == 2
        user_ids = [user.id for user in users]
        assert user1.id in user_ids
        assert user2.id in user_ids


class TestUser:
    """用户模型测试"""
    
    def test_user_creation(self):
        """测试用户创建"""
        user = User("testuser", "test@example.com", "hashed_password")
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.id is not None
        assert user.created_at is not None
        assert user.is_active is True
    
    def test_user_validation(self):
        """测试用户验证"""
        # 测试有效用户
        user = User("testuser", "test@example.com", "hashed_password")
        assert user.validate() is True
        
        # 测试无效用户名
        user.username = ""
        assert user.validate() is False
        
        # 测试无效邮箱
        user.username = "testuser"
        user.email = "invalid_email"
        assert user.validate() is False


class TestRole:
    """角色模型测试"""
    
    def test_role_creation(self):
        """测试角色创建"""
        role = Role("admin", "Administrator role")
        
        assert role.name == "admin"
        assert role.description == "Administrator role"
        assert role.id is not None
        assert role.created_at is not None


class TestPermission:
    """权限模型测试"""
    
    def test_permission_creation(self):
        """测试权限创建"""
        permission = Permission("read_users", "Read user data")
        
        assert permission.name == "read_users"
        assert permission.description == "Read user data"
        assert permission.id is not None
        assert permission.created_at is not None


@pytest.mark.parametrize("username,email,password", [
    ("user1", "user1@example.com", "password123"),
    ("user2", "user2@example.com", "secure_password"),
    ("admin", "admin@example.com", "admin_password"),
])
def test_register_multiple_users(username, email, password):
    """测试注册多个用户"""
    service = AuthService()
    
    user = service.register_user(username, email, password)
    
    assert user.username == username
    assert user.email == email
    assert user.id is not None


@pytest.mark.parametrize("role_name,description", [
    ("admin", "Administrator role"),
    ("user", "Regular user role"),
    ("guest", "Guest user role"),
])
def test_create_multiple_roles(role_name, description):
    """测试创建多个角色"""
    service = AuthService()
    
    role = service.create_role(role_name, description)
    
    assert role.name == role_name
    assert role.description == description
    assert role.id is not None


@pytest.mark.parametrize("permission_name,description", [
    ("read", "Read permission"),
    ("write", "Write permission"),
    ("delete", "Delete permission"),
])
def test_create_multiple_permissions(permission_name, description):
    """测试创建多个权限"""
    service = AuthService()
    
    permission = service.create_permission(permission_name, description)
    
    assert permission.name == permission_name
    assert permission.description == description
    assert permission.id is not None
