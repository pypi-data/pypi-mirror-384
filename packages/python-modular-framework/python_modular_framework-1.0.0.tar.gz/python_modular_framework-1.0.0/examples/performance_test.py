#!/usr/bin/env python3
"""
性能测试和优化示例

演示框架的性能优化功能，包括：
- 启动时间测试
- 内存使用监控
- 组件加载性能
- 中间件性能测试
- 插件性能测试
- 性能优化建议

作者：开发团队
创建时间：2024-01-XX
"""

import sys
import os
import time
import threading
import gc
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from framework.core.application import Application
from framework.core.middleware import MiddlewareManager, Request, Response
from framework.core.plugin import PluginManager


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.start_time = time.time()
        self.memory_samples = []
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self, interval: float = 0.1):
        """开始监控"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval,)
        )
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

    def _monitor_loop(self, interval: float):
        """监控循环"""
        while self.monitoring:
            try:
                # 使用gc模块获取内存使用情况
                gc.collect()  # 强制垃圾回收
                memory_mb = len(gc.get_objects()) / 1000  # 粗略估算
                self.memory_samples.append(memory_mb)
                time.sleep(interval)
            except Exception as e:
                print(f"监控错误: {e}")
                break

    def get_memory_stats(self) -> Dict[str, float]:
        """获取内存统计"""
        if not self.memory_samples:
            return {"current": 0, "min": 0, "max": 0, "avg": 0}

        return {
            "current": self.memory_samples[-1],
            "min": min(self.memory_samples),
            "max": max(self.memory_samples),
            "avg": sum(self.memory_samples) / len(self.memory_samples),
        }

    def get_current_memory(self) -> float:
        """获取当前内存使用"""
        try:
            gc.collect()
            return len(gc.get_objects()) / 1000  # 粗略估算
        except:
            return 0.0

    def get_uptime(self) -> float:
        """获取运行时间"""
        return time.time() - self.start_time


class PerformanceTest:
    """性能测试类"""

    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.results = {}

    def test_application_startup(self) -> Dict[str, Any]:
        """测试应用启动性能"""
        print("=== 测试应用启动性能 ===")

        # 开始监控
        self.monitor.start_monitoring()

        # 记录启动前状态
        start_memory = self.monitor.get_memory_stats()
        start_time = time.time()

        # 创建和启动应用
        app = Application(name="performance-test", version="1.0.0")
        config = {
            "app_name": "Performance Test Application",
            "debug": False,  # 关闭调试模式以提高性能
            "log_level": "WARNING",  # 减少日志输出
        }

        app.configure(config)
        app.start()

        # 记录启动后状态
        end_time = time.time()
        startup_time = end_time - start_time

        # 停止监控
        self.monitor.stop_monitoring()

        # 获取统计信息
        memory_stats = self.monitor.get_memory_stats()
        current_memory = self.monitor.get_current_memory()

        result = {
            "startup_time": startup_time,
            "memory_usage": memory_stats,
            "current_memory": current_memory,
            "components_loaded": len(app.list_components()),
        }

        print(f"启动时间: {startup_time:.3f}秒")
        print(
            f"内存使用: {memory_stats['current']:.1f}MB (峰值: {memory_stats['max']:.1f}MB)"
        )
        print(f"当前内存: {current_memory:.1f}MB")
        print(f"加载组件数: {result['components_loaded']}")

        # 停止应用
        app.stop()

        return result

    def test_middleware_performance(self) -> Dict[str, Any]:
        """测试中间件性能"""
        print("\n=== 测试中间件性能 ===")

        # 创建中间件管理器
        manager = MiddlewareManager()

        # 添加多个中间件
        from framework.core.middleware import (
            LoggingMiddleware,
            AuthMiddleware,
            CacheMiddleware,
        )

        for i in range(10):  # 添加10个中间件
            manager.register(LoggingMiddleware(f"logging_{i}"))
            manager.register(AuthMiddleware(f"auth_{i}", required=False))
            manager.register(CacheMiddleware(f"cache_{i}"))

        # 测试请求处理性能
        request = Request(method="GET", path="/api/test")

        # 预热
        for _ in range(10):
            manager.process_request(request)

        # 性能测试
        start_time = time.time()
        iterations = 1000

        for _ in range(iterations):
            manager.process_request(request)

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations

        result = {
            "total_time": total_time,
            "iterations": iterations,
            "avg_time_per_request": avg_time,
            "requests_per_second": iterations / total_time,
            "middleware_count": len(manager.list_middlewares()),
        }

        print(f"总时间: {total_time:.3f}秒")
        print(f"平均每请求时间: {avg_time*1000:.3f}毫秒")
        print(f"每秒请求数: {result['requests_per_second']:.0f}")
        print(f"中间件数量: {result['middleware_count']}")

        return result

    def test_plugin_performance(self) -> Dict[str, Any]:
        """测试插件性能"""
        print("\n=== 测试插件性能 ===")

        # 创建插件管理器
        manager = PluginManager(plugin_dirs=["example_plugins"])

        # 发现插件
        start_time = time.time()
        discovered = manager.discover_plugins()
        discovery_time = time.time() - start_time

        print(f"插件发现时间: {discovery_time:.3f}秒")
        print(f"发现插件数: {len(discovered)}")

        # 测试插件加载性能
        load_times = {}
        for name in discovered.keys():
            start_time = time.time()
            success = manager.load_plugin(name, f"example_plugins/{name}_plugin.py")
            load_time = time.time() - start_time

            if success:
                load_times[name] = load_time
                print(f"插件 {name} 加载时间: {load_time:.3f}秒")

        # 测试插件初始化性能
        init_times = {}
        for name in load_times.keys():
            start_time = time.time()
            success = manager.initialize_plugin(name, {"enabled": True})
            init_time = time.time() - start_time

            if success:
                init_times[name] = init_time
                print(f"插件 {name} 初始化时间: {init_time:.3f}秒")

        result = {
            "discovery_time": discovery_time,
            "discovered_count": len(discovered),
            "load_times": load_times,
            "init_times": init_times,
            "total_load_time": sum(load_times.values()),
            "total_init_time": sum(init_times.values()),
        }

        # 清理
        for name in load_times.keys():
            manager.stop_plugin(name)
            manager.unload_plugin(name)

        return result

    def test_memory_usage(self) -> Dict[str, Any]:
        """测试内存使用"""
        print("\n=== 测试内存使用 ===")

        # 记录初始内存
        initial_memory = self.monitor.get_memory_stats()

        # 创建多个应用实例
        apps = []
        for i in range(5):
            app = Application(name=f"memory-test-{i}", version="1.0.0")
            app.configure({"debug": False, "log_level": "ERROR"})
            app.start()
            apps.append(app)

        # 记录内存使用
        apps_memory = self.monitor.get_memory_stats()

        # 停止所有应用
        for app in apps:
            app.stop()

        # 记录清理后内存
        final_memory = self.monitor.get_memory_stats()

        result = {
            "initial_memory": initial_memory,
            "apps_memory": apps_memory,
            "final_memory": final_memory,
            "memory_per_app": (apps_memory["current"] - initial_memory["current"]) / 5,
            "memory_leak": final_memory["current"] - initial_memory["current"],
        }

        print(f"初始内存: {initial_memory['current']:.1f}MB")
        print(f"5个应用内存: {apps_memory['current']:.1f}MB")
        print(f"清理后内存: {final_memory['current']:.1f}MB")
        print(f"每个应用内存: {result['memory_per_app']:.1f}MB")
        print(f"内存泄漏: {result['memory_leak']:.1f}MB")

        return result

    def generate_optimization_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 基于测试结果生成建议
        if "startup_time" in self.results:
            startup_time = self.results["startup_time"]
            if startup_time > 2.0:
                recommendations.append("启动时间过长，建议：")
                recommendations.append("  - 减少不必要的组件加载")
                recommendations.append("  - 使用延迟加载策略")
                recommendations.append("  - 优化组件初始化顺序")

        if "middleware_performance" in self.results:
            middleware_perf = self.results["middleware_performance"]
            if middleware_perf["avg_time_per_request"] > 0.01:
                recommendations.append("中间件性能需要优化：")
                recommendations.append("  - 减少中间件数量")
                recommendations.append("  - 优化中间件逻辑")
                recommendations.append("  - 使用缓存减少重复计算")

        if "memory_usage" in self.results:
            memory_usage = self.results["memory_usage"]
            if memory_usage["memory_per_app"] > 50:
                recommendations.append("内存使用过高，建议：")
                recommendations.append("  - 优化数据结构")
                recommendations.append("  - 及时释放不需要的资源")
                recommendations.append("  - 使用对象池减少内存分配")

        if "plugin_performance" in self.results:
            plugin_perf = self.results["plugin_performance"]
            if plugin_perf["discovery_time"] > 0.5:
                recommendations.append("插件发现时间过长，建议：")
                recommendations.append("  - 缓存插件信息")
                recommendations.append("  - 优化插件扫描算法")
                recommendations.append("  - 使用索引文件加速发现")

        return recommendations

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有性能测试"""
        print("=== Python模块化框架 - 性能测试 ===\n")

        try:
            # 测试应用启动性能
            self.results["startup_performance"] = self.test_application_startup()

            # 测试中间件性能
            self.results["middleware_performance"] = self.test_middleware_performance()

            # 测试插件性能
            self.results["plugin_performance"] = self.test_plugin_performance()

            # 测试内存使用
            self.results["memory_usage"] = self.test_memory_usage()

            # 生成优化建议
            recommendations = self.generate_optimization_recommendations()

            # 显示结果摘要
            print("\n=== 性能测试结果摘要 ===")
            for test_name, result in self.results.items():
                print(f"\n{test_name}:")
                for key, value in result.items():
                    if isinstance(value, (int, float)):
                        print(f"  {key}: {value}")
                    elif isinstance(value, dict):
                        print(f"  {key}: {value}")

            # 显示优化建议
            if recommendations:
                print("\n=== 性能优化建议 ===")
                for rec in recommendations:
                    print(rec)
            else:
                print("\n✅ 性能表现良好，无需特别优化")

            print("\n=== 性能测试完成 ===")
            return self.results

        except Exception as e:
            print(f"\n❌ 性能测试过程中发生错误: {e}")
            import traceback

            traceback.print_exc()
            return {}


def main():
    """主函数"""
    test = PerformanceTest()
    results = test.run_all_tests()
    return 0


if __name__ == "__main__":
    exit(main())
