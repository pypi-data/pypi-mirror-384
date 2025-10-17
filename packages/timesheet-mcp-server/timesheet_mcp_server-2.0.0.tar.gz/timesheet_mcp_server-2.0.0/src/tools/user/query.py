"""用户查询 Tools."""
from typing import Any, Optional

from fastmcp import Context

from src.client import api_client
from src.server import mcp


@mcp.tool()
async def get_user_by_name(
    ctx: Context,
    name: str,
    page: int = 1,
    limit: int = 10,
) -> dict[str, Any]:
    """根据用户名查询用户.

    根据用户名（支持模糊搜索）查询用户信息。可以搜索用户的真实姓名或用户名。

    Args:
        ctx: FastMCP 上下文
        name: 用户名（支持模糊搜索）
        page: 页码，默认为 1
        limit: 每页数量，默认为 10

    Returns:
        匹配的用户列表（包含 user_id, username, real_name, email 等）
    """
    try:
        result = await api_client.get(
            "/users",
            params={"keyword": name, "page": page, "limit": limit},
        )

        if "data" in result:
            users = result["data"]
            total = result.get("total", 0)

            return {
                "success": True,
                "data": result,
                "message": f"找到 {total} 个匹配 '{name}' 的用户",
            }
        else:
            return {"success": False, "data": {}, "message": "API响应格式异常"}

    except Exception as e:
        return {"success": False, "data": {}, "message": f"查询用户失败: {str(e)}"}


@mcp.tool()
async def get_user_detail(
    ctx: Context,
    user_id: int,
) -> dict[str, Any]:
    """获取用户详细信息.

    根据用户ID获取用户的详细信息，包括基本信息、角色、权限等。

    Args:
        ctx: FastMCP 上下文
        user_id: 用户ID

    Returns:
        用户详细信息
    """
    try:
        result = await api_client.get(f"/users/{user_id}")

        return {
            "success": True,
            "data": result,
            "message": f"成功获取用户 {user_id} 的详细信息",
        }

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取用户信息失败: {str(e)}"}


@mcp.tool()
async def get_user_time_entries(
    ctx: Context,
    user_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
) -> dict[str, Any]:
    """查询指定用户的工时记录.

    查询指定用户在特定时间范围内的工时记录。需要相应的查看权限。

    Args:
        ctx: FastMCP 上下文
        user_id: 用户ID
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        page: 页码，默认为 1
        limit: 每页数量，默认为 10

    Returns:
        用户工时记录列表
    """
    # 构建查询参数
    params: dict[str, Any] = {
        "user_id": user_id,
        "page": page,
        "limit": limit,
    }

    if start_date:
        params["start_date"] = start_date

    if end_date:
        params["end_date"] = end_date

    try:
        result = await api_client.get("/time-entries/list", params=params)

        if "data" in result:
            return {
                "success": True,
                "data": result,
                "message": f"成功获取用户 {user_id} 的工时记录",
            }
        else:
            return {"success": False, "data": {}, "message": "API响应格式异常"}

    except Exception as e:
        return {"success": False, "data": {}, "message": f"查询用户工时记录失败: {str(e)}"}
