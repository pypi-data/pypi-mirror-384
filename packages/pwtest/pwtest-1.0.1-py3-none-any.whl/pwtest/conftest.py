"""Pytest 配置文件 - Playwright 测试框架配置和 fixture 定义模块

此模块提供了完整的 Playwright + pytest + Allure 自动化测试框架配置，
包括浏览器管理、视频录制、截图处理、日志记录和测试报告功能。

主要功能：
    - 多浏览器并行测试支持
    - 自动化视频录制和截图功能
    - Allure 测试报告集成
    - 智能测试失败处理
    - 日志记录和时间统计
    - 浏览器状态管理

配置依赖：
    - config/config.py - 配置文件
    - utils/browser_state_manager.py - 浏览器状态管理器
    - utils/env_info.py - 环境信息收集
"""

from loguru import logger
import os
import sys
import pytest
from datetime import datetime
from playwright.sync_api import  sync_playwright
# 优先使用业务项目的配置,如果不存在则使用框架默认配置
try:
    from config.config import settings
except ImportError:
    from pwtest.config.config_base import settings
import allure
from allure import attachment_type
from pwtest.utils.browser_state_manager import BrowserStateManager
from pwtest.utils.env_info import collect_all_environment_info
import xml.etree.ElementTree as ET
import time


def _write_allure_environment_xml(env_data: dict, output_dir: str) -> None:
    """写入 Allure 所需的 environment.xml 文件（支持 UTF-8 中文）。"""

    if not env_data:
        logger.warning("Allure 环境信息为空，跳过写入 environment.xml")
        return

    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "environment.xml")

    root = ET.Element("environment")
    for key, value in env_data.items():
        parameter = ET.SubElement(root, "parameter")
        ET.SubElement(parameter, "key").text = str(key).strip()
        ET.SubElement(parameter, "value").text = str(value).replace("\n", " ").strip()

    tree = ET.ElementTree(root)
    try:
        tree.write(file_path, encoding="utf-8", xml_declaration=True)
        logger.info(f"Allure 环境信息已写入: {file_path}")
    except Exception as exc:
        logger.warning(f"写入 Allure 环境信息失败: {exc}")


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """会话开始时收集并写入 Allure 环境信息。"""

    # 获取 alluredir 参数,如果未指定或为 None,使用默认值
    allure_dir = session.config.getoption("--alluredir", default=None)
    if not allure_dir:
        allure_dir = "allure-results"
    
    base_env = {
        "框架配置-BASE_URL": getattr(settings, "BASE_URL", "未配置"),
        "框架配置-BROWSER": getattr(settings, "BROWSER", getattr(settings, "BROWSER_TYPE", "chromium")),
        "框架配置-HEADLESS": getattr(settings, "HEADLESS", "未配置"),
        "框架配置-SLOW_MO(ms)": getattr(settings, "SLOW_MO", "未配置"),
        "框架配置-VIEWPORT": f"{getattr(settings, 'VIEWPORT_WIDTH', '未知')}x{getattr(settings, 'VIEWPORT_HEIGHT', '未知')}",
        "框架配置-DEFAULT_TIMEOUT(ms)": getattr(settings, "DEFAULT_TIMEOUT", "未配置"),
        "框架配置-NAVIGATION_TIMEOUT(ms)": getattr(settings, "NAVIGATION_TIMEOUT", "未配置"),
        "框架配置-SCREENSHOT_ON_FAILURE": getattr(settings, "SCREENSHOT_ON_FAILURE", "未配置"),
        "框架配置-VIDEO_RECORD": getattr(settings, "VIDEO_RECORD", "未配置"),
        "框架配置-TRACING_ON": getattr(settings, "TRACING_ON", "未配置"),
        "执行信息-Pytest命令": " ".join(sys.argv),
    }

    env_data = collect_all_environment_info(base_env=base_env)
    _write_allure_environment_xml(env_data, allure_dir)

# 创建日志目录
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# 配置 loguru
logger.remove()  # 移除默认的处理器

# 添加控制台输出
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# 添加文件输出
logger.add(
    os.path.join(log_dir, "test_{time:YYYY-MM-DD}.log"),
    rotation="10 MB",  # 日志文件大小达到 10MB 时轮转
    retention="30 days",  # 保留30天的日志
    compression="zip",  # 压缩旧日志
    encoding="utf-8",
    level="DEBUG"
)

@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """设置全局日志配置。

    配置 loguru 日志系统，包括控制台输出和文件输出。
    自动创建日志目录，设置日志轮转和压缩策略。

    Note:
        此 fixture 自动应用于所有测试会话，无需手动调用。
    """
    logger.info("=" * 50)
    logger.info(f"测试开始执行 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    yield
    logger.info(f"测试执行结束 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)




# Playwright相关的fixture
def pytest_addoption(parser):
    """注册命令行参数 --browsers（避免与 pytest-playwright 的 --browser 冲突）

    运行方式示例:
        - 单浏览器: pytest --browsers=chromium
        - 多浏览器: pytest --browsers=chromium,firefox
        - 所有浏览器: pytest --browsers=all
        - 系统浏览器: pytest --browsers=chrome 或 --browsers=msedge

    Args:
        parser: pytest 命令行参数解析器对象。
    """
    parser.addoption(
        "--browsers",
        action="store",
        default=getattr(settings, "BROWSER", "chromium"),
        help="选择浏览器列表：chromium|firefox|webkit|chrome|msedge，逗号分隔或 'all'"
    )

def _parse_browsers(opt: str):
    """解析浏览器选项字符串。

    支持 'all' 关键字返回所有浏览器列表，
    也支持逗号分隔的浏览器名称列表。

    Args:
        opt (str): 浏览器选项字符串，支持的格式：
            - 'all': 返回所有浏览器 ['chromium', 'firefox', 'webkit']
            - 'chromium,firefox': 返回指定浏览器列表
            - 空字符串: 返回默认浏览器 ['chromium']

    Returns:
        List[str]: 浏览器名称列表。
    """
    opt = (opt or "").lower().strip()
    if opt == "all":
        return ["chromium", "firefox", "webkit"]
    parts = [p.strip() for p in opt.split(",") if p.strip()]
    return parts or ["chromium"]

def pytest_generate_tests(metafunc):
    """为包含 'cascade_browser_name' 的用例/fixture 提供参数化。

    优先读取 --browsers 命令行参数；若未提供则回退到 pytest-playwright 的 --browser 参数。
    使用独立的 fixture 名称以避免与其它插件/测试对 'browser_name' 的参数化冲突。

    Args:
        metafunc: pytest 的 metafunc 对象，包含测试函数的元数据。
    """
    if "cascade_browser_name" in metafunc.fixturenames:
        # 1) 我们自定义的多浏览器参数
        opt_multi = getattr(metafunc.config.option, "browsers", None)
        if opt_multi:
            names = _parse_browsers(opt_multi)
        
        # 2) 回退 settings.BROWSER
        else:
            names = _parse_browsers(getattr(settings, "BROWSER", "chromium"))
        metafunc.parametrize("cascade_browser_name", names, scope="session")
@pytest.fixture(scope="session")
def playwright():
    """创建 Playwright 实例。

    使用 sync_playwright 上下文管理器创建 Playwright 实例，
    为整个测试会话提供浏览器自动化功能支持。

    Yields:
        playwright: Playwright 实例对象。

    Note:
        此 fixture 的作用域为 session，会在整个测试会话中复用同一个实例。
    """
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright, cascade_browser_name):
    """创建浏览器实例并配置测试环境。

    根据配置创建指定类型的浏览器实例，支持多种浏览器类型：
    - chromium/firefox/webkit: 原生 Playwright 浏览器引擎
    - chrome/msedge: 系统安装的 Chrome/Edge 浏览器

    运行方式示例:
        - 指定单个: pytest --browsers=chromium / firefox / webkit
        - 指定多个: pytest --browsers=chromium,firefox
        - 全部运行: pytest --browsers=all
        - 使用系统浏览器: pytest --browsers=chrome 或 --browsers=msedge

    Args:
        playwright: Playwright 实例。
        cascade_browser_name (str): 浏览器名称。

    Yields:
        browser: 配置完成的浏览器实例。

    Raises:
        pytest.fail: 当不支持的浏览器类型或启动失败时抛出。
    """
    # 创建截图和视频目录
    if settings.SCREENSHOT_ON_FAILURE:
        os.makedirs(settings.SCREENSHOT_PATH, exist_ok=True)
        # 清空目录
        for file in os.listdir(settings.SCREENSHOT_PATH):
            os.remove(os.path.join(settings.SCREENSHOT_PATH, file))
    if settings.VIDEO_RECORD:
        os.makedirs(settings.VIDEO_PATH, exist_ok=True)
        # 清空目录
        for file in os.listdir(settings.VIDEO_PATH):
            os.remove(os.path.join(settings.VIDEO_PATH, file))
    if settings.TRACING_ON:
        os.makedirs(settings.TRACING_PATH, exist_ok=True)
        # 清空目录
        for file in os.listdir(settings.TRACING_PATH):
            os.remove(os.path.join(settings.TRACING_PATH, file))

    
    launch_kwargs = dict(headless=settings.HEADLESS, slow_mo=settings.SLOW_MO)
    try:
        browser_name = cascade_browser_name

        if browser_name in ("chrome", "msedge"):

            browser = playwright.chromium.launch(channel=browser_name, **launch_kwargs)
        elif browser_name in ("chromium", "firefox", "webkit"):
            engine = getattr(playwright, browser_name)
            browser = engine.launch(**launch_kwargs)
        else:
            pytest.fail(f"不支持的浏览器: {browser_name}")
    except Exception as e:
        pytest.fail(f"启动浏览器失败 ({browser_name}): {e}")
    yield browser
    browser.close()


@pytest.fixture(scope="session")
def context(browser, request):
    """创建浏览器上下文并配置登录状态。

    创建带有预配置的浏览器上下文，包括视窗大小、视频录制、
    超时设置和登录状态。使用浏览器状态管理器确保状态文件的有效性。

    Args:
        browser: 浏览器实例。
        request: pytest 请求对象，用于获取 login_callback fixture。

    Yields:
        context: 配置完成的浏览器上下文。

    Note:
        此 fixture 的作用域为 session，会在整个测试会话中复用同一个上下文。
        如果测试项目提供了 login_callback fixture，将自动使用它进行登录。
    """

    viewport_size = {
        "width": settings.VIEWPORT_WIDTH,
        "height": settings.VIEWPORT_HEIGHT
    }

    # 尝试获取用户定义的 login_callback
    login_callback = None
    try:
        login_callback = request.getfixturevalue("login_callback")
        logger.info("检测到用户定义的 login_callback")
    except Exception:
        logger.warning("未找到 login_callback fixture，将跳过登录状态管理")

    # 检查状态文件（如果提供了 login_callback）
    if login_callback:
        check_state = BrowserStateManager(browser, login_callback=login_callback)
        check_state.ensure_valid_state()

    # 创建带有登录状态的窗口上下文
    context = browser.new_context(
        viewport=viewport_size,
        record_video_dir=settings.VIDEO_PATH if settings.VIDEO_RECORD else None,
        record_video_size=viewport_size,
        ignore_https_errors=True,
        storage_state=settings.STATE_PATH if login_callback else None
    )
    
    # 设置默认超时
    context.set_default_timeout(settings.DEFAULT_TIMEOUT)
    context.set_default_navigation_timeout(settings.NAVIGATION_TIMEOUT)
    
    yield context
    context.close()

@pytest.fixture(scope="function", autouse=True)
def page(request, context, browser):
    """创建页面实例并智能管理上下文。

    (自动使用) 这是主要的 page fixture。
    它会根据测试用例的标记或名称，智能地决定是使用全新实例还是复用登录状态。

    对于带有 @pytest.mark.no_login 标记的测试，创建全新的上下文和页面。
    对于其他测试，复用已认证的上下文。

    Args:
        request: pytest 请求对象。
        context: 浏览器上下文。
        browser: 浏览器实例。

    Yields:
        page: Playwright 页面实例。

    Note:
        此 fixture 自动应用于所有测试函数，无需手动调用。
    """
    trace_path = None
    video_path = None
    test_name = request.node.name
    # test_name = test_name.replace("[", "-").replace("]", "").replace("\\", "-").replace(" | ", "-")
    test_name = test_name.encode('latin-1').decode('unicode_escape') if "\\u" in test_name else test_name
 
    if settings.TRACING_ON:
        trace_path = settings.TRACING_PATH + f"/{test_name}.zip"

    viewport_size = {
        "width": settings.VIEWPORT_WIDTH,
        "height": settings.VIEWPORT_HEIGHT
    }


    # 检查当前测试是否被 @pytest.mark.no_login 装饰
    if request.node.get_closest_marker("no_login"):
        logger.info(f"Test {test_name} requires a fresh browser. Creating new instance.")
        # 为登录测试创建全新的context和页面
        context = browser.new_context(
            viewport=viewport_size,
            record_video_dir=settings.VIDEO_PATH if settings.VIDEO_RECORD else None,
            record_video_size=viewport_size,
            ignore_https_errors=True
        )
    
        # 设置默认超时
        context.set_default_timeout(settings.DEFAULT_TIMEOUT)
        context.set_default_navigation_timeout(settings.NAVIGATION_TIMEOUT)

        # 开始录制
        if settings.TRACING_ON:
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        yield page
        if settings.VIDEO_RECORD and page.video:
            video_path = page.video.path()
        page.close()
        
        # 结束录制

        if settings.TRACING_ON and trace_path:
            context.tracing.stop(path=trace_path)

        # 调用失败处理函数
        if settings.VIDEO_RECORD or settings.TRACING_ON:
            handle_test_failure(video_path, request, trace_path, test_name)
        context.close()

    else:
        # 对于所有其他测试，复用已登录的 context
        logger.info(f"Test {request.node.name} reusing logged-in context.")
        # 在已认证的上下文中创建一个新页面
        if settings.TRACING_ON:
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        yield page
        # 关闭此测试的页面，但保留 context
        if settings.VIDEO_RECORD and page.video:
            video_path = page.video.path()
        page.close()
        
        # 结束录制
        if settings.TRACING_ON and trace_path:  
            context.tracing.stop(path=trace_path)
        
        # 调用失败处理函数
        if settings.VIDEO_RECORD or settings.TRACING_ON:
            handle_test_failure(video_path, request, trace_path, test_name)



# 使用handle_test_failure fixture来处理测试失败的用例


def handle_test_failure(video_path, request, trace_path, test_name):
    """处理测试失败的用例。

    根据测试执行结果智能处理视频、trace 文件和 Allure 报告附件：
    - 测试通过：自动清理视频和 trace 文件（如果配置了自动清理）
    - 测试失败：将视频和 trace 文件附加到 Allure 报告
    - 测试跳过：自动清理相关文件

    Args:
        video_path (str): 视频文件路径。
        request: pytest 请求对象。
        trace_path (str): trace 文件路径。
        test_name (str): 测试用例名称。

    Note:
        此函数通过 request.addfinalizer 注册为 finalizer，
        在测试结束后自动执行。
    """
    
    def _attach_if_failed():

        # 检查测试节点是否有rep_call属性，或者测试是否失败
        # 如果测试没有失败(rep_call.failed为False)，则直接返回
        if not hasattr(request.node, "rep_call") or not request.node.rep_call.failed:
            max_attempts = 5
            if settings.VIDEO_RECORD and settings.AUTO_CLEANUP_PASSED_VIDEOS:

                if video_path and os.path.exists(video_path):

                    for attempt in range(max_attempts):
                        try:
                            os.remove(video_path)
                            logger.info(f"✅ 删除视频成功: {video_path}")
                            break
                        except PermissionError as e:
                            logger.warning(f"❌ 删除视频失败 (尝试 {attempt + 1}/{max_attempts}): {e}")
                            time.sleep(0.4)
                        except Exception as e:
                            logger.error(f"❌ 删除视频失败: {e}")

            if settings.TRACING_ON and settings.AUTO_CLEANUP_PASSED_TRACINGS:
                if trace_path and os.path.exists(trace_path):

                    for attempt in range(max_attempts):
                        try:
                            os.remove(trace_path)
                            logger.info(f"✅ 删除trace成功: {trace_path}")
                            break
                        except PermissionError as e:
                            logger.warning(f"❌ 删除trace失败 (尝试 {attempt + 1}/{max_attempts}): {e}")
                            time.sleep(0.4)
                        except Exception as e:
                            logger.error(f"❌ 删除trace失败: {e}")
            return
        
        # 检查视频路径是否存在
        # 如果视频路径为空或文件不存在，记录错误日志并返回
        if settings.VIDEO_RECORD:
            if not video_path or not os.path.exists(video_path):
                logger.error("❌ 测试失败，但未找到视频文件")
                return
        if settings.TRACING_ON:
            if not trace_path or not os.path.exists(trace_path):
                logger.error("❌ 测试失败，但未找到trace文件")
                return
            
      
        # 用明确命名的 step 包裹，让 Allure 显示为独立步骤
        with allure.step("📸 测试失败 - 查看执行过程"):

            if settings.VIDEO_RECORD and video_path:
                try:
                    allure.attach.file(
                        video_path,
                        name=f"📹 视频记录 - {test_name}",
                        attachment_type=attachment_type.WEBM
                    )
                    logger.info(f"✅ 视频已附加到 Allure: {video_path}")
                except Exception as e:
                    logger.error(f"❌ 附加视频失败: {e}")
                
            if settings.TRACING_ON and trace_path:
                try:
                    allure.attach.file(
                        trace_path,
                        name=f"trace_record_{test_name}",
                        extension="zip"
                    )
                    logger.info(f"✅ trace已附加到 Allure: {trace_path}")
                except Exception as e:
                    logger.error(f"❌ 附加trace失败: {e}")



    # 注册为 finalizer，在 page.close() 之后执行
    request.addfinalizer(_attach_if_failed)


# 测试类级别的fixture
@pytest.fixture(scope="class", autouse=True)
def class_timer(request):
    """测试类级别的时间统计和日志。

    为测试类提供自动的时间统计功能，包括开始时间、结束时间
    和总耗时记录。同时在 Allure 报告中添加相应的步骤和附件。

    Args:
        request: pytest 请求对象，包含测试类信息。

    Yields:
        None: 此 fixture 主要用于副作用（日志和报告）。

    Note:
        此 fixture 自动应用于所有测试类，无需手动调用。
    """
    class_start_time = datetime.now()
    class_name = request.cls.__name__ if request.cls else "Unknown"
    
    # 日志记录
    logger.info("=" * 60)
    logger.info(f"开始执行测试类: {class_name}")
    logger.info(f"开始时间: {class_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Allure报告
    with allure.step(f"开始执行测试类: {class_name}"):
        allure.attach(
            f"测试类: {class_name}\n开始时间: {class_start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            name="测试类信息",
            attachment_type=attachment_type.TEXT
        )
    
    yield
    
    class_end_time = datetime.now()
    duration = class_end_time - class_start_time
    
    # 日志记录
    logger.info("=" * 60)
    logger.info(f"测试类执行完毕: {class_name}")
    logger.info(f"结束时间: {class_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"总耗时: {duration}")
    logger.info("=" * 60)
    
    # Allure报告
    with allure.step(f"测试类执行完毕: {class_name}"):
        allure.attach(
            f"测试类: {class_name}\n结束时间: {class_end_time.strftime('%Y-%m-%d %H:%M:%S')}\n总耗时: {duration}",
            name="测试类结果",
            attachment_type=attachment_type.TEXT
        )


@pytest.fixture(scope="function", autouse=True)
def method_timer(request):
    """测试方法级别的时间统计和日志。

    为每个测试方法提供详细的时间统计，包括开始时间、结束时间、
    耗时和执行状态。同时在 Allure 报告中添加相应的标签和附件。

    Args:
        request: pytest 请求对象，包含测试方法信息。

    Yields:
        None: 此 fixture 主要用于副作用（日志和报告）。

    Note:
        此 fixture 自动应用于所有测试方法，无需手动调用。
    """
    test_start_time = datetime.now()
    test_name = request.node.name
    # 解码 Unicode 转义序列
    test_name = test_name.encode('latin-1').decode('unicode_escape') if "\\u" in test_name else test_name
    start_time_str = test_start_time.strftime('%Y-%m-%d %H:%M:%S')

    
    # 日志记录
    logger.info(f"\n{'='*30} 开始执行测试用例 {'='*30}")
    logger.info(f"测试方法: {test_name}")
    logger.info(f"开始时间: {start_time_str}")
    
    # Allure报告 - 设置测试开始信息（使用前缀来排序）
    allure.dynamic.tag("开始时间: " + start_time_str)
    allure.dynamic.label("start_time", start_time_str)
    
    # 如果没有静态title，设置动态title
    if not hasattr(request.function, '_allure_title'):
        allure.dynamic.title(test_name)
    
    yield
    
    test_end_time = datetime.now()
    duration = test_end_time - test_start_time
    end_time_str = test_end_time.strftime('%Y-%m-%d %H:%M:%S')
    duration_str = str(duration).split('.')[0]  # 去掉微秒
    
    # 日志记录
    logger.info(f"结束时间: {end_time_str}")
    logger.info(f"测试耗时: {duration_str}")
    logger.info(f"{'='*30} 测试用例执行结束 {'='*30}\n")
    
    # Allure报告 - 添加结束信息
    # 获取测试执行结果（如果已生成）
    execution_status = "未知"
    if hasattr(request.node, 'rep_call'):
        if request.node.rep_call.passed:
            execution_status = "通过"
        elif request.node.rep_call.failed:
            execution_status = "失败"
        else:
            execution_status = "跳过"
    
    allure.attach(
        f"测试方法: {test_name}\n结束时间: {end_time_str}\n测试耗时: {duration_str}\n执行状态: {execution_status}",
        name="测试执行信息",
        attachment_type=attachment_type.TEXT
    )
        
    # 添加更多时间相关标签（使用前缀来排序）
    allure.dynamic.tag("结束时间: " + end_time_str)
    allure.dynamic.tag("执行耗时: " + duration_str)
    allure.dynamic.tag("执行状态: " + execution_status)
    allure.dynamic.label("end_time", end_time_str)
    allure.dynamic.label("duration", duration_str)
    allure.dynamic.label("execution_status", execution_status)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """获取测试结果的hook并处理失败截图。

    此 hook 函数在每个测试阶段（setup、call、teardown）结束后执行，
    主要用于：
    - 保存测试结果供后续 fixture 使用
    - 在测试失败时自动调用失败截图处理函数

    Args:
        item: pytest 测试项对象。
        call: pytest 调用信息对象。

    Yields:
        None: 此 hook 主要用于副作用。
    """
    outcome = yield
    rep = outcome.get_result()
    
    # 将结果保存到item中，供后续使用
    setattr(item, "rep_" + rep.when, rep)
    
    # 在测试结束时添加结果信息和失败截图
    if rep.when == "call":
        if rep.passed:
            allure.dynamic.tag("✅ 测试通过")
        elif rep.failed:
            allure.dynamic.tag("❌ 测试失败")
            # 处理失败截图
            _handle_test_failure_screenshot(item)
        elif rep.skipped:
            allure.dynamic.tag("⏭️ 测试跳过")



def _handle_test_failure_screenshot(item):
    """处理测试失败时的截图和HTML源码附件。

    当测试失败时，此函数会：
    1. 截取当前页面截图并保存
    2. 获取页面HTML源码
    3. 记录当前页面URL和时间信息
    4. 将所有诊断信息附加到 Allure 报告

    Args:
        item: pytest 测试项对象，包含测试失败信息。

    Note:
        此函数仅在测试失败时被调用，由 pytest_runtest_makereport hook 触发。
    """
    try:
        # 获取page对象（从 fixture 中获取）
        page = None
        for fixture_name in item.fixturenames:
            if fixture_name == 'page':
                page = item.funcargs.get('page')
                break
        
        if not page:
            logger.warning("无法获取page对象，跳过截图")
            return
            
        # 生成简洁的文件名，避免中文编码问题
        test_name = item.name
        # 移除参数中的中文字符，只保留基本测试名称
        # clean_test_name = test_name.split('[')[0] if '[' in test_name else test_name

        test_name = test_name.encode('latin-1').decode('unicode_escape') if "\\u" in test_name else test_name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        

        
        # 使用Allure步骤来组织失败信息
        with allure.step("📸 测试失败 - 收集诊断信息"):
            # 1. 截取屏幕截图
            try:
                screenshot_bytes = page.screenshot(full_page=True)
                allure.attach(
                    screenshot_bytes,
                    name=f"📸 失败截图 - {test_name}",
                    attachment_type=attachment_type.PNG
                )
                logger.error(f"测试失败，截图已添加到Allure报告: {test_name}")
                
                # 同时保存到文件（如果配置了）
                if settings.SCREENSHOT_ON_FAILURE:
                    screenshot_name = f"{test_name}_{timestamp}.png"
                    screenshot_path = os.path.join(settings.SCREENSHOT_PATH, screenshot_name)
                    page.screenshot(path=screenshot_path, full_page=True)
                    logger.info(f"截图也已保存到文件: {screenshot_path}")
                    
            except Exception as screenshot_error:
                logger.error(f"截图失败: {screenshot_error}")
                allure.attach(
                    f"截图失败: {str(screenshot_error)}",
                    name="截图错误信息",
                    attachment_type=attachment_type.TEXT
                )
            
            # 3. 获取页面HTML源码
            try:
                page_content = page.content()
                allure.attach(
                    page_content,
                    name=f"📜 页面HTML源码 - {test_name}",
                    attachment_type=attachment_type.HTML
                )
                logger.info(f"HTML源码已添加到Allure报告: {test_name}")
                
            except Exception as html_error:
                logger.warning(f"获取HTML源码失败: {html_error}")
                allure.attach(
                    f"HTML源码获取失败: {str(html_error)}",
                    name="HTML错误信息",
                    attachment_type=attachment_type.TEXT
                )
            
            # 4. 获取当前页面URL
            try:
                current_url = page.url
                allure.attach(
                    f"当前页面URL: {current_url}\n失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n测试用例: {test_name}",
                    name=f"🔗 页面信息 - {test_name}",
                    attachment_type=attachment_type.TEXT
                )
                
            except Exception as url_error:
                logger.warning(f"获取页面URL失败: {url_error}")
            
            # 5. 获取浏览器控制台日志（如果可用）
            try:
                # 这里可以添加浏览器控制台日志的获取
                # Playwright 目前不直接支持获取控制台日志
                # 但可以通过监听器来收集
                pass
                
            except Exception as console_error:
                logger.warning(f"获取控制台日志失败: {console_error}")
                
    except Exception as e:
        logger.error(f"处理测试失败截图时发生错误: {e}")
