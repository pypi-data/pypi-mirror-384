import os
import sys
import platform
from importlib.metadata import version, PackageNotFoundError


def get_system_info() -> dict:
    """获取详细的跨平台系统信息。

    Returns:
        dict: 包含系统类型、版本、架构等信息的字典。
    """
    info = {
        "系统类型": platform.system(),
        "系统版本": platform.version(),
        "架构": platform.machine(),
        "处理器": platform.processor() or "未知",
    }
    if platform.system() in ("Linux", "Darwin"):
        info["内核版本"] = platform.release()
    return info


def get_dependency_versions() -> dict:
    """获取关键依赖库的版本号。

    自动检测并返回项目中关键依赖（如 pytest, playwright）和 Python 的版本。

    Returns:
        dict: 包含依赖名称和其版本号的字典。如果某个依赖未安装，其值将是 "未安装"。
    """
    dependencies = [
        "pytest",
        "pytest-playwright",
        "playwright",
        "allure-pytest",
        "loguru",
        "python",
    ]
    versions = {}
    for dep in dependencies:
        try:
            if dep == "python":
                versions[dep] = sys.version.split()[0]
            else:
                versions[dep] = version(dep)
        except PackageNotFoundError:
            versions[dep] = "未安装"
    return versions


def is_ci_environment() -> str:
    """检测当前是否在持续集成 (CI) 环境中运行。

    通过检查常见的 CI 环境变量 (如 GITHUB_ACTIONS, JENKINS_URL) 来判断。

    Returns:
        str: 如果在 CI 环境中，返回 "是（<环境变量名>）"；否则返回 "否"。
    """
    ci_env_vars = [
        "CI",
        "GITHUB_ACTIONS",
        "JENKINS_URL",
        "GITLAB_CI",
        "TRAVIS",
        "APPVEYOR",
        "CIRCLECI",
    ]
    for var in ci_env_vars:
        if os.environ.get(var) in ("true", "1"):
            return f"是（{var}）"
    return "否"


def collect_all_environment_info(base_env: dict | None = None) -> dict:
    """收集并合并所有环境信息。

    整合基础环境信息、系统详情、依赖版本和执行上下文信息，
    形成一个扁平的字典，适用于 Allure 报告。

    Args:
        base_env (dict, optional): 基础环境信息字典。默认为 None。

    Returns:
        dict: 包含所有环境信息的扁平字典。
    """
    base_env = base_env or {}
    system_info = get_system_info()
    dep_versions = get_dependency_versions()
    execution_info = {
        "执行机器": os.environ.get("HOSTNAME", platform.node()),
        "CI环境": is_ci_environment(),
    }
    return {
        **base_env,
        **system_info,
        **dep_versions,
        **execution_info,
    }
