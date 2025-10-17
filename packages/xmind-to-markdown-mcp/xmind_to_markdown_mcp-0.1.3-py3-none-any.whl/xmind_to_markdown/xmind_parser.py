"""
XMind 文件解析模块
支持解析 .xmind 文件并提取主题树结构
"""
import xmindparser
from typing import Dict, List, Any, Optional
from pathlib import Path


class XMindParser:
    """XMind 文件解析器"""
    
    def __init__(self, file_path: str):
        """
        初始化解析器
        
        Args:
            file_path: XMind 文件路径
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"XMind 文件不存在: {file_path}")
        
        if not self.file_path.suffix.lower() == '.xmind':
            raise ValueError(f"文件格式错误，需要 .xmind 文件: {file_path}")
    
    def parse(self) -> Dict[str, Any]:
        """
        解析 XMind 文件
        
        Returns:
            包含完整思维导图结构的字典
        """
        try:
            # 使用 xmindparser 解析文件
            content = xmindparser.xmind_to_dict(str(self.file_path))
            return self._normalize_structure(content)
        except Exception as e:
            raise RuntimeError(f"解析 XMind 文件失败: {str(e)}")
    
    def _normalize_structure(self, raw_data: List[Dict]) -> Dict[str, Any]:
        """
        标准化解析结果结构
        
        Args:
            raw_data: xmindparser 返回的原始数据
            
        Returns:
            标准化后的数据结构
        """
        if not raw_data:
            return {"sheets": []}
        
        sheets = []
        for sheet_data in raw_data:
            sheet = {
                "title": sheet_data.get("title", "未命名画布"),
                "root_topic": self._parse_topic(sheet_data.get("topic", {}))
            }
            sheets.append(sheet)
        
        return {"sheets": sheets}
    
    def _parse_topic(self, topic_data: Dict) -> Dict[str, Any]:
        """
        递归解析主题节点
        
        Args:
            topic_data: 主题节点原始数据
            
        Returns:
            标准化的主题节点
        """
        topic = {
            "title": topic_data.get("title", ""),
            "note": topic_data.get("note", ""),
            "labels": topic_data.get("labels", []),
            "markers": topic_data.get("markers", []),
            "children": []
        }
        
        # 递归解析子主题
        children = topic_data.get("topics", [])
        for child in children:
            topic["children"].append(self._parse_topic(child))
        
        return topic
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取文件元信息
        
        Returns:
            文件元信息字典
        """
        stat = self.file_path.stat()
        return {
            "file_name": self.file_path.name,
            "file_size": stat.st_size,
            "created_time": stat.st_ctime,
            "modified_time": stat.st_mtime
        }