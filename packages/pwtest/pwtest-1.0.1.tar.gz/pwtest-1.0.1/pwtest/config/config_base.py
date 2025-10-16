"""
Playwright测试框架配置文件
"""

class Config:
    """测试配置类"""
    
    # 基础URL配置
    BASE_URL = "https://demo.tinyauth.app"  # 请替换为实际的测试网站URL
    
    # 浏览器配置
    BROWSER_TYPE = "chromium"  # chromium, firefox, webkit
    HEADLESS = False  # 是否无头模式
    SLOW_MO = 100  # 操作间隔时间(毫秒)
    
    # 超时配置
    DEFAULT_TIMEOUT = 30000  # 默认超时时间(毫秒)
    NAVIGATION_TIMEOUT = 30000  # 页面导航超时时间
    
    # 视窗配置
    VIEWPORT_WIDTH = 1920
    VIEWPORT_HEIGHT = 1080
    
    # 截图配置
    SCREENSHOT_ON_FAILURE = True
    SCREENSHOT_PATH = "screenshots"
    
    # 视频录制配置
    VIDEO_RECORD = True
    VIDEO_PATH = "videos"
    AUTO_CLEANUP_PASSED_VIDEOS = True  # 自动清理通过测试的视频文件
    
    # 操作录制配置
    TRACING_ON = False
    TRACING_PATH = "tracings"
    AUTO_CLEANUP_PASSED_TRACINGS = True # 自动清理通过测试的操作记录
        
    # 测试数据
    VALID_USERNAME = "user"
    VALID_PASSWORD = "password"

    # 状态保存
    STATE_PATH = "state.json"

# 创建全局配置实例
settings = Config()
