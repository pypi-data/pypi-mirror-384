"""
支付服务接口定义
- 定义支付服务的标准接口
- 提供支付流程管理接口
- 支持多种支付方式接口

主要接口：
- PaymentServiceInterface: 支付服务接口
- PaymentRepositoryInterface: 支付仓储接口

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from decimal import Decimal
from .models import (
    PaymentModel,
    PaymentCreate,
    PaymentUpdate,
    PaymentQuery,
    RefundRequest,
    PaymentCallback,
    PaymentStats,
    PaymentStatus,
)


class PaymentServiceInterface(ABC):
    """
    支付服务接口

    定义支付管理的标准接口，包括支付创建、
    支付查询、支付更新、退款处理等功能。
    """

    # 支付管理
    @abstractmethod
    def create_payment(self, payment_data: PaymentCreate) -> PaymentModel:
        """
        创建支付

        Args:
            payment_data (PaymentCreate): 支付创建数据

        Returns:
            PaymentModel: 创建的支付对象

        Raises:
            PaymentError: 创建失败时抛出异常
        """

    @abstractmethod
    def get_payment_by_id(self, payment_id: int) -> Optional[PaymentModel]:
        """
        根据ID获取支付

        Args:
            payment_id (int): 支付ID

        Returns:
            Optional[PaymentModel]: 支付对象，如果不存在则返回None
        """

    @abstractmethod
    def get_payment_by_order_id(self, order_id: str) -> Optional[PaymentModel]:
        """
        根据订单ID获取支付

        Args:
            order_id (str): 订单ID

        Returns:
            Optional[PaymentModel]: 支付对象，如果不存在则返回None
        """

    @abstractmethod
    def list_payments(self, query: PaymentQuery) -> List[PaymentModel]:
        """
        获取支付列表

        Args:
            query (PaymentQuery): 查询参数

        Returns:
            List[PaymentModel]: 支付列表
        """

    @abstractmethod
    def update_payment(
        self, payment_id: int, payment_data: PaymentUpdate
    ) -> Optional[PaymentModel]:
        """
        更新支付信息

        Args:
            payment_id (int): 支付ID
            payment_data (PaymentUpdate): 支付更新数据

        Returns:
            Optional[PaymentModel]: 更新后的支付对象，如果不存在则返回None
        """

    @abstractmethod
    def delete_payment(self, payment_id: int) -> bool:
        """
        删除支付

        Args:
            payment_id (int): 支付ID

        Returns:
            bool: 是否删除成功
        """

    # 支付流程
    @abstractmethod
    def initiate_payment(self, payment_id: int) -> Dict[str, Any]:
        """
        发起支付

        Args:
            payment_id (int): 支付ID

        Returns:
            Dict[str, Any]: 支付发起结果，包含支付URL等信息
        """

    @abstractmethod
    def process_payment_callback(self, callback_data: PaymentCallback) -> bool:
        """
        处理支付回调

        Args:
            callback_data (PaymentCallback): 支付回调数据

        Returns:
            bool: 是否处理成功
        """

    @abstractmethod
    def check_payment_status(self, payment_id: int) -> Optional[PaymentStatus]:
        """
        检查支付状态

        Args:
            payment_id (int): 支付ID

        Returns:
            Optional[PaymentStatus]: 支付状态，如果不存在则返回None
        """

    @abstractmethod
    def cancel_payment(self, payment_id: int, reason: Optional[str] = None) -> bool:
        """
        取消支付

        Args:
            payment_id (int): 支付ID
            reason (Optional[str]): 取消原因

        Returns:
            bool: 是否取消成功
        """

    # 退款管理
    @abstractmethod
    def create_refund(self, refund_request: RefundRequest) -> Optional[PaymentModel]:
        """
        创建退款

        Args:
            refund_request (RefundRequest): 退款请求

        Returns:
            Optional[PaymentModel]: 退款后的支付对象，如果失败则返回None
        """

    @abstractmethod
    def process_refund_callback(self, refund_data: Dict[str, Any]) -> bool:
        """
        处理退款回调

        Args:
            refund_data (Dict[str, Any]): 退款回调数据

        Returns:
            bool: 是否处理成功
        """

    @abstractmethod
    def get_refund_status(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """
        获取退款状态

        Args:
            payment_id (int): 支付ID

        Returns:
            Optional[Dict[str, Any]]: 退款状态信息，如果不存在则返回None
        """

    # 统计查询
    @abstractmethod
    def get_payment_stats(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> PaymentStats:
        """
        获取支付统计信息

        Args:
            user_id (Optional[int]): 用户ID过滤
            start_date (Optional[str]): 开始日期
            end_date (Optional[str]): 结束日期

        Returns:
            PaymentStats: 支付统计信息
        """

    @abstractmethod
    def get_user_payment_summary(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户支付摘要

        Args:
            user_id (int): 用户ID

        Returns:
            Dict[str, Any]: 用户支付摘要信息
        """

    # 支付方式管理
    @abstractmethod
    def get_available_payment_methods(self, user_id: int, amount: Decimal) -> List[str]:
        """
        获取可用的支付方式

        Args:
            user_id (int): 用户ID
            amount (Decimal): 支付金额

        Returns:
            List[str]: 可用的支付方式列表
        """

    @abstractmethod
    def validate_payment_method(self, payment_method: str, amount: Decimal) -> bool:
        """
        验证支付方式

        Args:
            payment_method (str): 支付方式
            amount (Decimal): 支付金额

        Returns:
            bool: 是否有效
        """


class PaymentRepositoryInterface(ABC):
    """
    支付仓储接口

    定义支付数据访问的标准接口。
    """

    @abstractmethod
    def create_payment(self, payment_data: PaymentCreate) -> PaymentModel:
        """创建支付"""

    @abstractmethod
    def get_payment_by_id(self, payment_id: int) -> Optional[PaymentModel]:
        """根据ID获取支付"""

    @abstractmethod
    def get_payment_by_order_id(self, order_id: str) -> Optional[PaymentModel]:
        """根据订单ID获取支付"""

    @abstractmethod
    def list_payments(self, query: PaymentQuery) -> List[PaymentModel]:
        """获取支付列表"""

    @abstractmethod
    def update_payment(
        self, payment_id: int, payment_data: PaymentUpdate
    ) -> Optional[PaymentModel]:
        """更新支付"""

    @abstractmethod
    def delete_payment(self, payment_id: int) -> bool:
        """删除支付"""

    @abstractmethod
    def count_payments(self, query: PaymentQuery) -> int:
        """统计支付数量"""


class PaymentProviderInterface(ABC):
    """
    支付提供商接口

    定义支付提供商的标准接口。
    """

    @abstractmethod
    def create_payment(self, payment_data: PaymentCreate) -> Dict[str, Any]:
        """
        创建支付

        Args:
            payment_data (PaymentCreate): 支付数据

        Returns:
            Dict[str, Any]: 支付创建结果
        """

    @abstractmethod
    def query_payment(self, external_id: str) -> Dict[str, Any]:
        """
        查询支付状态

        Args:
            external_id (str): 外部支付ID

        Returns:
            Dict[str, Any]: 支付状态信息
        """

    @abstractmethod
    def cancel_payment(self, external_id: str) -> bool:
        """
        取消支付

        Args:
            external_id (str): 外部支付ID

        Returns:
            bool: 是否取消成功
        """

    @abstractmethod
    def create_refund(
        self, payment_id: int, refund_amount: Decimal, reason: str
    ) -> Dict[str, Any]:
        """
        创建退款

        Args:
            payment_id (int): 支付ID
            refund_amount (Decimal): 退款金额
            reason (str): 退款原因

        Returns:
            Dict[str, Any]: 退款创建结果
        """

    @abstractmethod
    def verify_callback(self, callback_data: Dict[str, Any]) -> bool:
        """
        验证回调签名

        Args:
            callback_data (Dict[str, Any]): 回调数据

        Returns:
            bool: 签名是否有效
        """


class PaymentError(Exception):
    """支付异常基类"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        初始化支付异常

        Args:
            message (str): 错误消息
            details (Optional[Dict[str, Any]]): 错误详情
        """
        self.details = details or {}
        super().__init__(message)


class PaymentNotFoundError(PaymentError):
    """支付未找到异常"""



class PaymentValidationError(PaymentError):
    """支付验证异常"""



class PaymentProcessingError(PaymentError):
    """支付处理异常"""



class RefundError(PaymentError):
    """退款异常"""



class PaymentProviderError(PaymentError):
    """支付提供商异常"""

