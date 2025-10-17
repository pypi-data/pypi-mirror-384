"""FastMCP 服务器主文件."""
import logging
from typing import Any

from fastmcp import FastMCP

from config.settings import settings

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.MCP_LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建 FastMCP 服务器实例
mcp = FastMCP("timesheet-mcp-server")


# 导入所有 tools
def register_tools() -> None:
    """注册所有 MCP tools - 聚焦查询功能."""
    # 工时记录查询 tools
    from src.tools.time_entry.query import get_my_time_entries, get_recent_time_entries

    # 用户查询 tools
    from src.tools.user.query import get_user_by_name, get_user_detail, get_user_time_entries

    # 项目查询 tools
    from src.tools.project.detail import (
        get_business_lines,
        get_project_detail,
        get_project_time_plan,
    )
    from src.tools.project.list import get_my_projects, get_my_projects_tree, get_projects
    from src.tools.project.members import get_project_members

    # 报表统计 tools
    from src.tools.report.advanced import (
        get_project_time_report,
        get_time_entry_report,
        get_time_entry_warnings,
        get_working_days,
    )
    from src.tools.report.time_stats import get_time_stats

    # 注册到 mcp server
    # FastMCP 会自动发现带有装饰器的函数
    logger.info("所有查询类 tools 已注册")


# 注册 tools
register_tools()


# 健康检查 tool
@mcp.tool()
async def health_check() -> dict[str, Any]:
    """健康检查.

    返回服务器状态和配置信息。
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "api_base_url": settings.API_BASE_URL,
        "transport": settings.MCP_TRANSPORT,
    }


if __name__ == "__main__":
    # 验证配置
    try:
        settings.validate()
        logger.info("配置验证成功")
    except ValueError as e:
        logger.error(f"配置验证失败: {e}")
        raise

    # 启动服务器
    logger.info(f"启动 MCP 服务器，传输方式: {settings.MCP_TRANSPORT}")
    mcp.run(transport=settings.MCP_TRANSPORT)
