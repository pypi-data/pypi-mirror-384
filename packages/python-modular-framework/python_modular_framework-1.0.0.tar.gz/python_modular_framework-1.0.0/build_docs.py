#!/usr/bin/env python3
"""
文档构建脚本

该脚本用于构建Python模块化框架的文档。
支持多种输出格式：HTML、PDF、LaTeX等。

使用方法:
    python build_docs.py [选项]

选项:
    --format FORMAT    输出格式 (html, pdf, latex, epub)
    --clean           清理构建目录
    --serve           构建后启动本地服务器
    --help            显示帮助信息
"""

import os
import sys
import argparse
import subprocess
import webbrowser
from pathlib import Path


def run_command(command, cwd=None):
    """运行命令并返回结果"""
    try:
        # 安全地解析命令，避免shell注入
        if isinstance(command, str):
            # 对于简单命令，使用shlex.split安全解析
            import shlex
            cmd_args = shlex.split(command)
        else:
            cmd_args = command
            
        result = subprocess.run(
            cmd_args, cwd=cwd, capture_output=True, text=True, check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except Exception as e:
        return False, str(e)


def clean_build_dir(docs_dir):
    """清理构建目录"""
    build_dir = docs_dir / "_build"
    if build_dir.exists():
        import shutil

        shutil.rmtree(build_dir)
        print("✅ 构建目录已清理")


def build_docs(docs_dir, format_type="html"):
    """构建文档"""
    print(f"📚 开始构建 {format_type.upper()} 格式文档...")

    # 检查Sphinx是否安装
    success, output = run_command("sphinx-build --version")
    if not success:
        print("❌ Sphinx未安装，请先安装: pip install sphinx sphinx-rtd-theme")
        return False

    # 构建文档
    build_cmd = f"sphinx-build -b {format_type} . _build/{format_type}"
    success, output = run_command(build_cmd, cwd=docs_dir)

    if success:
        print(f"✅ {format_type.upper()} 文档构建成功")
        print(f"📁 输出目录: {docs_dir / '_build' / format_type}")
        return True
    else:
        print(f"❌ 文档构建失败: {output}")
        return False


def serve_docs(docs_dir, port=8000):
    """启动文档服务器"""
    build_dir = docs_dir / "_build" / "html"
    if not build_dir.exists():
        print("❌ HTML文档不存在，请先构建文档")
        return False

    print(f"🚀 启动文档服务器: http://localhost:{port}")

    try:
        # 启动HTTP服务器
        import http.server
        import socketserver
        import threading

        os.chdir(build_dir)
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"📖 文档服务器已启动: http://localhost:{port}")
            print("按 Ctrl+C 停止服务器")

            # 自动打开浏览器
            threading.Timer(
                1.0, lambda: webbrowser.open(f"http://localhost:{port}")
            ).start()

            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")
        return False

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Python模块化框架文档构建工具")
    parser.add_argument(
        "--format",
        "-f",
        choices=["html", "pdf", "latex", "epub"],
        default="html",
        help="输出格式 (默认: html)",
    )
    parser.add_argument("--clean", "-c", action="store_true", help="清理构建目录")
    parser.add_argument(
        "--serve", "-s", action="store_true", help="构建后启动本地服务器"
    )
    parser.add_argument(
        "--port", "-p", type=int, default=8000, help="服务器端口 (默认: 8000)"
    )

    args = parser.parse_args()

    # 获取项目根目录
    project_root = Path(__file__).parent
    docs_dir = project_root / "docs"

    if not docs_dir.exists():
        print("❌ docs目录不存在")
        return 1

    print("🐍 Python模块化框架 - 文档构建工具")
    print("=" * 50)

    # 清理构建目录
    if args.clean:
        clean_build_dir(docs_dir)

    # 构建文档
    if not build_docs(docs_dir, args.format):
        return 1

    # 启动服务器
    if args.serve and args.format == "html":
        serve_docs(docs_dir, args.port)

    print("🎉 文档构建完成!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
