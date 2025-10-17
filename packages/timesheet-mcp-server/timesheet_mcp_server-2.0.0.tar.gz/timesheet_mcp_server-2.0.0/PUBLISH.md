# 发布到 PyPI 指南

## 📦 发布步骤

### 1. 获取 PyPI API Token

1. 访问 https://pypi.org/manage/account/token/
2. 点击 "Add API token"
3. 设置名称（如 "timesheet-mcp-server"）
4. 选择范围：
   - 如果是首次发布，选择 "Entire account"
   - 已存在项目则选择 "Project: timesheet-mcp-server"
5. 复制生成的 token（格式：`pypi-...`）

### 2. 配置 Token

**方式一：使用环境变量（推荐）**

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here
```

**方式二：创建 ~/.pypirc 文件**

```ini
[pypi]
  username = __token__
  password = pypi-your-token-here
```

### 3. 构建包

```bash
# 进入项目目录
cd /Users/vincentyang/Documents/Github/ai-emp/timesheet-mcp-server-v2

# 激活虚拟环境
source venv/bin/activate

# 清理旧构建（如果存在）
rm -rf dist/ build/ *.egg-info

# 构建新包
python -m build
```

这会在 `dist/` 目录生成两个文件：
- `timesheet_mcp_server-2.0.0.tar.gz` (源码分发)
- `timesheet_mcp_server-2.0.0-py3-none-any.whl` (wheel 包)

### 4. 检查包

```bash
twine check dist/*
```

应该看到：
```
Checking dist/timesheet_mcp_server-2.0.0-py3-none-any.whl: PASSED
Checking dist/timesheet_mcp_server-2.0.0.tar.gz: PASSED
```

### 5. 上传到 PyPI

**首次发布（建议先发布到 TestPyPI 测试）：**

```bash
# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 从 TestPyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ timesheet-mcp-server
```

**正式发布到 PyPI：**

```bash
# 使用环境变量
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here
twine upload dist/*

# 或直接指定
twine upload dist/* -u __token__ -p pypi-your-token-here
```

成功后会看到：
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading timesheet_mcp_server-2.0.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Uploading timesheet_mcp_server-2.0.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View at:
https://pypi.org/project/timesheet-mcp-server/2.0.0/
```

## 🎉 发布成功后

### 用户安装方式

**最简单（推荐）：**
```bash
uvx timesheet-mcp-server
```

**使用 pip：**
```bash
pip install timesheet-mcp-server
```

**从源码：**
```bash
pip install timesheet-mcp-server[dev]
```

### Claude Desktop 配置

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

## 🔄 发布新版本

### 1. 更新版本号

编辑 `pyproject.toml`：
```toml
version = "2.0.1"  # 或 2.1.0, 3.0.0
```

### 2. 更新 CHANGELOG

创建或更新 `CHANGELOG.md`：
```markdown
## [2.0.1] - 2025-10-17

### Fixed
- 修复了 XXX 问题

### Added
- 新增了 XXX 功能
```

### 3. 重新构建和发布

```bash
# 清理旧版本
rm -rf dist/ build/ *.egg-info

# 构建新版本
python -m build

# 检查
twine check dist/*

# 上传
twine upload dist/*
```

## 📊 包信息

访问以下链接查看包信息：
- PyPI 页面: https://pypi.org/project/timesheet-mcp-server/
- 下载统计: https://pypistats.org/packages/timesheet-mcp-server
- 文档: README.md 会自动显示在 PyPI 页面

## 🛠️ 故障排除

### 问题 1: 包名已存在

```
ERROR HTTPError: 403 Forbidden from https://upload.pypi.org/legacy/
The name 'timesheet-mcp-server' is too similar to an existing project
```

**解决**: 修改 `pyproject.toml` 中的 name，例如：
```toml
name = "timesheet-mcp-server-v2"
# 或
name = "your-org-timesheet-mcp"
```

### 问题 2: Token 无效

```
ERROR HTTPError: 403 Forbidden
Invalid or non-existent authentication information
```

**解决**:
1. 检查 token 是否正确（包含 `pypi-` 前缀）
2. 用户名必须是 `__token__`（双下划线）
3. 重新生成 token

### 问题 3: 文件已存在

```
ERROR HTTPError: 400 Bad Request
File already exists
```

**解决**:
1. 更新版本号
2. 不能重新上传相同版本

## 📋 发布前检查清单

- [ ] 版本号已更新（遵循语义化版本）
- [ ] README.md 内容完整
- [ ] LICENSE 文件存在
- [ ] requirements.txt 依赖完整
- [ ] 所有测试通过
- [ ] CHANGELOG.md 已更新
- [ ] Git tag 已创建：`git tag v2.0.0`
- [ ] PyPI token 已配置
- [ ] 包构建成功：`python -m build`
- [ ] 包检查通过：`twine check dist/*`

## 🚀 完整发布流程（自动化脚本）

创建 `scripts/publish.sh`：

```bash
#!/bin/bash
set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./scripts/publish.sh <version>"
    exit 1
fi

echo "📦 发布版本 $VERSION"

# 1. 更新版本号
sed -i '' "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

# 2. Git 提交
git add pyproject.toml
git commit -m "chore: bump version to $VERSION"
git tag "v$VERSION"

# 3. 清理构建
rm -rf dist/ build/ *.egg-info

# 4. 构建
python -m build

# 5. 检查
twine check dist/*

# 6. 上传（需要配置 TWINE_PASSWORD）
twine upload dist/*

# 7. 推送到 Git
git push origin main
git push origin "v$VERSION"

echo "✅ 发布完成！"
echo "📦 PyPI: https://pypi.org/project/timesheet-mcp-server/$VERSION/"
```

使用：
```bash
chmod +x scripts/publish.sh
./scripts/publish.sh 2.0.1
```

## 📝 维护最佳实践

1. **语义化版本**：
   - `2.0.0` → `2.0.1` - 修复 bug（patch）
   - `2.0.0` → `2.1.0` - 新功能（minor）
   - `2.0.0` → `3.0.0` - 破坏性更改（major）

2. **发布频率**：
   - Bug 修复：立即发布 patch 版本
   - 新功能：积累到一定程度发布 minor 版本
   - 破坏性更改：谨慎发布 major 版本

3. **版本支持**：
   - 最新版本：全力支持
   - 前一个 major 版本：安全更新
   - 更老版本：停止支持

4. **沟通**：
   - 在 GitHub Releases 发布说明
   - 更新文档
   - 通知用户（邮件/内部通知）
