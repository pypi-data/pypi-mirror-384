# MCP Server 部署和分发方案

本文档介绍多种便捷的部署方式，让团队成员无需直接接触源代码即可使用 MCP Server。

---

## 🚀 方案对比

| 方案 | 难度 | 用户体验 | 适用场景 |
|------|------|----------|----------|
| **PyPI 公开发布** | 中 | ⭐⭐⭐⭐⭐ | 开源项目 |
| **私有 PyPI 服务器** | 高 | ⭐⭐⭐⭐⭐ | 企业内部 |
| **Git 私有仓库** | 低 | ⭐⭐⭐⭐ | 有 Git 权限的团队 |
| **Docker 镜像** | 中 | ⭐⭐⭐⭐ | 容器化环境 |
| **安装脚本** | 低 | ⭐⭐⭐ | 快速部署 |

---

## 📦 方案一：发布到 PyPI（推荐）

### 优势
- ✅ 用户一行命令安装：`uvx timesheet-mcp-server`
- ✅ 自动版本管理和更新
- ✅ 无需 Git 权限
- ✅ 标准化的 Python 包管理

### 发布步骤

#### 1. 准备发布

确保 `pyproject.toml` 配置完整：

```toml
[project]
name = "timesheet-mcp-server"
version = "2.0.0"
description = "工时管理系统 MCP Server - 基于 FastMCP 2.0"
authors = [{name = "Your Team", email = "team@example.com"}]
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
keywords = ["mcp", "timesheet", "fastmcp"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "fastmcp>=2.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
]

[project.urls]
Homepage = "https://github.com/your-org/timesheet-mcp-server"
Documentation = "https://github.com/your-org/timesheet-mcp-server#readme"
Repository = "https://github.com/your-org/timesheet-mcp-server"

[project.scripts]
timesheet-mcp = "src.server:main"
```

#### 2. 构建包

```bash
# 安装构建工具
pip install build twine

# 构建发行包
python -m build
```

这会在 `dist/` 目录生成：
- `timesheet-mcp-server-2.0.0.tar.gz`
- `timesheet_mcp_server-2.0.0-py3-none-any.whl`

#### 3. 发布到 PyPI

```bash
# 检查包
twine check dist/*

# 发布到 PyPI（需要 PyPI 账号）
twine upload dist/*
```

#### 4. 用户安装（发布后）

用户只需：

```bash
# 使用 uvx（推荐）
uvx timesheet-mcp-server

# 或使用 pip
pip install timesheet-mcp-server
```

**Claude Desktop 配置**：

```json
{
  "mcpServers": {
    "timesheet": {
      "command": "uvx",
      "args": ["timesheet-mcp-server"],
      "env": {
        "TIMESHEET_API_BASE_URL": "http://127.0.0.1:8080/api",
        "TIMESHEET_API_TOKEN": "your-jwt-token"
      }
    }
  }
}
```

---

## 🏢 方案二：私有 PyPI 服务器（企业内部）

### 使用 DevPI

DevPI 是一个轻量级的私有 PyPI 服务器。

#### 1. 搭建 DevPI 服务器

```bash
# 安装 devpi
pip install devpi-server devpi-web

# 初始化
devpi-init

# 启动服务器
devpi-server --start --host 0.0.0.0 --port 3141
```

#### 2. 配置和上传

```bash
# 配置客户端
devpi use http://your-devpi-server:3141

# 登录
devpi login root --password=<password>

# 创建索引
devpi index -c dev

# 上传包
devpi upload
```

#### 3. 用户安装

```bash
# 从私有 PyPI 安装
pip install timesheet-mcp-server --index-url http://your-devpi-server:3141/root/dev/+simple/

# 或配置 uvx
uvx --index-url http://your-devpi-server:3141/root/dev/+simple/ timesheet-mcp-server
```

---

## 🔐 方案三：Git 私有仓库 + uvx

### 优势
- ✅ 利用现有 Git 权限控制
- ✅ 无需额外基础设施
- ✅ 支持 uvx 直接安装

### 用户安装

```bash
# 从 Git 仓库安装（需要访问权限）
uvx --from git+https://github.com/your-org/ai-emp.git#subdirectory=timesheet-mcp-server-v2 timesheet-mcp-server
```

**Claude Desktop 配置**：

```json
{
  "mcpServers": {
    "timesheet": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/your-org/ai-emp.git#subdirectory=timesheet-mcp-server-v2",
        "fastmcp",
        "run",
        "src/server.py"
      ],
      "env": {
        "TIMESHEET_API_BASE_URL": "http://127.0.0.1:8080/api",
        "TIMESHEET_API_TOKEN": "your-jwt-token"
      }
    }
  }
}
```

---

## 🐳 方案四：Docker 镜像

### 创建 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt pyproject.toml ./
COPY src ./src
COPY config ./config

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露健康检查端点
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# 运行服务器
ENTRYPOINT ["python", "-m", "src.server"]
```

### 构建和发布

```bash
# 构建镜像
docker build -t your-registry/timesheet-mcp-server:2.0.0 .

# 推送到私有镜像仓库
docker push your-registry/timesheet-mcp-server:2.0.0
```

### 用户使用

```bash
# 拉取镜像
docker pull your-registry/timesheet-mcp-server:2.0.0

# 运行
docker run -it \
  -e TIMESHEET_API_BASE_URL=http://127.0.0.1:8080/api \
  -e TIMESHEET_API_TOKEN=your-token \
  your-registry/timesheet-mcp-server:2.0.0
```

---

## 📜 方案五：一键安装脚本

创建自动化安装脚本，让用户无需手动操作。

### 创建安装脚本

```bash
#!/bin/bash
# install.sh

set -e

echo "🚀 开始安装 Timesheet MCP Server..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装，请先安装 Python 3.10+"
    exit 1
fi

# 检查 uvx
if ! command -v uvx &> /dev/null; then
    echo "📦 安装 uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# 安装 MCP Server
echo "📦 安装 Timesheet MCP Server..."
uvx --from git+https://github.com/your-org/ai-emp.git#subdirectory=timesheet-mcp-server-v2 fastmcp install

# 获取配置信息
echo ""
echo "🔧 请提供配置信息："
read -p "API Base URL (默认: http://127.0.0.1:8080/api): " API_URL
API_URL=${API_URL:-http://127.0.0.1:8080/api}

read -p "JWT Token: " TOKEN

# 创建配置文件
CONFIG_DIR="$HOME/Library/Application Support/Claude"
CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

mkdir -p "$CONFIG_DIR"

# 生成配置
cat > "$CONFIG_FILE" <<EOF
{
  "mcpServers": {
    "timesheet": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/your-org/ai-emp.git#subdirectory=timesheet-mcp-server-v2",
        "fastmcp",
        "run",
        "src/server.py"
      ],
      "env": {
        "TIMESHEET_API_BASE_URL": "$API_URL",
        "TIMESHEET_API_TOKEN": "$TOKEN"
      }
    }
  }
}
EOF

echo ""
echo "✅ 安装完成！"
echo ""
echo "📝 配置文件已保存到: $CONFIG_FILE"
echo "🔄 请重启 Claude Desktop 以应用配置"
echo ""
echo "🎉 安装成功！现在可以在 Claude Desktop 中使用工时查询功能了！"
```

### 用户一键安装

```bash
# 下载并运行安装脚本
curl -fsSL https://your-server.com/install.sh | bash
```

---

## 🌐 方案六：发布到内部网站

创建一个简单的内部网站，提供下载和文档。

### 目录结构

```
internal-site/
├── index.html              # 主页
├── downloads/
│   ├── timesheet-mcp-server-2.0.0.tar.gz
│   └── install.sh
└── docs/
    ├── quick-start.html
    └── faq.html
```

### 用户访问

1. 访问 `http://internal-site.company.com`
2. 下载安装包或运行安装脚本
3. 按照页面指引配置

---

## 📋 推荐方案

根据不同场景的推荐：

### 1. 内部小团队（< 20人）
**推荐：Git 私有仓库 + uvx**
- 简单快速
- 利用现有权限
- 无需额外设施

### 2. 企业内部（> 20人）
**推荐：私有 PyPI 服务器（DevPI）**
- 专业的包管理
- 版本控制清晰
- 安装体验好

### 3. 开源项目
**推荐：公开 PyPI**
- 最大化易用性
- 社区标准
- 自动版本管理

### 4. 快速验证
**推荐：一键安装脚本**
- 零门槛
- 自动化配置
- 适合演示

---

## 🔄 版本更新策略

### 自动更新检查

在 `src/server.py` 添加版本检查：

```python
import httpx
from packaging import version

CURRENT_VERSION = "2.0.0"
VERSION_CHECK_URL = "https://your-server.com/api/version"

async def check_update():
    """检查是否有新版本"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(VERSION_CHECK_URL)
            latest = resp.json()["version"]
            if version.parse(latest) > version.parse(CURRENT_VERSION):
                logger.warning(
                    f"🔔 发现新版本 {latest}，当前版本 {CURRENT_VERSION}\n"
                    f"更新命令: uvx --upgrade timesheet-mcp-server"
                )
    except Exception:
        pass
```

### 发布新版本

```bash
# 1. 更新版本号
# 编辑 pyproject.toml 中的 version

# 2. 重新构建
python -m build

# 3. 发布
twine upload dist/*

# 4. 通知用户
# 发送邮件或内部通知
```

---

## 📊 监控和统计

### 使用分析

创建简单的使用统计：

```python
# src/analytics.py
import httpx
from datetime import datetime

async def track_usage(tool_name: str):
    """跟踪工具使用情况"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://your-analytics.com/api/track",
                json={
                    "tool": tool_name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "2.0.0"
                }
            )
    except Exception:
        pass  # 不影响主功能
```

---

## 🆘 用户支持

### 内部支持渠道

1. **文档中心**：`http://internal-docs.company.com/mcp-server`
2. **问题追踪**：内部 Issue 系统
3. **实时支持**：企业 IM（钉钉/飞书/企业微信）
4. **FAQ 页面**：常见问题解答

---

## ✅ 最佳实践

1. **语义化版本**：遵循 semver（主版本.次版本.修订版）
2. **变更日志**：维护 CHANGELOG.md
3. **向后兼容**：尽量不破坏现有配置
4. **清晰文档**：每个发布版本都有文档
5. **快速修复**：关键 bug 快速发布补丁版本

---

## 📝 总结

选择合适的发布方式：

- **快速开始**: 使用 Git 仓库 + uvx
- **长期运营**: 搭建私有 PyPI 服务器
- **最佳体验**: 发布到公开 PyPI
- **临时演示**: 使用一键安装脚本

无论选择哪种方式，都要确保：
✅ 用户安装简单
✅ 配置清晰明了
✅ 更新方便快捷
✅ 问题及时响应
