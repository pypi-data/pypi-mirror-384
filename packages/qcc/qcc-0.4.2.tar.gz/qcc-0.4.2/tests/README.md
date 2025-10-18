# QCC 测试

## 测试文件说明

- `test_providers.py` - 厂商配置管理器测试
- `test_fc_command.py` - 厂商快速配置命令完整流程测试  
- `test_simplified_fc.py` - 简化流程测试

## 运行测试

```bash
# 激活虚拟环境
source fastcc_test_env/bin/activate

# 运行单个测试
python3 tests/test_providers.py
python3 tests/test_fc_command.py
python3 tests/test_simplified_fc.py

# 或运行所有测试
python3 -m pytest tests/ -v
```

## 测试内容

### 厂商配置管理器测试
- 云端配置获取
- 厂商信息解析
- API Key 验证
- Base URL 验证

### 厂商快速配置流程测试
- 完整的 5 步配置流程
- 用户交互模拟
- 浏览器跳转功能
- 配置创建流程

### 简化流程测试
- 优化后的用户体验流程
- 减少确认步骤
- 更流畅的操作体验