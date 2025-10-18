# QCC 双重认证策略文档

## 概述

QCC 代理服务器采用**双重认证策略**，同时发送 Anthropic 和 OpenAI 两种认证格式，确保最大兼容性。

## 认证策略

### 同时发送的认证头

```python
headers = {
    # Anthropic 原生格式
    'x-api-key': endpoint.api_key,
    'anthropic-version': '2023-06-01',

    # OpenAI 兼容格式
    'Authorization': f'Bearer {endpoint.api_key}'
}
```

### 为什么采用双重认证？

| 原因 | 说明 |
|------|------|
| **最大兼容性** | 支持 Anthropic 原生和 OpenAI 兼容的第三方服务 |
| **无需配置** | 用户无需关心 endpoint 使用哪种格式，自动适配 |
| **向后兼容** | 支持同时使用不同格式的多个 endpoint |
| **简化维护** | 不需要为每个 endpoint 配置协议类型 |

## 测试结果

使用 AnyRouter endpoint (`https://q.quuvv.cn`) 测试：

| 认证方式 | 状态码 | 结果 |
|---------|--------|------|
| **双重认证** (x-api-key + Authorization) | 200 | ✅ 成功 |
| **仅 x-api-key** | 200 | ✅ 成功 |
| **仅 Authorization** | 200 | ✅ 成功 |

**结论：** 服务器会自动选择其中一种认证方式，双重发送不会造成冲突。

## 实现位置

### 1. 代理服务器转发 ([server.py:344-357](../fastcc/proxy/server.py#L344-L357))

```python
# 同时发送两种认证方式，确保兼容性
# Anthropic 原生格式
forward_headers['x-api-key'] = endpoint.api_key
forward_headers['anthropic-version'] = '2023-06-01'

# OpenAI 兼容格式
forward_headers['Authorization'] = f'Bearer {endpoint.api_key}'
```

### 2. 健康检查器 ([conversational_checker.py:138-146](../fastcc/proxy/conversational_checker.py#L138-L146))

```python
headers = {
    'Content-Type': 'application/json',
    # Anthropic 原生格式
    'x-api-key': endpoint.api_key,
    'anthropic-version': '2023-06-01',
    # OpenAI 兼容格式
    'Authorization': f'Bearer {endpoint.api_key}'
}
```

## 支持的 Endpoint 类型

### ✅ Anthropic 原生 API
- 官方 Anthropic API (`https://api.anthropic.com`)
- 使用 `x-api-key` 认证

### ✅ OpenAI 兼容服务
- 任何支持 OpenAI 格式的第三方服务
- 使用 `Authorization: Bearer` 认证

### ✅ 混合支持服务
- 同时支持两种格式的服务（如 AnyRouter）
- 会自动选择其中一种

## 协议端点

QCC 默认使用 **Anthropic 原生端点**：

| 功能 | 端点 | 说明 |
|------|------|------|
| **消息对话** | `/v1/messages` | Claude Code 使用的标准端点 |
| ~~聊天完成~~ | ~~/v1/chat/completions~~ | 不使用（OpenAI 格式） |

## 请求格式

### 标准请求体（Anthropic 格式）

```json
{
  "model": "claude-3-5-haiku-20241022",
  "max_tokens": 1024,
  "messages": [
    {
      "role": "user",
      "content": "Hello"
    }
  ]
}
```

### 响应格式（Anthropic 格式）

```json
{
  "id": "msg_...",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hello! How can I help you?"
    }
  ],
  "model": "claude-3-5-haiku-20241022",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 15
  }
}
```

## 配置示例

### Endpoint 配置

```json
{
  "endpoints": [
    {
      "id": "anyrouter-claude",
      "base_url": "https://q.quuvv.cn",
      "api_key": "sk-...",
      "models": ["claude-3-5-haiku-20241022"],
      "weight": 1.0,
      "enabled": true
    }
  ]
}
```

**注意：** 无需指定 `protocol` 字段，双重认证会自动适配。

## 优势总结

### ✅ 用户角度
- 无需关心 endpoint 使用什么协议
- 配置简单，一键添加 endpoint
- 同时支持官方和第三方服务

### ✅ 开发角度
- 代码简洁，无需协议检测逻辑
- 维护成本低，不需要协议配置
- 兼容性强，支持各种第三方服务

### ✅ 兼容性
- ✅ Anthropic 官方 API
- ✅ Claude Code 客户端
- ✅ OpenAI 兼容服务
- ✅ AnyRouter 等聚合服务
- ✅ 自建代理服务

## 测试验证

### 运行测试

```bash
# 测试双重认证策略
python test_dual_auth.py

# 测试 Anthropic 协议
python test_anthropic_protocol.py

# 测试代理服务器
uvx qcc proxy start
python test_proxy_anthropic.py
```

### 预期结果

所有测试应该显示：
```
✓ 双重认证：成功
✓ 仅 x-api-key：成功
✓ 仅 Authorization：成功（取决于服务器）
```

## 注意事项

### 1. API Key 格式
- 确保 API Key 正确且有效
- 大多数服务接受 `sk-` 开头的 key

### 2. 版本头
- Anthropic 协议需要 `anthropic-version: 2023-06-01`
- 始终自动添加，无需手动配置

### 3. 端点路径
- 使用 `/v1/messages` 端点
- 不使用 `/v1/chat/completions`

### 4. 模型名称
- 使用 Anthropic 模型名称（如 `claude-3-5-haiku-20241022`）
- 不是 OpenAI 模型名称（如 ~~`gpt-4`~~）

## 故障排除

### 问题：401 Unauthorized

**可能原因：**
- API Key 无效或过期
- API Key 格式错误

**解决方案：**
1. 验证 API Key 是否正确
2. 检查是否有访问权限
3. 尝试重新生成 API Key

### 问题：404 Not Found

**可能原因：**
- 模型名称错误
- Endpoint 不支持该模型

**解决方案：**
1. 使用 `test_anthropic_protocol.py` 测试可用模型
2. 更换为支持的模型名称

### 问题：500 Server Error

**可能原因：**
- 服务器负载过高
- 模型暂时不可用

**解决方案：**
1. 稍后重试
2. 更换为其他可用模型（如 haiku 系列）

## 相关文档

- [Anthropic 协议迁移报告](./anthropic_protocol_migration.md)
- [代理服务器源码](../fastcc/proxy/server.py)
- [健康检查器源码](../fastcc/proxy/conversational_checker.py)

## 更新历史

- **2025-10-17**: 实现双重认证策略，支持 Anthropic 和 OpenAI 格式
- **2025-10-17**: 验证 AnyRouter endpoint 兼容性
- **2025-10-17**: 创建测试脚本和文档
