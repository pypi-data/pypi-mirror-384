"""高级报表查询 Tools."""
from typing import Any, Optional

from fastmcp import Context

from src.client import api_client
from src.server import mcp


@mcp.tool()
async def get_time_entry_report(
    ctx: Context,
    start_date: str,
    end_date: str,
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    business_line_id: Optional[int] = None,
) -> dict[str, Any]:
    """获取工时统计报表.

    获取指定时间范围和过滤条件的工时统计报表数据。

    Args:
        ctx: FastMCP 上下文
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        user_id: 用户ID过滤（可选）
        project_id: 项目ID过滤（可选）
        business_line_id: 业务线ID过滤（可选）

    Returns:
        工时统计报表数据
    """
    params: dict[str, Any] = {
        "start_date": start_date,
        "end_date": end_date,
    }

    if user_id is not None:
        params["user_id"] = user_id

    if project_id is not None:
        params["project_id"] = project_id

    if business_line_id is not None:
        params["business_line_id"] = business_line_id

    try:
        result = await api_client.get("/time-entry-report", params=params)

        return {
            "success": True,
            "data": result,
            "message": f"成功获取 {start_date} 至 {end_date} 的工时统计报表",
        }

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取工时统计报表失败: {str(e)}"}


@mcp.tool()
async def get_project_time_report(
    ctx: Context,
    start_date: str,
    end_date: str,
    project_id: Optional[int] = None,
) -> dict[str, Any]:
    """获取项目工时报表.

    获取项目维度的工时统计报表。

    Args:
        ctx: FastMCP 上下文
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        project_id: 项目ID过滤（可选）

    Returns:
        项目工时报表数据
    """
    params: dict[str, Any] = {
        "start_date": start_date,
        "end_date": end_date,
    }

    if project_id is not None:
        params["project_id"] = project_id

    try:
        result = await api_client.get("/project-report", params=params)

        return {
            "success": True,
            "data": result,
            "message": f"成功获取 {start_date} 至 {end_date} 的项目工时报表",
        }

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取项目工时报表失败: {str(e)}"}


@mcp.tool()
async def get_working_days(
    ctx: Context,
    month: str,
) -> dict[str, Any]:
    """获取工作日信息.

    获取指定月份的工作日信息，包括工作日列表、节假日等。

    Args:
        ctx: FastMCP 上下文
        month: 月份 (YYYY-MM格式)

    Returns:
        工作日列表和统计
    """
    try:
        result = await api_client.get(f"/settings/working-days/{month}")

        return {
            "success": True,
            "data": result,
            "message": f"成功获取 {month} 的工作日信息",
        }

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取工作日信息失败: {str(e)}"}


@mcp.tool()
async def get_time_entry_warnings(
    ctx: Context,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict[str, Any]:
    """获取工时预警.

    获取工时预警信息，包括缺失工时、异常工时等。

    Args:
        ctx: FastMCP 上下文
        start_date: 开始日期 (YYYY-MM-DD)（可选）
        end_date: 结束日期 (YYYY-MM-DD)（可选）

    Returns:
        工时预警列表
    """
    params: dict[str, Any] = {}

    if start_date:
        params["start_date"] = start_date

    if end_date:
        params["end_date"] = end_date

    try:
        result = await api_client.get("/time-entries/warnings", params=params)

        return {
            "success": True,
            "data": result,
            "message": "成功获取工时预警信息",
        }

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取工时预警失败: {str(e)}"}
