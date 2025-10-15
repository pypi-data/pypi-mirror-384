"""
XMind to Markdown MCP Server
将 XMind 思维导图文件转换为 Markdown 格式的 MCP 服务
"""

from .server import app, convert_xmind_to_markdown, read_xmind_structure
from .xmind_parser import XMindParser
from .md_converter import MarkdownConverter

__version__ = "0.1.1"
__author__ = "jiandong.liu"
__email__ = "jiandong.yh@gmail.com"

__all__ = [
    "app",
    "convert_xmind_to_markdown",
    "read_xmind_structure",
    "XMindParser",
    "MarkdownConverter",
]

def main():
    """MCP Server 入口点"""
    app.run(transport='stdio')