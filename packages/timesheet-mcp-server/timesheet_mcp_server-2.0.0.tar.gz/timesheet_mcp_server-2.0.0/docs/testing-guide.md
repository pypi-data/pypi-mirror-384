# MCP Server 测试指南

## 测试方式

MCP Server 可以通过多种方式进行测试，确保功能正常。

---

## 1. 使用 MCP Inspector 测试（推荐）

MCP Inspector 是官方提供的 MCP 测试工具，提供可视化界面。

### 安装

```bash
npx @modelcontextprotocol/inspector
```

### 使用方式

```bash
# 在项目目录下运行
cd /path/to/timesheet-mcp-server-v2

# 启动 Inspector
npx @modelcontextprotocol/inspector uvx --from . fastmcp run src/server.py
```

### 功能
- ✅ 可视化界面测试所有 tools
- ✅ 查看工具参数和返回值
- ✅ 实时查看服务器日志
- ✅ 测试不同参数组合

---

## 2. 使用 FastMCP 内置测试工具

FastMCP 提供了内置的测试客户端。

### 方式一：Python REPL 测试

```python
import asyncio
from fastmcp import FastMCP
from src.server import mcp

async def test_tool():
    # 创建测试上下文
    from fastmcp import Context
    ctx = Context()

    # 导入要测试的 tool
    from src.tools.time_entry.query import get_my_time_entries

    # 调用测试
    result = await get_my_time_entries(ctx, page=1, limit=5)
    print(result)

# 运行测试
asyncio.run(test_tool())
```

### 方式二：使用 FastMCP CLI

```bash
# 进入项目目录
cd /path/to/timesheet-mcp-server-v2

# 使用 fastmcp 命令行测试
uvx fastmcp dev src/server.py
```

---

## 3. 使用 Claude Desktop 测试

这是最真实的测试环境。

### 配置步骤

1. **编辑 Claude Desktop 配置**

```bash
# macOS
code ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Windows
code %APPDATA%/Claude/claude_desktop_config.json
```

2. **添加 MCP Server 配置**

```json
{
  "mcpServers": {
    "timesheet": {
      "command": "uvx",
      "args": [
        "--from", "/Users/vincentyang/Documents/Github/ai-emp/timesheet-mcp-server-v2",
        "fastmcp", "run", "src/server.py"
      ],
      "env": {
        "TIMESHEET_API_BASE_URL": "http://127.0.0.1:8080/api",
        "TIMESHEET_API_TOKEN": "your-jwt-token"
      }
    }
  }
}
```

3. **重启 Claude Desktop**

4. **测试命令示例**

在 Claude Desktop 中尝试：

```
请帮我查询我的工时记录
请列出所有项目
请查询用户"张三"的信息
请获取本周的工时统计
```

---

## 4. 单元测试（即将支持）

### 测试框架

项目使用 `pytest` + `pytest-asyncio` 进行单元测试。

### 运行测试

```bash
# 安装测试依赖
pip install -r requirements.txt

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_time_entry_tools.py

# 查看测试覆盖率
pytest --cov=src --cov-report=html
```

### 测试示例

```python
# tests/test_time_entry_tools.py
import pytest
from unittest.mock import AsyncMock, patch
from fastmcp import Context

@pytest.mark.asyncio
async def test_get_my_time_entries():
    """测试获取我的工时记录"""
    from src.tools.time_entry.query import get_my_time_entries

    # Mock API 响应
    with patch('src.client.api_client.get') as mock_get:
        mock_get.return_value = {
            "data": [
                {
                    "id": 1,
                    "work_date": "2025-10-17",
                    "hours": 8.0,
                    "work_content": "开发功能"
                }
            ],
            "total": 1
        }

        # 调用 tool
        ctx = Context()
        result = await get_my_time_entries(ctx, page=1, limit=10)

        # 验证结果
        assert result["success"] is True
        assert "data" in result
        mock_get.assert_called_once()
```

---

## 5. 集成测试

### 使用 Postman/Thunder Client

可以直接测试后端 API，确保 API 正常：

```bash
# 测试 API
curl -X GET "http://127.0.0.1:8080/api/time-entries/my?page=1&limit=10" \
  -H "Authorization: Bearer your-token"
```

---

## 6. 日志调试

### 启用调试日志

在 `.env` 文件中设置：

```env
MCP_LOG_LEVEL=DEBUG
DEBUG=true
```

### 查看日志

```bash
# 运行服务器并查看日志
uvx --from . fastmcp run src/server.py
```

日志会显示：
- Tool 调用记录
- API 请求详情
- 错误堆栈信息

---

## 测试清单

### 功能测试

- [ ] **工时记录查询**
  - [ ] get_my_time_entries - 分页、过滤测试
  - [ ] get_recent_time_entries - 限制数量测试

- [ ] **用户查询**
  - [ ] get_user_by_name - 模糊搜索测试
  - [ ] get_user_detail - ID 查询测试
  - [ ] get_user_time_entries - 时间范围过滤测试

- [ ] **项目查询**
  - [ ] get_projects - 关键词、业务线、类型过滤测试
  - [ ] get_my_projects - 我的项目列表测试
  - [ ] get_my_projects_tree - 树状结构测试
  - [ ] get_project_members - 成员列表测试
  - [ ] get_project_detail - 项目详情测试
  - [ ] get_project_time_plan - 工时计划测试
  - [ ] get_business_lines - 业务线列表测试

- [ ] **报表统计**
  - [ ] get_time_stats - 分组统计测试
  - [ ] get_time_entry_report - 工时报表测试
  - [ ] get_project_time_report - 项目报表测试
  - [ ] get_working_days - 工作日查询测试
  - [ ] get_time_entry_warnings - 预警信息测试

### 异常测试

- [ ] 无效的 Token
- [ ] API 超时
- [ ] 无效的参数
- [ ] 权限不足
- [ ] 网络错误

### 性能测试

- [ ] 大数据量查询（1000+ 条记录）
- [ ] 并发请求测试
- [ ] 响应时间测试（< 2s）

---

## 常见问题

### Q: 如何模拟 API 响应？

**A**: 使用 `unittest.mock` 或 `pytest-mock`：

```python
with patch('src.client.api_client.get') as mock_get:
    mock_get.return_value = {"data": [...]}
    result = await tool_function(ctx)
```

### Q: 如何测试错误处理？

**A**: Mock API 抛出异常：

```python
with patch('src.client.api_client.get') as mock_get:
    mock_get.side_effect = Exception("API Error")
    result = await tool_function(ctx)
    assert result["success"] is False
```

### Q: 如何查看 MCP 通信日志？

**A**: 设置环境变量：

```bash
export MCP_LOG_LEVEL=DEBUG
uvx --from . fastmcp run src/server.py
```

---

## 自动化测试

### CI/CD 集成

在 GitHub Actions 中添加：

```yaml
name: Test MCP Server

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 最佳实践

1. ✅ **每个 tool 至少有一个测试用例**
2. ✅ **测试正常流程和异常流程**
3. ✅ **使用 Mock 隔离外部依赖**
4. ✅ **保持测试覆盖率 ≥ 80%**
5. ✅ **在 CI/CD 中自动运行测试**

---

## 参考资料

- [FastMCP 官方文档](https://gofastmcp.com)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [pytest 文档](https://docs.pytest.org)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io)
