开发环境设置
============

本指南将帮助您设置Python模块化框架的开发环境。

系统要求
--------

* **Python**: 3.8 或更高版本
* **操作系统**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
* **内存**: 至少 4GB RAM
* **磁盘空间**: 至少 1GB 可用空间

开发工具
--------

推荐工具
~~~~~~~~

* **IDE**: VS Code, PyCharm, 或 Vim/Emacs
* **版本控制**: Git
* **包管理**: pip, conda (可选)
* **虚拟环境**: venv, virtualenv, 或 conda

VS Code 配置
~~~~~~~~~~~~

推荐安装的VS Code扩展：

* Python
* Python Docstring Generator
* GitLens
* REST Client
* Thunder Client

配置文件 ``.vscode/settings.json``::

    {
        "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
        "python.linting.enabled": true,
        "python.linting.flake8Enabled": true,
        "python.linting.mypyEnabled": true,
        "python.formatting.provider": "black",
        "python.testing.pytestEnabled": true,
        "python.testing.pytestArgs": ["tests"],
        "files.exclude": {
            "**/__pycache__": true,
            "**/*.pyc": true,
            "**/.pytest_cache": true
        }
    }

环境设置步骤
------------

1. 克隆项目
~~~~~~~~~~~

::

    git clone https://github.com/your-org/python-modular-framework.git
    cd python-modular-framework

2. 创建虚拟环境
~~~~~~~~~~~~~~~

使用venv (推荐)::

    python -m venv venv

    # Windows
    venv\Scripts\activate

    # Linux/macOS
    source venv/bin/activate

使用conda::

    conda create -n framework python=3.9
    conda activate framework

3. 安装依赖
~~~~~~~~~~~

开发模式安装::

    pip install -e .[dev]

手动安装依赖::

    pip install -r requirements.txt
    pip install black flake8 mypy pytest bandit safety

4. 验证安装
~~~~~~~~~~~

::

    python -c "from framework.core.application import Application; print('安装成功！')"

运行测试::

    python -m pytest

运行代码检查::

    python quality_check.py

项目结构
--------

::

    framework/
    ├── components/              # 组件模块
    │   ├── auth/               # 认证组件
    │   ├── common/             # 通用组件
    │   ├── payment/            # 支付组件
    │   └── user/               # 用户组件
    ├── example_plugins/        # 示例插件
    ├── examples/               # 示例应用
    ├── framework/              # 框架核心
    │   ├── core/              # 核心模块
    │   ├── interfaces/        # 接口定义
    ├── docs/                  # 文档
    ├── tests/                 # 测试文件
    ├── requirements.txt       # 依赖列表
    ├── setup.py              # 安装脚本
    └── pyproject.toml        # 项目配置

开发工作流
----------

日常开发流程
~~~~~~~~~~~~

1. **创建分支**::

    git checkout -b feature/my-new-feature

2. **编写代码**: 遵循代码规范

3. **运行测试**::

    python -m pytest

4. **代码检查**::

    python quality_check.py

5. **提交代码**::

    git add .
    git commit -m "feat: 添加新功能"
    git push origin feature/my-new-feature

6. **创建PR**: 在GitHub上创建Pull Request

调试技巧
--------

日志配置
~~~~~~~~

开发环境日志配置::

    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

使用调试器
~~~~~~~~~~

VS Code调试配置 ``.vscode/launch.json``::

    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Current File",
                "type": "python",
                "request": "launch",
                "program": "${file}",
                "console": "integratedTerminal",
                "cwd": "${workspaceFolder}"
            },
            {
                "name": "Python: Framework Test",
                "type": "python",
                "request": "launch",
                "module": "pytest",
                "args": ["tests/", "-v"],
                "console": "integratedTerminal",
                "cwd": "${workspaceFolder}"
            }
        ]
    }

性能分析
~~~~~~~~

使用cProfile分析性能::

    python -m cProfile -o profile.stats examples/performance_test.py
    python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"

内存分析
~~~~~~~~

使用memory_profiler::

    pip install memory-profiler

    # 在代码中添加装饰器
    from memory_profiler import profile

    @profile
    def my_function():
        # 函数代码
        pass

测试环境
--------

单元测试
~~~~~~~~

运行单元测试::

    python -m pytest tests/unit/ -v

运行特定测试::

    python -m pytest tests/unit/test_components/test_auth.py::test_authenticate -v

集成测试
~~~~~~~~

运行集成测试::

    python -m pytest tests/integration/ -v

性能测试
~~~~~~~~

运行性能测试::

    python examples/performance_test.py

代码覆盖率
~~~~~~~~~~

生成覆盖率报告::

    python -m pytest --cov=framework --cov-report=html

查看HTML报告::

    open htmlcov/index.html

持续集成
--------

GitHub Actions
~~~~~~~~~~~~~~

项目使用GitHub Actions进行CI/CD，配置文件位于 ``.github/workflows/ci.yml``。

本地运行CI检查::

    # 运行所有检查
    python quality_check.py --all

    # 运行特定检查
    python quality_check.py --black
    python quality_check.py --flake8
    python quality_check.py --mypy
    python quality_check.py --bandit

常见问题
--------

虚拟环境问题
~~~~~~~~~~~~

**问题**: 虚拟环境激活失败
**解决**: 检查Python路径和权限::

    # Windows
    venv\Scripts\python.exe --version

    # Linux/macOS
    source venv/bin/activate
    which python

依赖冲突
~~~~~~~~

**问题**: 包依赖冲突
**解决**: 使用虚拟环境隔离::

    pip install --upgrade pip
    pip install -e .[dev] --force-reinstall

测试失败
~~~~~~~~

**问题**: 测试运行失败
**解决**: 检查测试环境和依赖::

    python -m pytest --tb=short -v

文档构建失败
~~~~~~~~~~~~

**问题**: Sphinx文档构建失败
**解决**: 检查依赖和配置::

    cd docs
    pip install sphinx sphinx-rtd-theme
    make html

获取帮助
--------

* **GitHub Issues**: 报告问题和获取帮助
* **文档**: 查看项目文档
* **代码审查**: 通过PR获取代码审查

更多信息
--------

* :doc:`guidelines` - 贡献指南
* :doc:`code_style` - 代码风格指南
* :doc:`../troubleshooting/common_issues` - 常见问题
