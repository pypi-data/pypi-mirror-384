#!/bin/bash
# Timesheet MCP Server 一键安装脚本

set -e

echo "========================================="
echo "  Timesheet MCP Server 安装向导"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检测操作系统
OS=$(uname -s)
if [ "$OS" = "Darwin" ]; then
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
elif [ "$OS" = "Linux" ]; then
    CONFIG_DIR="$HOME/.config/Claude"
else
    echo -e "${RED}❌ 不支持的操作系统: $OS${NC}"
    exit 1
fi

# 检查 Python
echo "🔍 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 未安装${NC}"
    echo "请先安装 Python 3.10 或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"

# 检查 uvx
echo ""
echo "🔍 检查 uvx..."
if ! command -v uvx &> /dev/null; then
    echo -e "${YELLOW}⚠️  uvx 未安装，正在安装...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    if ! command -v uvx &> /dev/null; then
        echo -e "${RED}❌ uvx 安装失败${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ uvx 已安装${NC}"

# 检查 Claude Desktop
echo ""
echo "🔍 检查 Claude Desktop..."
if [ ! -d "$CONFIG_DIR" ]; then
    echo -e "${YELLOW}⚠️  Claude Desktop 配置目录不存在${NC}"
    echo "请先安装 Claude Desktop: https://claude.ai/download"
    read -p "是否继续安装（配置将在 Claude Desktop 安装后生效）？[y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    mkdir -p "$CONFIG_DIR"
fi

# 获取安装方式
echo ""
echo "📦 请选择安装方式："
echo "  1) 从本地目录安装（开发模式）"
echo "  2) 从 Git 仓库安装（推荐）"
echo "  3) 从 PyPI 安装（暂不可用）"
read -p "请选择 [1-3]: " INSTALL_METHOD

# 获取配置信息
echo ""
echo "🔧 配置信息："
read -p "API Base URL [http://127.0.0.1:8080/api]: " API_URL
API_URL=${API_URL:-http://127.0.0.1:8080/api}

read -p "JWT Token: " TOKEN
if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Token 不能为空${NC}"
    exit 1
fi

# 生成配置
CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

# 备份现有配置
if [ -f "$CONFIG_FILE" ]; then
    BACKUP_FILE="$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$CONFIG_FILE" "$BACKUP_FILE"
    echo -e "${GREEN}✅ 已备份现有配置到: $BACKUP_FILE${NC}"
fi

# 根据安装方式生成配置
case $INSTALL_METHOD in
    1)
        # 本地目录
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        cat > "$CONFIG_FILE" <<EOF
{
  "mcpServers": {
    "timesheet": {
      "command": "uvx",
      "args": [
        "--from", "$SCRIPT_DIR",
        "fastmcp", "run", "src/server.py"
      ],
      "env": {
        "TIMESHEET_API_BASE_URL": "$API_URL",
        "TIMESHEET_API_TOKEN": "$TOKEN"
      }
    }
  }
}
EOF
        ;;
    2)
        # Git 仓库
        read -p "Git 仓库 URL [https://g.ktvsky.com/yangyuezheng/ai-emp.git]: " GIT_URL
        GIT_URL=${GIT_URL:-https://g.ktvsky.com/yangyuezheng/ai-emp.git}

        read -p "分支名 [feature/mcp-server-v2-fastmcp]: " BRANCH
        BRANCH=${BRANCH:-feature/mcp-server-v2-fastmcp}

        cat > "$CONFIG_FILE" <<EOF
{
  "mcpServers": {
    "timesheet": {
      "command": "uvx",
      "args": [
        "--from", "git+${GIT_URL}@${BRANCH}#subdirectory=timesheet-mcp-server-v2",
        "fastmcp", "run", "src/server.py"
      ],
      "env": {
        "TIMESHEET_API_BASE_URL": "$API_URL",
        "TIMESHEET_API_TOKEN": "$TOKEN"
      }
    }
  }
}
EOF
        ;;
    3)
        echo -e "${YELLOW}PyPI 发布功能暂不可用${NC}"
        exit 1
        ;;
    *)
        echo -e "${RED}无效的选择${NC}"
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo -e "${GREEN}✅ 安装完成！${NC}"
echo "========================================="
echo ""
echo "📝 配置文件: $CONFIG_FILE"
echo ""
echo "🔄 下一步操作："
echo "  1. 重启 Claude Desktop"
echo "  2. 在对话中尝试："
echo "     '请帮我查询我的工时记录'"
echo ""
echo "📚 更多文档："
echo "  - 使用指南: $(dirname "${BASH_SOURCE[0]}")/docs/internal-distribution-guide.md"
echo "  - 测试指南: $(dirname "${BASH_SOURCE[0]}")/docs/testing-guide.md"
echo ""
echo "🆘 遇到问题？"
echo "  - 查看日志: $HOME/Library/Logs/Claude/ (macOS)"
echo "  - 运行测试: cd $(dirname "${BASH_SOURCE[0]}") && python3 test_tools.py"
echo ""
echo "🎉 祝使用愉快！"
