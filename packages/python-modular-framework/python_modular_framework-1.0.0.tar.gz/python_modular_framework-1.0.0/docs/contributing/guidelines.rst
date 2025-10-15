贡献指南
========

感谢您对Python模块化框架项目的关注！本指南将帮助您了解如何为项目做出贡献。

如何贡献
--------

报告问题
~~~~~~~~

如果您发现了bug或有功能建议，请通过以下方式报告：

1. **GitHub Issues**: 在GitHub上创建issue
2. **详细描述**: 提供问题的详细描述和复现步骤
3. **环境信息**: 包含Python版本、操作系统等信息

提交代码
~~~~~~~~

1. **Fork项目**: 在GitHub上fork项目
2. **创建分支**: 创建功能分支或bug修复分支
3. **编写代码**: 遵循项目的代码规范
4. **编写测试**: 为新功能编写测试用例
5. **提交PR**: 创建Pull Request

代码规范
--------

代码风格
~~~~~~~~

项目使用以下工具确保代码质量：

* **Black**: 代码格式化
* **Flake8**: 代码检查
* **MyPy**: 类型检查
* **Bandit**: 安全扫描

运行代码检查::

    python quality_check.py

命名规范
~~~~~~~~

* **文件名**: 使用小写字母和下划线
* **类名**: 使用大驼峰命名法 (PascalCase)
* **函数名**: 使用小写字母和下划线
* **常量**: 使用大写字母和下划线

文档规范
~~~~~~~~

* **文件头注释**: 每个文件都需要有文件头注释
* **函数注释**: 每个函数都需要有详细的文档字符串
* **类型注解**: 使用完整的类型注解
* **中文注释**: 使用中文编写注释和文档

提交规范
--------

提交信息格式
~~~~~~~~~~~~

使用以下格式编写提交信息::

    <类型>(<范围>): <描述>

    [可选的正文]

    [可选的脚注]

类型包括：
* **feat**: 新功能
* **fix**: 修复bug
* **docs**: 文档更新
* **style**: 代码格式调整
* **refactor**: 代码重构
* **test**: 测试相关
* **chore**: 构建过程或辅助工具的变动

示例::

    feat(middleware): 添加限流中间件

    实现了基于令牌桶算法的限流中间件，支持配置请求频率限制。

    Closes #123

分支命名
~~~~~~~~

* **feature/**: 新功能分支
* **bugfix/**: bug修复分支
* **hotfix/**: 紧急修复分支
* **docs/**: 文档更新分支

示例::
    feature/add-cache-middleware
    bugfix/fix-dependency-resolution
    docs/update-api-documentation

开发环境设置
------------

环境要求
~~~~~~~~

* Python 3.8+
* Git
* 虚拟环境工具 (venv, conda等)

设置步骤
~~~~~~~~

1. **克隆项目**::

    git clone https://github.com/your-org/python-modular-framework.git
    cd python-modular-framework

2. **创建虚拟环境**::

    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # 或
    venv\Scripts\activate     # Windows

3. **安装依赖**::

    pip install -e .[dev]

4. **运行测试**::

    python -m pytest

5. **运行代码检查**::

    python quality_check.py

测试指南
--------

编写测试
~~~~~~~~

* **单元测试**: 为每个函数编写单元测试
* **集成测试**: 测试组件间的交互
* **性能测试**: 确保性能要求
* **边界测试**: 测试边界条件

测试文件结构::

    tests/
    ├── unit/                 # 单元测试
    │   ├── test_components/
    │   ├── test_middleware/
    │   └── test_plugins/
    ├── integration/          # 集成测试
    │   ├── test_app_integration.py
    │   └── test_component_interaction.py
    └── performance/          # 性能测试
        └── test_performance.py

运行测试::

    # 运行所有测试
    python -m pytest

    # 运行特定测试
    python -m pytest tests/unit/test_components/

    # 运行测试并生成覆盖率报告
    python -m pytest --cov=framework

文档贡献
--------

文档类型
~~~~~~~~

* **API文档**: 使用Sphinx自动生成
* **用户指南**: 手写的使用说明
* **开发指南**: 面向开发者的文档
* **示例代码**: 可运行的代码示例

文档格式
~~~~~~~~

* **reStructuredText**: 使用RST格式编写
* **中文编写**: 使用中文编写文档
* **代码示例**: 提供可运行的代码示例
* **交叉引用**: 使用适当的交叉引用

构建文档::

    cd docs
    make html

发布流程
--------

版本管理
~~~~~~~~

项目使用语义化版本控制 (SemVer):

* **主版本号**: 不兼容的API修改
* **次版本号**: 向下兼容的功能性新增
* **修订号**: 向下兼容的问题修正

发布步骤
~~~~~~~~

1. **更新版本号**: 在相关文件中更新版本号
2. **更新CHANGELOG**: 记录变更内容
3. **运行测试**: 确保所有测试通过
4. **构建包**: 构建发布包
5. **发布**: 发布到PyPI

行为准则
--------

我们的承诺
~~~~~~~~~~

为了营造开放和友好的环境，我们承诺：

* 尊重所有贡献者
* 接受建设性的批评
* 关注对社区最有利的事情
* 对其他社区成员保持同理心

不可接受的行为
~~~~~~~~~~~~~~

以下行为是不可接受的：

* 使用性暗示的言语或图像
* 挑衅、侮辱或贬损性评论
* 公开或私下的骚扰
* 未经许可发布他人私人信息

联系方式
--------

* **GitHub Issues**: 报告问题和功能请求
* **GitHub Discussions**: 讨论和问答
* **Email**: 联系维护者

感谢您的贡献！

更多信息
--------

* :doc:`development_setup` - 开发环境设置
* :doc:`code_style` - 代码风格指南
* :doc:`../api/framework` - API参考
