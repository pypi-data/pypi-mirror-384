# XMind to Markdown MCP Server

[![PyPI version](https://badge.fury.io/py/xmind-to-markdown-mcp.svg)](https://badge.fury.io/py/xmind-to-markdown-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

将 XMind 思维导图文件转换为 Markdown 格式的 MCP (Model Context Protocol) 服务。

## ✨ 特性

- 🚀 **快速转换**：将 XMind 文件转换为结构化的 Markdown 文档
- 📊 **保留层级**：完整保留思维导图的层级结构
- 🏷️ **支持元数据**：可选包含文件元信息（大小、时间等）
- 🔧 **双工具支持**：提供转换和结构查看两种工具
- 🌐 **MCP 协议**：标准化的 AI 工具接口，易于集成

## 📦 安装

### 使用 uvx（推荐）

```bash
uvx xmind-to-markdown-mcp
```

### 使用 pip

```bash
pip install xmind-to-markdown-mcp
```

## 🚀 快速开始

### 作为 MCP Server 使用

在支持 MCP 的客户端（如 Claude Desktop、Cursor、Cline）中配置：

```json
{
  "mcpServers": {
    "xmind-to-markdown": {
      "command": "uvx",
      "args": ["xmind-to-markdown-mcp"]
    }
  }
}
```

### 可用工具

#### 1. convert_xmind_to_markdown

将 XMind 文件转换为 Markdown 格式。

**参数：**
- `xmind_path` (必需): XMind 文件路径
- `output_path` (可选): 输出 Markdown 文件路径，不提供则自动保存到 `output/` 目录
- `include_metadata` (可选): 是否包含文件元信息，默认 `true`

**示例：**
```json
{
  "xmind_path": "/path/to/file.xmind",
  "output_path": "/path/to/output.md",
  "include_metadata": true
}
```

#### 2. read_xmind_structure

读取并返回 XMind 文件的结构化数据（JSON 格式）。

**参数：**
- `xmind_path` (必需): XMind 文件路径

**示例：**
```json
{
  "xmind_path": "/path/to/file.xmind"
}
```

## 📝 Markdown 转换格式

转换后的 Markdown 采用以下层级结构：

```markdown
# [中心主题]

## [一级分支1]
- 子主题1.1
  - 详细内容1.1.1
  - 详细内容1.1.2
- 子主题1.2

## [一级分支2]
- 子主题2.1
  > 备注：这里是XMind中的备注内容
- 子主题2.2

---
**文件元信息**
- 文件名: example.xmind
- 文件大小: 15.32 KB
- 创建时间: 2025-01-01 10:00:00
- 修改时间: 2025-01-02 15:30:00
```

## 🔧 客户端配置示例

### Claude Desktop (macOS)

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "xmind-to-markdown": {
      "command": "uvx",
      "args": ["xmind-to-markdown-mcp"]
    }
  }
}
```

### Cursor IDE

在项目的 `.vscode/settings.json` 中添加：

```json
{
  "mcp.servers": {
    "xmind-to-markdown": {
      "command": "uvx",
      "args": ["xmind-to-markdown-mcp"]
    }
  }
}
```

### Cline (VS Code Extension)

在 Cline 的 MCP 设置中添加：

```json
{
  "xmind-to-markdown": {
    "command": "uvx",
    "args": ["xmind-to-markdown-mcp"]
  }
}
```

## 🛠️ 开发

### 克隆仓库

```bash
git clone https://github.com/yourusername/xmind-to-markdown-mcp.git
cd xmind-to-markdown-mcp
```

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

## 📮 联系方式

- GitHub Issues: [提交问题](https://github.com/yourusername/xmind-to-markdown-mcp/issues)
- Email: your.email@example.com

## 🙏 致谢

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP 服务框架
- [xmindparser](https://github.com/tobyqin/xmindparser) - XMind 文件解析库
- [Model Context Protocol](https://modelcontextprotocol.io) - MCP 协议规范