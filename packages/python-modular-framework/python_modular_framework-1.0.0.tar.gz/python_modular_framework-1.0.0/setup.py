"""
Python模块化框架安装配置文件
- 提供框架的安装和分发功能
- 定义包依赖和元数据
- 支持开发模式和发布模式

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from setuptools import setup, find_packages
import os


# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()


# 读取requirements文件
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [
            line.strip() for line in fh if line.strip() and not line.startswith("#")
        ]


setup(
    name="python-modular-framework",
    version="1.0.0",
    author="Python模块化框架开发团队",
    author_email="dev@python-modular-framework.org",
    description="一个基于Python的模块化框架系统",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/python-modular-framework/python-modular-framework",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Frameworks",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "isort>=5.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "database": [
            "sqlalchemy>=2.0.0",
            "psycopg2-binary>=2.9.0",
            "pymysql>=1.0.0",
        ],
        "cache": [
            "redis>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "framework-cli=framework.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
