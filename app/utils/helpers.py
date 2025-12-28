"""
通用工具函数
"""
from typing import Dict, Any, Optional


def filter_none_values(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    过滤字典中的 None 值
    
    Args:
        data: 待过滤的字典
        
    Returns:
        过滤后的字典，如果过滤后为空字典或输入为 None，则返回 None
    """
    if data is None:
        return None
    
    if not isinstance(data, dict):
        return data
    
    filtered = {k: v for k, v in data.items() if v is not None}
    return filtered if filtered else None


def build_semantic_dict(
    action: Optional[str] = None,
    target: Optional[str] = None,
    position: Optional[str] = None,
    value: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    构建语义字典，自动过滤 None 值
    
    Args:
        action: 动作
        target: 目标
        position: 位置
        value: 值
        
    Returns:
        过滤后的语义字典，如果所有字段都是 None，则返回 None
    """
    semantic = {
        "action": action,
        "target": target,
        "position": position,
        "value": value
    }
    
    # 过滤 None 值
    filtered = filter_none_values(semantic)
    
    # 只有当至少有一个字段有值时才返回
    return filtered if filtered else None

