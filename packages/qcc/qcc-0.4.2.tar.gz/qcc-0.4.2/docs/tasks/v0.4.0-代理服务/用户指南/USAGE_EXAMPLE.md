# 终端UI升级说明

## 新功能特性

### 1. 交互式命令升级
- ✅ `qcc default` - 交互式设置默认配置
- ✅ `qcc remove` - 交互式删除配置
- ✅ `qcc use` - 交互式选择并启动配置
- ✅ 向下兼容：依然支持 `qcc use <配置名>` 的直接调用方式

### 2. 交互式选择界面
- ✅ 支持 ↑↓ 箭头键导航
- ✅ 实时高亮当前选中项
- ✅ 智能倒计时：用户交互后自动停止计时
- ✅ 跨平台兼容：Windows, macOS, Linux
- ✅ 错误回退：如果新UI无法启动，自动使用简化模式

### 2. 增强的视觉效果
- 使用 `rich` 库提供彩色输出和更好的格式化
- 改进的加载动画和状态提示
- 更清晰的界面布局

### 3. 使用方式

#### 交互式命令使用
```bash
# 本地开发测试
uvx --from . qcc default                # 交互式选择默认配置
uvx --from . qcc remove                 # 交互式删除配置
uvx --from . qcc use                    # 交互式选择并启动配置
uvx --from . qcc default <配置名>       # 传统方式（依然支持）
uvx --from . qcc remove <配置名>        # 传统方式
uvx --from . qcc use <配置名>           # 传统方式

# 远程安装使用
uvx qcc default                         # 交互式选择默认配置
uvx qcc remove                          # 交互式删除配置
uvx qcc use                             # 交互式选择并启动配置
uvx qcc default <配置名>                # 传统方式（依然支持）
uvx qcc remove <配置名>                 # 传统方式
uvx qcc use <配置名>                    # 传统方式
```

#### 编程接口使用
```python
from fastcc.utils.ui import select_from_list

items = ["选项1", "选项2", "选项3"]
selected = select_from_list(
    items=items,
    prompt="请选择配置",
    timeout=3,      # 3秒后自动选择
    default_index=1 # 默认选择第2项
)
```

#### 操作说明
- **方向键 ↑↓**: 上下选择选项
- **Enter**: 确认当前选择
- **数字键 1-9**: 直接选择对应选项
- **Ctrl+C 或 ESC**: 取消选择
- **倒计时**: 如果用户不操作，会自动选择默认项
- **交互停止倒计时**: 一旦用户按了方向键，倒计时会停止

### 4. 兼容性保证

- ✅ 保持原有函数接口不变
- ✅ 自动错误处理和回退机制
- ✅ 现有代码无需修改即可享受新功能
- ✅ 支持非交互环境（CI/CD等）

### 5. 技术实现

- **主要框架**: `rich` + `prompt_toolkit`
- **回退机制**: 如果新UI失败，自动使用原来的实现
- **跨平台**: 针对Windows系统进行了特殊优化
- **线程安全**: 倒计时使用独立线程，不阻塞UI更新

### 6. 依赖更新

在 `requirements.txt` 中添加了：
```
rich>=12.0.0
prompt_toolkit>=3.0.0
```

安装命令：
```bash
pip install rich>=12.0.0 prompt_toolkit>=3.0.0
```

### 7. 实际效果

在支持的终端中，用户会看到：
- 彩色高亮的选项列表
- 实时倒计时显示
- 方向键控制的光标移动
- 优雅的视觉反馈

在不支持的环境中，会自动回退到简化模式，保证功能正常工作。