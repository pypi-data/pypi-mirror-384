"""项目成员管理 Tools."""
from typing import Any

from fastmcp import Context

from src.client import api_client
from src.server import mcp


@mcp.tool()
async def get_project_members(
    ctx: Context,
    project_id: int,
    page: int = 1,
    limit: int = 10,
) -> dict[str, Any]:
    """获取项目成员列表.

    根据项目ID获取该项目的所有成员信息，包括成员的用户信息、在项目中的角色等。
    支持分页查询，返回成员的详细信息。

    Args:
        ctx: FastMCP 上下文
        project_id: 项目ID
        page: 页码，默认为 1
        limit: 每页数量，默认为 10

    Returns:
        项目成员列表数据，包含分页信息和成员数组
    """
    try:
        result = await api_client.get(
            f"/projects/{project_id}/members",
            params={"page": page, "limit": limit},
        )

        if "data" in result:
            members_data = result["data"]
            total = result.get("total", 0)

            return {
                "success": True,
                "data": result,
                "message": f"成功获取项目 {project_id} 的成员列表，共 {total} 个成员",
            }
        else:
            return {"success": False, "data": {}, "message": "API响应格式异常"}

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取项目成员失败: {str(e)}"}
