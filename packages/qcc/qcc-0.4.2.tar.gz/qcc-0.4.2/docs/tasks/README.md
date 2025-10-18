# QCC 开发任务文档中心

## 📚 文档导航

本目录包含 QCC 各版本的开发任务、设计文档和技术报告。

### 📂 目录结构

```
docs/tasks/
├── README.md                                    # 本文件 - 文档索引
└── v0.4.0-代理服务/                              # v0.4.0 版本文档
    ├── README.md                                # v0.4.0 总览
    ├── COMPLETION_REPORT.md                     # 完成报告
    ├── 设计文档/
    │   ├── claude-code-proxy-development-plan.md    # 主开发计划
    │   ├── endpoint-reuse-implementation.md         # Endpoint 复用设计
    │   ├── auto-failover-mechanism.md               # 自动故障转移机制
    │   ├── intelligent-health-check.md              # 智能健康检测设计
    │   └── intelligent-health-check-implementation.md # 健康检测实现报告
    └── 用户指南/
        ├── USAGE_EXAMPLE.md                     # 使用示例
        └── TESTING.md                          # 测试指南
```

---

## 🗂️ 版本文档

### [v0.4.0 - Claude Code 代理服务](./v0.4.0-代理服务/)

**状态**: ✅ 已完成 (2025-10-16)
**完成度**: 95%
**核心特性**:

1. **代理服务器** - 本地 HTTP 代理，拦截和转发 Claude Code API 请求
2. **多 Endpoint 管理** - 支持多个 API Key 和 Base URL，实现负载均衡
3. **三级优先级体系** - Primary/Secondary/Fallback 配置自动故障转移
4. **智能健康检测** - 对话式健康测试，多维度性能评估
5. **失败队列机制** - 自动重试，支持多种重试策略
6. **完善的 CLI** - 35+ 命令，覆盖所有功能管理

**快速链接**:
- [📖 开发计划](./v0.4.0-代理服务/设计文档/claude-code-proxy-development-plan.md)
- [✅ 完成报告](./v0.4.0-代理服务/COMPLETION_REPORT.md)
- [📘 使用示例](./v0.4.0-代理服务/用户指南/USAGE_EXAMPLE.md)

---

## 📋 未来版本规划

### v0.5.0 - 待规划
- 性能优化和压力测试
- Web Dashboard 监控界面
- 配置版本管理
- 增强的统计和分析

---

## 🔍 文档查找指南

### 按类型查找

- **设计文档**: 查看各版本的 \`设计文档/\` 目录
- **使用指南**: 查看各版本的 \`用户指南/\` 目录
- **开发计划**: 查看各版本的主开发计划文档
- **完成报告**: 查看各版本的 COMPLETION_REPORT.md

### 按主题查找

| 主题 | 相关文档 |
|------|----------|
| 代理服务 | [v0.4.0/claude-code-proxy-development-plan.md](./v0.4.0-代理服务/设计文档/claude-code-proxy-development-plan.md) |
| Endpoint 管理 | [v0.4.0/endpoint-reuse-implementation.md](./v0.4.0-代理服务/设计文档/endpoint-reuse-implementation.md) |
| 故障转移 | [v0.4.0/auto-failover-mechanism.md](./v0.4.0-代理服务/设计文档/auto-failover-mechanism.md) |
| 健康检测 | [v0.4.0/intelligent-health-check.md](./v0.4.0-代理服务/设计文档/intelligent-health-check.md) |
| 使用示例 | [v0.4.0/USAGE_EXAMPLE.md](./v0.4.0-代理服务/用户指南/USAGE_EXAMPLE.md) |

---

## 📝 文档编写规范

### 新版本文档结构

每个版本应包含以下文档:

```
vX.X.X-版本名称/
├── README.md                    # 版本总览
├── COMPLETION_REPORT.md         # 完成报告
├── 设计文档/
│   └── *.md                     # 各功能设计文档
└── 用户指南/
    ├── USAGE_EXAMPLE.md         # 使用示例
    └── TESTING.md               # 测试指南
```

### 文档命名规范

- **设计文档**: 使用英文小写 + 连字符,如 \`auto-failover-mechanism.md\`
- **报告文档**: 使用大写 + 下划线,如 \`COMPLETION_REPORT.md\`
- **中文目录**: 使用中文 + 连字符,如 \`v0.4.0-代理服务/\`

---

## 🔗 相关资源

- **主仓库**: https://github.com/lghguge520/qcc
- **主文档**: [README.md](../../README.md)
- **问题反馈**: https://github.com/lghguge520/qcc/issues

---

**最后更新**: 2025-10-17
**维护者**: QCC Development Team
