"""
支付组件实现
- 实现ComponentInterface接口
- 提供统一的支付管理功能
- 支持多种支付方式和支付流程管理

主要功能：
- 支付创建和管理
- 支付流程处理
- 退款管理
- 支付统计
- 多种支付方式支持

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import asyncio
import threading
import time
from typing import Any, Dict, List, Optional
from decimal import Decimal
from framework.interfaces.component import (
    ComponentInterface,
    ComponentStatus,
    ComponentInfo,
    ComponentError,
    ComponentInitializationError,
)
from .models import (
    PaymentModel,
    PaymentCreate,
    RefundRequest,
    PaymentCallback,
    PaymentStats,
    PaymentStatus,
    PaymentMethod,
)
from .interfaces import PaymentServiceInterface
from .service import OptimizedPaymentService


class PaymentComponent(ComponentInterface):
    """
    支付组件

    提供统一的支付管理功能，支持多种支付方式、
    支付流程管理、退款处理等特性。
    """

    def __init__(self, name: str = "payment"):
        """
        初始化支付组件

        Args:
            name (str): 组件名称
        """
        self._name = name
        self._version = "0.1.0"
        self._description = "统一支付管理组件"
        self._dependencies = ["user", "auth"]  # 支付组件依赖用户和权限组件
        self._status = ComponentStatus.UNINITIALIZED
        self._config = {}

        # 支付相关
        self._payment_service = None
        self._supported_methods = [
            PaymentMethod.ALIPAY,
            PaymentMethod.WECHAT,
            PaymentMethod.UNIONPAY,
            PaymentMethod.BANK_CARD,
        ]

        # 统计信息
        self._stats = {
            "payments_created": 0,
            "payments_success": 0,
            "payments_failed": 0,
            "payments_cancelled": 0,
            "refunds_created": 0,
            "total_amount": Decimal("0"),
            "total_refunded": Decimal("0"),
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
        初始化支付组件

        Args:
            config (Dict[str, Any]): 组件配置参数

        Raises:
            ComponentInitializationError: 初始化失败时抛出异常
        """
        try:
            self._status = ComponentStatus.INITIALIZING

            # 更新配置
            self._config = config or {}
            
            # 获取数据库配置（必需）
            db_session = self._config.get('database_session')
            if not db_session:
                raise ValueError("database_session是必需的配置参数")

            # 创建支付服务
            self._payment_service = OptimizedPaymentService(
                supported_methods=self._supported_methods, 
                session=db_session,
                config=self._config
            )

            self._status = ComponentStatus.INITIALIZED
            self._start_time = time.time()

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentInitializationError(
                self._name, f"Failed to initialize payment component: {e}"
            )

    def start(self) -> None:
        """
        启动支付组件

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
            raise ComponentError(self._name, f"Failed to start payment component: {e}")
    
    def _create_tables(self, engine) -> None:
        """
        创建数据库表
        
        Args:
            engine: SQLAlchemy引擎实例
        """
        try:
            from .models import PaymentTable, RefundTable
            from components.common.database.models import Base
            
            if PaymentTable is not None:
                Base.metadata.create_all(engine, tables=[
                    PaymentTable.__table__,
                    RefundTable.__table__,
                ], checkfirst=True)
                print(f"Payment tables created/verified")
        except Exception as e:
            print(f"Error creating payment tables: {e}")

    def stop(self) -> None:
        """
        停止支付组件

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
            raise ComponentError(self._name, f"Failed to stop payment component: {e}")

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
                "supported_methods": [
                    method.value for method in self._supported_methods
                ],
                "stats": {
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in self._stats.items()
                },
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
            "message": "Payment component is running normally",
            "details": {
                "component_status": self._status.value,
                "supported_methods": [
                    method.value for method in self._supported_methods
                ],
                "payment_service_available": self._payment_service is not None,
                "stats": {
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in self._stats.items()
                },
            },
        }

        if self._status != ComponentStatus.RUNNING:
            health_status["status"] = "unhealthy"
            health_status["message"] = f"Component is not running: {self._status.value}"

        return health_status

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
                    self._cleanup_expired_payments()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"Error in payment cleanup worker: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_worker())

    def _cleanup_expired_payments(self) -> None:
        """清理过期支付"""
        if self._payment_service:
            try:
                # 这里可以添加清理过期支付的逻辑
                pass
            except Exception as e:
                print(f"Error cleaning up expired payments: {e}")

    # 支付服务代理方法
    def get_payment_service(self) -> Optional[PaymentServiceInterface]:
        """
        获取支付服务

        Returns:
            Optional[PaymentServiceInterface]: 支付服务实例
        """
        return self._payment_service

    def create_payment(self, payment_data: PaymentCreate) -> Optional[PaymentModel]:
        """
        创建支付

        Args:
            payment_data (PaymentCreate): 支付创建数据

        Returns:
            Optional[PaymentModel]: 创建的支付对象
        """
        if not self._payment_service:
            return None

        try:
            payment = self._payment_service.create_payment(payment_data)
            if payment:
                self._stats["payments_created"] += 1
                self._stats["total_amount"] += payment.amount
            return payment
        except Exception as e:
            return None

    def get_payment_by_id(self, payment_id: int) -> Optional[PaymentModel]:
        """
        根据ID获取支付

        Args:
            payment_id (int): 支付ID

        Returns:
            Optional[PaymentModel]: 支付对象
        """
        if not self._payment_service:
            return None

        try:
            return self._payment_service.get_payment_by_id(payment_id)
        except Exception as e:
            return None

    def initiate_payment(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """
        发起支付

        Args:
            payment_id (int): 支付ID

        Returns:
            Optional[Dict[str, Any]]: 支付发起结果
        """
        if not self._payment_service:
            return None

        try:
            return self._payment_service.initiate_payment(payment_id)
        except Exception as e:
            return None

    def process_payment_callback(self, callback_data: PaymentCallback) -> bool:
        """
        处理支付回调

        Args:
            callback_data (PaymentCallback): 支付回调数据

        Returns:
            bool: 是否处理成功
        """
        if not self._payment_service:
            return False

        try:
            result = self._payment_service.process_payment_callback(callback_data)
            if result:
                # 更新统计信息
                if callback_data.status == PaymentStatus.SUCCESS:
                    self._stats["payments_success"] += 1
                elif callback_data.status == PaymentStatus.FAILED:
                    self._stats["payments_failed"] += 1
                elif callback_data.status == PaymentStatus.CANCELLED:
                    self._stats["payments_cancelled"] += 1
            return result
        except Exception as e:
            return False

    def create_refund(self, refund_request: RefundRequest) -> Optional[PaymentModel]:
        """
        创建退款

        Args:
            refund_request (RefundRequest): 退款请求

        Returns:
            Optional[PaymentModel]: 退款后的支付对象
        """
        if not self._payment_service:
            return None

        try:
            result = self._payment_service.create_refund(refund_request)
            if result:
                self._stats["refunds_created"] += 1
                if refund_request.refund_amount:
                    self._stats["total_refunded"] += refund_request.refund_amount
            return result
        except Exception as e:
            return None

    def get_payment_stats(
        self, user_id: Optional[int] = None
    ) -> Optional[PaymentStats]:
        """
        获取支付统计信息

        Args:
            user_id (Optional[int]): 用户ID过滤

        Returns:
            Optional[PaymentStats]: 支付统计信息
        """
        if not self._payment_service:
            return None

        try:
            return self._payment_service.get_payment_stats(user_id)
        except Exception as e:
            return None

    def get_available_payment_methods(self, user_id: int, amount: Decimal) -> List[str]:
        """
        获取可用的支付方式

        Args:
            user_id (int): 用户ID
            amount (Decimal): 支付金额

        Returns:
            List[str]: 可用的支付方式列表
        """
        if not self._payment_service:
            return []

        try:
            return self._payment_service.get_available_payment_methods(user_id, amount)
        except Exception as e:
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        获取支付组件统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self._stats.copy()
        stats["uptime"] = time.time() - self._start_time if self._start_time else 0
        # 转换Decimal为字符串以便JSON序列化
        for key, value in stats.items():
            if isinstance(value, Decimal):
                stats[key] = str(value)
        return stats

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "payments_created": 0,
            "payments_success": 0,
            "payments_failed": 0,
            "payments_cancelled": 0,
            "refunds_created": 0,
            "total_amount": Decimal("0"),
            "total_refunded": Decimal("0"),
        }
