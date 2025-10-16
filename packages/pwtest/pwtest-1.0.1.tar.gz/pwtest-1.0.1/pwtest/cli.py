"""
pwtest 命令行工具

提供项目初始化和其他实用命令。
"""

import os
import sys
import shutil
from pathlib import Path
from loguru import logger

# 配置 logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")


class ProjectInitializer:
    """项目初始化器"""
    
    def __init__(self, target_dir: str = "."):
        self.target_dir = Path(target_dir).resolve()
        self.package_dir = Path(__file__).parent
        
    def check_existing_files(self):
        """检查已存在的文件和目录"""
        items_to_check = {
            "directories": ["pages", "tests", "config"],
            "files": ["conftest.py", "pytest.ini", "README.md", "config/config.py"]
        }
        
        existing = {"directories": [], "files": []}
        
        for dir_name in items_to_check["directories"]:
            dir_path = self.target_dir / dir_name
            if dir_path.exists():
                existing["directories"].append(dir_name)
        
        for file_name in items_to_check["files"]:
            file_path = self.target_dir / file_name
            if file_path.exists():
                existing["files"].append(file_name)
        
        return existing
    
    def create_directories(self):
        """创建项目目录结构"""
        directories = ["pages", "tests", "config"]
        created = []
        
        for dir_name in directories:
            dir_path = self.target_dir / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created.append(dir_name)
                logger.info(f"✓ 创建目录: {dir_name}/")
                
                # 创建 __init__.py
                init_file = dir_path / "__init__.py"
                init_file.write_text("", encoding="utf-8")
                logger.debug(f"  创建文件: {dir_name}/__init__.py")
            else:
                logger.debug(f"✓ 目录已存在: {dir_name}/")
        
        return created
    
    def create_pytest_ini(self):
        """创建 pytest.ini 配置文件"""
        target_file = self.target_dir / "pytest.ini"
        
        if target_file.exists():
            logger.warning(f"⊘ 文件已存在，跳过: pytest.ini")
            return False
        
        # 从包内复制 pytest.ini
        source_file = self.package_dir / "pytest.ini"
        if source_file.exists():
            shutil.copy2(source_file, target_file)
            logger.info(f"✓ 创建文件: pytest.ini (从框架复制)")
        else:
            # 如果包内没有，使用默认模板
            content = """[pytest]
# pytest 配置文件

# 最小 pytest 版本
minversion = 8.0

# 测试路径
testpaths = tests

# 测试文件模式
python_files = test_*.py *_test.py

# 测试类模式
python_classes = Test*

# 测试函数模式
python_functions = test_*

# 命令行选项
addopts = 
    -v
    --tb=short
    --capture=no
    --strict-markers

# 自定义标记
markers =
    smoke: 冒烟测试用例
    regression: 回归测试用例
    no_login: 需要全新浏览器实例的测试
    slow: 运行缓慢的测试
"""
            target_file.write_text(content, encoding="utf-8")
            logger.info(f"✓ 创建文件: pytest.ini (使用默认模板)")
        
        return True
    
    def create_conftest(self):
        """创建 conftest.py 文件"""
        target_file = self.target_dir / "conftest.py"
        
        if target_file.exists():
            logger.warning(f"⊘ 文件已存在，跳过: conftest.py")
            return False
        
        content = '''"""
pytest 配置文件 - 导入框架 fixtures 并定义项目特定的 fixtures
"""

# 导入框架的所有 fixtures
from pwtest.conftest import *
from config.config import settings

# 定义 login_callback 以启用登录状态管理
@pytest.fixture(scope="session")
def login_callback():
    """提供登录回调给框架
    
    此 fixture 会被框架自动检测和使用。
    如果不需要登录状态管理，可以删除此 fixture。
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
'''
        target_file.write_text(content, encoding="utf-8")
        logger.info(f"✓ 创建文件: conftest.py")
        return True
    
    def create_config(self):
        """创建配置文件"""
        target_file = self.target_dir / "config" / "config.py"
        
        if target_file.exists():
            logger.warning(f"⊘ 文件已存在，跳过: config/config.py")
            return False
        
        content = '''"""
测试项目配置文件

继承框架默认配置，并覆盖项目特定的配置。
"""

from pwtest import Config as BaseConfig


class Config(BaseConfig):
    """项目配置类"""
    
    # ========== 基础配置 ==========
    BASE_URL = "https://demo.tinyauth.app"  # 修改为你的测试站点
    
    # ========== 浏览器配置 ==========
    BROWSER_TYPE = "chromium"  # chromium, firefox, webkit, chrome, edge
    HEADLESS = False           # 是否无头模式
    SLOW_MO = 100              # 操作间隔(毫秒)，0 表示无延迟
    
    # ========== 超时配置 ==========
    DEFAULT_TIMEOUT = 30000         # 默认超时(毫秒)
    NAVIGATION_TIMEOUT = 30000      # 导航超时(毫秒)
    
    # ========== 视窗配置 ==========
    VIEWPORT_WIDTH = 1920
    VIEWPORT_HEIGHT = 1080
    
    # ========== 截图配置 ==========
    SCREENSHOT_ON_FAILURE = True    # 失败时自动截图
    SCREENSHOT_PATH = "screenshots"
    
    # ========== 视频录制配置 ==========
    VIDEO_RECORD = True             # 是否录制视频
    VIDEO_PATH = "videos"
    AUTO_CLEANUP_PASSED_VIDEOS = True  # 通过的测试自动清理视频
    
    # ========== 操作录制配置 ==========
    TRACING_ON = False              # 是否启用 Playwright Trace
    TRACING_PATH = "tracings"
    AUTO_CLEANUP_PASSED_TRACINGS = True
    
    # ========== 业务配置 ==========
    VALID_USERNAME = "user"     # 修改为你的测试账号
    VALID_PASSWORD = "password"  # 修改为你的测试密码
    
    # ========== 状态管理 ==========
    STATE_PATH = "state.json"       # 登录状态保存路径


# 创建全局配置实例
settings = Config()
'''
        target_file.write_text(content, encoding="utf-8")
        logger.info(f"✓ 创建文件: config/config.py")
        return True
    
    def create_login_page(self):
        """创建登录页面对象示例"""
        target_file = self.target_dir / "pages" / "login_page.py"
        
        if target_file.exists():
            logger.warning(f"⊘ 文件已存在，跳过: pages/login_page.py")
            return False
        
        content = '''"""
登录页面对象

使用页面对象模式(POM)封装登录页面的元素和操作。
"""

from config.config import settings
from playwright.sync_api import expect
import re  # 正则表达式
import allure

class LoginPage:
    """登录页面"""
    
    def __init__(self, page):
        """初始化登录页面
        
        Args:
            page: Playwright page 对象
        """
        self.page = page
        
        # 定义页面元素 - 根据实际页面修改选择器
        self.username_input = page.get_by_role("textbox", name="用户名")
        self.password_input = page.get_by_role("textbox", name="密码")
        self.login_button = page.get_by_role("button", name="登录")
        self.login_fail = page.get_by_text("登录失败")
    
    @allure.step("导航到登录页面")
    def goto_login(self):
        """导航到登录页面"""
        self.page.goto(f"{settings.BASE_URL}/login")
    
    @allure.step("输入用户名")
    def input_username(self, username: str):
        """输入用户名"""
        self.username_input.fill(username)
    
    @allure.step("输入密码")
    def input_password(self, password: str):
        """输入密码"""
        self.password_input.fill(password)
    
    @allure.step("点击登录按钮")
    def click_login_button(self):
        """点击登录按钮"""
        self.login_button.click()
    
    @allure.step("等待页面加载完成")
    def wait_for_load_state(self):
        """等待页面加载完成"""
        self.page.wait_for_load_state("networkidle", timeout=settings.DEFAULT_TIMEOUT)

    @allure.step("检查是否已登录")
    def is_logged_in(self):
        """检查是否已登录"""
        expect(self.page).to_have_url(re.compile(r"^(?!.*login).*$"))
    
    @allure.step("检查登录失败")
    def is_login_fail(self):
        """检查登录失败"""
        expect(self.login_fail).to_be_visible(timeout=settings.DEFAULT_TIMEOUT)

    def login(self, username: str, password: str):
        """执行登录操作
        
        Args:
            username: 用户名
            password: 密码
        """
        self.goto_login()
        self.input_username(username)
        self.input_password(password)
        self.click_login_button()
        self.wait_for_load_state()
        self.is_logged_in()
            
    def check_login_status(self):
        """检查是否已登录
        
        Returns:
            None  
        """
        self.goto_login()
        self.wait_for_load_state()
        self.is_logged_in()
'''
        target_file.write_text(content, encoding="utf-8")
        logger.info(f"✓ 创建文件: pages/login_page.py")
        return True
    
    def create_test_example(self):
        """创建测试用例示例"""
        target_file = self.target_dir / "tests" / "test_example.py"
        
        if target_file.exists():
            logger.warning(f"⊘ 文件已存在，跳过: tests/test_example.py")
            return False
        
        content = '''"""
示例测试用例

演示如何使用 pwtest 框架编写测试用例。
"""

import allure
import pytest
from config.config import settings
from pages.login_page import LoginPage

@allure.epic("登录模块-示例")
@allure.feature("登录功能")
class TestLogin:
    """登录功能测试
    
    """

    @allure.story("正确用户名密码登录成功")
    @pytest.mark.no_login
    def test_successful_login(self, page):
        """测试成功登录
        
        Args:
            page: Playwright page fixture (由框架提供，不包含登录状态)
        """
        login_page = LoginPage(page)
        login_page.goto_login()
        login_page.input_username(settings.VALID_USERNAME)
        login_page.input_password(settings.VALID_PASSWORD)
        login_page.click_login_button()
        login_page.wait_for_load_state()
        login_page.is_logged_in()

    @allure.story("错误用户名密码登录失败")
    @pytest.mark.no_login
    def test_unsuccessful_login(self, page):
        """测试失败登录
        
        Args:
            page: Playwright page fixture (由框架提供，不包含登录状态)
        """
        login_page = LoginPage(page)
        login_page.goto_login()
        login_page.input_username("user")
        login_page.input_password("user")
        login_page.click_login_button()
        login_page.wait_for_load_state()
        login_page.is_login_fail()


    @allure.story("重用登录状态（正向）")
    def test_login_status_success(self, page):
        """测试用户登录状态
        
        Args:
            page: Playwright page fixture (由框架提供，包含登录状态)
        """
        login_page = LoginPage(page)
        login_page.goto_login()
        login_page.wait_for_load_state()
        login_page.is_logged_in()


    @allure.story("重用登录状态（反向）")
    @pytest.mark.no_login
    def test_login_status_unsuccess(self, page):
        """测试用户登录状态
        
        Args:
            page: Playwright page fixture (由框架提供，不包含登录状态)
        """
        login_page = LoginPage(page)   
        login_page.goto_login()
        login_page.wait_for_load_state()
        login_page.is_logged_in()

'''
        target_file.write_text(content, encoding="utf-8")
        logger.info(f"✓ 创建文件: tests/test_example.py")
        return True
    
    def create_readme(self):
        """创建项目 README"""
        target_file = self.target_dir / "README.md"
        
        if target_file.exists():
            logger.warning(f"⊘ 文件已存在，跳过: README.md")
            return False
        
        project_name = self.target_dir.name
        content = f'''# {project_name}

基于 pwtest 框架的 UI 自动化测试项目。

## 📁 项目结构

```
{project_name}/
├── config/
│   ├── __init__.py
│   └── config.py          # 项目配置
├── pages/
│   ├── __init__.py
│   └── login_page.py      # 页面对象
├── tests/
│   ├── __init__.py
│   └── test_example.py    # 测试用例
├── conftest.py            # pytest 配置
├── pytest.ini             # pytest 配置文件
└── README.md              # 项目说明
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pwtest
playwright install 
```

### 2. 配置项目

编辑 `config/config.py`,修改以下配置:
- `BASE_URL`: 测试站点地址
- `VALID_USERNAME`: 测试账号
- `VALID_PASSWORD`: 测试密码

### 3. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行指定测试
pytest tests/test_example.py -v

# 临时查看 Allure 报告
allure serve allure-results

# 生成 Allure 报告
allure generate ./allure-results -o ./allure-report --clean --lang zh
allure open ./allure-report

```

## 📝 编写测试

### 基本测试用例

```python
import allure

@allure.feature("功能模块")
@allure.story("用户故事")
def test_example(page):
    \"\"\"测试示例\"\"\"
    page.goto("/")
    expect(page).to_have_title("预期标题")
```

### 使用页面对象

```python
from pages.login_page import LoginPage

def test_with_page_object(page):
    login_page = LoginPage(page)
    login_page.goto_login()
    login_page.input_username(settings.VALID_USERNAME)
    login_page.input_password(settings.VALID_PASSWORD)
    login_page.click_login_button()

```

## 🔧 配置说明

### 浏览器配置

在 `config/config.py` 中修改:

```python
BROWSER_TYPE = "chromium"  # chromium, firefox, webkit
HEADLESS = False           # 是否无头模式
SLOW_MO = 100              # 操作间隔(毫秒)
```

### 视频录制

```python
VIDEO_RECORD = True                 # 启用视频录制
AUTO_CLEANUP_PASSED_VIDEOS = True   # 通过的测试自动清理视频
```

### 截图配置

```python
SCREENSHOT_ON_FAILURE = True  # 失败时自动截图
SCREENSHOT_PATH = "screenshots"
```

## 📚 更多文档

- [pwtest 框架文档](https://github.com/mofanx/pwtest)
- [Playwright 文档](https://playwright.dev/python/)
- [Pytest 文档](https://docs.pytest.org/)
- [Allure 文档](https://allurereport.org/docs/)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

MIT License
'''
        target_file.write_text(content, encoding="utf-8")
        logger.info(f"✓ 创建文件: README.md")
        return True
    
    def create_gitignore(self):
        """创建 .gitignore 文件"""
        target_file = self.target_dir / ".gitignore"
        
        if target_file.exists():
            logger.warning(f"⊘ 文件已存在，跳过: .gitignore")
            return False
        
        content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual Environment
venv/
ENV/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/

# Playwright/Test Results
allure-results/
allure-report/
screenshots/
videos/
tracings/
logs/
reports/
state.json
*.log

# Temporary files
*.tmp
*.bak
.temp/
'''
        target_file.write_text(content, encoding="utf-8")
        logger.info(f"✓ 创建文件: .gitignore")
        return True
    
    def initialize(self, force: bool = False):
        """初始化项目
        
        Args:
            force: 是否强制覆盖已存在的文件
        """
        logger.info(f"🚀 开始初始化项目: {self.target_dir}")
        logger.info("=" * 60)
        
        # 检查已存在的文件
        if not force:
            existing = self.check_existing_files()
            if existing["directories"] or existing["files"]:
                logger.warning("⚠️  检测到已存在的文件或目录:")
                for dir_name in existing["directories"]:
                    logger.warning(f"  - {dir_name}/")
                for file_name in existing["files"]:
                    logger.warning(f"  - {file_name}")
                logger.info("")
                logger.info("提示: 已存在的文件将被跳过，不会覆盖")
                logger.info("=" * 60)
        
        # 创建目录结构
        logger.info("📁 创建目录结构...")
        self.create_directories()
        logger.info("")
        
        # 创建配置文件
        logger.info("📝 创建配置文件...")
        self.create_pytest_ini()
        self.create_conftest()
        self.create_config()
        logger.info("")
        
        # 创建示例文件
        logger.info("📄 创建示例文件...")
        self.create_login_page()
        self.create_test_example()
        self.create_readme()
        self.create_gitignore()
        logger.info("")
        
        # 完成
        logger.info("=" * 60)
        logger.success("✅ 项目初始化完成!")
        logger.info("")
        logger.info("📚 下一步:")
        logger.info("  1. 编辑 config/config.py 配置测试站点信息")
        logger.info("  2. 编辑 pages/login_page.py 修改页面元素选择器")
        logger.info("  3. 运行测试: pytest tests/ -v")
        logger.info("")
        logger.info("📖 查看 README.md 获取更多帮助")


def main():
    """CLI 入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="pwtest - Playwright + Pytest + Allure UI 自动化测试框架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  pwtest init                    # 在当前目录初始化项目
  pwtest init --dir my_project   # 在指定目录初始化项目
  pwtest init --force            # 强制覆盖已存在的文件
  pwtest --version               # 显示版本信息
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # init 命令
    init_parser = subparsers.add_parser("init", help="初始化测试项目")
    init_parser.add_argument(
        "--dir",
        default=".",
        help="项目目录 (默认: 当前目录)"
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖已存在的文件"
    )
    
    # version 命令
    parser.add_argument(
        "--version",
        action="version",
        version="pwtest 1.0.1"
    )
    
    args = parser.parse_args()
    
    if args.command == "init":
        initializer = ProjectInitializer(args.dir)
        initializer.initialize(force=args.force)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
