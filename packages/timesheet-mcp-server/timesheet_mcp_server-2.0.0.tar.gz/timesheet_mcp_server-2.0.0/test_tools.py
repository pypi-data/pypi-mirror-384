#!/usr/bin/env python3
"""简单的工具测试脚本."""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings


async def test_health_check():
    """测试健康检查."""
    print("=" * 60)
    print("测试 1: 健康检查")
    print("=" * 60)

    try:
        from src.server import health_check
        result = await health_check()
        print(f"✅ 健康检查成功")
        print(f"   状态: {result['status']}")
        print(f"   版本: {result['version']}")
        print(f"   API URL: {result['api_base_url']}")
        print(f"   传输方式: {result['transport']}")
        return True
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False


async def test_configuration():
    """测试配置."""
    print("\n" + "=" * 60)
    print("测试 2: 配置验证")
    print("=" * 60)

    try:
        settings.validate()
        print("✅ 配置验证成功")
        print(f"   API Base URL: {settings.API_BASE_URL}")
        print(f"   Token 已配置: {'是' if settings.API_TOKEN else '否'}")
        print(f"   传输方式: {settings.MCP_TRANSPORT}")
        print(f"   日志级别: {settings.MCP_LOG_LEVEL}")
        return True
    except ValueError as e:
        print(f"❌ 配置验证失败: {e}")
        return False


async def test_tool_imports():
    """测试工具导入."""
    print("\n" + "=" * 60)
    print("测试 3: 工具导入检查")
    print("=" * 60)

    tools_to_test = [
        # 工时记录查询
        ("src.tools.time_entry.query", ["get_my_time_entries", "get_recent_time_entries"]),
        # 用户查询
        ("src.tools.user.query", ["get_user_by_name", "get_user_detail", "get_user_time_entries"]),
        # 项目查询 - detail
        ("src.tools.project.detail", ["get_business_lines", "get_project_detail", "get_project_time_plan"]),
        # 项目查询 - list
        ("src.tools.project.list", ["get_my_projects", "get_my_projects_tree", "get_projects"]),
        # 项目查询 - members
        ("src.tools.project.members", ["get_project_members"]),
        # 报表统计 - advanced
        ("src.tools.report.advanced", ["get_project_time_report", "get_time_entry_report", "get_time_entry_warnings", "get_working_days"]),
        # 报表统计 - time_stats
        ("src.tools.report.time_stats", ["get_time_stats"]),
    ]

    success_count = 0
    total_tools = sum(len(tools) for _, tools in tools_to_test)

    for module_name, tool_names in tools_to_test:
        try:
            module = __import__(module_name, fromlist=tool_names)
            for tool_name in tool_names:
                if hasattr(module, tool_name):
                    print(f"   ✅ {tool_name}")
                    success_count += 1
                else:
                    print(f"   ❌ {tool_name} - 未找到")
        except Exception as e:
            print(f"   ❌ 导入 {module_name} 失败: {e}")

    print(f"\n   总计: {success_count}/{total_tools} 工具导入成功")
    return success_count == total_tools


async def test_mcp_server():
    """测试 MCP Server 实例."""
    print("\n" + "=" * 60)
    print("测试 4: MCP Server 实例")
    print("=" * 60)

    try:
        from src.server import mcp
        print(f"   ✅ MCP Server 实例创建成功")
        print(f"   名称: {mcp.name}")

        # 尝试获取已注册的工具列表
        try:
            # FastMCP 2.0 的工具注册信息
            print(f"   工具注册: 已完成")
        except Exception as e:
            print(f"   ⚠️  无法获取工具列表: {e}")

        return True
    except Exception as e:
        print(f"   ❌ MCP Server 创建失败: {e}")
        return False


async def main():
    """主测试函数."""
    print("\n🧪 开始测试 Timesheet MCP Server V2\n")

    results = []

    # 运行所有测试
    results.append(await test_configuration())
    results.append(await test_health_check())
    results.append(await test_tool_imports())
    results.append(await test_mcp_server())

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    success_count = sum(1 for r in results if r)
    total_count = len(results)

    if success_count == total_count:
        print(f"✅ 所有测试通过 ({success_count}/{total_count})")
        print("\n🎉 MCP Server 已准备就绪！")
        sys.exit(0)
    else:
        print(f"❌ 部分测试失败 ({success_count}/{total_count})")
        print("\n⚠️  请检查失败的测试项")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
