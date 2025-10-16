# Publishing Guide

本指南帮助你将 Search MCP Server 发布到公众平台。

## 📦 发布前准备

### 1. 更新版本号

在 `pyproject.toml` 中更新版本号：

```toml
[project]
version = "0.1.0"  # 更新为新版本
```

在 `searcher/__init__.py` 中同步更新：

```python
__version__ = "0.1.0"
```

### 2. 更新 CHANGELOG

创建 `CHANGELOG.md` 记录版本变更：

```markdown
## [0.1.0] - 2025-01-XX

### Added
- Initial release
- Baidu search integration
- AI-powered reranking
- Web content extraction
```

### 3. 运行测试

```bash
# 安装开发依赖
uv pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black searcher/
ruff check searcher/
```

## 🚀 发布到 PyPI

### 方式一：使用 uv（推荐）

```bash
# 构建包
uv build

# 发布到 PyPI（需要 PyPI token）
uv publish
```

### 方式二：使用传统工具

```bash
# 安装构建工具
pip install build twine

# 构建分发包
python -m build

# 检查包
twine check dist/*

# 上传到 TestPyPI（测试）
twine upload --repository testpypi dist/*

# 上传到 PyPI（正式发布）
twine upload dist/*
```

## 🌐 发布到 GitHub

### 1. 推送代码

```bash
git add .
git commit -m "Release version 0.1.0"
git push origin main
```

### 2. 创建 Release

```bash
# 创建标签
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

然后在 GitHub 上：
1. 进入 Repository → Releases
2. 点击 "Draft a new release"
3. 选择刚创建的 tag `v0.1.0`
4. 填写 Release 标题和说明
5. 上传构建产物（可选）
6. 发布 Release

## 📝 发布到 MCP 服务器列表

### Smithery (推荐)

Smithery 是 MCP 服务器的官方发现平台。

访问：https://smithery.ai/submit

提交信息：
- **Name**: Search MCP Server
- **Description**: AI-powered Baidu search with intelligent reranking and web content extraction
- **GitHub URL**: https://github.com/Vist233/Google-Search-Tool
- **Install Command**: 
  ```bash
  npx -y @smithery/cli install search-mcp --client claude
  ```

### 其他平台

1. **MCP Awesome List**
   - 提交 PR 到：https://github.com/punkpeye/awesome-mcp-servers
   
2. **MCP Hub**
   - 访问：https://mcp-hub.com
   - 提交你的服务器信息

## 📢 推广

### 1. 更新 README Badges

在 README.md 顶部添加：

```markdown
[![PyPI version](https://badge.fury.io/py/search-mcp.svg)](https://badge.fury.io/py/search-mcp)
[![Downloads](https://pepy.tech/badge/search-mcp)](https://pepy.tech/project/search-mcp)
```

### 2. 社交媒体

- 在 Twitter/X 上发布
- 在相关 Discord/Slack 社区分享
- 在 Reddit 的 r/python、r/LocalLLaMA 等社区分享
- 在知乎、掘金等中文平台分享

### 3. 博客文章

撰写技术博客介绍：
- 项目背景和动机
- 技术实现细节
- 使用场景和案例
- 未来规划

## 🔧 配置示例

提供清晰的配置示例供用户复制：

```json
{
  "mcpServers": {
    "search-tools": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/search-mcp/searcher/src",
        "run",
        "python",
        "server.py"
      ],
      "env": {
        "DASHSCOPE_API_KEY": "your-api-key"
      }
    }
  }
}
```

## ✅ 发布检查清单

- [ ] 所有测试通过
- [ ] 代码格式化完成
- [ ] 文档更新完整
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新
- [ ] LICENSE 文件存在
- [ ] README 包含安装和使用说明
- [ ] 配置示例清晰易懂
- [ ] PyPI 包已发布
- [ ] GitHub Release 已创建
- [ ] 提交到 Smithery
- [ ] 社交媒体推广

## 📊 监控和维护

### 1. 监控下载量

- PyPI 统计：https://pypistats.org/packages/search-mcp
- GitHub Stars/Forks

### 2. 处理 Issues

- 及时回复用户问题
- 收集功能需求
- 修复 bug

### 3. 持续改进

- 根据反馈优化功能
- 定期更新依赖
- 发布新版本

## 🎯 后续版本规划

### v0.2.0
- [ ] 添加 Google 搜索支持
- [ ] 支持更多语言
- [ ] 性能优化

### v0.3.0
- [ ] 缓存机制
- [ ] 结果去重
- [ ] WebSocket 支持

### v1.0.0
- [ ] 稳定 API
- [ ] 完整测试覆盖
- [ ] 详细文档

## 💡 提示

1. **从小版本开始**：先发布 0.1.0，收集反馈后迭代
2. **保持活跃**：定期更新维护，增加项目可信度
3. **文档优先**：清晰的文档比复杂的功能更重要
4. **社区互动**：积极与用户交流，建立社区

Good luck! 🚀
