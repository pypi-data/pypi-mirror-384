#!/usr/bin/env python3
"""
XMind 转 Markdown MCP 服务器
提供读取 XMind 文件并转换为 Markdown 的工具
"""
import asyncio
import json
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from xmind_parser import XMindParser
from md_converter import MarkdownConverter


# 创建 MCP 服务器实例
app = Server("xmind-to-markdown")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    列出所有可用工具
    """
    return [
        Tool(
            name="convert_xmind_to_markdown",
            description="读取 XMind 文件并转换为 Markdown 格式。支持解析思维导图的层级结构、备注、标签等信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "xmind_path": {
                        "type": "string",
                        "description": "XMind 文件的路径（支持相对路径或绝对路径）"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "输出 Markdown 文件的路径（可选）。如果不提供，将自动保存到 output/ 目录下，文件名与原 XMind 文件同名。"
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "description": "是否在 Markdown 中包含文件元信息（默认为 true）",
                        "default": True
                    }
                },
                "required": ["xmind_path"]
            }
        ),
        Tool(
            name="read_xmind_structure",
            description="仅读取并返回 XMind 文件的结构化数据（JSON 格式），不进行 Markdown 转换。用于查看思维导图的原始结构。",
            inputSchema={
                "type": "object",
                "properties": {
                    "xmind_path": {
                        "type": "string",
                        "description": "XMind 文件的路径（支持相对路径或绝对路径）"
                    }
                },
                "required": ["xmind_path"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    处理工具调用
    """
    try:
        if name == "convert_xmind_to_markdown":
            return await convert_xmind_to_markdown(arguments)
        elif name == "read_xmind_structure":
            return await read_xmind_structure(arguments)
        else:
            return [TextContent(
                type="text",
                text=f"未知工具: {name}"
            )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"工具执行失败: {str(e)}"
        )]


async def convert_xmind_to_markdown(arguments: dict) -> list[TextContent]:
    """
    转换 XMind 到 Markdown
    """
    xmind_path = arguments.get("xmind_path")
    output_path = arguments.get("output_path")
    include_metadata = arguments.get("include_metadata", True)
    
    if not xmind_path:
        return [TextContent(
            type="text",
            text="错误: 缺少必需参数 xmind_path"
        )]
    
    try:
        # 解析 XMind 文件
        parser = XMindParser(xmind_path)
        xmind_data = parser.parse()
        metadata = parser.get_metadata() if include_metadata else None
        
        # 转换为 Markdown
        converter = MarkdownConverter()
        markdown_content = converter.convert(xmind_data, metadata)
        
        # 如果未指定输出路径，使用默认路径
        if not output_path:
            # 创建默认输出目录
            default_output_dir = Path("output")
            default_output_dir.mkdir(exist_ok=True)
            
            # 使用原文件名，替换扩展名为 .md
            xmind_file = Path(xmind_path)
            output_filename = xmind_file.stem + ".md"
            output_path = str(default_output_dir / output_filename)
        
        # 保存文件
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown_content, encoding="utf-8")
        
        return [TextContent(
            type="text",
            text=f"✅ 转换成功！\n\n文件已保存到: {output_path}\n\n预览前 500 字符:\n\n{markdown_content[:500]}..."
        )]
    
    except FileNotFoundError as e:
        return [TextContent(
            type="text",
            text=f"❌ 文件不存在: {str(e)}"
        )]
    except ValueError as e:
        return [TextContent(
            type="text",
            text=f"❌ 参数错误: {str(e)}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ 转换失败: {str(e)}"
        )]


async def read_xmind_structure(arguments: dict) -> list[TextContent]:
    """
    读取 XMind 结构化数据
    """
    xmind_path = arguments.get("xmind_path")
    
    if not xmind_path:
        return [TextContent(
            type="text",
            text="错误: 缺少必需参数 xmind_path"
        )]
    
    try:
        # 解析 XMind 文件
        parser = XMindParser(xmind_path)
        xmind_data = parser.parse()
        metadata = parser.get_metadata()
        
        # 返回 JSON 格式的结构化数据
        result = {
            "metadata": metadata,
            "structure": xmind_data
        }
        
        return [TextContent(
            type="text",
            text=f"✅ 解析成功！\n\n```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```"
        )]
    
    except FileNotFoundError as e:
        return [TextContent(
            type="text",
            text=f"❌ 文件不存在: {str(e)}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ 解析失败: {str(e)}"
        )]


async def main():
    """
    启动 MCP 服务器
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())