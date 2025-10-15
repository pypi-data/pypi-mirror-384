高级使用示例
============

本页面提供Python模块化框架的高级使用示例，包括复杂场景和最佳实践。

复杂应用架构
------------

多层架构应用
~~~~~~~~~~~~

.. code-block:: python

    """
    多层架构应用示例
    
    演示如何构建一个具有多层架构的复杂应用。
    """

    from framework.core.application import Application
    from framework.interfaces.component import ComponentInterface
    from framework.core.config import Config
    from typing import Dict, Any, List
    import logging
    import asyncio

    class DataLayer(ComponentInterface):
        """数据层组件"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.logger = logging.getLogger(f"layer.{name}")
            self.data = {}
        
        def initialize(self) -> None:
            self.logger.info("初始化数据层")
            # 模拟数据库连接
            self.data = {
                "users": {},
                "products": {},
                "orders": {}
            }
        
        def start(self) -> None:
            self.logger.info("启动数据层")
        
        def stop(self) -> None:
            self.logger.info("停止数据层")
        
        def get_health_status(self) -> Dict[str, Any]:
            return {"status": "healthy", "data_count": len(self.data)}
        
        def create_user(self, user_data: Dict[str, Any]) -> str:
            """创建用户"""
            user_id = f"user_{len(self.data['users']) + 1}"
            self.data['users'][user_id] = user_data
            return user_id
        
        def get_user(self, user_id: str) -> Dict[str, Any]:
            """获取用户"""
            return self.data['users'].get(user_id)

    class BusinessLayer(ComponentInterface):
        """业务层组件"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.logger = logging.getLogger(f"layer.{name}")
            self.data_layer = None
        
        def initialize(self) -> None:
            self.logger.info("初始化业务层")
        
        def start(self) -> None:
            self.logger.info("启动业务层")
            # 获取数据层依赖
            self.data_layer = self.get_dependency("data-layer")
        
        def stop(self) -> None:
            self.logger.info("停止业务层")
        
        def get_health_status(self) -> Dict[str, Any]:
            return {"status": "healthy"}
        
        def register_user(self, username: str, email: str) -> Dict[str, Any]:
            """注册用户"""
            # 业务逻辑验证
            if not username or not email:
                raise ValueError("用户名和邮箱不能为空")
            
            if "@" not in email:
                raise ValueError("邮箱格式不正确")
            
            # 调用数据层
            user_data = {
                "username": username,
                "email": email,
                "status": "active"
            }
            
            user_id = self.data_layer.create_user(user_data)
            
            return {
                "user_id": user_id,
                "message": "用户注册成功"
            }

    class PresentationLayer(ComponentInterface):
        """表现层组件"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.logger = logging.getLogger(f"layer.{name}")
            self.business_layer = None
        
        def initialize(self) -> None:
            self.logger.info("初始化表现层")
        
        def start(self) -> None:
            self.logger.info("启动表现层")
            self.business_layer = self.get_dependency("business-layer")
        
        def stop(self) -> None:
            self.logger.info("停止表现层")
        
        def get_health_status(self) -> Dict[str, Any]:
            return {"status": "healthy"}
        
        def handle_user_registration(self, request: Dict[str, Any]) -> Dict[str, Any]:
            """处理用户注册请求"""
            try:
                username = request.get("username")
                email = request.get("email")
                
                result = self.business_layer.register_user(username, email)
                
                return {
                    "status": "success",
                    "data": result
                }
            except ValueError as e:
                return {
                    "status": "error",
                    "message": str(e)
                }
            except Exception as e:
                self.logger.error(f"处理用户注册失败: {e}")
                return {
                    "status": "error",
                    "message": "内部服务器错误"
                }

    def main():
        """主函数"""
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        
        # 创建应用
        app = Application("layered-app", "1.0.0")
        
        # 配置应用
        app.configure({
            "debug": True,
            "log_level": "INFO"
        })
        
        try:
            # 注册组件（按依赖顺序）
            data_layer = DataLayer("data-layer", app.config)
            business_layer = BusinessLayer("business-layer", app.config)
            presentation_layer = PresentationLayer("presentation-layer", app.config)
            
            app.register_component(data_layer)
            app.register_component(business_layer)
            app.register_component(presentation_layer)
            
            # 启动应用
            app.start()
            
            # 模拟请求处理
            presentation = app.get_component("presentation-layer")
            
            # 测试用户注册
            request = {
                "username": "john_doe",
                "email": "john@example.com"
            }
            
            response = presentation.handle_user_registration(request)
            print(f"注册响应: {response}")
            
        except Exception as e:
            print(f"应用运行失败: {e}")
        finally:
            app.stop()

    if __name__ == "__main__":
        main()

异步处理示例
------------

异步组件
~~~~~~~~

.. code-block:: python

    """
    异步处理示例
    
    演示如何在框架中使用异步编程。
    """

    import asyncio
    import aiohttp
    from framework.interfaces.component import ComponentInterface
    from framework.core.config import Config
    from typing import Dict, Any, List
    import logging

    class AsyncDataFetcher(ComponentInterface):
        """异步数据获取组件"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.logger = logging.getLogger(f"component.{name}")
            self.session = None
            self.running = False
        
        def initialize(self) -> None:
            self.logger.info("初始化异步数据获取组件")
        
        def start(self) -> None:
            self.logger.info("启动异步数据获取组件")
            self.running = True
        
        def stop(self) -> None:
            self.logger.info("停止异步数据获取组件")
            self.running = False
            if self.session:
                asyncio.create_task(self.session.close())
        
        def get_health_status(self) -> Dict[str, Any]:
            return {
                "status": "healthy" if self.running else "stopped",
                "session_active": self.session is not None
            }
        
        async def fetch_data(self, url: str) -> Dict[str, Any]:
            """异步获取数据"""
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            try:
                async with self.session.get(url) as response:
                    data = await response.json()
                    return {
                        "status": "success",
                        "data": data,
                        "status_code": response.status
                    }
            except Exception as e:
                self.logger.error(f"获取数据失败: {e}")
                return {
                    "status": "error",
                    "message": str(e)
                }
        
        async def fetch_multiple_data(self, urls: List[str]) -> List[Dict[str, Any]]:
            """并发获取多个数据源"""
            tasks = [self.fetch_data(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "url": urls[i],
                        "status": "error",
                        "message": str(result)
                    })
                else:
                    processed_results.append({
                        "url": urls[i],
                        **result
                    })
            
            return processed_results

    class AsyncProcessor(ComponentInterface):
        """异步处理器组件"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.logger = logging.getLogger(f"component.{name}")
            self.fetcher = None
            self.running = False
        
        def initialize(self) -> None:
            self.logger.info("初始化异步处理器")
        
        def start(self) -> None:
            self.logger.info("启动异步处理器")
            self.fetcher = self.get_dependency("data-fetcher")
            self.running = True
        
        def stop(self) -> None:
            self.logger.info("停止异步处理器")
            self.running = False
        
        def get_health_status(self) -> Dict[str, Any]:
            return {"status": "healthy" if self.running else "stopped"}
        
        async def process_data(self, urls: List[str]) -> Dict[str, Any]:
            """处理数据"""
            self.logger.info(f"开始处理 {len(urls)} 个数据源")
            
            # 获取数据
            results = await self.fetcher.fetch_multiple_data(urls)
            
            # 处理结果
            successful = [r for r in results if r["status"] == "success"]
            failed = [r for r in results if r["status"] == "error"]
            
            return {
                "total": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "results": results
            }

    async def main():
        """异步主函数"""
        from framework.core.application import Application
        
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        
        # 创建应用
        app = Application("async-app", "1.0.0")
        app.configure({"debug": True})
        
        try:
            # 注册组件
            fetcher = AsyncDataFetcher("data-fetcher", app.config)
            processor = AsyncProcessor("processor", app.config)
            
            app.register_component(fetcher)
            app.register_component(processor)
            
            # 启动应用
            app.start()
            
            # 异步处理数据
            urls = [
                "https://api.github.com/users/octocat",
                "https://api.github.com/users/defunkt",
                "https://api.github.com/users/mojombo"
            ]
            
            processor_component = app.get_component("processor")
            result = await processor_component.process_data(urls)
            
            print(f"处理结果: {result}")
            
        except Exception as e:
            print(f"应用运行失败: {e}")
        finally:
            app.stop()

    if __name__ == "__main__":
        asyncio.run(main())

事件驱动架构
------------

事件系统
~~~~~~~~

.. code-block:: python

    """
    事件驱动架构示例
    
    演示如何构建事件驱动的应用架构。
    """

    from framework.interfaces.component import ComponentInterface
    from framework.core.config import Config
    from typing import Dict, Any, Callable, List
    import logging
    import threading
    from queue import Queue
    from dataclasses import dataclass
    from datetime import datetime

    @dataclass
    class Event:
        """事件类"""
        name: str
        data: Dict[str, Any]
        timestamp: datetime
        source: str

    class EventBus(ComponentInterface):
        """事件总线组件"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.logger = logging.getLogger(f"component.{name}")
            self.handlers: Dict[str, List[Callable]] = {}
            self.event_queue = Queue()
            self.running = False
            self.worker_thread = None
        
        def initialize(self) -> None:
            self.logger.info("初始化事件总线")
        
        def start(self) -> None:
            self.logger.info("启动事件总线")
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_events)
            self.worker_thread.start()
        
        def stop(self) -> None:
            self.logger.info("停止事件总线")
            self.running = False
            if self.worker_thread:
                self.worker_thread.join()
        
        def get_health_status(self) -> Dict[str, Any]:
            return {
                "status": "healthy" if self.running else "stopped",
                "handlers_count": len(self.handlers),
                "queue_size": self.event_queue.qsize()
            }
        
        def subscribe(self, event_name: str, handler: Callable) -> None:
            """订阅事件"""
            if event_name not in self.handlers:
                self.handlers[event_name] = []
            self.handlers[event_name].append(handler)
            self.logger.info(f"订阅事件: {event_name}")
        
        def publish(self, event: Event) -> None:
            """发布事件"""
            self.event_queue.put(event)
            self.logger.debug(f"发布事件: {event.name}")
        
        def _process_events(self) -> None:
            """处理事件"""
            while self.running:
                try:
                    event = self.event_queue.get(timeout=1)
                    self._handle_event(event)
                except:
                    continue
        
        def _handle_event(self, event: Event) -> None:
            """处理单个事件"""
            handlers = self.handlers.get(event.name, [])
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    self.logger.error(f"事件处理失败: {e}")

    class UserService(ComponentInterface):
        """用户服务组件"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.logger = logging.getLogger(f"component.{name}")
            self.event_bus = None
            self.users = {}
        
        def initialize(self) -> None:
            self.logger.info("初始化用户服务")
        
        def start(self) -> None:
            self.logger.info("启动用户服务")
            self.event_bus = self.get_dependency("event-bus")
            
            # 订阅事件
            self.event_bus.subscribe("user.created", self._on_user_created)
            self.event_bus.subscribe("user.updated", self._on_user_updated)
        
        def stop(self) -> None:
            self.logger.info("停止用户服务")
        
        def get_health_status(self) -> Dict[str, Any]:
            return {"status": "healthy", "users_count": len(self.users)}
        
        def create_user(self, username: str, email: str) -> str:
            """创建用户"""
            user_id = f"user_{len(self.users) + 1}"
            user_data = {
                "id": user_id,
                "username": username,
                "email": email,
                "created_at": datetime.now()
            }
            
            self.users[user_id] = user_data
            
            # 发布事件
            event = Event(
                name="user.created",
                data=user_data,
                timestamp=datetime.now(),
                source=self.name
            )
            self.event_bus.publish(event)
            
            return user_id
        
        def _on_user_created(self, event: Event) -> None:
            """处理用户创建事件"""
            self.logger.info(f"用户创建事件: {event.data['username']}")
        
        def _on_user_updated(self, event: Event) -> None:
            """处理用户更新事件"""
            self.logger.info(f"用户更新事件: {event.data['username']}")

    class NotificationService(ComponentInterface):
        """通知服务组件"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.logger = logging.getLogger(f"component.{name}")
            self.event_bus = None
        
        def initialize(self) -> None:
            self.logger.info("初始化通知服务")
        
        def start(self) -> None:
            self.logger.info("启动通知服务")
            self.event_bus = self.get_dependency("event-bus")
            
            # 订阅事件
            self.event_bus.subscribe("user.created", self._send_welcome_email)
        
        def stop(self) -> None:
            self.logger.info("停止通知服务")
        
        def get_health_status(self) -> Dict[str, Any]:
            return {"status": "healthy"}
        
        def _send_welcome_email(self, event: Event) -> None:
            """发送欢迎邮件"""
            user_data = event.data
            self.logger.info(f"发送欢迎邮件给: {user_data['email']}")

    def main():
        """主函数"""
        from framework.core.application import Application
        
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        
        # 创建应用
        app = Application("event-driven-app", "1.0.0")
        app.configure({"debug": True})
        
        try:
            # 注册组件
            event_bus = EventBus("event-bus", app.config)
            user_service = UserService("user-service", app.config)
            notification_service = NotificationService("notification-service", app.config)
            
            app.register_component(event_bus)
            app.register_component(user_service)
            app.register_component(notification_service)
            
            # 启动应用
            app.start()
            
            # 创建用户（触发事件）
            user_service_component = app.get_component("user-service")
            user_id = user_service_component.create_user("john_doe", "john@example.com")
            print(f"创建用户: {user_id}")
            
            # 等待事件处理
            import time
            time.sleep(1)
            
        except Exception as e:
            print(f"应用运行失败: {e}")
        finally:
            app.stop()

    if __name__ == "__main__":
        main()

性能优化示例
------------

缓存优化
~~~~~~~~

.. code-block:: python

    """
    性能优化示例
    
    演示如何使用缓存和连接池优化性能。
    """

    from framework.interfaces.component import ComponentInterface
    from framework.core.config import Config
    from typing import Dict, Any, Optional
    import logging
    import time
    import threading
    from functools import wraps

    def cache_result(ttl: int = 300):
        """缓存装饰器"""
        def decorator(func):
            cache = {}
            cache_times = {}
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                # 检查缓存
                now = time.time()
                if cache_key in cache:
                    if now - cache_times[cache_key] < ttl:
                        return cache[cache_key]
                    else:
                        # 缓存过期
                        del cache[cache_key]
                        del cache_times[cache_key]
                
                # 执行函数并缓存结果
                result = func(*args, **kwargs)
                cache[cache_key] = result
                cache_times[cache_key] = now
                
                return result
            
            return wrapper
        return decorator

    class OptimizedDataService(ComponentInterface):
        """优化的数据服务组件"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.logger = logging.getLogger(f"component.{name}")
            self.cache = {}
            self.cache_lock = threading.Lock()
            self.connection_pool = []
            self.pool_lock = threading.Lock()
            self.max_connections = config.get(f"components.{name}.max_connections", 10)
        
        def initialize(self) -> None:
            self.logger.info("初始化优化的数据服务")
            # 初始化连接池
            for _ in range(self.max_connections):
                self.connection_pool.append(self._create_connection())
        
        def start(self) -> None:
            self.logger.info("启动优化的数据服务")
        
        def stop(self) -> None:
            self.logger.info("停止优化的数据服务")
            # 关闭连接池
            with self.pool_lock:
                for conn in self.connection_pool:
                    self._close_connection(conn)
                self.connection_pool.clear()
        
        def get_health_status(self) -> Dict[str, Any]:
            return {
                "status": "healthy",
                "cache_size": len(self.cache),
                "available_connections": len(self.connection_pool)
            }
        
        def _create_connection(self):
            """创建连接"""
            # 模拟数据库连接
            return {"id": f"conn_{len(self.connection_pool)}", "active": True}
        
        def _close_connection(self, conn):
            """关闭连接"""
            conn["active"] = False
        
        def _get_connection(self):
            """获取连接"""
            with self.pool_lock:
                if self.connection_pool:
                    return self.connection_pool.pop()
                else:
                    # 连接池为空，创建新连接
                    return self._create_connection()
        
        def _return_connection(self, conn):
            """归还连接"""
            with self.pool_lock:
                if len(self.connection_pool) < self.max_connections:
                    self.connection_pool.append(conn)
        
        @cache_result(ttl=60)  # 缓存1分钟
        def get_user_data(self, user_id: str) -> Dict[str, Any]:
            """获取用户数据（带缓存）"""
            # 模拟数据库查询
            time.sleep(0.1)  # 模拟网络延迟
            
            return {
                "id": user_id,
                "name": f"User {user_id}",
                "email": f"user{user_id}@example.com",
                "created_at": "2024-01-01"
            }
        
        def get_user_data_batch(self, user_ids: list) -> Dict[str, Any]:
            """批量获取用户数据"""
            results = {}
            
            # 使用线程池并发处理
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_id = {
                    executor.submit(self.get_user_data, user_id): user_id
                    for user_id in user_ids
                }
                
                for future in concurrent.futures.as_completed(future_to_id):
                    user_id = future_to_id[future]
                    try:
                        results[user_id] = future.result()
                    except Exception as e:
                        self.logger.error(f"获取用户数据失败: {e}")
                        results[user_id] = {"error": str(e)}
            
            return results

    def main():
        """主函数"""
        from framework.core.application import Application
        
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        
        # 创建应用
        app = Application("optimized-app", "1.0.0")
        app.configure({
            "debug": True,
            "components": {
                "data-service": {
                    "max_connections": 5
                }
            }
        })
        
        try:
            # 注册组件
            data_service = OptimizedDataService("data-service", app.config)
            app.register_component(data_service)
            
            # 启动应用
            app.start()
            
            # 测试性能
            service = app.get_component("data-service")
            
            # 测试缓存效果
            print("测试缓存效果...")
            start_time = time.time()
            
            # 第一次调用（无缓存）
            user1 = service.get_user_data("user1")
            first_call_time = time.time() - start_time
            
            # 第二次调用（有缓存）
            start_time = time.time()
            user1_cached = service.get_user_data("user1")
            second_call_time = time.time() - start_time
            
            print(f"第一次调用耗时: {first_call_time:.3f}秒")
            print(f"第二次调用耗时: {second_call_time:.3f}秒")
            print(f"缓存加速比: {first_call_time/second_call_time:.1f}x")
            
            # 测试批量处理
            print("\n测试批量处理...")
            user_ids = [f"user{i}" for i in range(1, 11)]
            
            start_time = time.time()
            batch_results = service.get_user_data_batch(user_ids)
            batch_time = time.time() - start_time
            
            print(f"批量处理 {len(user_ids)} 个用户耗时: {batch_time:.3f}秒")
            print(f"平均每个用户: {batch_time/len(user_ids):.3f}秒")
            
        except Exception as e:
            print(f"应用运行失败: {e}")
        finally:
            app.stop()

    if __name__ == "__main__":
        main()

更多示例
--------

* :doc:`real_world_applications` - 实际应用示例
* :doc:`basic_usage` - 基本使用示例
* :doc:`../api/framework` - API参考
* :doc:`../concepts/overview` - 核心概念
