import os
from typing import Optional, Callable
from playwright.sync_api import Browser, Page, TimeoutError as PlaywrightTimeoutError
from loguru import logger

# 优先使用业务项目的配置,如果不存在则使用框架默认配置
try:
    from config.config import settings
except ImportError:
    from pwtest.config.config_base import settings

class BrowserStateManager:
    """管理浏览器登录状态，实现会话复用。

    此类负责创建、保存、验证和管理 Playwright 的浏览器登录状态文件。
    它可以自动检测状态文件的有效性，并在需要时重新执行登录以生成新的状态，
    从而避免在每次测试运行时都重复登录。
    """
    
    def __init__(self, browser: Browser, state_path: Optional[str] = None, login_callback=None):
        """初始化 BrowserStateManager。

        Args:
            browser (Browser): Playwright 的 Browser 实例。
            state_path (Optional[str], optional): 登录状态文件的保存路径。
                如果为 None，则使用配置文件中的默认路径。默认为 None。
        """
        self.browser = browser
        self.state_path = state_path or self._get_default_state_path()
        self._ensure_state_dir()
        self.login_callback = login_callback
    
    def _get_default_state_path(self) -> str:
        """获取默认的状态文件路径。

        从配置文件 (settings) 中读取 `STATE_PATH` 并构造完整的绝对路径。

        Returns:
            str: 默认状态文件的绝对路径。
        """
        return os.path.join(os.getcwd(), settings.STATE_PATH)
    
    def _ensure_state_dir(self) -> None:
        """确保状态文件所在的目录存在。

        如果目录不存在，则会自动创建。
        """
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
    
    def state_exists(self) -> bool:
        """检查登录状态文件是否存在。

        Returns:
            bool: 如果文件存在则返回 True，否则返回 False。
        """
        return os.path.exists(self.state_path)
    
    def is_state_valid(self, max_retries: int = 1) -> bool:
        """验证当前登录状态是否仍然有效。

        通过多种通用方法验证状态的有效性：
        1. 检查URL是否还包含"login"路径（最通用）
        2. 检查是否跳转到了预期的主页面

        Args:
            max_retries (int, optional): 验证失败时的最大重试次数。默认为 1。

        Returns:
            bool: 如果状态有效则返回 True，否则返回 False。
        """
        if not self.state_exists():
            logger.info("状态文件不存在")
            return False

        for attempt in range(max_retries):
            try:
                logger.info(f"正在验证状态文件: {self.state_path}")
                context = self.browser.new_context(
                    ignore_https_errors=True,
                    storage_state=self.state_path
                )
                page = context.new_page()

                # 方法1：访问登录页面，检查是否自动跳转
                page.goto(settings.BASE_URL + "/login")

                # 等待页面加载完成
                page.wait_for_load_state("networkidle", timeout=settings.DEFAULT_TIMEOUT)

                # 检查当前URL是否还包含"login"路径
                current_url = page.url.lower()
                if "login" not in current_url:
                    logger.info(f"状态验证成功：URL已跳转至 {current_url}（不含login路径）")
                    return True

                # 方法2：检查是否跳转到了首页或仪表板
                base_url_lower = settings.BASE_URL.lower()
                if (current_url.startswith(base_url_lower) and
                    not current_url.replace(base_url_lower, "").startswith("/login")):
                    logger.info(f"状态验证成功：已跳转至主页面 {current_url}")
                    return True

            except (PlaywrightTimeoutError, Exception) as e:
                logger.warning(f"状态验证失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return False
            finally:
                try:
                    page.close()
                    context.close()
                except:
                    pass
    
 
    def create_new_state(self) -> None:
        """执行登录并创建一个新的状态文件。

        该方法会根据当前环境选择合适的登录流程，执行登录操作，
        然后将浏览器上下文的存储状态保存到文件中。

        Raises:
            Exception: 如果在登录或保存状态过程中发生任何错误。
        """
        context = self.browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:

            if self.login_callback:
                self.login_callback(page)
            else:
                raise NotImplementedError("请提供login_callback")

            # 等待页面加载完成
            page.wait_for_load_state("networkidle", timeout=settings.DEFAULT_TIMEOUT)
            
            # 保存状态
            context.storage_state(path=self.state_path)
            logger.info(f"登录状态已保存至: {self.state_path}")
            
            # 记录状态文件内容（调试用）
            if os.path.exists(self.state_path):
                with open(self.state_path, "r") as f:
                    logger.debug(f"状态文件内容: {f.read()}")
                    
        except Exception as e:
            logger.error(f"创建登录状态时出错: {e}")
            raise
        finally:
            page.close()
            context.close()
    
    def ensure_valid_state(self) -> None:
        """确保存在一个有效的登录状态。

        如果状态文件不存在或已失效，此方法会自动调用 `create_new_state`
        来生成一个新的有效状态。
        """
        if not self.state_exists() or not self.is_state_valid():
            logger.info("未找到有效登录状态，正在创建新的登录会话...")
            self.create_new_state()
        else:
            logger.info("检测到有效登录状态")
    
    def get_state_path(self) -> str:
        """获取当前状态文件的路径。

        Returns:
            str: 状态文件的绝对路径。
        """
        return self.state_path

