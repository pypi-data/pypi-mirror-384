# QCC v0.4.0 发布步骤（手动）

由于网络连接问题，请按以下步骤手动完成发布：

## ✅ 已完成

- [x] 代码开发完成
- [x] 所有测试通过
- [x] 版本号更新为 0.4.0
- [x] Release Notes 编写完成
- [x] 代码已提交到本地仓库

## 📋 待执行步骤

### 步骤 1: 推送代码到 GitHub

等待网络恢复后执行：

```bash
# 推送功能分支
git push origin feature/v0.4.0-development

# 如果推送失败，尝试使用代理或 SSH
```

### 步骤 2: 合并到 main 分支

```bash
# 切换到 main 分支
git checkout main

# 拉取最新代码
git pull origin main

# 合并功能分支
git merge feature/v0.4.0-development --no-ff -m "Merge feature/v0.4.0-development - Release v0.4.0"

# 推送 main 分支
git push origin main
```

### 步骤 3: 创建 Git Tag

```bash
# 创建标签
git tag -a v0.4.0 -m "Release v0.4.0

🎉 主要功能：
- Anthropic 原生协议支持
- 双重认证策略
- 多 Endpoint 代理服务
- 智能负载均衡与故障转移

详见：docs/releases/v0.4.0.md"

# 推送标签
git push origin v0.4.0
```

### 步骤 4: 创建 GitHub Release

#### 方法 A: 使用 GitHub Web 界面（推荐）

1. 访问：https://github.com/yxhpy/qcc/releases/new
2. 选择标签：`v0.4.0`
3. Release 标题：`QCC v0.4.0 - Anthropic 协议支持`
4. 描述：复制 `docs/releases/v0.4.0.md` 的内容
5. 点击 "Publish release"

#### 方法 B: 使用 GitHub CLI（如果已安装）

```bash
gh release create v0.4.0 \
  --title "QCC v0.4.0 - Anthropic 协议支持" \
  --notes-file docs/releases/v0.4.0.md
```

### 步骤 5: 构建 Python 包

```bash
# 清理旧构建
rm -rf dist/ build/ *.egg-info
# Windows: rmdir /s /q dist build

# 构建包
python -m build
```

### 步骤 6: 检查包

```bash
# 检查包完整性
python -m twine check dist/*
```

预期输出：
```
Checking dist/qcc-0.4.0-py3-none-any.whl: PASSED
Checking dist/qcc-0.4.0.tar.gz: PASSED
```

### 步骤 7: 上传到 TestPyPI（可选，测试用）

```bash
python -m twine upload --repository testpypi dist/*
```

测试安装：
```bash
pip install --index-url https://test.pypi.org/simple/ qcc==0.4.0
```

### 步骤 8: 上传到正式 PyPI

```bash
python -m twine upload dist/*
```

需要输入：
- Username: `__token__`
- Password: 你的 PyPI API token

或者使用环境变量：
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmc...

python -m twine upload dist/*
```

### 步骤 9: 验证发布

等待 5-10 分钟后：

```bash
# 测试 uvx 安装
uvx qcc --version

# 测试 pip 安装
pip install qcc
qcc --version
```

预期输出：
```
qcc version 0.4.0
```

## 🔍 验证清单

发布完成后，验证以下项目：

- [ ] GitHub 仓库显示最新提交
- [ ] GitHub Releases 页面显示 v0.4.0
- [ ] PyPI 页面显示 v0.4.0：https://pypi.org/project/qcc/
- [ ] `uvx qcc --version` 返回 0.4.0
- [ ] `pip install qcc` 可以正常安装
- [ ] 代理功能正常工作

## 🐛 故障排除

### 问题 1: 推送失败（网络）

**症状：** `fatal: unable to access 'https://github.com/...'`

**解决方案：**
```bash
# 方法 1: 使用代理
git config --global http.proxy http://127.0.0.1:7890

# 方法 2: 使用 SSH
git remote set-url origin git@github.com:yxhpy/qcc.git
git push origin feature/v0.4.0-development
```

### 问题 2: PyPI 上传失败

**症状：** `403 Forbidden` 或 `Invalid credentials`

**解决方案：**
1. 检查 PyPI token 是否正确
2. 确保 token 有上传权限
3. 生成新的 API token：https://pypi.org/manage/account/token/

### 问题 3: 版本已存在

**症状：** `File already exists`

**解决方案：**
版本号无法重复，需要使用新版本号（如 0.4.1）

### 问题 4: 构建失败

**症状：** `ModuleNotFoundError: No module named 'build'`

**解决方案：**
```bash
pip install --upgrade build setuptools wheel
```

## 📞 需要帮助？

- **文档：** [docs/RELEASE_GUIDE.md](docs/RELEASE_GUIDE.md)
- **Issues：** https://github.com/yxhpy/qcc/issues
- **PyPI 帮助：** https://packaging.python.org/

## ✅ 完成后

发布成功后：

1. 更新 README.md 中的版本号和徽章
2. 在 Discussions 发布公告
3. 关注用户反馈和 Issues
4. 准备下一版本的开发

---

**当前状态：** 等待网络恢复后推送到 GitHub

**下一步：** 执行步骤 1 - 推送代码到 GitHub

🤖 Generated with [Claude Code](https://claude.com/claude-code)
