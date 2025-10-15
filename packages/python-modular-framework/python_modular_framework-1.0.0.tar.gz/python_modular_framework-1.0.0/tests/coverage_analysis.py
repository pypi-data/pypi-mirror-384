"""
测试覆盖率分析工具

分析测试覆盖率数据，提供详细的覆盖率报告和分析。

功能：
- 覆盖率数据分析
- 未覆盖代码识别
- 覆盖率趋势分析
- 覆盖率报告生成

作者：开发团队
创建时间：2025-01-12
"""

import os
import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class FileCoverage:
    """文件覆盖率信息"""
    filename: str
    total_lines: int
    covered_lines: int
    missing_lines: List[int]
    coverage_percentage: float
    branches_total: int = 0
    branches_covered: int = 0
    branch_coverage: float = 0.0


@dataclass
class CoverageSummary:
    """覆盖率摘要"""
    total_files: int
    total_lines: int
    covered_lines: int
    overall_coverage: float
    file_coverage: List[FileCoverage]
    low_coverage_files: List[FileCoverage]
    uncovered_files: List[str]


class CoverageAnalyzer:
    """覆盖率分析器"""
    
    def __init__(self, project_root: Path = None):
        """
        初始化覆盖率分析器
        
        Args:
            project_root (Path): 项目根目录
        """
        self.project_root = project_root or Path(__file__).parent.parent
        self.coverage_xml = self.project_root / "coverage.xml"
        self.coverage_data = self.project_root / ".coverage"
        self.htmlcov_dir = self.project_root / "htmlcov"
        
        # 覆盖率阈值
        self.low_coverage_threshold = 70.0
        self.target_coverage = 80.0
    
    def analyze_coverage(self) -> CoverageSummary:
        """
        分析覆盖率数据
        
        Returns:
            CoverageSummary: 覆盖率摘要
        """
        if not self.coverage_xml.exists():
            raise FileNotFoundError(f"覆盖率XML文件不存在: {self.coverage_xml}")
        
        # 解析XML覆盖率数据
        tree = ET.parse(self.coverage_xml)
        root = tree.getroot()
        
        file_coverage = []
        total_lines = 0
        covered_lines = 0
        
        # 解析每个文件的覆盖率
        for package in root.findall('.//package'):
            for class_elem in package.findall('.//class'):
                filename = class_elem.get('filename')
                if not filename:
                    continue
                
                # 获取行覆盖率信息
                lines = class_elem.findall('.//line')
                if not lines:
                    continue
                
                file_total = len(lines)
                file_covered = sum(1 for line in lines if int(line.get('hits', 0)) > 0)
                file_missing = [int(line.get('number')) for line in lines if int(line.get('hits', 0)) == 0]
                
                # 计算分支覆盖率
                branches_total = 0
                branches_covered = 0
                for line in lines:
                    branch_elem = line.find('.//branch')
                    if branch_elem is not None:
                        branches_total += 1
                        if int(branch_elem.get('hits', 0)) > 0:
                            branches_covered += 1
                
                coverage_percentage = (file_covered / file_total * 100) if file_total > 0 else 0.0
                branch_coverage = (branches_covered / branches_total * 100) if branches_total > 0 else 0.0
                
                file_cov = FileCoverage(
                    filename=filename,
                    total_lines=file_total,
                    covered_lines=file_covered,
                    missing_lines=file_missing,
                    coverage_percentage=coverage_percentage,
                    branches_total=branches_total,
                    branches_covered=branches_covered,
                    branch_coverage=branch_coverage
                )
                
                file_coverage.append(file_cov)
                total_lines += file_total
                covered_lines += file_covered
        
        # 计算总体覆盖率
        overall_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
        
        # 识别低覆盖率文件
        low_coverage_files = [
            f for f in file_coverage 
            if f.coverage_percentage < self.low_coverage_threshold
        ]
        
        # 识别未覆盖文件
        uncovered_files = [
            f.filename for f in file_coverage 
            if f.coverage_percentage == 0.0
        ]
        
        return CoverageSummary(
            total_files=len(file_coverage),
            total_lines=total_lines,
            covered_lines=covered_lines,
            overall_coverage=overall_coverage,
            file_coverage=file_coverage,
            low_coverage_files=low_coverage_files,
            uncovered_files=uncovered_files
        )
    
    def generate_detailed_report(self, summary: CoverageSummary) -> str:
        """
        生成详细的覆盖率报告
        
        Args:
            summary (CoverageSummary): 覆盖率摘要
            
        Returns:
            str: 详细报告文本
        """
        report = []
        report.append("=" * 80)
        report.append("测试覆盖率详细报告")
        report.append("=" * 80)
        report.append("")
        
        # 总体统计
        report.append("总体统计:")
        report.append(f"  总文件数: {summary.total_files}")
        report.append(f"  总行数: {summary.total_lines}")
        report.append(f"  已覆盖行数: {summary.covered_lines}")
        report.append(f"  总体覆盖率: {summary.overall_coverage:.2f}%")
        report.append(f"  目标覆盖率: {self.target_coverage}%")
        
        if summary.overall_coverage >= self.target_coverage:
            report.append("  ✅ 已达到目标覆盖率")
        else:
            report.append(f"  ❌ 未达到目标覆盖率 (差 {self.target_coverage - summary.overall_coverage:.2f}%)")
        
        report.append("")
        
        # 低覆盖率文件
        if summary.low_coverage_files:
            report.append(f"低覆盖率文件 (< {self.low_coverage_threshold}%):")
            for file_cov in sorted(summary.low_coverage_files, key=lambda x: x.coverage_percentage):
                report.append(f"  {file_cov.filename}: {file_cov.coverage_percentage:.1f}%")
            report.append("")
        
        # 未覆盖文件
        if summary.uncovered_files:
            report.append("未覆盖文件:")
            for filename in sorted(summary.uncovered_files):
                report.append(f"  {filename}")
            report.append("")
        
        # 覆盖率排名
        report.append("覆盖率排名 (前10名):")
        top_files = sorted(summary.file_coverage, key=lambda x: x.coverage_percentage, reverse=True)[:10]
        for i, file_cov in enumerate(top_files, 1):
            report.append(f"  {i:2d}. {file_cov.filename}: {file_cov.coverage_percentage:.1f}%")
        report.append("")
        
        # 覆盖率排名 (后10名)
        report.append("覆盖率排名 (后10名):")
        bottom_files = sorted(summary.file_coverage, key=lambda x: x.coverage_percentage)[:10]
        for i, file_cov in enumerate(bottom_files, 1):
            report.append(f"  {i:2d}. {file_cov.filename}: {file_cov.coverage_percentage:.1f}%")
        report.append("")
        
        return "\n".join(report)
    
    def generate_missing_lines_report(self, summary: CoverageSummary) -> str:
        """
        生成未覆盖行报告
        
        Args:
            summary (CoverageSummary): 覆盖率摘要
            
        Returns:
            str: 未覆盖行报告
        """
        report = []
        report.append("=" * 80)
        report.append("未覆盖代码行报告")
        report.append("=" * 80)
        report.append("")
        
        for file_cov in summary.file_coverage:
            if file_cov.missing_lines:
                report.append(f"文件: {file_cov.filename}")
                report.append(f"覆盖率: {file_cov.coverage_percentage:.1f}%")
                report.append(f"未覆盖行数: {len(file_cov.missing_lines)}")
                report.append("未覆盖行:")
                
                # 按行号排序
                missing_lines = sorted(file_cov.missing_lines)
                
                # 显示前20行未覆盖的代码
                for line_num in missing_lines[:20]:
                    try:
                        file_path = self.project_root / file_cov.filename
                        if file_path.exists():
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                if line_num <= len(lines):
                                    line_content = lines[line_num - 1].strip()
                                    report.append(f"  {line_num:4d}: {line_content}")
                    except Exception:
                        report.append(f"  {line_num:4d}: [无法读取行内容]")
                
                if len(missing_lines) > 20:
                    report.append(f"  ... 还有 {len(missing_lines) - 20} 行未覆盖")
                
                report.append("")
        
        return "\n".join(report)
    
    def save_reports(self, summary: CoverageSummary, output_dir: Path = None):
        """
        保存覆盖率报告到文件
        
        Args:
            summary (CoverageSummary): 覆盖率摘要
            output_dir (Path): 输出目录
        """
        if output_dir is None:
            output_dir = self.project_root / "coverage_reports"
        
        output_dir.mkdir(exist_ok=True)
        
        # 保存详细报告
        detailed_report = self.generate_detailed_report(summary)
        with open(output_dir / "coverage_detailed.txt", 'w', encoding='utf-8') as f:
            f.write(detailed_report)
        
        # 保存未覆盖行报告
        missing_lines_report = self.generate_missing_lines_report(summary)
        with open(output_dir / "missing_lines.txt", 'w', encoding='utf-8') as f:
            f.write(missing_lines_report)
        
        # 保存JSON格式的摘要
        summary_data = {
            "overall_coverage": summary.overall_coverage,
            "total_files": summary.total_files,
            "total_lines": summary.total_lines,
            "covered_lines": summary.covered_lines,
            "target_coverage": self.target_coverage,
            "low_coverage_files": [
                {
                    "filename": f.filename,
                    "coverage_percentage": f.coverage_percentage,
                    "missing_lines_count": len(f.missing_lines)
                }
                for f in summary.low_coverage_files
            ],
            "uncovered_files": summary.uncovered_files
        }
        
        with open(output_dir / "coverage_summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"覆盖率报告已保存到: {output_dir}")
    
    def print_summary(self, summary: CoverageSummary):
        """
        打印覆盖率摘要
        
        Args:
            summary (CoverageSummary): 覆盖率摘要
        """
        print("=" * 60)
        print("测试覆盖率摘要")
        print("=" * 60)
        print(f"总体覆盖率: {summary.overall_coverage:.2f}%")
        print(f"目标覆盖率: {self.target_coverage}%")
        print(f"总文件数: {summary.total_files}")
        print(f"总行数: {summary.total_lines}")
        print(f"已覆盖行数: {summary.covered_lines}")
        
        if summary.overall_coverage >= self.target_coverage:
            print("✅ 已达到目标覆盖率")
        else:
            print(f"❌ 未达到目标覆盖率 (差 {self.target_coverage - summary.overall_coverage:.2f}%)")
        
        if summary.low_coverage_files:
            print(f"\n低覆盖率文件 (< {self.low_coverage_threshold}%): {len(summary.low_coverage_files)}")
        
        if summary.uncovered_files:
            print(f"未覆盖文件: {len(summary.uncovered_files)}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="测试覆盖率分析工具")
    parser.add_argument("--detailed", action="store_true", help="显示详细报告")
    parser.add_argument("--missing-lines", action="store_true", help="显示未覆盖行报告")
    parser.add_argument("--save", action="store_true", help="保存报告到文件")
    parser.add_argument("--output-dir", help="输出目录")
    
    args = parser.parse_args()
    
    analyzer = CoverageAnalyzer()
    
    try:
        # 分析覆盖率
        summary = analyzer.analyze_coverage()
        
        # 打印摘要
        analyzer.print_summary(summary)
        
        # 显示详细报告
        if args.detailed:
            print("\n" + analyzer.generate_detailed_report(summary))
        
        # 显示未覆盖行报告
        if args.missing_lines:
            print("\n" + analyzer.generate_missing_lines_report(summary))
        
        # 保存报告
        if args.save:
            output_dir = Path(args.output_dir) if args.output_dir else None
            analyzer.save_reports(summary, output_dir)
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请先运行测试生成覆盖率数据")
        sys.exit(1)
    except Exception as e:
        print(f"分析覆盖率时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

