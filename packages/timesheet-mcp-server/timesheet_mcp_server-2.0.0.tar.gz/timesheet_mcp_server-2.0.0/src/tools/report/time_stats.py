"""工时统计报表 Tools."""
from typing import Any, Optional

from fastmcp import Context

from src.client import api_client
from src.server import mcp


@mcp.tool()
async def get_time_stats(
    ctx: Context,
    start_date: str,
    end_date: str,
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    group_by: Optional[str] = None,
) -> dict[str, Any]:
    """获取工时统计数据.

    根据指定的时间范围和过滤条件，获取工时统计信息。支持多种分组方式：
    - day: 按天统计
    - week: 按周统计
    - month: 按月统计
    - project: 按项目统计
    - user: 按用户统计

    返回详细的工时统计数据，包括总工时、平均工时等信息。

    Args:
        ctx: FastMCP 上下文
        start_date: 开始日期 (YYYY-MM-DD格式)
        end_date: 结束日期 (YYYY-MM-DD格式)
        user_id: 用户ID过滤，不指定则统计所有用户
        project_id: 项目ID过滤，不指定则统计所有项目
        group_by: 分组方式 (day/week/month/project/user)

    Returns:
        工时统计数据
    """
    # 构建查询参数
    params: dict[str, Any] = {
        "start_date": start_date,
        "end_date": end_date,
    }

    if user_id is not None:
        params["user_id"] = user_id

    if project_id is not None:
        params["project_id"] = project_id

    if group_by:
        params["group_by"] = group_by

    # 调用 API
    try:
        result = await api_client.get("/time-entries/stats", params=params)

        if "data" in result:
            return {
                "success": True,
                "data": result,
                "message": f"成功获取 {start_date} 至 {end_date} 的工时统计数据",
            }
        else:
            # 兼容直接返回数据的情况
            return {
                "success": True,
                "data": {"data": result},
                "message": f"成功获取 {start_date} 至 {end_date} 的工时统计数据",
            }

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取工时统计失败: {str(e)}"}
