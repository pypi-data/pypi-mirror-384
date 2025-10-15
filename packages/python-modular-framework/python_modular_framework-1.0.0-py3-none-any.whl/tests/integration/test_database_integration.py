"""
数据库集成测试
- 测试User、Auth、Payment组件的数据库集成
- 验证数据库表创建、CRUD操作、事务处理
- 测试组件间的数据关联

主要测试：
- 数据库连接和表创建
- User组件数据库操作
- Auth组件数据库操作
- Payment组件数据库操作
- 组件间数据关联测试

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 导入组件
from components.user import UserComponent, UserCreate, UserStatus, UserRole
from components.auth import AuthComponent, PermissionCreate, RoleCreate, PermissionType
from components.payment import PaymentComponent, PaymentCreate, PaymentMethod, PaymentStatus
from components.common.database import DatabaseComponent, DatabaseConfig


class TestDatabaseIntegration:
    """数据库集成测试类"""
    
    @pytest.fixture(scope="class")
    def database_setup(self):
        """数据库设置"""
        # 创建临时SQLite数据库
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        
        # 数据库配置
        config = DatabaseConfig(
            type="sqlite",
            database=db_path,
            echo=False
        )
        
        # 创建数据库组件
        db_component = DatabaseComponent()
        db_component.initialize(config.dict())
        db_component.start()
        
        yield db_component
        
        # 清理
        db_component.stop()
        os.close(db_fd)
        os.unlink(db_path)
    
    @pytest.fixture
    def session(self, database_setup):
        """数据库会话"""
        return database_setup.get_session()
    
    def test_database_connection(self, database_setup):
        """测试数据库连接"""
        assert database_setup.is_connected()
        assert database_setup.get_engine() is not None
    
    def test_user_component_database_integration(self, session):
        """测试User组件数据库集成"""
        # 创建User组件
        user_component = UserComponent()
        user_component.initialize({
            'database_session': session,
            'database_engine': session.bind
        })
        user_component.start()
        
        # 创建用户
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            full_name="Test User"
        )
        
        user_service = user_component.get_service()
        user = user_service.create_user(user_data, "password123")
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.status == UserStatus.ACTIVE
        
        # 验证用户认证
        authenticated_user = user_service.authenticate_user("testuser", "password123")
        assert authenticated_user is not None
        assert authenticated_user.username == "testuser"
        
        # 清理
        user_component.stop()
    
    def test_auth_component_database_integration(self, session):
        """测试Auth组件数据库集成"""
        # 创建Auth组件
        auth_component = AuthComponent()
        auth_component.initialize({
            'jwt_secret': 'test_secret_key',
            'database_session': session,
            'database_engine': session.bind
        })
        auth_component.start()
        
        auth_service = auth_component.get_service()
        
        # 创建权限
        permission_data = PermissionCreate(
            name="测试权限",
            code="test_permission",
            description="测试权限描述",
            resource="test_resource",
            action=PermissionType.READ
        )
        permission = auth_service.create_permission(permission_data)
        assert permission.id is not None
        assert permission.code == "test_permission"
        
        # 创建角色
        role_data = RoleCreate(
            name="测试角色",
            code="test_role",
            description="测试角色描述"
        )
        role = auth_service.create_role(role_data)
        assert role.id is not None
        assert role.code == "test_role"
        
        # 为角色分配权限
        success = auth_service.assign_permission_to_role(role.id, permission.id)
        assert success
        
        # 为用户分配角色
        success = auth_service.assign_role_to_user(1, role.id)
        assert success
        
        # 检查权限
        has_permission = auth_service.check_permission(1, "test_resource", "read")
        assert has_permission
        
        # 清理
        auth_component.stop()
    
    def test_payment_component_database_integration(self, session):
        """测试Payment组件数据库集成"""
        # 创建Payment组件
        payment_component = PaymentComponent()
        payment_component.initialize({
            'database_session': session,
            'database_engine': session.bind,
            'supported_methods': [PaymentMethod.ALIPAY, PaymentMethod.WECHAT_PAY]
        })
        payment_component.start()
        
        payment_service = payment_component.get_service()
        
        # 创建支付
        payment_data = PaymentCreate(
            order_id="test_order_001",
            user_id=1,
            amount=Decimal("100.00"),
            currency="CNY",
            payment_method=PaymentMethod.ALIPAY,
            description="测试支付"
        )
        
        payment = payment_service.create_payment(payment_data)
        assert payment.id is not None
        assert payment.order_id == "test_order_001"
        assert payment.amount == Decimal("100.00")
        assert payment.status == PaymentStatus.PENDING
        
        # 更新支付状态
        success = payment_service.update_payment_status(
            payment.id, 
            PaymentStatus.SUCCESS,
            provider_transaction_id="alipay_123456"
        )
        assert success
        
        # 获取支付统计
        stats = payment_service.get_payment_stats()
        assert stats['total_payments'] >= 1
        assert stats['total_amount'] >= 100.0
        
        # 清理
        payment_component.stop()
    
    def test_component_data_association(self, session):
        """测试组件间数据关联"""
        # 创建所有组件
        user_component = UserComponent()
        user_component.initialize({
            'database_session': session,
            'database_engine': session.bind
        })
        user_component.start()
        
        auth_component = AuthComponent()
        auth_component.initialize({
            'jwt_secret': 'test_secret_key',
            'database_session': session,
            'database_engine': session.bind
        })
        auth_component.start()
        
        payment_component = PaymentComponent()
        payment_component.initialize({
            'database_session': session,
            'database_engine': session.bind,
            'use_database': True,
            'supported_methods': [PaymentMethod.ALIPAY]
        })
        payment_component.start()
        
        # 创建用户
        user_data = UserCreate(
            username="integration_user",
            email="integration@example.com",
            full_name="Integration User"
        )
        user_service = user_component.get_service()
        user = user_service.create_user(user_data, "password123")
        
        # 创建权限和角色
        auth_service = auth_component.get_service()
        permission = auth_service.create_permission(PermissionCreate(
            name="支付权限",
            code="payment_permission",
            resource="payment",
            action=PermissionType.CREATE
        ))
        role = auth_service.create_role(RoleCreate(
            name="支付用户",
            code="payment_user"
        ))
        auth_service.assign_permission_to_role(role.id, permission.id)
        auth_service.assign_role_to_user(user.id, role.id)
        
        # 验证用户权限
        has_payment_permission = auth_service.check_permission(
            user.id, "payment", "create"
        )
        assert has_payment_permission
        
        # 创建支付
        payment_service = payment_component.get_service()
        payment_data = PaymentCreate(
            order_id="integration_order_001",
            user_id=user.id,
            amount=Decimal("200.00"),
            currency="CNY",
            payment_method=PaymentMethod.ALIPAY,
            description="集成测试支付"
        )
        payment = payment_service.create_payment(payment_data)
        
        # 验证支付与用户关联
        assert payment.user_id == user.id
        assert payment.order_id == "integration_order_001"
        
        # 获取用户支付列表
        user_payments = payment_service.get_user_payments(user.id)
        assert len(user_payments) >= 1
        assert user_payments[0].user_id == user.id
        
        # 清理
        user_component.stop()
        auth_component.stop()
        payment_component.stop()
    
    def test_transaction_rollback(self, session):
        """测试事务回滚"""
        user_component = UserComponent()
        user_component.initialize({
            'database_session': session,
            'database_engine': session.bind
        })
        user_component.start()
        
        user_service = user_component.get_service()
        
        # 尝试创建重复用户（应该失败）
        user_data1 = UserCreate(
            username="duplicate_user",
            email="duplicate@example.com",
            full_name="Duplicate User"
        )
        user_data2 = UserCreate(
            username="duplicate_user",  # 重复用户名
            email="duplicate2@example.com",
            full_name="Duplicate User 2"
        )
        
        # 创建第一个用户
        user1 = user_service.create_user(user_data1, "password123")
        assert user1 is not None
        
        # 尝试创建重复用户（应该失败）
        with pytest.raises(Exception):
            user_service.create_user(user_data2, "password123")
        
        # 验证只有一个用户被创建
        users = user_service.search_users("duplicate_user")
        assert len(users) == 1
        assert users[0].username == "duplicate_user"
        
        # 清理
        user_component.stop()
    
    def test_database_performance(self, session):
        """测试数据库性能"""
        user_component = UserComponent()
        user_component.initialize({
            'database_session': session,
            'database_engine': session.bind
        })
        user_component.start()
        
        user_service = user_component.get_service()
        
        # 批量创建用户
        start_time = datetime.now()
        user_ids = []
        
        for i in range(100):
            user_data = UserCreate(
                username=f"perf_user_{i}",
                email=f"perf_{i}@example.com",
                full_name=f"Performance User {i}"
            )
            user = user_service.create_user(user_data, "password123")
            user_ids.append(user.id)
        
        creation_time = datetime.now() - start_time
        print(f"创建100个用户耗时: {creation_time.total_seconds():.2f}秒")
        
        # 批量查询用户
        start_time = datetime.now()
        for user_id in user_ids[:10]:  # 查询前10个用户
            user = user_service.get_user_by_id(user_id)
            assert user is not None
        
        query_time = datetime.now() - start_time
        print(f"查询10个用户耗时: {query_time.total_seconds():.2f}秒")
        
        # 清理
        user_component.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
