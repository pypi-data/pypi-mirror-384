"""工时记录查询 Tools."""
from typing import Any, Optional

from fastmcp import Context

from src.client import api_client
from src.server import mcp


@mcp.tool()
async def get_my_time_entries(
    ctx: Context,
    page: int = 1,
    limit: int = 10,
    project_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
) -> dict[str, Any]:
    """获取我的工时记录.

    获取当前用户的工时记录列表，支持多种过滤条件：
    - 按项目ID过滤
    - 按时间范围过滤
    - 按状态过滤

    返回工时记录的详细信息，包括工作日期、工时数、工作内容、审批状态等。

    Args:
        ctx: FastMCP 上下文
        page: 页码，默认为 1
        limit: 每页数量，默认为 10
        project_id: 项目ID过滤
        start_date: 开始日期过滤 (YYYY-MM-DD格式)
        end_date: 结束日期过滤 (YYYY-MM-DD格式)
        status: 状态过滤 (submitted/approved/rejected)

    Returns:
        工时记录数据，包含分页信息和工时数组
    """
    # 构建查询参数
    params: dict[str, Any] = {"page": page, "limit": limit}

    if project_id is not None:
        params["project_id"] = project_id

    if start_date:
        params["start_date"] = start_date

    if end_date:
        params["end_date"] = end_date

    if status:
        params["status"] = status

    # 调用 API
    try:
        result = await api_client.get("/time-entries/my", params=params)

        # 检查响应格式
        if isinstance(result, list):
            # 直接返回列表的情况
            return {
                "success": True,
                "data": {"data": result, "total": len(result)},
                "message": f"成功获取我的工时记录，共 {len(result)} 条",
            }
        elif "data" in result:
            # 包含分页信息的情况
            time_entries_data = result["data"]
            total = result.get("total", 0)

            return {
                "success": True,
                "data": result,
                "message": f"成功获取我的工时记录，共 {total} 条",
            }
        else:
            return {"success": False, "data": {}, "message": "API响应格式异常"}

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取我的工时记录失败: {str(e)}"}


@mcp.tool()
async def get_recent_time_entries(
    ctx: Context,
    limit: int = 10,
) -> dict[str, Any]:
    """获取最近工时记录.

    获取最近的工时记录，便于快速查看和复用。

    Args:
        ctx: FastMCP 上下文
        limit: 返回记录数，默认 10

    Returns:
        最近工时记录列表
    """
    try:
        result = await api_client.get("/time-entries/recent", params={"limit": limit})

        return {
            "success": True,
            "data": result,
            "message": f"成功获取最近 {limit} 条工时记录",
        }

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取最近工时记录失败: {str(e)}"}
