"""
支付组件测试

测试components.payment模块中的支付组件。

测试内容：
- 支付组件接口
- 支付服务
- 支付模型
- 支付流程

作者：开发团队
创建时间：2025-01-12
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from components.payment.component import PaymentComponent
from components.payment.interfaces import PaymentInterface, PaymentStatus
from components.payment.models import Payment, PaymentMethod, PaymentResult
from components.payment.service import PaymentService


class TestPaymentComponent:
    """支付组件测试"""
    
    def test_payment_component_initialization(self):
        """测试支付组件初始化"""
        component = PaymentComponent()
        
        assert component.name == "payment"
        assert component.version == "1.0.0"
        assert component.description == "Payment processing component"
        assert component.author == "Framework Team"
    
    def test_payment_component_interface_implementation(self):
        """测试支付组件接口实现"""
        component = PaymentComponent()
        
        # 验证实现了PaymentInterface
        assert isinstance(component, PaymentInterface)
        
        # 验证接口方法存在
        assert hasattr(component, 'process_payment')
        assert hasattr(component, 'refund_payment')
        assert hasattr(component, 'get_payment_status')
        assert hasattr(component, 'validate_payment_method')
    
    def test_payment_component_process_payment(self):
        """测试处理支付"""
        component = PaymentComponent()
        
        # 模拟支付数据
        payment_data = {
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "credit_card",
            "customer_id": "customer_123"
        }
        
        # 模拟支付服务
        with patch.object(component, '_payment_service') as mock_service:
            mock_result = PaymentResult(
                payment_id="pay_123",
                status=PaymentStatus.COMPLETED,
                amount=100.00,
                currency="USD"
            )
            mock_service.process_payment.return_value = mock_result
            
            result = component.process_payment(payment_data)
            
            assert result is not None
            assert result.payment_id == "pay_123"
            assert result.status == PaymentStatus.COMPLETED
            assert result.amount == 100.00
            mock_service.process_payment.assert_called_once_with(payment_data)
    
    def test_payment_component_refund_payment(self):
        """测试退款支付"""
        component = PaymentComponent()
        
        # 模拟退款数据
        refund_data = {
            "payment_id": "pay_123",
            "amount": 50.00,
            "reason": "Customer request"
        }
        
        # 模拟支付服务
        with patch.object(component, '_payment_service') as mock_service:
            mock_result = PaymentResult(
                payment_id="pay_123",
                status=PaymentStatus.REFUNDED,
                amount=50.00,
                currency="USD"
            )
            mock_service.refund_payment.return_value = mock_result
            
            result = component.refund_payment(refund_data)
            
            assert result is not None
            assert result.payment_id == "pay_123"
            assert result.status == PaymentStatus.REFUNDED
            assert result.amount == 50.00
            mock_service.refund_payment.assert_called_once_with(refund_data)
    
    def test_payment_component_get_payment_status(self):
        """测试获取支付状态"""
        component = PaymentComponent()
        
        payment_id = "pay_123"
        
        # 模拟支付服务
        with patch.object(component, '_payment_service') as mock_service:
            mock_payment = Payment(
                payment_id=payment_id,
                amount=100.00,
                currency="USD",
                status=PaymentStatus.COMPLETED,
                payment_method=PaymentMethod.CREDIT_CARD
            )
            mock_service.get_payment.return_value = mock_payment
            
            result = component.get_payment_status(payment_id)
            
            assert result is not None
            assert result.payment_id == payment_id
            assert result.status == PaymentStatus.COMPLETED
            mock_service.get_payment.assert_called_once_with(payment_id)
    
    def test_payment_component_validate_payment_method(self):
        """测试验证支付方式"""
        component = PaymentComponent()
        
        payment_method_data = {
            "type": "credit_card",
            "card_number": "4111111111111111",
            "expiry_month": "12",
            "expiry_year": "2025",
            "cvv": "123"
        }
        
        # 模拟支付服务
        with patch.object(component, '_payment_service') as mock_service:
            mock_service.validate_payment_method.return_value = True
            
            result = component.validate_payment_method(payment_method_data)
            
            assert result is True
            mock_service.validate_payment_method.assert_called_once_with(payment_method_data)
    
    def test_payment_component_initialization_with_config(self):
        """测试使用配置初始化支付组件"""
        config = {
            "payment_gateway": "stripe",
            "api_key": "sk_test_123",
            "webhook_secret": "whsec_123",
            "default_currency": "USD"
        }
        
        component = PaymentComponent()
        component.initialize(config)
        
        # 验证配置被正确设置
        assert component._config == config
        assert component._payment_service is not None
    
    def test_payment_component_error_handling(self):
        """测试支付组件错误处理"""
        component = PaymentComponent()
        
        # 测试无效支付数据
        invalid_payment_data = {
            "amount": -100.00,  # 负数金额
            "currency": "USD"
        }
        
        with patch.object(component, '_payment_service') as mock_service:
            mock_service.process_payment.side_effect = ValueError("Invalid amount")
            
            with pytest.raises(ValueError, match="Invalid amount"):
                component.process_payment(invalid_payment_data)
    
    def test_payment_component_payment_methods(self):
        """测试支持的支付方式"""
        component = PaymentComponent()
        
        # 验证支持的支付方式
        supported_methods = component.get_supported_payment_methods()
        
        assert isinstance(supported_methods, list)
        assert len(supported_methods) > 0
        
        # 验证包含常见的支付方式
        expected_methods = ["credit_card", "debit_card", "paypal", "bank_transfer"]
        for method in expected_methods:
            assert method in supported_methods


class TestPaymentService:
    """支付服务测试"""
    
    def test_payment_service_initialization(self):
        """测试支付服务初始化"""
        service = PaymentService()
        
        assert service._config == {}
        assert service._gateway is None
    
    def test_payment_service_initialization_with_config(self):
        """测试使用配置初始化支付服务"""
        config = {
            "gateway": "stripe",
            "api_key": "sk_test_123",
            "webhook_secret": "whsec_123"
        }
        
        service = PaymentService(config)
        
        assert service._config == config
    
    def test_payment_service_process_payment(self):
        """测试处理支付"""
        service = PaymentService()
        
        payment_data = {
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "credit_card",
            "customer_id": "customer_123"
        }
        
        # 模拟支付网关
        with patch.object(service, '_gateway') as mock_gateway:
            mock_gateway.process_payment.return_value = {
                "payment_id": "pay_123",
                "status": "completed",
                "amount": 100.00,
                "currency": "USD"
            }
            
            result = service.process_payment(payment_data)
            
            assert result is not None
            assert result.payment_id == "pay_123"
            assert result.status == PaymentStatus.COMPLETED
            assert result.amount == 100.00
            assert result.currency == "USD"
    
    def test_payment_service_refund_payment(self):
        """测试退款支付"""
        service = PaymentService()
        
        refund_data = {
            "payment_id": "pay_123",
            "amount": 50.00,
            "reason": "Customer request"
        }
        
        # 模拟支付网关
        with patch.object(service, '_gateway') as mock_gateway:
            mock_gateway.refund_payment.return_value = {
                "payment_id": "pay_123",
                "status": "refunded",
                "amount": 50.00,
                "currency": "USD"
            }
            
            result = service.refund_payment(refund_data)
            
            assert result is not None
            assert result.payment_id == "pay_123"
            assert result.status == PaymentStatus.REFUNDED
            assert result.amount == 50.00
    
    def test_payment_service_get_payment(self):
        """测试获取支付信息"""
        service = PaymentService()
        
        payment_id = "pay_123"
        
        # 模拟支付网关
        with patch.object(service, '_gateway') as mock_gateway:
            mock_gateway.get_payment.return_value = {
                "payment_id": payment_id,
                "amount": 100.00,
                "currency": "USD",
                "status": "completed",
                "payment_method": "credit_card"
            }
            
            result = service.get_payment(payment_id)
            
            assert result is not None
            assert result.payment_id == payment_id
            assert result.amount == 100.00
            assert result.status == PaymentStatus.COMPLETED
    
    def test_payment_service_validate_payment_method(self):
        """测试验证支付方式"""
        service = PaymentService()
        
        payment_method_data = {
            "type": "credit_card",
            "card_number": "4111111111111111",
            "expiry_month": "12",
            "expiry_year": "2025",
            "cvv": "123"
        }
        
        # 模拟支付网关
        with patch.object(service, '_gateway') as mock_gateway:
            mock_gateway.validate_payment_method.return_value = True
            
            result = service.validate_payment_method(payment_method_data)
            
            assert result is True
            mock_gateway.validate_payment_method.assert_called_once_with(payment_method_data)
    
    def test_payment_service_error_handling(self):
        """测试支付服务错误处理"""
        service = PaymentService()
        
        # 测试无效支付数据
        invalid_payment_data = {
            "amount": -100.00,  # 负数金额
            "currency": "USD"
        }
        
        with pytest.raises(ValueError, match="Invalid payment data"):
            service.process_payment(invalid_payment_data)
    
    def test_payment_service_gateway_integration(self):
        """测试支付网关集成"""
        config = {
            "gateway": "stripe",
            "api_key": "sk_test_123"
        }
        
        service = PaymentService(config)
        
        # 验证网关被正确初始化
        assert service._gateway is not None
        assert service._gateway.api_key == "sk_test_123"


class TestPaymentModels:
    """支付模型测试"""
    
    def test_payment_model_creation(self):
        """测试支付模型创建"""
        payment = Payment(
            payment_id="pay_123",
            amount=100.00,
            currency="USD",
            status=PaymentStatus.COMPLETED,
            payment_method=PaymentMethod.CREDIT_CARD
        )
        
        assert payment.payment_id == "pay_123"
        assert payment.amount == 100.00
        assert payment.currency == "USD"
        assert payment.status == PaymentStatus.COMPLETED
        assert payment.payment_method == PaymentMethod.CREDIT_CARD
    
    def test_payment_model_validation(self):
        """测试支付模型验证"""
        # 测试有效支付
        payment = Payment(
            payment_id="pay_123",
            amount=100.00,
            currency="USD",
            status=PaymentStatus.COMPLETED,
            payment_method=PaymentMethod.CREDIT_CARD
        )
        
        assert payment.is_valid() is True
        
        # 测试无效支付（负数金额）
        invalid_payment = Payment(
            payment_id="pay_123",
            amount=-100.00,
            currency="USD",
            status=PaymentStatus.COMPLETED,
            payment_method=PaymentMethod.CREDIT_CARD
        )
        
        assert invalid_payment.is_valid() is False
    
    def test_payment_result_model(self):
        """测试支付结果模型"""
        result = PaymentResult(
            payment_id="pay_123",
            status=PaymentStatus.COMPLETED,
            amount=100.00,
            currency="USD"
        )
        
        assert result.payment_id == "pay_123"
        assert result.status == PaymentStatus.COMPLETED
        assert result.amount == 100.00
        assert result.currency == "USD"
        assert result.is_successful() is True
    
    def test_payment_method_enum(self):
        """测试支付方式枚举"""
        assert PaymentMethod.CREDIT_CARD.value == "credit_card"
        assert PaymentMethod.DEBIT_CARD.value == "debit_card"
        assert PaymentMethod.PAYPAL.value == "paypal"
        assert PaymentMethod.BANK_TRANSFER.value == "bank_transfer"
    
    def test_payment_status_enum(self):
        """测试支付状态枚举"""
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.COMPLETED.value == "completed"
        assert PaymentStatus.FAILED.value == "failed"
        assert PaymentStatus.REFUNDED.value == "refunded"
        assert PaymentStatus.CANCELLED.value == "cancelled"


class TestPaymentIntegration:
    """支付集成测试"""
    
    def test_complete_payment_flow(self):
        """测试完整支付流程"""
        component = PaymentComponent()
        
        # 初始化组件
        config = {
            "gateway": "stripe",
            "api_key": "sk_test_123"
        }
        component.initialize(config)
        
        # 模拟支付数据
        payment_data = {
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "credit_card",
            "customer_id": "customer_123"
        }
        
        # 模拟支付服务
        with patch.object(component, '_payment_service') as mock_service:
            # 模拟支付处理
            mock_payment_result = PaymentResult(
                payment_id="pay_123",
                status=PaymentStatus.COMPLETED,
                amount=100.00,
                currency="USD"
            )
            mock_service.process_payment.return_value = mock_payment_result
            
            # 模拟获取支付状态
            mock_payment = Payment(
                payment_id="pay_123",
                amount=100.00,
                currency="USD",
                status=PaymentStatus.COMPLETED,
                payment_method=PaymentMethod.CREDIT_CARD
            )
            mock_service.get_payment.return_value = mock_payment
            
            # 执行支付流程
            result = component.process_payment(payment_data)
            
            # 验证支付结果
            assert result is not None
            assert result.payment_id == "pay_123"
            assert result.status == PaymentStatus.COMPLETED
            
            # 验证支付状态
            status = component.get_payment_status("pay_123")
            assert status is not None
            assert status.status == PaymentStatus.COMPLETED
    
    def test_payment_refund_flow(self):
        """测试支付退款流程"""
        component = PaymentComponent()
        
        # 初始化组件
        config = {
            "gateway": "stripe",
            "api_key": "sk_test_123"
        }
        component.initialize(config)
        
        # 模拟退款数据
        refund_data = {
            "payment_id": "pay_123",
            "amount": 50.00,
            "reason": "Customer request"
        }
        
        # 模拟支付服务
        with patch.object(component, '_payment_service') as mock_service:
            # 模拟退款处理
            mock_refund_result = PaymentResult(
                payment_id="pay_123",
                status=PaymentStatus.REFUNDED,
                amount=50.00,
                currency="USD"
            )
            mock_service.refund_payment.return_value = mock_refund_result
            
            # 执行退款流程
            result = component.refund_payment(refund_data)
            
            # 验证退款结果
            assert result is not None
            assert result.payment_id == "pay_123"
            assert result.status == PaymentStatus.REFUNDED
            assert result.amount == 50.00


@pytest.mark.parametrize("amount,currency,expected_valid", [
    (100.00, "USD", True),
    (0.01, "EUR", True),
    (999.99, "GBP", True),
    (-100.00, "USD", False),
    (0.00, "USD", False),
    (100.00, "INVALID", False),
])
def test_payment_amount_validation(amount, currency, expected_valid):
    """测试支付金额验证"""
    payment = Payment(
        payment_id="pay_123",
        amount=amount,
        currency=currency,
        status=PaymentStatus.PENDING,
        payment_method=PaymentMethod.CREDIT_CARD
    )
    
    assert payment.is_valid() == expected_valid


@pytest.mark.parametrize("status,expected_successful", [
    (PaymentStatus.COMPLETED, True),
    (PaymentStatus.PENDING, False),
    (PaymentStatus.FAILED, False),
    (PaymentStatus.REFUNDED, False),
    (PaymentStatus.CANCELLED, False),
])
def test_payment_result_success(status, expected_successful):
    """测试支付结果成功状态"""
    result = PaymentResult(
        payment_id="pay_123",
        status=status,
        amount=100.00,
        currency="USD"
    )
    
    assert result.is_successful() == expected_successful

