"""
词汇组管理器
负责加载和管理可复用的正则词汇组
"""
import json
import re
from typing import Dict, List, Optional, Set
from pathlib import Path
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VocabularyManager:
    """词汇组管理器类"""
    
    def __init__(self):
        self.groups: Dict[str, Dict[str, any]] = {}  # 词汇组定义
        self.group_aliases: Dict[str, str] = {}  # 组别名映射（group_id -> alias）
        self.item_to_alias: Dict[str, str] = {}  # 词汇项到alias的反向映射（中文词汇 -> alias）
        self.compiled_patterns: Dict[str, str] = {}  # 编译后的正则模式缓存
        self._loaded = False
    
    def load_vocabularies(self, config_path: Optional[Path] = None):
        """加载词汇组配置"""
        if self._loaded:
            return
        
        if config_path is None:
            # 默认配置文件路径
            config_path = Path(settings.VOCABULARY_GROUPS_PATH)
        
        if not config_path.exists():
            logger.warning(f"Vocabulary groups file not found: {config_path}")
            logger.info("Creating default vocabulary groups file...")
            self._create_default_config(config_path)
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # 加载词汇组
                groups = config.get("groups", {})
                for group_id, group_data in groups.items():
                    items = group_data.get("items", [])
                    alias = group_data.get("alias", group_id)  # 如果没有alias，使用group_id
                    
                    self.groups[group_id] = {
                        "name": group_data.get("name", group_id),
                        "description": group_data.get("description", ""),
                        "items": items,
                        "alias": alias
                    }
                    
                    # 存储组别名映射
                    self.group_aliases[group_id] = alias
                    
                    # 建立词汇项到alias的反向映射
                    # 如果item已存在，不覆盖（保留更具体的映射，因为先加载的通常是更具体的组）
                    for item in items:
                        if item not in self.item_to_alias:
                            self.item_to_alias[item] = alias
                
                # 验证词汇组
                self._validate_groups()
                
                logger.info(f"Loaded {len(self.groups)} vocabulary groups")
                logger.debug(f"Groups: {list(self.groups.keys())}")
                
                self._loaded = True
                
        except Exception as e:
            logger.error(f"Failed to load vocabulary groups: {e}", exc_info=True)
            raise
    
    def _validate_groups(self):
        """验证词汇组配置"""
        # 可以在这里添加其他验证逻辑
        pass
    
    def get_group(self, group_id: str) -> Optional[List[str]]:
        """
        获取词汇组的所有词汇
        
        Args:
            group_id: 词汇组ID
            
        Returns:
            词汇列表，如果组不存在返回None
        """
        if group_id not in self.groups:
            logger.warning(f"Vocabulary group '{group_id}' not found")
            return None
        
        return self.groups[group_id]["items"].copy()
    
    def get_group_alias(self, group_id: str) -> Optional[str]:
        """
        获取词汇组的alias
        
        Args:
            group_id: 词汇组ID
            
        Returns:
            alias字符串，如果组不存在返回None
        """
        if group_id in self.group_aliases:
            return self.group_aliases[group_id]
        return None
    
    def get_alias_by_item(self, item: str) -> Optional[str]:
        """
        根据词汇项（中文）获取对应的alias
        
        Args:
            item: 词汇项（如"车窗"）
            
        Returns:
            alias字符串，如果找不到返回None
        """
        return self.item_to_alias.get(item)
    
    def get_group_pattern(self, group_id: str, escape: bool = True) -> Optional[str]:
        """
        获取词汇组的正则表达式模式
        
        Args:
            group_id: 词汇组ID或别名
            escape: 是否对特殊字符进行转义（默认True）
            
        Returns:
            正则表达式模式字符串，如果组不存在返回None
        """
        items = self.get_group(group_id)
        if not items:
            return None
        
        # 转义特殊字符
        if escape:
            items = [re.escape(item) for item in items]
        
        # 按长度降序排列，确保长词优先匹配（避免"主驾"匹配到"主驾驶"的一部分）
        items.sort(key=len, reverse=True)
        
        # 组合成正则表达式
        pattern = "|".join(items)
        return pattern
    
    def expand_pattern(self, pattern_template: str) -> str:
        """
        展开模式模板，将词汇组引用替换为实际的正则表达式
        
        支持以下语法：
        - {{group_id}} : 引用词汇组（不转义）
        - {{group_id:escaped}} : 引用词汇组（转义特殊字符）
        - {group_id} : 简写形式（默认转义）
        
        Args:
            pattern_template: 包含词汇组引用的模式模板
            
        Returns:
            展开后的正则表达式模式
        """
        if not self._loaded:
            logger.warning("Vocabulary groups not loaded, cannot expand pattern")
            return pattern_template
        
        # 编译缓存键
        cache_key = pattern_template
        
        # 检查缓存
        if cache_key in self.compiled_patterns:
            return self.compiled_patterns[cache_key]
        
        result = pattern_template
        
        # 匹配 {{group_id}} 或 {{group_id:escaped}} 或 {{group_id:raw}} 格式
        def replace_group(match):
            full_match = match.group(0)
            content = match.group(1)  # 组ID或 group_id:escaped
            
            # 解析参数
            if ":" in content:
                group_id, mode = content.split(":", 1)
                escape = mode != "raw"
            else:
                group_id = content
                escape = True  # 默认转义
            
            # 获取词汇组模式
            group_pattern = self.get_group_pattern(group_id, escape=escape)
            
            if group_pattern is None:
                logger.warning(f"Group '{group_id}' not found in pattern template, keeping original: {full_match}")
                return full_match
            
            return f"({group_pattern})"
        
        # 匹配 {group_id} 简写格式（单大括号）
        def replace_simple_group(match):
            group_id = match.group(1)
            group_pattern = self.get_group_pattern(group_id, escape=True)
            
            if group_pattern is None:
                logger.warning(f"Group '{group_id}' not found, keeping original")
                return match.group(0)
            
            return f"({group_pattern})"
        
        # 先处理双大括号格式 {{...}}
        result = re.sub(r'\{\{([^}]+)\}\}', replace_group, result)
        
        # 再处理单大括号格式 {group_id}（避免与命名分组冲突，只在特定上下文中使用）
        # 注意：这里使用更保守的策略，只匹配明确的格式
        # 如果模板中使用 {group_id} 格式，建议使用双大括号 {{group_id}}
        
        # 缓存结果
        self.compiled_patterns[cache_key] = result
        
        logger.debug(f"Expanded pattern: {pattern_template} -> {result}")
        
        return result
    
    def clear_cache(self):
        """清空编译缓存"""
        self.compiled_patterns.clear()
        logger.debug("Vocabulary pattern cache cleared")
    
    def _create_default_config(self, config_path: Path):
        """创建默认的词汇组配置文件"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            "description": "可复用的正则词汇组定义",
            "version": "1.0",
            "groups": {
                "action_open": {
                    "name": "打开动作",
                    "description": "表示打开、开启的动作词汇",
                    "items": ["打开", "开启", "启动", "开"]
                },
                "action_close": {
                    "name": "关闭动作",
                    "description": "表示关闭、停止的动作词汇",
                    "items": ["关闭", "停止", "关", "关上"]
                }
            },
            "aliases": {
                "打开": "action_open",
                "关闭": "action_close"
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Created default vocabulary groups config at {config_path}")
        # 重新加载
        self.load_vocabularies(config_path)

