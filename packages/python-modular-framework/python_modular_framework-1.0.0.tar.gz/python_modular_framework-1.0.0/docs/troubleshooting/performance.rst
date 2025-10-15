性能问题故障排除
================

本页面专门介绍Python模块化框架的性能问题诊断和优化方法。

性能监控
--------

性能指标
~~~~~~~~

关键性能指标包括：

* **启动时间**: 应用启动到就绪的时间
* **内存使用**: 应用运行时的内存消耗
* **响应时间**: 请求处理时间
* **吞吐量**: 每秒处理的请求数
* **并发数**: 同时处理的请求数

监控工具
~~~~~~~~

使用内置性能监控::

    from framework.core.application import Application
    import time

    def monitor_performance():
        """监控应用性能"""
        app = Application("monitor-app", "1.0.0")
        
        # 记录启动时间
        start_time = time.time()
        app.start()
        startup_time = time.time() - start_time
        
        print(f"启动时间: {startup_time:.3f}秒")
        
        # 获取组件健康状态
        for component_name in app.get_component_names():
            component = app.get_component(component_name)
            health = component.get_health_status()
            print(f"组件 {component_name}: {health}")

使用外部监控工具::

    # 使用psutil监控系统资源
    import psutil
    import time

    def monitor_system_resources():
        """监控系统资源使用"""
        process = psutil.Process()
        
        while True:
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            print(f"CPU使用率: {cpu_percent}%")
            print(f"内存使用: {memory_mb:.1f}MB")
            
            time.sleep(1)

性能分析
--------

使用cProfile分析
~~~~~~~~~~~~~~~

.. code-block:: python

    """
    性能分析示例
    
    使用cProfile分析应用性能瓶颈。
    """

    import cProfile
    import pstats
    from framework.core.application import Application

    def profile_application():
        """分析应用性能"""
        app = Application("profile-app", "1.0.0")
        
        # 创建性能分析器
        profiler = cProfile.Profile()
        
        # 开始分析
        profiler.enable()
        
        try:
            # 启动应用
            app.start()
            
            # 执行一些操作
            for i in range(1000):
                # 模拟一些工作
                pass
            
        finally:
            # 停止分析
            profiler.disable()
            app.stop()
        
        # 分析结果
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # 显示前10个最耗时的函数

    if __name__ == "__main__":
        profile_application()

使用line_profiler分析
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    """
    行级性能分析示例
    
    使用line_profiler分析代码行级性能。
    """

    from line_profiler import LineProfiler
    from framework.core.application import Application

    def slow_function():
        """模拟慢函数"""
        result = 0
        for i in range(1000000):
            result += i * i
        return result

    def profile_lines():
        """分析代码行性能"""
        profiler = LineProfiler()
        profiler.add_function(slow_function)
        
        profiler.enable_by_count()
        
        # 执行函数
        result = slow_function()
        
        profiler.disable_by_count()
        
        # 输出结果
        profiler.print_stats()

    if __name__ == "__main__":
        profile_lines()

内存分析
--------

使用memory_profiler
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    """
    内存分析示例
    
    使用memory_profiler分析内存使用情况。
    """

    from memory_profiler import profile
    from framework.core.application import Application

    @profile
    def memory_intensive_operation():
        """内存密集型操作"""
        # 创建大量数据
        data = []
        for i in range(100000):
            data.append({
                "id": i,
                "name": f"item_{i}",
                "data": "x" * 1000
            })
        
        # 处理数据
        result = [item["name"] for item in data if item["id"] % 2 == 0]
        
        return result

    def analyze_memory():
        """分析内存使用"""
        result = memory_intensive_operation()
        print(f"处理了 {len(result)} 个项目")

    if __name__ == "__main__":
        analyze_memory()

使用tracemalloc
~~~~~~~~~~~~~~~

.. code-block:: python

    """
    使用tracemalloc分析内存分配
    """

    import tracemalloc
    from framework.core.application import Application

    def analyze_memory_allocation():
        """分析内存分配"""
        # 开始跟踪内存分配
        tracemalloc.start()
        
        app = Application("memory-app", "1.0.0")
        app.start()
        
        # 执行一些操作
        for i in range(1000):
            # 模拟内存分配
            data = [j for j in range(1000)]
        
        app.stop()
        
        # 获取内存统计
        current, peak = tracemalloc.get_traced_memory()
        print(f"当前内存使用: {current / 1024 / 1024:.1f}MB")
        print(f"峰值内存使用: {peak / 1024 / 1024:.1f}MB")
        
        # 获取内存分配统计
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        print("内存分配统计:")
        for stat in top_stats[:10]:
            print(stat)
        
        tracemalloc.stop()

    if __name__ == "__main__":
        analyze_memory_allocation()

性能优化
--------

启动时间优化
~~~~~~~~~~~~

**问题**: 应用启动时间过长

**优化方法**:

1. 延迟加载组件::

    class LazyComponent(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self._initialized = False
        
        def initialize(self) -> None:
            """延迟初始化"""
            if not self._initialized:
                # 只在需要时初始化
                self._do_initialization()
                self._initialized = True
        
        def _do_initialization(self):
            """实际初始化逻辑"""
            pass

2. 并行初始化::

    import concurrent.futures
    from framework.core.application import Application

    def parallel_initialization():
        """并行初始化组件"""
        app = Application("parallel-app", "1.0.0")
        
        # 获取所有组件
        components = app.get_components()
        
        # 并行初始化
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for component in components:
                future = executor.submit(component.initialize)
                futures.append(future)
            
            # 等待所有组件初始化完成
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"组件初始化失败: {e}")

3. 缓存配置::

    import pickle
    import os

    class ConfigCache:
        """配置缓存"""
        
        def __init__(self, cache_file="config_cache.pkl"):
            self.cache_file = cache_file
        
        def load_config(self, config_source):
            """加载配置（带缓存）"""
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
            
            # 加载配置
            config = self._load_from_source(config_source)
            
            # 缓存配置
            with open(self.cache_file, 'wb') as f:
                pickle.dump(config, f)
            
            return config

内存使用优化
~~~~~~~~~~~~

**问题**: 内存使用过高

**优化方法**:

1. 使用生成器::

    def process_large_dataset(data_source):
        """使用生成器处理大数据集"""
        for item in data_source:
            # 处理单个项目
            processed_item = process_item(item)
            yield processed_item

    def process_item(item):
        """处理单个项目"""
        return item * 2

2. 及时释放资源::

    class ResourceManager(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.resources = []
        
        def start(self) -> None:
            """启动时分配资源"""
            self.resources.append(self._allocate_resource())
        
        def stop(self) -> None:
            """停止时释放资源"""
            for resource in self.resources:
                self._release_resource(resource)
            self.resources.clear()
        
        def _allocate_resource(self):
            """分配资源"""
            pass
        
        def _release_resource(self, resource):
            """释放资源"""
            pass

3. 使用对象池::

    class ObjectPool:
        """对象池"""
        
        def __init__(self, factory, max_size=100):
            self.factory = factory
            self.max_size = max_size
            self.pool = []
            self.in_use = set()
        
        def get_object(self):
            """获取对象"""
            if self.pool:
                obj = self.pool.pop()
            else:
                obj = self.factory()
            
            self.in_use.add(obj)
            return obj
        
        def return_object(self, obj):
            """归还对象"""
            if obj in self.in_use:
                self.in_use.remove(obj)
                if len(self.pool) < self.max_size:
                    self.pool.append(obj)

响应时间优化
~~~~~~~~~~~~

**问题**: 请求响应时间过长

**优化方法**:

1. 使用缓存::

    from functools import lru_cache
    import time

    class CachedService(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.cache = {}
            self.cache_ttl = config.get(f"components.{name}.cache_ttl", 300)
        
        @lru_cache(maxsize=128)
        def expensive_calculation(self, param):
            """缓存计算结果"""
            time.sleep(0.1)  # 模拟耗时计算
            return param * param
        
        def get_cached_data(self, key):
            """获取缓存数据"""
            if key in self.cache:
                data, timestamp = self.cache[key]
                if time.time() - timestamp < self.cache_ttl:
                    return data
            
            # 计算新数据
            data = self._compute_data(key)
            self.cache[key] = (data, time.time())
            return data

2. 异步处理::

    import asyncio
    import aiohttp

    class AsyncService(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.session = None
        
        async def start(self) -> None:
            """异步启动"""
            self.session = aiohttp.ClientSession()
        
        async def stop(self) -> None:
            """异步停止"""
            if self.session:
                await self.session.close()
        
        async def fetch_data_async(self, url):
            """异步获取数据"""
            async with self.session.get(url) as response:
                return await response.json()

3. 连接池::

    from sqlalchemy.pool import QueuePool
    from sqlalchemy import create_engine

    class DatabaseService(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.engine = None
        
        def initialize(self) -> None:
            """初始化数据库连接池"""
            database_url = self.config.get(f"components.{self.name}.database_url")
            
            self.engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )

并发性能优化
~~~~~~~~~~~~

**问题**: 并发处理能力不足

**优化方法**:

1. 使用线程池::

    import concurrent.futures
    import threading

    class ConcurrentProcessor(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.thread_pool = None
            self.max_workers = config.get(f"components.{name}.max_workers", 4)
        
        def start(self) -> None:
            """启动线程池"""
            self.thread_pool = concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers
            )
        
        def stop(self) -> None:
            """停止线程池"""
            if self.thread_pool:
                self.thread_pool.shutdown(wait=True)
        
        def process_requests(self, requests):
            """并发处理请求"""
            with self.thread_pool as executor:
                futures = [
                    executor.submit(self._process_request, req)
                    for req in requests
                ]
                
                results = []
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        print(f"处理请求失败: {e}")
                
                return results

2. 使用异步IO::

    import asyncio
    import aiohttp

    class AsyncProcessor(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.session = None
        
        async def start(self) -> None:
            """异步启动"""
            self.session = aiohttp.ClientSession()
        
        async def stop(self) -> None:
            """异步停止"""
            if self.session:
                await self.session.close()
        
        async def process_requests_async(self, requests):
            """异步处理请求"""
            tasks = [
                self._process_request_async(req)
                for req in requests
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results

性能测试
--------

基准测试
~~~~~~~~

.. code-block:: python

    """
    性能基准测试示例
    """

    import time
    import statistics
    from framework.core.application import Application

    class PerformanceBenchmark:
        """性能基准测试"""
        
        def __init__(self):
            self.results = {}
        
        def benchmark_startup_time(self, iterations=10):
            """测试启动时间"""
            times = []
            
            for i in range(iterations):
                app = Application("benchmark-app", "1.0.0")
                
                start_time = time.time()
                app.start()
                startup_time = time.time() - start_time
                
                app.stop()
                times.append(startup_time)
            
            self.results['startup_time'] = {
                'mean': statistics.mean(times),
                'median': statistics.median(times),
                'std': statistics.stdev(times),
                'min': min(times),
                'max': max(times)
            }
        
        def benchmark_memory_usage(self):
            """测试内存使用"""
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            
            # 记录初始内存
            initial_memory = process.memory_info().rss / 1024 / 1024
            
            # 启动应用
            app = Application("memory-benchmark", "1.0.0")
            app.start()
            
            # 记录运行内存
            running_memory = process.memory_info().rss / 1024 / 1024
            
            app.stop()
            
            # 记录停止后内存
            final_memory = process.memory_info().rss / 1024 / 1024
            
            self.results['memory_usage'] = {
                'initial': initial_memory,
                'running': running_memory,
                'final': final_memory,
                'peak': running_memory - initial_memory
            }
        
        def benchmark_throughput(self, requests=1000):
            """测试吞吐量"""
            app = Application("throughput-benchmark", "1.0.0")
            app.start()
            
            start_time = time.time()
            
            # 模拟处理请求
            for i in range(requests):
                # 模拟请求处理
                pass
            
            end_time = time.time()
            duration = end_time - start_time
            
            app.stop()
            
            self.results['throughput'] = {
                'requests': requests,
                'duration': duration,
                'requests_per_second': requests / duration
            }
        
        def run_all_benchmarks(self):
            """运行所有基准测试"""
            print("运行性能基准测试...")
            
            self.benchmark_startup_time()
            self.benchmark_memory_usage()
            self.benchmark_throughput()
            
            self.print_results()
        
        def print_results(self):
            """打印测试结果"""
            print("\n=== 性能基准测试结果 ===")
            
            if 'startup_time' in self.results:
                st = self.results['startup_time']
                print(f"启动时间: {st['mean']:.3f}秒 (平均)")
                print(f"启动时间: {st['min']:.3f}秒 (最小)")
                print(f"启动时间: {st['max']:.3f}秒 (最大)")
            
            if 'memory_usage' in self.results:
                mu = self.results['memory_usage']
                print(f"内存使用: {mu['peak']:.1f}MB (峰值)")
            
            if 'throughput' in self.results:
                tp = self.results['throughput']
                print(f"吞吐量: {tp['requests_per_second']:.1f} 请求/秒")

    if __name__ == "__main__":
        benchmark = PerformanceBenchmark()
        benchmark.run_all_benchmarks()

负载测试
~~~~~~~~

.. code-block:: python

    """
    负载测试示例
    """

    import asyncio
    import aiohttp
    import time
    from concurrent.futures import ThreadPoolExecutor

    class LoadTester:
        """负载测试器"""
        
        def __init__(self, target_url, concurrent_users=10, duration=60):
            self.target_url = target_url
            self.concurrent_users = concurrent_users
            self.duration = duration
            self.results = []
        
        async def single_user_test(self, user_id):
            """单个用户测试"""
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                request_count = 0
                error_count = 0
                
                while time.time() - start_time < self.duration:
                    try:
                        async with session.get(self.target_url) as response:
                            if response.status == 200:
                                request_count += 1
                            else:
                                error_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"用户 {user_id} 请求失败: {e}")
                    
                    # 短暂延迟
                    await asyncio.sleep(0.1)
                
                return {
                    'user_id': user_id,
                    'requests': request_count,
                    'errors': error_count,
                    'duration': time.time() - start_time
                }
        
        async def run_load_test(self):
            """运行负载测试"""
            print(f"开始负载测试: {self.concurrent_users} 并发用户, {self.duration} 秒")
            
            tasks = [
                self.single_user_test(i)
                for i in range(self.concurrent_users)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # 统计结果
            total_requests = sum(r['requests'] for r in results)
            total_errors = sum(r['errors'] for r in results)
            total_duration = max(r['duration'] for r in results)
            
            print(f"\n=== 负载测试结果 ===")
            print(f"总请求数: {total_requests}")
            print(f"总错误数: {total_errors}")
            print(f"成功率: {(total_requests - total_errors) / total_requests * 100:.1f}%")
            print(f"平均响应时间: {total_duration / total_requests:.3f}秒")
            print(f"吞吐量: {total_requests / total_duration:.1f} 请求/秒")

    # 使用示例
    async def main():
        tester = LoadTester("http://localhost:8000/api/test", concurrent_users=20, duration=30)
        await tester.run_load_test()

    if __name__ == "__main__":
        asyncio.run(main())

性能调优建议
------------

1. **定期监控**: 建立性能监控体系，定期检查关键指标
2. **渐进优化**: 先识别瓶颈，再针对性优化
3. **测试验证**: 每次优化后都要测试验证效果
4. **文档记录**: 记录优化过程和结果，便于后续维护

更多信息
--------

* :doc:`common_issues` - 常见问题故障排除
* :doc:`debugging` - 调试指南
* :doc:`../examples/advanced_usage` - 高级使用示例
