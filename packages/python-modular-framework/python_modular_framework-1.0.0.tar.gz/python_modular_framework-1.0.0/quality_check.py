#!/usr/bin/env python3
"""
代码质量检查脚本

该脚本用于运行各种代码质量检查工具，包括：
- Black: 代码格式化检查
- Flake8: 代码风格检查
- MyPy: 类型检查
- Bandit: 安全漏洞检查
- Safety: 依赖安全检查
- Pytest: 单元测试和覆盖率检查

使用方法:
    python quality_check.py [选项]

选项:
    --format         运行代码格式化检查
    --lint           运行代码风格检查
    --type           运行类型检查
    --security       运行安全检查
    --test           运行测试和覆盖率检查
    --all            运行所有检查
    --fix            自动修复可修复的问题
    --help           显示帮助信息
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any


class QualityChecker:
    """代码质量检查器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {}

    def run_command(self, command: str, cwd: Path = None) -> Tuple[bool, str, str]:
        """运行命令并返回结果"""
        try:
            # 安全地解析命令，避免shell注入
            import shlex
            cmd_args = shlex.split(command)
            
            result = subprocess.run(
                cmd_args,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def check_black(self, fix: bool = False) -> Dict[str, Any]:
        """运行Black代码格式化检查"""
        print("🔍 运行Black代码格式化检查...")

        if fix:
            command = "black ."
            success, stdout, stderr = self.run_command(command)
            if success:
                print("✅ 代码格式化完成")
                return {
                    "status": "success",
                    "message": "代码格式化完成",
                    "output": stdout,
                }
            else:
                print(f"❌ 代码格式化失败: {stderr}")
                return {"status": "error", "message": "代码格式化失败", "error": stderr}
        else:
            command = "black --check --diff ."
            success, stdout, stderr = self.run_command(command)
            if success:
                print("✅ 代码格式检查通过")
                return {"status": "success", "message": "代码格式检查通过"}
            else:
                print("⚠️ 代码格式需要调整")
                return {
                    "status": "warning",
                    "message": "代码格式需要调整",
                    "diff": stdout,
                }

    def check_flake8(self) -> Dict[str, Any]:
        """运行Flake8代码风格检查"""
        print("🔍 运行Flake8代码风格检查...")

        command = "flake8 ."
        success, stdout, stderr = self.run_command(command)

        if success:
            print("✅ 代码风格检查通过")
            return {"status": "success", "message": "代码风格检查通过"}
        else:
            print("⚠️ 发现代码风格问题")
            issues = stdout.strip().split("\n") if stdout.strip() else []
            return {
                "status": "warning",
                "message": f"发现 {len(issues)} 个代码风格问题",
                "issues": issues,
            }

    def check_mypy(self) -> Dict[str, Any]:
        """运行MyPy类型检查"""
        print("🔍 运行MyPy类型检查...")

        command = "mypy ."
        success, stdout, stderr = self.run_command(command)

        if success:
            print("✅ 类型检查通过")
            return {"status": "success", "message": "类型检查通过"}
        else:
            print("⚠️ 发现类型问题")
            issues = stdout.strip().split("\n") if stdout.strip() else []
            return {
                "status": "warning",
                "message": f"发现 {len(issues)} 个类型问题",
                "issues": issues,
            }

    def check_bandit(self) -> Dict[str, Any]:
        """运行Bandit安全漏洞检查"""
        print("🔍 运行Bandit安全漏洞检查...")

        command = "bandit -r . -f json"
        success, stdout, stderr = self.run_command(command)

        try:
            result = json.loads(stdout) if stdout else {}
            high_severity = len(
                [
                    r
                    for r in result.get("results", [])
                    if r.get("issue_severity") == "HIGH"
                ]
            )
            medium_severity = len(
                [
                    r
                    for r in result.get("results", [])
                    if r.get("issue_severity") == "MEDIUM"
                ]
            )
            low_severity = len(
                [
                    r
                    for r in result.get("results", [])
                    if r.get("issue_severity") == "LOW"
                ]
            )

            if high_severity > 0:
                print(f"❌ 发现 {high_severity} 个高危安全问题")
                return {
                    "status": "error",
                    "message": f"发现 {high_severity} 个高危安全问题",
                    "high": high_severity,
                    "medium": medium_severity,
                    "low": low_severity,
                    "results": result.get("results", []),
                }
            elif medium_severity > 0:
                print(f"⚠️ 发现 {medium_severity} 个中危安全问题")
                return {
                    "status": "warning",
                    "message": f"发现 {medium_severity} 个中危安全问题",
                    "high": high_severity,
                    "medium": medium_severity,
                    "low": low_severity,
                }
            else:
                print("✅ 安全检查通过")
                return {
                    "status": "success",
                    "message": "安全检查通过",
                    "high": high_severity,
                    "medium": medium_severity,
                    "low": low_severity,
                }
        except json.JSONDecodeError:
            print("❌ 安全检查结果解析失败")
            return {
                "status": "error",
                "message": "安全检查结果解析失败",
                "output": stdout,
            }

    def check_safety(self) -> Dict[str, Any]:
        """运行Safety依赖安全检查"""
        print("🔍 运行Safety依赖安全检查...")

        command = "safety check --json"
        success, stdout, stderr = self.run_command(command)

        try:
            result = json.loads(stdout) if stdout else []
            if result:
                print(f"❌ 发现 {len(result)} 个依赖安全问题")
                return {
                    "status": "error",
                    "message": f"发现 {len(result)} 个依赖安全问题",
                    "vulnerabilities": result,
                }
            else:
                print("✅ 依赖安全检查通过")
                return {"status": "success", "message": "依赖安全检查通过"}
        except json.JSONDecodeError:
            if success:
                print("✅ 依赖安全检查通过")
                return {"status": "success", "message": "依赖安全检查通过"}
            else:
                print("❌ 依赖安全检查失败")
                return {
                    "status": "error",
                    "message": "依赖安全检查失败",
                    "error": stderr,
                }

    def check_tests(self) -> Dict[str, Any]:
        """运行测试和覆盖率检查"""
        print("🔍 运行测试和覆盖率检查...")

        command = "pytest --cov=framework --cov=components --cov-report=term-missing --cov-report=json"
        success, stdout, stderr = self.run_command(command)

        # 解析覆盖率报告
        coverage_file = self.project_root / "coverage.json"
        coverage_data = {}
        if coverage_file.exists():
            try:
                with open(coverage_file, "r") as f:
                    coverage_data = json.load(f)
            except json.JSONDecodeError:
                pass

        if success:
            print("✅ 测试通过")
            coverage_percent = coverage_data.get("totals", {}).get("percent_covered", 0)
            print(f"📊 代码覆盖率: {coverage_percent:.1f}%")
            return {
                "status": "success",
                "message": "测试通过",
                "coverage": coverage_percent,
                "output": stdout,
            }
        else:
            print("❌ 测试失败")
            return {
                "status": "error",
                "message": "测试失败",
                "error": stderr,
                "output": stdout,
            }

    def run_all_checks(self, fix: bool = False) -> Dict[str, Any]:
        """运行所有检查"""
        print("🚀 开始运行所有代码质量检查...")
        print("=" * 60)

        results = {}

        # 代码格式化
        results["black"] = self.check_black(fix)
        print()

        # 代码风格
        results["flake8"] = self.check_flake8()
        print()

        # 类型检查
        results["mypy"] = self.check_mypy()
        print()

        # 安全检查
        results["bandit"] = self.check_bandit()
        print()

        # 依赖安全
        results["safety"] = self.check_safety()
        print()

        # 测试和覆盖率
        results["tests"] = self.check_tests()
        print()

        # 生成总结报告
        self.generate_summary(results)

        return results

    def generate_summary(self, results: Dict[str, Any]) -> None:
        """生成检查总结报告"""
        print("=" * 60)
        print("📋 代码质量检查总结")
        print("=" * 60)

        total_checks = len(results)
        passed_checks = sum(1 for r in results.values() if r["status"] == "success")
        warning_checks = sum(1 for r in results.values() if r["status"] == "warning")
        error_checks = sum(1 for r in results.values() if r["status"] == "error")

        print(f"总检查项: {total_checks}")
        print(f"✅ 通过: {passed_checks}")
        print(f"⚠️ 警告: {warning_checks}")
        print(f"❌ 错误: {error_checks}")
        print()

        # 详细结果
        for check_name, result in results.items():
            status_icon = {"success": "✅", "warning": "⚠️", "error": "❌"}.get(
                result["status"], "❓"
            )

            print(f"{status_icon} {check_name.upper()}: {result['message']}")

        print()

        # 总体评估
        if error_checks == 0 and warning_checks == 0:
            print("🎉 所有检查都通过了！代码质量优秀！")
        elif error_checks == 0:
            print("👍 代码质量良好，有一些警告需要关注")
        else:
            print("⚠️ 发现了一些问题，需要修复后再提交")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Python模块化框架代码质量检查工具")
    parser.add_argument(
        "--format", "-f", action="store_true", help="运行代码格式化检查"
    )
    parser.add_argument("--lint", "-l", action="store_true", help="运行代码风格检查")
    parser.add_argument("--type", "-t", action="store_true", help="运行类型检查")
    parser.add_argument("--security", "-s", action="store_true", help="运行安全检查")
    parser.add_argument(
        "--test", "-T", action="store_true", help="运行测试和覆盖率检查"
    )
    parser.add_argument("--all", "-a", action="store_true", help="运行所有检查")
    parser.add_argument("--fix", action="store_true", help="自动修复可修复的问题")

    args = parser.parse_args()

    # 获取项目根目录
    project_root = Path(__file__).parent

    # 创建质量检查器
    checker = QualityChecker(project_root)

    print("🐍 Python模块化框架 - 代码质量检查工具")
    print("=" * 60)

    # 运行指定的检查
    if args.all:
        results = checker.run_all_checks(args.fix)
    else:
        results = {}

        if args.format:
            results["black"] = checker.check_black(args.fix)

        if args.lint:
            results["flake8"] = checker.check_flake8()

        if args.type:
            results["mypy"] = checker.check_mypy()

        if args.security:
            results["bandit"] = checker.check_bandit()
            results["safety"] = checker.check_safety()

        if args.test:
            results["tests"] = checker.check_tests()

        if not any([args.format, args.lint, args.type, args.security, args.test]):
            print("请指定要运行的检查类型，或使用 --all 运行所有检查")
            print("使用 --help 查看帮助信息")
            return 1

    # 检查是否有错误
    has_errors = any(r["status"] == "error" for r in results.values())
    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
