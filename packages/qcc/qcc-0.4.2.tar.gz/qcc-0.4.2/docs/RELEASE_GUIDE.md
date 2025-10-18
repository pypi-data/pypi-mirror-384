# QCC 发布指南

本文档说明如何发布 QCC 新版本到 GitHub 和 PyPI。

## 前置要求

### 1. 安装发布工具

```bash
# 安装构建工具
pip install build twine

# (可选) 安装 GitHub CLI
# Windows: winget install GitHub.cli
# Mac: brew install gh
```

### 2. 配置 PyPI 凭据

创建 `~/.pypirc` 文件：

```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # 你的 PyPI token

[testpypi]
username = __token__
password = pypi-AgENdGVzdC5weXBp...  # 测试用 token
```

或使用环境变量：

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmc...
```

## 发布流程

### 方法 1: 使用自动化脚本（推荐）

#### Windows

```bash
# 运行发布脚本
scripts\release_windows.bat
```

#### Linux/Mac

```bash
# 添加执行权限
chmod +x scripts/release.sh

# 运行发布脚本
./scripts/release.sh
```

脚本会自动完成以下步骤：
1. ✅ 检查 Git 状态
2. ✅ 推送到远程仓库
3. ✅ 合并到 main 分支
4. ✅ 创建 Git Tag
5. ✅ 提示创建 GitHub Release
6. ✅ 构建 Python 包
7. ✅ 检查包完整性
8. ✅ 上传到 PyPI

### 方法 2: 手动发布

#### 步骤 1: 推送代码

```bash
# 推送功能分支
git push origin feature/v0.4.0-development

# 合并到 main
git checkout main
git merge feature/v0.4.0-development
git push origin main
```

#### 步骤 2: 创建 Tag

```bash
# 创建标签
git tag -a v0.4.0 -m "Release v0.4.0 - Anthropic Protocol Support"

# 推送标签
git push origin v0.4.0
```

#### 步骤 3: 创建 GitHub Release

##### 使用 GitHub CLI

```bash
gh release create v0.4.0 \
  --title "QCC v0.4.0" \
  --notes-file docs/releases/v0.4.0.md
```

##### 使用 Web 界面

1. 访问 https://github.com/yxhpy/qcc/releases/new
2. 选择标签: `v0.4.0`
3. 标题: `QCC v0.4.0`
4. 描述: 复制 `docs/releases/v0.4.0.md` 的内容
5. 点击 "Publish release"

#### 步骤 4: 构建包

```bash
# 清理旧构建
rm -rf dist/ build/ *.egg-info

# 构建包
python -m build
```

#### 步骤 5: 检查包

```bash
# 检查包完整性
python -m twine check dist/*
```

#### 步骤 6: 上传到 PyPI

##### 先上传到 TestPyPI 测试

```bash
python -m twine upload --repository testpypi dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ qcc==0.4.0
```

##### 上传到正式 PyPI

```bash
python -m twine upload dist/*
```

#### 步骤 7: 验证发布

```bash
# 等待几分钟后测试
uvx qcc --version

# 或
pip install qcc
qcc --version
```

## 发布检查清单

### 发布前

- [ ] 所有测试通过
- [ ] 版本号已更新（`fastcc/__init__.py`）
- [ ] Release Notes 已编写（`docs/releases/v0.4.0.md`）
- [ ] CHANGELOG 已更新
- [ ] 文档已更新
- [ ] 所有更改已提交

### 发布中

- [ ] 代码已推送到远程
- [ ] Tag 已创建并推送
- [ ] GitHub Release 已创建
- [ ] PyPI 包已构建
- [ ] PyPI 包已检查
- [ ] 包已上传到 PyPI

### 发布后

- [ ] 验证 `uvx qcc` 可以安装
- [ ] 验证 `pip install qcc` 可以安装
- [ ] 版本号正确
- [ ] 功能正常工作
- [ ] 文档链接有效
- [ ] Release 公告已发布

## 常见问题

### 1. 推送失败（网络问题）

```bash
# 使用代理
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 或使用 SSH
git remote set-url origin git@github.com:yxhpy/qcc.git
```

### 2. PyPI 上传失败

```bash
# 检查凭据
python -m twine upload --verbose dist/*

# 使用 token 而不是密码
# 在 PyPI 设置中生成 API token
```

### 3. 版本已存在

```bash
# 删除远程 tag
git push origin :refs/tags/v0.4.0

# 删除本地 tag
git tag -d v0.4.0

# 重新创建
git tag -a v0.4.0 -m "Release v0.4.0"
git push origin v0.4.0
```

### 4. 构建失败

```bash
# 更新构建工具
pip install --upgrade build setuptools wheel

# 清理缓存
rm -rf dist/ build/ *.egg-info __pycache__/
```

## 版本号规范

QCC 使用 [语义化版本](https://semver.org/lang/zh-CN/)：

- **主版本号（Major）**：不兼容的 API 修改
- **次版本号（Minor）**：向下兼容的功能性新增
- **修订号（Patch）**：向下兼容的问题修正

示例：
- `0.4.0` - 新功能发布
- `0.4.1` - Bug 修复
- `1.0.0` - 第一个稳定版本

## 发布节奏

- **主要版本（Major）**：重大架构变更
- **次要版本（Minor）**：每 1-2 月，新功能完成时
- **修订版本（Patch）**：根据需要，Bug 修复

## 回滚发布

如果发现发布有严重问题：

### 1. 删除 PyPI 版本

无法直接删除，但可以：
- 立即发布修复版本（如 0.4.1）
- 在 PyPI 上标记为 "yanked"（不推荐安装）

### 2. 删除 GitHub Release

```bash
# 使用 gh cli
gh release delete v0.4.0

# 或在 Web 界面删除
```

### 3. 删除 Git Tag

```bash
# 删除本地 tag
git tag -d v0.4.0

# 删除远程 tag
git push origin :refs/tags/v0.4.0
```

## 发布后任务

1. **公告发布**
   - 在 GitHub Discussions 发布公告
   - 更新项目 README
   - 社交媒体分享

2. **监控反馈**
   - 关注 GitHub Issues
   - 检查错误报告
   - 收集用户反馈

3. **准备下一版本**
   - 创建下一版本的里程碑
   - 规划新功能
   - 更新开发分支

## 相关资源

- **PyPI 文档**: https://packaging.python.org/
- **GitHub Releases**: https://docs.github.com/en/repositories/releasing-projects-on-github
- **语义化版本**: https://semver.org/lang/zh-CN/
- **Twine 文档**: https://twine.readthedocs.io/

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
