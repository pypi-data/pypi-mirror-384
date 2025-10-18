#!/bin/bash
# QCC Release Script
# 用于自动化发布流程

set -e

VERSION="0.4.0"
BRANCH="feature/v0.4.0-development"

echo "=================================="
echo "  QCC v$VERSION 发布脚本"
echo "=================================="

# 1. 检查工作目录是否干净
echo ""
echo "📝 检查 Git 状态..."
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ 工作目录不干净，请先提交所有更改"
    exit 1
fi
echo "✅ 工作目录干净"

# 2. 推送到远程
echo ""
echo "📤 推送到远程仓库..."
git push origin $BRANCH
echo "✅ 推送成功"

# 3. 合并到 main 分支
echo ""
echo "🔀 合并到 main 分支..."
git checkout main
git pull origin main
git merge $BRANCH --no-ff -m "Merge branch '$BRANCH' - Release v$VERSION"
git push origin main
echo "✅ 已合并到 main 并推送"

# 4. 创建 Git Tag
echo ""
echo "🏷️  创建 Git Tag v$VERSION..."
git tag -a "v$VERSION" -m "Release v$VERSION

🎉 主要功能：
- Anthropic 原生协议支持
- 双重认证策略
- 多 Endpoint 代理服务
- 智能负载均衡与故障转移

详见：docs/releases/v$VERSION.md"
git push origin "v$VERSION"
echo "✅ Tag 创建成功"

# 5. 创建 GitHub Release
echo ""
echo "📦 创建 GitHub Release..."
echo "请手动在 GitHub 上创建 Release，或使用 gh cli："
echo ""
echo "  gh release create v$VERSION \\"
echo "    --title \"QCC v$VERSION\" \\"
echo "    --notes-file docs/releases/v$VERSION.md"
echo ""

# 6. 构建 Python 包
echo ""
echo "🏗️  构建 Python 包..."
rm -rf dist/ build/ *.egg-info
python -m build
echo "✅ 构建完成"

# 7. 检查包
echo ""
echo "🔍 检查包..."
python -m twine check dist/*
echo "✅ 包检查通过"

# 8. 上传到 PyPI
echo ""
echo "📤 准备上传到 PyPI..."
echo "请确认以下信息："
echo "  - 版本号: $VERSION"
echo "  - 包文件: $(ls dist/)"
echo ""
read -p "是否继续上传到 PyPI? (y/N): " confirm

if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    echo ""
    echo "上传到 PyPI..."
    python -m twine upload dist/*
    echo "✅ 上传成功！"
    echo ""
    echo "🎉 发布完成！"
    echo ""
    echo "现在可以使用以下命令安装："
    echo "  uvx qcc"
    echo "  pip install qcc"
else
    echo ""
    echo "ℹ️  跳过 PyPI 上传"
    echo ""
    echo "手动上传命令："
    echo "  python -m twine upload dist/*"
fi

echo ""
echo "=================================="
echo "  发布流程完成"
echo "=================================="
