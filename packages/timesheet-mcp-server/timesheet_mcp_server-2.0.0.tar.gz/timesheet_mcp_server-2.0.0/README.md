# Timesheet MCP Server V2

基于 FastMCP 2.0 框架构建的工时管理系统 MCP Server。

## 特性

- 🚀 使用 FastMCP 2.0 框架，性能优异
- 📡 支持 stdio 传输方式（默认）
- 🔐 JWT Token 认证
- 📊 完整的工时管理功能
- ✅ 完善的单元测试
- 📖 详细的文档

## 快速开始

### 方式一：使用 uvx（推荐）⭐

```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 API URL 和 Token

# 直接运行（uvx 会自动安装依赖）
uvx --from . fastmcp run src/server.py
```

### 方式二：使用 uv

```bash
# 安装依赖
uv pip install -r requirements.txt

# 运行服务器
uv run src/server.py
```

### 方式三：传统 pip 方式

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行服务器
python src/server.py
```

### 配置环境变量

编辑 `.env` 文件：

```env
# API 配置
TIMESHEET_API_BASE_URL=http://127.0.0.1:8080/api
TIMESHEET_API_TOKEN=your-jwt-token-here

# MCP 配置
MCP_TRANSPORT=stdio
MCP_LOG_LEVEL=INFO

# 功能开关
ENABLE_CACHE=true
CACHE_TTL=300
```

### 在 Claude Desktop 中使用

#### 使用 uvx（推荐）

```json
{
  "mcpServers": {
    "timesheet": {
      "command": "uvx",
      "args": [
        "--from", "/path/to/timesheet-mcp-server-v2",
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

#### 使用 Python（传统方式）

```json
{
  "mcpServers": {
    "timesheet": {
      "command": "python",
      "args": ["/path/to/timesheet-mcp-server-v2/src/server.py"],
      "env": {
        "TIMESHEET_API_BASE_URL": "http://127.0.0.1:8080/api",
        "TIMESHEET_API_TOKEN": "your-jwt-token"
      }
    }
  }
}
```

## 可用 Tools

### 工时记录管理
- `create_time_entry` - 创建工时记录
- `update_time_entry` - 更新工时记录
- `delete_time_entry` - 删除工时记录
- `submit_time_entry` - 提交工时记录审批
- `batch_create_time_entries` - 批量创建工时记录
- `get_my_time_entries` - 获取我的工时记录
- `get_recent_time_entries` - 获取最近工时记录

### 用户查询
- `get_user_by_name` - 根据用户名查询用户
- `get_user_time_entries` - 查询指定用户工时记录

### 审批管理
- `get_pending_approvals` - 获取待我审批的工时
- `approve_time_entry` - 审批通过工时记录
- `reject_time_entry` - 拒绝工时记录
- `batch_approve_time_entries` - 批量审批工时
- `get_my_approval_history` - 获取我的审批历史

### 项目管理
- `get_projects` - 获取项目列表
- `get_my_projects` - 获取我参与的项目
- `get_project_detail` - 获取项目详情
- `get_my_projects_tree` - 获取我的项目树
- `get_project_members` - 获取项目成员
- `get_project_time_plan` - 获取项目工时计划
- `get_business_lines` - 获取业务线列表

### 通知管理
- `get_my_notifications` - 获取我的通知
- `get_unread_notification_count` - 获取未读通知数量
- `mark_notification_read` - 标记通知为已读

### 报表统计
- `get_time_stats` - 获取工时统计
- `get_time_entry_report` - 获取工时统计报表
- `get_project_time_report` - 获取项目工时报表
- `get_working_days` - 获取工作日信息

## 项目结构

```
timesheet-mcp-server-v2/
├── README.md                    # 项目说明
├── pyproject.toml              # 项目配置
├── requirements.txt            # 依赖列表
├── .env.example                # 环境变量示例
├── .env                        # 环境变量配置（不提交）
├── .gitignore                  # Git 忽略文件
├── config/
│   └── settings.py             # 配置管理
├── src/
│   ├── __init__.py
│   ├── server.py               # FastMCP 服务器主文件
│   ├── client.py               # API 客户端封装
│   ├── auth.py                 # 认证管理
│   ├── models.py               # 数据模型
│   ├── utils.py                # 工具函数
│   └── tools/                  # MCP Tools
│       ├── __init__.py
│       ├── time_entry/         # 工时记录相关
│       ├── user/               # 用户相关
│       ├── approval/           # 审批相关
│       ├── project/            # 项目相关
│       ├── notification/       # 通知相关
│       └── report/             # 报表相关
├── tests/                      # 测试文件
│   ├── __init__.py
│   ├── conftest.py
│   └── test_*.py
└── docs/                       # 文档
    ├── api.md
    ├── configuration.md
    └── development.md
```

## 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_time_entry_tools.py

# 查看测试覆盖率
pytest --cov=src --cov-report=html
```

### 代码规范

项目使用以下工具保证代码质量：

- `black` - 代码格式化
- `isort` - import 排序
- `flake8` - 代码检查
- `mypy` - 类型检查

```bash
# 格式化代码
black src tests

# 排序 imports
isort src tests

# 代码检查
flake8 src tests

# 类型检查
mypy src
```

## 文档

详细文档请查看 `docs/` 目录：

- [API 文档](docs/api.md) - 所有 tools 的详细说明
- [配置文档](docs/configuration.md) - 环境变量和配置项说明
- [开发文档](docs/development.md) - 架构设计和开发指南

## 许可证

MIT License
