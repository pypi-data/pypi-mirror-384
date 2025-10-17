"""
Markdown 转换器模块
将 XMind 结构化数据转换为 Markdown 格式
"""
from typing import Dict, List, Any
from datetime import datetime


class MarkdownConverter:
    """XMind 到 Markdown 的转换器"""
    
    def __init__(self):
        self.indent_size = 2  # 缩进空格数
    
    def convert(self, xmind_data: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
        """
        将 XMind 数据转换为 Markdown
        
        Args:
            xmind_data: 标准化的 XMind 数据结构
            metadata: 文件元信息（可选）
            
        Returns:
            Markdown 格式的字符串
        """
        md_lines = []
        
        sheets = xmind_data.get("sheets", [])
        
        for idx, sheet in enumerate(sheets):
            if idx > 0:
                md_lines.append("\n---\n")  # 多个画布之间分隔
            
            # 处理画布标题（如果不是默认的"未命名画布"）
            sheet_title = sheet.get("title", "")
            if sheet_title and sheet_title != "未命名画布":
                md_lines.append(f"# 画布: {sheet_title}\n")
            
            # 处理根主题（中心主题）
            root_topic = sheet.get("root_topic", {})
            md_lines.extend(self._convert_root_topic(root_topic))
        
        # 添加元信息
        if metadata:
            md_lines.append("\n---\n")
            md_lines.append("**文件元信息**\n")
            md_lines.append(f"- 文件名: {metadata.get('file_name', 'N/A')}")
            md_lines.append(f"- 文件大小: {self._format_size(metadata.get('file_size', 0))}")
            
            created = metadata.get('created_time')
            if created:
                md_lines.append(f"- 创建时间: {datetime.fromtimestamp(created).strftime('%Y-%m-%d %H:%M:%S')}")
            
            modified = metadata.get('modified_time')
            if modified:
                md_lines.append(f"- 修改时间: {datetime.fromtimestamp(modified).strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(md_lines)
    
    def _convert_root_topic(self, root_topic: Dict[str, Any]) -> List[str]:
        """
        转换根主题（中心主题）
        
        Args:
            root_topic: 根主题数据
            
        Returns:
            Markdown 行列表
        """
        lines = []
        
        # 中心主题作为一级标题
        title = root_topic.get("title", "未命名主题")
        lines.append(f"# {title}\n")
        
        # 添加备注（如果有）
        note = root_topic.get("note", "").strip()
        if note:
            lines.append(f"> {note}\n")
        
        # 处理标签
        labels = root_topic.get("labels", [])
        if labels:
            labels_str = " ".join([f"`{label}`" for label in labels])
            lines.append(f"**标签**: {labels_str}\n")
        
        # 处理子主题（主分支）
        children = root_topic.get("children", [])
        for child in children:
            lines.extend(self._convert_branch(child, level=2))
        
        return lines
    
    def _convert_branch(self, topic: Dict[str, Any], level: int) -> List[str]:
        """
        转换分支主题
        
        Args:
            topic: 主题数据
            level: 标题级别（2 表示二级标题）
            
        Returns:
            Markdown 行列表
        """
        lines = []
        
        title = topic.get("title", "")
        
        if level == 2:
            # 主分支使用二级标题
            lines.append(f"\n## {title}\n")
            
            # 添加备注
            note = topic.get("note", "").strip()
            if note:
                lines.append(f"> {note}\n")
            
            # 添加标签
            labels = topic.get("labels", [])
            if labels:
                labels_str = " ".join([f"`{label}`" for label in labels])
                lines.append(f"**标签**: {labels_str}\n")
            
            # 子主题使用列表
            children = topic.get("children", [])
            for child in children:
                lines.extend(self._convert_list_item(child, indent_level=0))
        else:
            # 更深层级使用列表
            lines.extend(self._convert_list_item(topic, indent_level=level - 2))
        
        return lines
    
    def _convert_list_item(self, topic: Dict[str, Any], indent_level: int) -> List[str]:
        """
        转换为列表项
        
        Args:
            topic: 主题数据
            indent_level: 缩进级别（0 表示无缩进）
            
        Returns:
            Markdown 行列表
        """
        lines = []
        indent = " " * (indent_level * self.indent_size)
        
        title = topic.get("title", "")
        lines.append(f"{indent}- {title}")
        
        # 添加备注（作为子项）
        note = topic.get("note", "").strip()
        if note:
            note_indent = " " * ((indent_level + 1) * self.indent_size)
            lines.append(f"{note_indent}> {note}")
        
        # 添加标签
        labels = topic.get("labels", [])
        if labels:
            labels_str = " ".join([f"`{label}`" for label in labels])
            label_indent = " " * ((indent_level + 1) * self.indent_size)
            lines.append(f"{label_indent}*标签: {labels_str}*")
        
        # 递归处理子主题
        children = topic.get("children", [])
        for child in children:
            lines.extend(self._convert_list_item(child, indent_level + 1))
        
        return lines
    
    def _format_size(self, size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 字节数
            
        Returns:
            格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"