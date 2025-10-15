"""
用户组件测试

测试components.user模块中的用户组件。

测试内容：
- 用户组件接口
- 用户服务
- 用户模型
- 用户管理功能

作者：开发团队
创建时间：2025-01-12
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from components.user.component import UserComponent
from components.user.interfaces import UserInterface, UserStatus
from components.user.models import User, UserProfile, UserRole
from components.user.service import UserService


class TestUserComponent:
    """用户组件测试"""
    
    def test_user_component_initialization(self):
        """测试用户组件初始化"""
        component = UserComponent()
        
        assert component.name == "user"
        assert component.version == "1.0.0"
        assert component.description == "User management component"
        assert component.author == "Framework Team"
    
    def test_user_component_interface_implementation(self):
        """测试用户组件接口实现"""
        component = UserComponent()
        
        # 验证实现了UserInterface
        assert isinstance(component, UserInterface)
        
        # 验证接口方法存在
        assert hasattr(component, 'create_user')
        assert hasattr(component, 'get_user')
        assert hasattr(component, 'update_user')
        assert hasattr(component, 'delete_user')
        assert hasattr(component, 'authenticate_user')
        assert hasattr(component, 'get_user_profile')
        assert hasattr(component, 'update_user_profile')
    
    def test_user_component_create_user(self):
        """测试创建用户"""
        component = UserComponent()
        
        # 模拟用户数据
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # 模拟用户服务
        with patch.object(component, '_user_service') as mock_service:
            mock_user = User(
                user_id="user_123",
                username="testuser",
                email="test@example.com",
                status=UserStatus.ACTIVE,
                role=UserRole.USER
            )
            mock_service.create_user.return_value = mock_user
            
            result = component.create_user(user_data)
            
            assert result is not None
            assert result.user_id == "user_123"
            assert result.username == "testuser"
            assert result.email == "test@example.com"
            assert result.status == UserStatus.ACTIVE
            mock_service.create_user.assert_called_once_with(user_data)
    
    def test_user_component_get_user(self):
        """测试获取用户"""
        component = UserComponent()
        
        user_id = "user_123"
        
        # 模拟用户服务
        with patch.object(component, '_user_service') as mock_service:
            mock_user = User(
                user_id=user_id,
                username="testuser",
                email="test@example.com",
                status=UserStatus.ACTIVE,
                role=UserRole.USER
            )
            mock_service.get_user.return_value = mock_user
            
            result = component.get_user(user_id)
            
            assert result is not None
            assert result.user_id == user_id
            assert result.username == "testuser"
            mock_service.get_user.assert_called_once_with(user_id)
    
    def test_user_component_update_user(self):
        """测试更新用户"""
        component = UserComponent()
        
        user_id = "user_123"
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        # 模拟用户服务
        with patch.object(component, '_user_service') as mock_service:
            mock_user = User(
                user_id=user_id,
                username="testuser",
                email="test@example.com",
                status=UserStatus.ACTIVE,
                role=UserRole.USER
            )
            mock_service.update_user.return_value = mock_user
            
            result = component.update_user(user_id, update_data)
            
            assert result is not None
            assert result.user_id == user_id
            mock_service.update_user.assert_called_once_with(user_id, update_data)
    
    def test_user_component_delete_user(self):
        """测试删除用户"""
        component = UserComponent()
        
        user_id = "user_123"
        
        # 模拟用户服务
        with patch.object(component, '_user_service') as mock_service:
            mock_service.delete_user.return_value = True
            
            result = component.delete_user(user_id)
            
            assert result is True
            mock_service.delete_user.assert_called_once_with(user_id)
    
    def test_user_component_authenticate_user(self):
        """测试用户认证"""
        component = UserComponent()
        
        credentials = {
            "username": "testuser",
            "password": "password123"
        }
        
        # 模拟用户服务
        with patch.object(component, '_user_service') as mock_service:
            mock_user = User(
                user_id="user_123",
                username="testuser",
                email="test@example.com",
                status=UserStatus.ACTIVE,
                role=UserRole.USER
            )
            mock_service.authenticate_user.return_value = mock_user
            
            result = component.authenticate_user(credentials)
            
            assert result is not None
            assert result.user_id == "user_123"
            assert result.username == "testuser"
            mock_service.authenticate_user.assert_called_once_with(credentials)
    
    def test_user_component_get_user_profile(self):
        """测试获取用户资料"""
        component = UserComponent()
        
        user_id = "user_123"
        
        # 模拟用户服务
        with patch.object(component, '_user_service') as mock_service:
            mock_profile = UserProfile(
                user_id=user_id,
                first_name="Test",
                last_name="User",
                bio="Test user bio",
                avatar_url="https://example.com/avatar.jpg"
            )
            mock_service.get_user_profile.return_value = mock_profile
            
            result = component.get_user_profile(user_id)
            
            assert result is not None
            assert result.user_id == user_id
            assert result.first_name == "Test"
            assert result.last_name == "User"
            mock_service.get_user_profile.assert_called_once_with(user_id)
    
    def test_user_component_update_user_profile(self):
        """测试更新用户资料"""
        component = UserComponent()
        
        user_id = "user_123"
        profile_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "bio": "Updated bio"
        }
        
        # 模拟用户服务
        with patch.object(component, '_user_service') as mock_service:
            mock_profile = UserProfile(
                user_id=user_id,
                first_name="Updated",
                last_name="Name",
                bio="Updated bio",
                avatar_url="https://example.com/avatar.jpg"
            )
            mock_service.update_user_profile.return_value = mock_profile
            
            result = component.update_user_profile(user_id, profile_data)
            
            assert result is not None
            assert result.user_id == user_id
            assert result.first_name == "Updated"
            assert result.last_name == "Name"
            assert result.bio == "Updated bio"
            mock_service.update_user_profile.assert_called_once_with(user_id, profile_data)
    
    def test_user_component_initialization_with_config(self):
        """测试使用配置初始化用户组件"""
        config = {
            "database_url": "sqlite:///users.db",
            "password_hash_algorithm": "bcrypt",
            "session_timeout": 3600
        }
        
        component = UserComponent()
        component.initialize(config)
        
        # 验证配置被正确设置
        assert component._config == config
        assert component._user_service is not None
    
    def test_user_component_error_handling(self):
        """测试用户组件错误处理"""
        component = UserComponent()
        
        # 测试无效用户数据
        invalid_user_data = {
            "username": "",  # 空用户名
            "email": "invalid-email"  # 无效邮箱
        }
        
        with patch.object(component, '_user_service') as mock_service:
            mock_service.create_user.side_effect = ValueError("Invalid user data")
            
            with pytest.raises(ValueError, match="Invalid user data"):
                component.create_user(invalid_user_data)
    
    def test_user_component_user_roles(self):
        """测试用户角色管理"""
        component = UserComponent()
        
        # 验证支持的用户角色
        supported_roles = component.get_supported_roles()
        
        assert isinstance(supported_roles, list)
        assert len(supported_roles) > 0
        
        # 验证包含常见的用户角色
        expected_roles = ["admin", "user", "moderator", "guest"]
        for role in expected_roles:
            assert role in supported_roles


class TestUserService:
    """用户服务测试"""
    
    def test_user_service_initialization(self):
        """测试用户服务初始化"""
        service = UserService()
        
        assert service._config == {}
        assert service._database is None
    
    def test_user_service_initialization_with_config(self):
        """测试使用配置初始化用户服务"""
        config = {
            "database_url": "sqlite:///users.db",
            "password_hash_algorithm": "bcrypt"
        }
        
        service = UserService(config)
        
        assert service._config == config
    
    def test_user_service_create_user(self):
        """测试创建用户"""
        service = UserService()
        
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # 模拟数据库
        with patch.object(service, '_database') as mock_db:
            mock_db.create_user.return_value = {
                "user_id": "user_123",
                "username": "testuser",
                "email": "test@example.com",
                "status": "active",
                "role": "user"
            }
            
            result = service.create_user(user_data)
            
            assert result is not None
            assert result.user_id == "user_123"
            assert result.username == "testuser"
            assert result.email == "test@example.com"
            assert result.status == UserStatus.ACTIVE
            assert result.role == UserRole.USER
    
    def test_user_service_get_user(self):
        """测试获取用户"""
        service = UserService()
        
        user_id = "user_123"
        
        # 模拟数据库
        with patch.object(service, '_database') as mock_db:
            mock_db.get_user.return_value = {
                "user_id": user_id,
                "username": "testuser",
                "email": "test@example.com",
                "status": "active",
                "role": "user"
            }
            
            result = service.get_user(user_id)
            
            assert result is not None
            assert result.user_id == user_id
            assert result.username == "testuser"
            mock_db.get_user.assert_called_once_with(user_id)
    
    def test_user_service_update_user(self):
        """测试更新用户"""
        service = UserService()
        
        user_id = "user_123"
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        # 模拟数据库
        with patch.object(service, '_database') as mock_db:
            mock_db.update_user.return_value = {
                "user_id": user_id,
                "username": "testuser",
                "email": "test@example.com",
                "status": "active",
                "role": "user"
            }
            
            result = service.update_user(user_id, update_data)
            
            assert result is not None
            assert result.user_id == user_id
            mock_db.update_user.assert_called_once_with(user_id, update_data)
    
    def test_user_service_delete_user(self):
        """测试删除用户"""
        service = UserService()
        
        user_id = "user_123"
        
        # 模拟数据库
        with patch.object(service, '_database') as mock_db:
            mock_db.delete_user.return_value = True
            
            result = service.delete_user(user_id)
            
            assert result is True
            mock_db.delete_user.assert_called_once_with(user_id)
    
    def test_user_service_authenticate_user(self):
        """测试用户认证"""
        service = UserService()
        
        credentials = {
            "username": "testuser",
            "password": "password123"
        }
        
        # 模拟数据库
        with patch.object(service, '_database') as mock_db:
            mock_db.authenticate_user.return_value = {
                "user_id": "user_123",
                "username": "testuser",
                "email": "test@example.com",
                "status": "active",
                "role": "user"
            }
            
            result = service.authenticate_user(credentials)
            
            assert result is not None
            assert result.user_id == "user_123"
            assert result.username == "testuser"
            mock_db.authenticate_user.assert_called_once_with(credentials)
    
    def test_user_service_get_user_profile(self):
        """测试获取用户资料"""
        service = UserService()
        
        user_id = "user_123"
        
        # 模拟数据库
        with patch.object(service, '_database') as mock_db:
            mock_db.get_user_profile.return_value = {
                "user_id": user_id,
                "first_name": "Test",
                "last_name": "User",
                "bio": "Test user bio",
                "avatar_url": "https://example.com/avatar.jpg"
            }
            
            result = service.get_user_profile(user_id)
            
            assert result is not None
            assert result.user_id == user_id
            assert result.first_name == "Test"
            assert result.last_name == "User"
            mock_db.get_user_profile.assert_called_once_with(user_id)
    
    def test_user_service_update_user_profile(self):
        """测试更新用户资料"""
        service = UserService()
        
        user_id = "user_123"
        profile_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "bio": "Updated bio"
        }
        
        # 模拟数据库
        with patch.object(service, '_database') as mock_db:
            mock_db.update_user_profile.return_value = {
                "user_id": user_id,
                "first_name": "Updated",
                "last_name": "Name",
                "bio": "Updated bio",
                "avatar_url": "https://example.com/avatar.jpg"
            }
            
            result = service.update_user_profile(user_id, profile_data)
            
            assert result is not None
            assert result.user_id == user_id
            assert result.first_name == "Updated"
            assert result.last_name == "Name"
            assert result.bio == "Updated bio"
            mock_db.update_user_profile.assert_called_once_with(user_id, profile_data)
    
    def test_user_service_error_handling(self):
        """测试用户服务错误处理"""
        service = UserService()
        
        # 测试无效用户数据
        invalid_user_data = {
            "username": "",  # 空用户名
            "email": "invalid-email"  # 无效邮箱
        }
        
        with pytest.raises(ValueError, match="Invalid user data"):
            service.create_user(invalid_user_data)
    
    def test_user_service_database_integration(self):
        """测试用户服务数据库集成"""
        config = {
            "database_url": "sqlite:///users.db",
            "password_hash_algorithm": "bcrypt"
        }
        
        service = UserService(config)
        
        # 验证数据库被正确初始化
        assert service._database is not None


class TestUserModels:
    """用户模型测试"""
    
    def test_user_model_creation(self):
        """测试用户模型创建"""
        user = User(
            user_id="user_123",
            username="testuser",
            email="test@example.com",
            status=UserStatus.ACTIVE,
            role=UserRole.USER
        )
        
        assert user.user_id == "user_123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.status == UserStatus.ACTIVE
        assert user.role == UserRole.USER
    
    def test_user_model_validation(self):
        """测试用户模型验证"""
        # 测试有效用户
        user = User(
            user_id="user_123",
            username="testuser",
            email="test@example.com",
            status=UserStatus.ACTIVE,
            role=UserRole.USER
        )
        
        assert user.is_valid() is True
        
        # 测试无效用户（空用户名）
        invalid_user = User(
            user_id="user_123",
            username="",
            email="test@example.com",
            status=UserStatus.ACTIVE,
            role=UserRole.USER
        )
        
        assert invalid_user.is_valid() is False
    
    def test_user_profile_model(self):
        """测试用户资料模型"""
        profile = UserProfile(
            user_id="user_123",
            first_name="Test",
            last_name="User",
            bio="Test user bio",
            avatar_url="https://example.com/avatar.jpg"
        )
        
        assert profile.user_id == "user_123"
        assert profile.first_name == "Test"
        assert profile.last_name == "User"
        assert profile.bio == "Test user bio"
        assert profile.avatar_url == "https://example.com/avatar.jpg"
    
    def test_user_role_enum(self):
        """测试用户角色枚举"""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.USER.value == "user"
        assert UserRole.MODERATOR.value == "moderator"
        assert UserRole.GUEST.value == "guest"
    
    def test_user_status_enum(self):
        """测试用户状态枚举"""
        assert UserStatus.ACTIVE.value == "active"
        assert UserStatus.INACTIVE.value == "inactive"
        assert UserStatus.SUSPENDED.value == "suspended"
        assert UserStatus.DELETED.value == "deleted"
    
    def test_user_model_methods(self):
        """测试用户模型方法"""
        user = User(
            user_id="user_123",
            username="testuser",
            email="test@example.com",
            status=UserStatus.ACTIVE,
            role=UserRole.USER
        )
        
        # 测试获取全名
        assert user.get_full_name() == "testuser"
        
        # 测试检查状态
        assert user.is_active() is True
        assert user.is_admin() is False
        
        # 测试角色检查
        assert user.has_role(UserRole.USER) is True
        assert user.has_role(UserRole.ADMIN) is False


class TestUserIntegration:
    """用户集成测试"""
    
    def test_complete_user_management_flow(self):
        """测试完整用户管理流程"""
        component = UserComponent()
        
        # 初始化组件
        config = {
            "database_url": "sqlite:///users.db",
            "password_hash_algorithm": "bcrypt"
        }
        component.initialize(config)
        
        # 模拟用户数据
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # 模拟用户服务
        with patch.object(component, '_user_service') as mock_service:
            # 模拟创建用户
            mock_user = User(
                user_id="user_123",
                username="testuser",
                email="test@example.com",
                status=UserStatus.ACTIVE,
                role=UserRole.USER
            )
            mock_service.create_user.return_value = mock_user
            
            # 模拟获取用户
            mock_service.get_user.return_value = mock_user
            
            # 模拟更新用户
            mock_service.update_user.return_value = mock_user
            
            # 模拟删除用户
            mock_service.delete_user.return_value = True
            
            # 执行用户管理流程
            # 1. 创建用户
            created_user = component.create_user(user_data)
            assert created_user is not None
            assert created_user.user_id == "user_123"
            
            # 2. 获取用户
            retrieved_user = component.get_user("user_123")
            assert retrieved_user is not None
            assert retrieved_user.username == "testuser"
            
            # 3. 更新用户
            update_data = {"first_name": "Updated"}
            updated_user = component.update_user("user_123", update_data)
            assert updated_user is not None
            
            # 4. 删除用户
            delete_result = component.delete_user("user_123")
            assert delete_result is True
    
    def test_user_authentication_flow(self):
        """测试用户认证流程"""
        component = UserComponent()
        
        # 初始化组件
        config = {
            "database_url": "sqlite:///users.db",
            "password_hash_algorithm": "bcrypt"
        }
        component.initialize(config)
        
        # 模拟认证凭据
        credentials = {
            "username": "testuser",
            "password": "password123"
        }
        
        # 模拟用户服务
        with patch.object(component, '_user_service') as mock_service:
            # 模拟用户认证
            mock_user = User(
                user_id="user_123",
                username="testuser",
                email="test@example.com",
                status=UserStatus.ACTIVE,
                role=UserRole.USER
            )
            mock_service.authenticate_user.return_value = mock_user
            
            # 执行认证流程
            authenticated_user = component.authenticate_user(credentials)
            
            # 验证认证结果
            assert authenticated_user is not None
            assert authenticated_user.user_id == "user_123"
            assert authenticated_user.username == "testuser"
            assert authenticated_user.status == UserStatus.ACTIVE


@pytest.mark.parametrize("username,email,expected_valid", [
    ("testuser", "test@example.com", True),
    ("user123", "user@domain.org", True),
    ("", "test@example.com", False),
    ("testuser", "invalid-email", False),
    ("testuser", "", False),
])
def test_user_validation(username, email, expected_valid):
    """测试用户验证"""
    user = User(
        user_id="user_123",
        username=username,
        email=email,
        status=UserStatus.ACTIVE,
        role=UserRole.USER
    )
    
    assert user.is_valid() == expected_valid


@pytest.mark.parametrize("status,expected_active", [
    (UserStatus.ACTIVE, True),
    (UserStatus.INACTIVE, False),
    (UserStatus.SUSPENDED, False),
    (UserStatus.DELETED, False),
])
def test_user_status_check(status, expected_active):
    """测试用户状态检查"""
    user = User(
        user_id="user_123",
        username="testuser",
        email="test@example.com",
        status=status,
        role=UserRole.USER
    )
    
    assert user.is_active() == expected_active


@pytest.mark.parametrize("role,expected_admin", [
    (UserRole.ADMIN, True),
    (UserRole.USER, False),
    (UserRole.MODERATOR, False),
    (UserRole.GUEST, False),
])
def test_user_role_check(role, expected_admin):
    """测试用户角色检查"""
    user = User(
        user_id="user_123",
        username="testuser",
        email="test@example.com",
        status=UserStatus.ACTIVE,
        role=role
    )
    
    assert user.is_admin() == expected_admin

