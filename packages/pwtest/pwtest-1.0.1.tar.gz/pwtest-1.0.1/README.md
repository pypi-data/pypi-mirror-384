# pwtest

> 基于 Playwright + Pytest + Allure 的 UI 自动化测试框架

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.54.0-brightgreen)](https://playwright.dev/)
[![Pytest](https://img.shields.io/badge/Pytest-8.4.1-yellow)](https://docs.pytest.org/)
[![Allure](https://img.shields.io/badge/Allure-2.15.0-orange)](https://docs.qameta.io/allure/)

## ✨ 特性

- 🚀 **开箱即用**: 集成 Playwright、Pytest、Allure,无需复杂配置
- 🎯 **POM 设计模式**: 清晰的页面对象模型,易于维护
- 📊 **美观的测试报告**: 自动生成 Allure 报告,支持视频录制和截图
- 🔄 **状态管理**: 智能的浏览器状态管理,避免重复登录
- 🌐 **多浏览器支持**: 支持 Chromium、Firefox、WebKit、Chrome、Edge
- 📝 **详细日志**: 基于 loguru 的日志系统,方便调试
- ⚡ **并行测试**: 支持多浏览器并行执行
- 🎨 **灵活配置**: 支持配置继承和覆盖

## 📦 安装

### 从 PyPI 安装(推荐)

```bash
pip install pwtest
```

### 从源码安装

```bash
git clone https://github.com/mofanx/pwtest.git
cd pwtest
pip install -e .
```

### 安装 Playwright 浏览器

```bash
# 安装框架后,需要安装 Playwright 浏览器
playwright install

# 或者只安装特定浏览器
playwright install chromium
```

## 🚀 快速开始

### 方式 1: 使用 CLI 初始化(推荐) ⭐

```bash
# 创建项目目录
mkdir my_test_project
cd my_test_project

# 使用 pwtest 命令初始化项目
pwtest init

# 完成! 所有必需的文件和目录都已创建
```

`pwtest init` 会自动创建:
- ✅ 目录结构 (config/, pages/, tests/)
- ✅ 配置文件 (pytest.ini, config/config.py)
- ✅ 测试配置 (conftest.py)
- ✅ 示例文件 (login_page.py, test_example.py)
- ✅ 项目文档 (README.md, .gitignore)

### 方式 2: 手动创建

如果你想手动创建项目结构:

```bash
mkdir my_test_project
cd my_test_project
mkdir -p config pages tests
```

### 2. 创建 pytest.ini (必需)

**重要**: 测试项目需要自己的 `pytest.ini`,框架内的配置不会自动生效。

```ini
# pytest.ini
[pytest]
minversion = 8.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --capture=no
markers =
    smoke: 冒烟测试用例
    regression: 回归测试用例
    user: 需要全新浏览器实例的测试
```

### 3. 创建配置文件

```python
# config/config.py
from pwtest import Config as BaseConfig

class Config(BaseConfig):
    BASE_URL = "https://your-test-site.com"
    VALID_USERNAME = "user"
    VALID_PASSWORD = "password"
    
    # 可选: 覆盖框架默认配置
    HEADLESS = False
    VIDEO_RECORD = True

settings = Config()
```

### 4. 创建 conftest.py (必需)

```python
# conftest.py
from pwtest.conftest import *  # 导入框架的所有 fixtures
from config.config import settings

# 定义 login_callback 以启用登录状态管理
@pytest.fixture(scope="session")
def login_callback():
    """提供登录回调函数
    
    此 fixture 会被框架自动检测和使用。
    如果不需要登录状态管理,可以不定义此 fixture。
    """
    def do_login(page):
        # 方式 1: 使用页面对象(推荐)
        from pages.login_page import LoginPage
        login_page = LoginPage(page)
        login_page.login(settings.VALID_USERNAME, settings.VALID_PASSWORD)
        
        # 方式 2: 直接操作(简单场景)
        # page.goto("/login")
        # page.fill("#username", settings.VALID_USERNAME)
        # page.fill("#password", settings.VALID_PASSWORD)
        # page.click("button[type='submit']")
    
    return do_login
```

**注意**: 
- `login_callback` 是可选的,只有需要登录状态管理时才定义
- 框架会自动检测并使用此 fixture
- 如果不定义,每个测试需要自己处理登录

### 5. 创建页面对象

```python
# pages/login_page.py
class LoginPage:
    def __init__(self, page):
        self.page = page
        self.username_input = page.get_by_placeholder("请输入账号")
        self.password_input = page.get_by_placeholder("请输入密码")
        self.login_button = page.get_by_role("button", name="登录")

    def login(self, username: str, password: str):
        self.page.goto("/login")
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
```

### 6. 编写测试用例

```python
# tests/test_example.py
import allure

@allure.feature("登录功能")
@allure.story("用户登录")
def test_successful_login(page):
    """测试成功登录"""
    page.goto("/dashboard")
    expect(page).to_have_title("预期标题")
```

### 7. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行指定浏览器
pytest tests/ --browsers=chromium

# 运行多个浏览器
pytest tests/ --browsers=chromium,firefox

# 生成 Allure 报告
pytest tests/ --alluredir=allure-results
allure serve allure-results
```

## 📖 详细文档

### 配置说明

框架提供了丰富的配置选项,可以通过继承 `Config` 类来覆盖默认配置:

```python
from pwtest import Config as BaseConfig

class Config(BaseConfig):
    # 基础配置
    BASE_URL = "https://example.com"
    
    # 浏览器配置
    BROWSER_TYPE = "chromium"  # chromium, firefox, webkit
    HEADLESS = False
    SLOW_MO = 100  # 操作间隔(毫秒)
    
    # 超时配置
    DEFAULT_TIMEOUT = 30000
    NAVIGATION_TIMEOUT = 30000
    
    # 视窗配置
    VIEWPORT_WIDTH = 1920
    VIEWPORT_HEIGHT = 1080
    
    # 截图配置
    SCREENSHOT_ON_FAILURE = True
    SCREENSHOT_PATH = "screenshots"
    
    # 视频录制配置
    VIDEO_RECORD = True
    VIDEO_PATH = "videos"
    AUTO_CLEANUP_PASSED_VIDEOS = True
    
    # 操作录制配置
    TRACING_ON = False
    TRACING_PATH = "tracings"
    AUTO_CLEANUP_PASSED_TRACINGS = True
    
    # 业务配置
    VALID_USERNAME = "testuser"
    VALID_PASSWORD = "password123"
    STATE_PATH = "state.json"

settings = Config()
```

### 登录回调函数

框架使用 `login_callback` 机制实现登录逻辑的解耦:

```python
@pytest.fixture(scope="session")
def login_callback():
    """提供登录回调函数"""
    def do_login(page):
        # 方式1: 使用页面对象
        login_page = LoginPage(page)
        login_page.login(username, password)
        
        # 方式2: 直接操作
        # page.goto("/login")
        # page.fill("#username", username)
        # page.fill("#password", password)
        # page.click("button[type='submit']")
    
    return do_login
```

### 多浏览器测试

```bash
# 单个浏览器
pytest --browsers=chromium

# 多个浏览器
pytest --browsers=chromium,firefox,webkit

# 所有浏览器
pytest --browsers=all

# 使用系统浏览器
pytest --browsers=chrome  # 或 msedge
```

### 测试标记

框架预定义了常用的测试标记:

```python
@pytest.mark.smoke
def test_critical_feature(page):
    """冒烟测试"""
    pass

@pytest.mark.no_login
def test_login(page):
    """需要全新浏览器的测试"""
    pass

@pytest.mark.regression
def test_all_features(page):
    """回归测试"""
    pass
```

## 🎯 最佳实践

### 1. 使用页面对象模式

```python
# pages/base_page.py
class BasePage:
    def __init__(self, page):
        self.page = page
    
    def navigate_to(self, path):
        self.page.goto(path)

# pages/login_page.py
class LoginPage(BasePage):
    def login(self, username, password):
        # 登录逻辑
        pass
```

### 2. 使用 Allure 装饰器

```python
import allure
from pages.login_page import LoginPage

@allure.feature("用户管理")
@allure.story("用户登录")
@allure.severity(allure.severity_level.CRITICAL)
def test_login(page):
    login_page = LoginPage(page)
    with allure.step("访问登录页"):
        login_page.goto_login()
    
    with allure.step("输入用户名和密码"):
        login_page.input_username(settings.VALID_USERNAME)
        login_page.input_password(settings.VALID_PASSWORD)
    
    with allure.step("点击登录按钮"):
        login_page.click_login_button()
```

### 3. 使用数据驱动测试

```python
import pytest

@pytest.mark.parametrize("username,password,expected", [
    ("user1", "pass1", True),
    ("user2", "pass2", False),
])
def test_login_with_data(page, username, password, expected):
    # 测试逻辑
    pass
```

### 4. 环境变量管理

```python
import os

class Config:
    BASE_URL = os.getenv("TEST_BASE_URL", "https://default.com")
    USERNAME = os.getenv("TEST_USERNAME", "default_user")
    PASSWORD = os.getenv("TEST_PASSWORD", "default_pass")
```

## 🔧 高级功能

### 自定义 Fixture

```python
# conftest.py

@pytest.fixture
def api_client():
    """API客户端fixture"""
    return APIClient(base_url=settings.API_URL)

@pytest.fixture
def test_data():
    """测试数据fixture"""
    return load_test_data("test_data.json")
```

### 覆盖框架 Fixture

```python
# 覆盖context fixture
@pytest.fixture(scope="session")
def context(browser):
    """自定义context配置"""
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        # 自定义配置
    )
    yield context
    context.close()
```

## 📊 测试报告

框架自动生成详细的测试报告:

- **Allure 报告**: 美观的 HTML 报告,包含测试步骤、截图、视频
- **HTML 报告**: pytest-html 生成的简单报告
- **日志文件**: 详细的测试执行日志

临时查看 Allure 报告:

```bash
allure serve allure-results
```

生成 Allure 报告:

```bash
allure generate ./allure-results -o ./allure-report --clean --lang zh
allure open ./allure-report
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

[MIT License](LICENSE)

## 🔗 相关链接

- [Playwright 文档](https://playwright.dev/python/)
- [Pytest 文档](https://docs.pytest.org/)
- [Allure 文档](https://docs.qameta.io/allure/)

## 🔧 CLI 命令

### pwtest init

初始化测试项目,自动创建所有必需的文件和目录。

```bash
# 在当前目录初始化
pwtest init

# 在指定目录初始化
pwtest init --dir my_project

# 强制覆盖已存在的文件
pwtest init --force
```

### pwtest --version

显示框架版本信息。

```bash
pwtest --version
```

---

## 📦 构建和发布

### 本地构建

```bash
# 安装构建工具
pip install build twine

# 构建包
python -m build

# 检查包
twine check dist/*
```

### 发布到 PyPI

```bash
# 发布到 TestPyPI (测试)
twine upload --repository testpypi dist/*

# 发布到 PyPI (正式)
twine upload dist/*
```

## 📮 联系方式

- GitHub: [https://github.com/mofanx/pwtest](https://github.com/mofanx/pwtest)
- 作者: mofanx
- Issues: [https://github.com/mofanx/pwtest/issues](https://github.com/mofanx/pwtest/issues)

## 🙏 致谢

感谢以下开源项目:

- [Playwright 文档](https://playwright.dev/python/) - 强大的浏览器自动化工具
- [Pytest 文档](https://docs.pytest.org/) - 优秀的 Python 测试框架
- [Allure 文档](https://allurereport.org/docs/) - 美观的测试报告框架
---

**pwtest** - 让 UI 自动化测试更简单! 🚀
