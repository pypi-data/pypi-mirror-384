# QCC v0.4.0 - Anthropic 协议支持更新

## 🎯 更新概要

QCC 代理服务器现已完全支持 **Anthropic Claude Code 原生协议**，采用**双重认证策略**确保最大兼容性。

## ✅ 主要变更

### 1. 双重认证支持

代理服务器同时发送两种认证方式：

```python
# Anthropic 原生格式
'x-api-key': endpoint.api_key
'anthropic-version': '2023-06-01'

# OpenAI 兼容格式
'Authorization': f'Bearer {endpoint.api_key}'
```

### 2. 使用 Anthropic 端点

- ✅ 使用 `/v1/messages` 端点
- ❌ 不再使用 `/v1/chat/completions`

### 3. 健康检查更新

- 使用可用的 Claude 模型：`claude-3-5-haiku-20241022`
- 采用相同的双重认证策略

## 🧪 测试结果

使用 AnyRouter (`https://q.quuvv.cn`) 测试通过：

| 测试项 | 结果 |
|--------|------|
| 双重认证 (x-api-key + Authorization) | ✅ 成功 |
| 仅 x-api-key | ✅ 成功 |
| 仅 Authorization Bearer | ✅ 成功 |
| 基础消息请求 | ✅ 成功 |
| 流式响应 | ✅ 成功 |
| 可用模型数量 | 2 个 (haiku 系列) |

## 📁 修改的文件

### 核心文件
- `fastcc/proxy/server.py` - 添加双重认证支持
- `fastcc/proxy/conversational_checker.py` - 更新模型和认证方式

### 测试文件
- `test_anthropic_protocol.py` - Anthropic 协议直接测试
- `test_dual_auth.py` - 双重认证验证测试
- `test_proxy_anthropic.py` - 代理服务器集成测试

### 文档
- `claudedocs/anthropic_protocol_migration.md` - 迁移详细报告
- `claudedocs/dual_auth_strategy.md` - 双重认证策略说明
- `anthropic_endpoint_config_example.json` - 配置示例

## 🚀 快速开始

### 1. 测试 Endpoint

```bash
# 测试双重认证
python test_dual_auth.py

# 测试 Anthropic 协议
python test_anthropic_protocol.py
```

### 2. 配置 Endpoint

```json
{
  "endpoints": [
    {
      "id": "anyrouter-claude",
      "base_url": "https://q.quuvv.cn",
      "api_key": "sk-your-api-key",
      "models": ["claude-3-5-haiku-20241022"],
      "weight": 1.0,
      "enabled": true
    }
  ]
}
```

### 3. 启动代理

```bash
uvx qcc proxy start
```

### 4. 配置 Claude Code

设置代理地址为：`http://127.0.0.1:7860`

## 💡 兼容性

### ✅ 支持的服务

- Anthropic 官方 API
- Claude Code 客户端
- AnyRouter 等第三方聚合服务
- 支持 Anthropic 协议的自建服务
- 支持 OpenAI 兼容格式的服务

### ✅ 无需配置

双重认证策略会自动适配，无需手动指定协议类型。

## 📊 可用模型

经 AnyRouter 测试，以下模型可用：

| 模型 | 状态 | 建议 |
|------|------|------|
| claude-3-5-haiku-20241022 | ✅ 可用 | 推荐（最快最便宜） |
| claude-haiku-4-5-20251001 | ✅ 可用 | 可选 |
| claude-3-5-sonnet-20241022 | ⚠️ 负载限制 | 高峰期可能不可用 |
| 其他高级模型 | ⚠️ 负载限制 | 按需使用 |

## ⚠️ 注意事项

1. **API Key 格式**：确保使用有效的 API Key
2. **模型名称**：使用 Anthropic 格式的模型名称
3. **端点路径**：服务必须支持 `/v1/messages` 端点
4. **响应格式**：返回 Anthropic 格式的响应

## 🐛 故障排除

### 401 Unauthorized
- 检查 API Key 是否正确
- 验证是否有访问权限

### 404 Not Found
- 确认模型名称正确
- 使用测试脚本检查可用模型

### 500 Server Error
- 服务器负载过高，稍后重试
- 更换为 haiku 等轻量级模型

## 📚 相关文档

- [Anthropic 协议迁移详细报告](claudedocs/anthropic_protocol_migration.md)
- [双重认证策略说明](claudedocs/dual_auth_strategy.md)
- [配置示例](anthropic_endpoint_config_example.json)

## 🎉 总结

**QCC 现在完全支持 Claude Code 原生协议！**

- ✅ 双重认证确保最大兼容性
- ✅ 自动适配 Anthropic 和 OpenAI 格式
- ✅ 无需额外配置
- ✅ 经过完整测试验证

开始使用：`uvx qcc proxy start` 🚀
