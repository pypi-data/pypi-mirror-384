"""项目详情查询 Tools."""
from typing import Any

from fastmcp import Context

from src.client import api_client
from src.server import mcp


@mcp.tool()
async def get_project_detail(
    ctx: Context,
    project_id: int,
) -> dict[str, Any]:
    """获取项目详情.

    获取项目的详细信息，包括基本信息、成员、工时计划等。

    Args:
        ctx: FastMCP 上下文
        project_id: 项目ID

    Returns:
        项目详细信息
    """
    try:
        result = await api_client.get(f"/projects/{project_id}")

        return {
            "success": True,
            "data": result,
            "message": f"成功获取项目 {project_id} 的详细信息",
        }

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取项目详情失败: {str(e)}"}


@mcp.tool()
async def get_project_time_plan(
    ctx: Context,
    project_id: int,
) -> dict[str, Any]:
    """获取项目工时计划.

    获取项目的工时计划信息，包括计划工时、已用工时、剩余工时等。

    Args:
        ctx: FastMCP 上下文
        project_id: 项目ID

    Returns:
        项目工时计划详情
    """
    try:
        result = await api_client.get(f"/projects/{project_id}/time-plan")

        return {
            "success": True,
            "data": result,
            "message": f"成功获取项目 {project_id} 的工时计划",
        }

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取项目工时计划失败: {str(e)}"}


@mcp.tool()
async def get_business_lines(
    ctx: Context,
    page: int = 1,
    limit: int = 20,
) -> dict[str, Any]:
    """获取业务线列表.

    获取所有业务线列表，可用于项目筛选和分类。

    Args:
        ctx: FastMCP 上下文
        page: 页码，默认为 1
        limit: 每页数量，默认为 20

    Returns:
        业务线列表
    """
    try:
        result = await api_client.get(
            "/business-lines",
            params={"page": page, "limit": limit},
        )

        if "data" in result:
            total = result.get("total", 0)

            return {
                "success": True,
                "data": result,
                "message": f"成功获取业务线列表，共 {total} 个业务线",
            }
        else:
            return {"success": False, "data": {}, "message": "API响应格式异常"}

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取业务线列表失败: {str(e)}"}
