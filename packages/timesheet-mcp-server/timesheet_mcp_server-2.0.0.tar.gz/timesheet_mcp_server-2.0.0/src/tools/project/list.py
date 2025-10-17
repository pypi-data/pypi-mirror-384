"""项目列表查询 Tools."""
from typing import Any, Optional

from fastmcp import Context

from src.client import api_client
from src.server import mcp


@mcp.tool()
async def get_projects(
    ctx: Context,
    page: int = 1,
    limit: int = 10,
    keyword: Optional[str] = None,
    business_line_id: Optional[int] = None,
    project_type: Optional[str] = None,
    level: Optional[str] = None,
) -> dict[str, Any]:
    """获取项目列表.

    支持分页查询和多种过滤条件，包括关键词搜索、业务线过滤、项目类型过滤等。
    返回项目的基本信息，包括项目ID、名称、类型、状态、负责人等。

    Args:
        ctx: FastMCP 上下文
        page: 页码，默认为 1
        limit: 每页数量，默认为 10
        keyword: 搜索关键词，用于项目名称模糊搜索
        business_line_id: 业务线ID过滤
        project_type: 项目类型过滤 (工程类/研发类/管理类)
        level: 项目级别 (level1/level2)

    Returns:
        项目列表数据，包含分页信息和项目数组
    """
    # 构建查询参数
    params: dict[str, Any] = {"page": page, "limit": limit}

    if keyword:
        params["keyword"] = keyword

    if business_line_id is not None:
        params["business_line_id"] = business_line_id

    if project_type:
        params["type"] = project_type

    if level:
        params["level"] = level

    # 调用 API
    try:
        result = await api_client.get("/projects", params=params)

        if "data" in result:
            projects_data = result["data"]
            total = result.get("total", 0)

            return {
                "success": True,
                "data": result,
                "message": f"成功获取项目列表，共 {total} 个项目",
            }
        else:
            return {"success": False, "data": {}, "message": "API响应格式异常"}

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取项目列表失败: {str(e)}"}


@mcp.tool()
async def get_my_projects(
    ctx: Context,
    page: int = 1,
    limit: int = 10,
) -> dict[str, Any]:
    """获取我参与的项目列表.

    获取当前用户作为项目成员参与的所有项目，包括用户担任的角色信息。
    返回项目的基本信息和用户在项目中的权限角色。

    Args:
        ctx: FastMCP 上下文
        page: 页码，默认为 1
        limit: 每页数量，默认为 10

    Returns:
        我参与的项目数据，包含分页信息和项目数组
    """
    try:
        result = await api_client.get("/projects/my", params={"page": page, "limit": limit})

        if "data" in result:
            projects_data = result["data"]
            total = result.get("total", 0)

            return {
                "success": True,
                "data": result,
                "message": f"成功获取我参与的项目列表，共 {total} 个项目",
            }
        else:
            return {"success": False, "data": {}, "message": "API响应格式异常"}

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取我参与的项目失败: {str(e)}"}


@mcp.tool()
async def get_my_projects_tree(ctx: Context) -> dict[str, Any]:
    """获取我参与项目的树状结构.

    获取我参与项目的树状结构视图，展示父子项目关系。

    Args:
        ctx: FastMCP 上下文

    Returns:
        项目树状结构数据
    """
    try:
        result = await api_client.get("/projects/my-tree")

        return {
            "success": True,
            "data": result,
            "message": "成功获取我的项目树状结构",
        }

    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取项目树状结构失败: {str(e)}"}
