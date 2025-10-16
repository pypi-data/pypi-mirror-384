"""
pwtest - 基于 Playwright + Pytest + Allure 的 UI 自动化测试框架

这是一个开箱即用的 UI 自动化测试框架，集成了 Playwright、Pytest 和 Allure，
提供了完整的测试基础设施，包括浏览器管理、状态管理、视频录制、截图和报告生成。

主要特性:
    - 🚀 开箱即用，无需复杂配置
    - 🎯 POM 设计模式支持
    - 📊 自动生成 Allure 报告
    - 🔄 智能的浏览器状态管理
    - 🌐 多浏览器并行测试支持
    - 📝 详细的日志记录

基本使用:
    >>> from pwtest import Config as BaseConfig
    >>> 
    >>> class MyConfig(BaseConfig):
    ...     BASE_URL = "https://example.com"
    ...     HEADLESS = False
    >>> 
    >>> settings = MyConfig()

更多信息请访问: https://github.com/mofanx/pwtest
"""

__version__ = "1.0.1"
__author__ = "mofanx"
__license__ = "MIT"
__url__ = "https://github.com/mofanx/pwtest"

# 导出配置类和实例
from pwtest.config.config_base import Config, settings

# 导出工具类
from pwtest.utils.browser_state_manager import BrowserStateManager
from pwtest.utils.env_info import (
    get_system_info,
    get_dependency_versions,
    is_ci_environment,
    collect_all_environment_info,
)

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__license__",
    "__url__",
    # 配置相关
    "Config",
    "settings",
    # 工具类
    "BrowserStateManager",
    "get_system_info",
    "get_dependency_versions",
    "is_ci_environment",
    "collect_all_environment_info",
]
