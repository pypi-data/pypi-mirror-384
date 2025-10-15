"""
测试覆盖率配置

提供测试覆盖率相关的配置和工具函数。

功能：
- 覆盖率报告配置
- 覆盖率分析工具
- 覆盖率报告生成

作者：开发团队
创建时间：2025-01-12
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any


class CoverageConfig:
    """测试覆盖率配置类"""
    
    def __init__(self):
        """初始化覆盖率配置"""
        self.project_root = Path(__file__).parent.parent
        self.source_dirs = ["framework", "components"]
        self.test_dirs = ["tests"]
        self.coverage_dir = self.project_root / "htmlcov"
        self.coverage_xml = self.project_root / "coverage.xml"
        self.coverage_data = self.project_root / ".coverage"
        
        # 覆盖率阈值
        self.fail_under = 80
        
        # 排除的文件和目录
        self.omit_patterns = [
            "*/tests/*",
            "*/test_*",
            "*/__pycache__/*",
            "*/migrations/*",
            "*/venv/*",
            "*/env/*",
            "*/build/*",
            "*/dist/*",
            "*/.*",
        ]
        
        # 排除的行模式
        self.exclude_lines = [
            "pragma: no cover",
            "def __repr__",
            "if self.debug:",
            "if settings.DEBUG",
            "raise AssertionError",
            "raise NotImplementedError",
            "if 0:",
            "if __name__ == .__main__.:",
            "class .*\\bProtocol\\):",
            "@(abc\\.)?abstractmethod",
        ]
    
    def get_coverage_command(self, test_path: str = None) -> List[str]:
        """
        获取覆盖率测试命令
        
        Args:
            test_path (str): 测试路径，如果为None则运行所有测试
            
        Returns:
            List[str]: 覆盖率测试命令
        """
        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=framework",
            "--cov=components",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            f"--cov-fail-under={self.fail_under}",
            "--cov-branch",
            "-v"
        ]
        
        if test_path:
            cmd.append(test_path)
        else:
            cmd.extend(self.test_dirs)
        
        return cmd
    
    def run_coverage(self, test_path: str = None) -> subprocess.CompletedProcess:
        """
        运行覆盖率测试
        
        Args:
            test_path (str): 测试路径
            
        Returns:
            subprocess.CompletedProcess: 测试结果
        """
        cmd = self.get_coverage_command(test_path)
        
        print(f"运行覆盖率测试: {' '.join(cmd)}")
        
        return subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
    
    def generate_coverage_report(self) -> Dict[str, Any]:
        """
        生成覆盖率报告
        
        Returns:
            Dict[str, Any]: 覆盖率报告信息
        """
        try:
            # 运行覆盖率测试
            result = self.run_coverage()
            
            # 解析覆盖率结果
            coverage_info = self._parse_coverage_output(result.stdout)
            
            # 生成HTML报告
            if self.coverage_dir.exists():
                print(f"HTML覆盖率报告已生成: {self.coverage_dir}")
            
            # 生成XML报告
            if self.coverage_xml.exists():
                print(f"XML覆盖率报告已生成: {self.coverage_xml}")
            
            return {
                "success": result.returncode == 0,
                "coverage_info": coverage_info,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "html_report": str(self.coverage_dir) if self.coverage_dir.exists() else None,
                "xml_report": str(self.coverage_xml) if self.coverage_xml.exists() else None,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "coverage_info": None,
            }
    
    def _parse_coverage_output(self, output: str) -> Dict[str, Any]:
        """
        解析覆盖率输出
        
        Args:
            output (str): 覆盖率输出文本
            
        Returns:
            Dict[str, Any]: 解析后的覆盖率信息
        """
        lines = output.split('\n')
        coverage_info = {
            "total_coverage": None,
            "file_coverage": {},
            "missing_lines": {},
        }
        
        for line in lines:
            line = line.strip()
            
            # 解析总覆盖率
            if "TOTAL" in line and "%" in line:
                try:
                    # 提取百分比
                    parts = line.split()
                    for part in parts:
                        if part.endswith('%'):
                            coverage_info["total_coverage"] = float(part[:-1])
                            break
                except (ValueError, IndexError):
                    pass
            
            # 解析文件覆盖率
            elif line and not line.startswith('-') and not line.startswith('='):
                parts = line.split()
                if len(parts) >= 4 and parts[0].endswith('.py'):
                    try:
                        filename = parts[0]
                        coverage = float(parts[-1].rstrip('%'))
                        coverage_info["file_coverage"][filename] = coverage
                    except (ValueError, IndexError):
                        pass
        
        return coverage_info
    
    def get_coverage_summary(self) -> str:
        """
        获取覆盖率摘要
        
        Returns:
            str: 覆盖率摘要文本
        """
        if not self.coverage_data.exists():
            return "未找到覆盖率数据文件"
        
        try:
            # 使用coverage命令获取摘要
            result = subprocess.run(
                [sys.executable, "-m", "coverage", "report"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"获取覆盖率摘要失败: {result.stderr}"
                
        except Exception as e:
            return f"获取覆盖率摘要时出错: {e}"
    
    def clean_coverage_data(self):
        """清理覆盖率数据"""
        files_to_clean = [
            self.coverage_data,
            self.coverage_xml,
        ]
        
        for file_path in files_to_clean:
            if file_path.exists():
                file_path.unlink()
                print(f"已删除: {file_path}")
        
        if self.coverage_dir.exists():
            import shutil
            shutil.rmtree(self.coverage_dir)
            print(f"已删除目录: {self.coverage_dir}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="测试覆盖率工具")
    parser.add_argument("--test-path", help="指定测试路径")
    parser.add_argument("--clean", action="store_true", help="清理覆盖率数据")
    parser.add_argument("--summary", action="store_true", help="显示覆盖率摘要")
    parser.add_argument("--report", action="store_true", help="生成覆盖率报告")
    
    args = parser.parse_args()
    
    config = CoverageConfig()
    
    if args.clean:
        config.clean_coverage_data()
        return
    
    if args.summary:
        summary = config.get_coverage_summary()
        print(summary)
        return
    
    if args.report:
        result = config.generate_coverage_report()
        if result["success"]:
            print("覆盖率报告生成成功")
            if result["coverage_info"] and result["coverage_info"]["total_coverage"]:
                print(f"总覆盖率: {result['coverage_info']['total_coverage']:.1f}%")
        else:
            print(f"覆盖率报告生成失败: {result.get('error', '未知错误')}")
        return
    
    # 默认运行覆盖率测试
    result = config.run_coverage(args.test_path)
    print(result.stdout)
    if result.stderr:
        print("错误输出:")
        print(result.stderr)
    
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

