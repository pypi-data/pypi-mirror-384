"""
数据库集成示例
- 演示如何使用数据库集成的User、Auth、Payment组件
- 展示组件间的数据关联和协作
- 提供完整的应用组装示例

主要功能：
- 数据库连接配置
- 组件初始化和启动
- 用户注册和认证
- 权限管理
- 支付处理

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.common.database import DatabaseComponent, DatabaseConfig
from components.user import UserComponent, UserCreate, UserStatus, UserRole
from components.auth import AuthComponent, PermissionCreate, RoleCreate, PermissionType
from components.payment import PaymentComponent, PaymentCreate, PaymentMethod, PaymentStatus


def main():
    """主函数"""
    print("🚀 数据库集成示例")
    print("=" * 50)
    
    # 1. 配置数据库连接
    print("\n1. 配置数据库连接...")
    db_config = DatabaseConfig(
        type="postgresql",
        host="localhost",
        port=5432,
        database="framework_db",
        username="postgres",
        password="password"
    )
    
    # 创建数据库组件
    db_component = DatabaseComponent()
    db_component.initialize(db_config.dict())
    db_component.start()
    
    if not db_component.is_connected():
        print("❌ 数据库连接失败")
        return
    
    print("✅ 数据库连接成功")
    
    # 获取数据库会话
    session = db_component.get_session()
    engine = db_component.get_engine()
    
    # 2. 初始化组件
    print("\n2. 初始化组件...")
    
    # User组件
    user_component = UserComponent()
    user_component.initialize({
        'database_session': session,
        'database_engine': engine
    })
    user_component.start()
    print("✅ User组件启动成功")
    
    # Auth组件
    auth_component = AuthComponent()
    auth_component.initialize({
        'jwt_secret': 'your_jwt_secret_key_here',
        'database_session': session,
        'database_engine': engine,
        'redis_url': 'redis://localhost:6379/0'  # 可选Redis缓存
    })
    auth_component.start()
    print("✅ Auth组件启动成功")
    
    # Payment组件
    payment_component = PaymentComponent()
    payment_component.initialize({
        'database_session': session,
        'database_engine': engine,
        'supported_methods': [PaymentMethod.ALIPAY, PaymentMethod.WECHAT_PAY]
    })
    payment_component.start()
    print("✅ Payment组件启动成功")
    
    # 3. 用户管理
    print("\n3. 用户管理...")
    user_service = user_component.get_service()
    
    # 创建用户
    user_data = UserCreate(
        username="demo_user",
        email="demo@example.com",
        full_name="Demo User",
        phone="13800138000"
    )
    
    try:
        user = user_service.create_user(user_data, "password123")
        print(f"✅ 用户创建成功: {user.username} (ID: {user.id})")
    except Exception as e:
        print(f"⚠️ 用户可能已存在: {e}")
        # 尝试获取现有用户
        user = user_service.get_user_by_username("demo_user")
        if user:
            print(f"✅ 获取现有用户: {user.username} (ID: {user.id})")
        else:
            print("❌ 无法创建或获取用户")
            return
    
    # 4. 权限管理
    print("\n4. 权限管理...")
    auth_service = auth_component.get_service()
    
    # 创建权限
    permissions = [
        PermissionCreate(
            name="用户管理",
            code="user_manage",
            description="用户管理权限",
            resource="user",
            action=PermissionType.CREATE
        ),
        PermissionCreate(
            name="支付管理",
            code="payment_manage",
            description="支付管理权限",
            resource="payment",
            action=PermissionType.CREATE
        ),
        PermissionCreate(
            name="支付查看",
            code="payment_view",
            description="支付查看权限",
            resource="payment",
            action=PermissionType.READ
        )
    ]
    
    created_permissions = []
    for perm_data in permissions:
        try:
            permission = auth_service.create_permission(perm_data)
            created_permissions.append(permission)
            print(f"✅ 权限创建成功: {permission.name}")
        except Exception as e:
            print(f"⚠️ 权限可能已存在: {e}")
            # 获取现有权限
            permission = auth_service.get_permission_by_code(perm_data.code)
            if permission:
                created_permissions.append(permission)
                print(f"✅ 获取现有权限: {permission.name}")
    
    # 创建角色
    role_data = RoleCreate(
        name="普通用户",
        code="normal_user",
        description="普通用户角色"
    )
    
    try:
        role = auth_service.create_role(role_data)
        print(f"✅ 角色创建成功: {role.name}")
    except Exception as e:
        print(f"⚠️ 角色可能已存在: {e}")
        role = auth_service.get_role_by_code("normal_user")
        if role:
            print(f"✅ 获取现有角色: {role.name}")
    
    # 为角色分配权限
    if role and created_permissions:
        for permission in created_permissions:
            try:
                success = auth_service.assign_permission_to_role(role.id, permission.id)
                if success:
                    print(f"✅ 权限分配成功: {permission.name} -> {role.name}")
            except Exception as e:
                print(f"⚠️ 权限分配可能已存在: {e}")
    
    # 为用户分配角色
    if role:
        try:
            success = auth_service.assign_role_to_user(user.id, role.id)
            if success:
                print(f"✅ 角色分配成功: {role.name} -> {user.username}")
        except Exception as e:
            print(f"⚠️ 角色分配可能已存在: {e}")
    
    # 5. 权限验证
    print("\n5. 权限验证...")
    
    # 检查用户权限
    has_user_manage = auth_service.check_permission(user.id, "user", "create")
    has_payment_manage = auth_service.check_permission(user.id, "payment", "create")
    has_payment_view = auth_service.check_permission(user.id, "payment", "read")
    
    print(f"用户管理权限: {'✅' if has_user_manage else '❌'}")
    print(f"支付管理权限: {'✅' if has_payment_manage else '❌'}")
    print(f"支付查看权限: {'✅' if has_payment_view else '❌'}")
    
    # 6. 支付处理
    print("\n6. 支付处理...")
    payment_service = payment_component.get_service()
    
    # 创建支付
    payment_data = PaymentCreate(
        order_id=f"order_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        user_id=user.id,
        amount=Decimal("99.99"),
        currency="CNY",
        payment_method=PaymentMethod.ALIPAY,
        description="示例支付订单"
    )
    
    try:
        payment = payment_service.create_payment(payment_data)
        print(f"✅ 支付创建成功: {payment.order_id} (金额: ¥{payment.amount})")
        
        # 模拟支付成功
        success = payment_service.update_payment_status(
            payment.id,
            PaymentStatus.SUCCESS,
            provider_transaction_id="alipay_demo_123456"
        )
        if success:
            print("✅ 支付状态更新成功")
        
        # 获取支付统计
        stats = payment_service.get_payment_stats()
        print(f"📊 支付统计: 总支付数 {stats['total_payments']}, 总金额 ¥{stats['total_amount']}")
        
    except Exception as e:
        print(f"❌ 支付处理失败: {e}")
    
    # 7. 数据查询示例
    print("\n7. 数据查询示例...")
    
    # 用户统计
    user_stats = user_service.get_user_stats()
    print(f"📊 用户统计: 总用户数 {user_stats.total_users}, 活跃用户 {user_stats.active_users}")
    
    # 用户搜索
    search_results = user_service.search_users("demo")
    print(f"🔍 用户搜索: 找到 {len(search_results)} 个用户")
    
    # 8. 清理资源
    print("\n8. 清理资源...")
    
    payment_component.stop()
    auth_component.stop()
    user_component.stop()
    db_component.stop()
    
    print("✅ 所有组件已停止")
    print("\n🎉 数据库集成示例完成！")


if __name__ == "__main__":
    main()