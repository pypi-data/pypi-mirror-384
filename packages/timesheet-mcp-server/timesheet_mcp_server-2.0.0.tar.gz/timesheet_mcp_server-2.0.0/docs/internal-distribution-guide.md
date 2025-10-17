# MCP Server 内部分发指南

## 📦 概览

本文档介绍如何在团队内部分发和使用 Timesheet MCP Server V2。

---

## 🎯 适用人群

- 开发人员
- 项目经理
- 需要查询工时数据的团队成员

---

## 📋 前置要求

### 1. 软件要求

- **Claude Desktop** (最新版本)
  - macOS: 从 [claude.ai](https://claude.ai/download) 下载
  - Windows: 从 [claude.ai](https://claude.ai/download) 下载

- **Python 环境** (可选，使用 uvx 时不需要)
  - Python 3.10 或更高版本
  - 或者使用 uvx (推荐)

### 2. 获取访问权限

- **JWT Token**: 联系系统管理员获取工时管理系统的 JWT Token
- **代码访问**: 确保有权限访问项目仓库

---

## 🚀 快速开始

### 方式一：使用 uvx（推荐）⭐

这是最简单的方式，无需手动安装 Python 依赖。

#### 步骤 1: 获取代码

```bash
# 克隆仓库
git clone <repository-url>
cd ai-emp

# 切换到 MCP Server 分支
git checkout feature/mcp-server-v2-fastmcp

# 进入 MCP Server 目录
cd timesheet-mcp-server-v2
```

#### 步骤 2: 配置 Claude Desktop

1. **打开 Claude Desktop 配置文件**

   macOS:
   ```bash
   open ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   Windows:
   ```bash
   notepad %APPDATA%\Claude\claude_desktop_config.json
   ```

2. **添加 MCP Server 配置**

   ```json
   {
     "mcpServers": {
       "timesheet": {
         "command": "uvx",
         "args": [
           "--from", "/完整路径/到/ai-emp/timesheet-mcp-server-v2",
           "fastmcp", "run", "src/server.py"
         ],
         "env": {
           "TIMESHEET_API_BASE_URL": "http://127.0.0.1:8080/api",
           "TIMESHEET_API_TOKEN": "你的-jwt-token"
         }
       }
     }
   }
   ```

   **重要**:
   - 将 `/完整路径/到/ai-emp/timesheet-mcp-server-v2` 替换为实际的绝对路径
   - 将 `你的-jwt-token` 替换为你的实际 JWT Token
   - 如果后端 API 地址不同，修改 `TIMESHEET_API_BASE_URL`

#### 步骤 3: 重启 Claude Desktop

完全退出 Claude Desktop 并重新启动。

#### 步骤 4: 验证安装

在 Claude Desktop 中输入：

```
请帮我查询我的工时记录
```

如果看到工时数据返回，说明配置成功！

---

### 方式二：使用 Python 虚拟环境

如果你的环境不支持 uvx，可以使用传统的 Python 方式。

#### 步骤 1: 创建虚拟环境

```bash
cd /path/to/ai-emp/timesheet-mcp-server-v2

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 步骤 2: 配置 Claude Desktop

```json
{
  "mcpServers": {
    "timesheet": {
      "command": "/完整路径/到/venv/bin/python",
      "args": ["/完整路径/到/timesheet-mcp-server-v2/src/server.py"],
      "env": {
        "TIMESHEET_API_BASE_URL": "http://127.0.0.1:8080/api",
        "TIMESHEET_API_TOKEN": "你的-jwt-token"
      }
    }
  }
}
```

#### 步骤 3: 重启 Claude Desktop

---

## 🔑 获取 JWT Token

### 方法 1: 通过 Web 界面登录

1. 访问工时管理系统: `http://127.0.0.1:8080`
2. 登录你的账号
3. 打开浏览器开发者工具 (F12)
4. 查看请求头中的 `Authorization` 字段
5. 复制 `Bearer ` 后面的 token

### 方法 2: 联系管理员

如果无法自行获取，请联系系统管理员获取你的 JWT Token。

---

## 📖 可用功能

配置成功后，你可以在 Claude Desktop 中使用以下功能：

### 工时记录查询 (2个)
- 查询我的工时记录
- 查询最近的工时记录

### 用户查询 (3个)
- 根据用户名查询用户
- 获取用户详细信息
- 查询指定用户的工时记录

### 项目查询 (7个)
- 获取项目列表
- 获取我参与的项目
- 获取我的项目树状结构
- 获取项目成员
- 获取项目详情
- 获取项目工时计划
- 获取业务线列表

### 报表统计 (5个)
- 获取工时统计
- 工时统计报表
- 项目工时报表
- 获取工作日信息
- 获取工时预警

---

## 💬 使用示例

在 Claude Desktop 中，你可以用自然语言提问：

```
请帮我查询我的工时记录

请列出所有项目

请查询用户"张三"的信息

请获取本周的工时统计

请帮我查看项目ID为123的详细信息

请给我看看最近5天的工时记录

请统计一下本月的工作时长
```

Claude 会自动调用相应的 MCP Tools 来获取数据。

---

## 🔧 故障排除

### 问题 1: Claude Desktop 无法连接 MCP Server

**可能原因**:
- 路径配置错误
- Python 环境问题
- Token 无效

**解决方法**:
1. 检查配置文件中的路径是否为绝对路径
2. 确认 Python 或 uvx 可用：
   ```bash
   uvx --version  # 或 python3 --version
   ```
3. 验证 Token 是否有效
4. 查看 Claude Desktop 日志：
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`

### 问题 2: API 请求失败

**可能原因**:
- 后端服务未启动
- Token 过期
- 网络问题

**解决方法**:
1. 确认后端服务运行正常：
   ```bash
   curl http://127.0.0.1:8080/api/health
   ```
2. 重新获取 Token
3. 检查 `TIMESHEET_API_BASE_URL` 配置

### 问题 3: 工具调用无响应

**解决方法**:
1. 重启 Claude Desktop
2. 检查是否有防火墙或代理拦截
3. 查看 MCP Server 日志

---

## 🔄 更新 MCP Server

当 MCP Server 有新版本时：

### 使用 uvx 方式

```bash
cd /path/to/ai-emp
git pull origin feature/mcp-server-v2-fastmcp
# uvx 会自动使用最新代码，无需额外操作
```

### 使用 Python 虚拟环境方式

```bash
cd /path/to/ai-emp
git pull origin feature/mcp-server-v2-fastmcp

cd timesheet-mcp-server-v2
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt --upgrade
```

重启 Claude Desktop 以应用更新。

---

## 📊 监控和日志

### 启用调试日志

在 Claude Desktop 配置中添加日志级别：

```json
{
  "mcpServers": {
    "timesheet": {
      "command": "uvx",
      "args": ["--from", "/path/to/timesheet-mcp-server-v2", "fastmcp", "run", "src/server.py"],
      "env": {
        "TIMESHEET_API_BASE_URL": "http://127.0.0.1:8080/api",
        "TIMESHEET_API_TOKEN": "your-token",
        "MCP_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### 查看日志

日志会输出到 Claude Desktop 的日志目录：
- macOS: `~/Library/Logs/Claude/mcp-server-timesheet.log`
- Windows: `%APPDATA%\Claude\logs\mcp-server-timesheet.log`

---

## 🔐 安全注意事项

1. **保护 Token**
   - 不要在公共场所泄露你的 JWT Token
   - 不要将 Token 提交到版本控制系统
   - 定期更换 Token

2. **配置文件安全**
   - `claude_desktop_config.json` 包含敏感信息
   - 确保文件权限设置正确
   - macOS: `chmod 600 ~/Library/Application\ Support/Claude/claude_desktop_config.json`

3. **网络安全**
   - 确保只在可信网络环境使用
   - 如果远程访问，使用 VPN

---

## 📚 进一步学习

- [MCP Server 完整文档](../README.md)
- [测试指南](./testing-guide.md)
- [开发任务规划](../../docs/mcp-server-task-plan.md)
- [FastMCP 官方文档](https://gofastmcp.com)
- [MCP 协议规范](https://spec.modelcontextprotocol.io)

---

## 🆘 获取帮助

遇到问题？

1. **查看文档**: 先查看上述故障排除部分
2. **查看日志**: 检查 Claude Desktop 和 MCP Server 日志
3. **联系支持**:
   - 技术问题: 联系开发团队
   - Token 问题: 联系系统管理员
   - 功能建议: 在内部反馈渠道提出

---

## 📝 常见问题 (FAQ)

### Q1: 是否需要安装 Python？

**A**: 如果使用 uvx 方式（推荐），不需要手动安装 Python。uvx 会自动管理 Python 环境。

### Q2: Token 有效期多久？

**A**: Token 有效期由后端系统控制，通常为 24 小时。过期后需要重新获取。

### Q3: 可以同时连接多个 MCP Server 吗？

**A**: 可以！在 `claude_desktop_config.json` 中添加多个配置即可：

```json
{
  "mcpServers": {
    "timesheet": { ... },
    "other-server": { ... }
  }
}
```

### Q4: 如何知道 MCP Server 版本？

**A**: 在 Claude Desktop 中询问：
```
请执行健康检查
```

### Q5: 支持哪些操作系统？

**A**:
- ✅ macOS 10.15+
- ✅ Windows 10/11
- ✅ Linux (需要 Claude Desktop Linux 版本)

---

## 🎉 开始使用

现在你已经了解了如何安装和使用 Timesheet MCP Server V2！

1. ✅ 获取 JWT Token
2. ✅ 配置 Claude Desktop
3. ✅ 重启并测试
4. ✅ 开始用自然语言查询工时数据

祝你使用愉快！🚀

---

**版本**: 2.0.0
**最后更新**: 2025-10-17
**维护团队**: AI-EMP Development Team
