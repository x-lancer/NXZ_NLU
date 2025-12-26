"""
正则匹配服务
负责加载正则表达式规则并进行匹配
"""
import json
import re
from typing import Optional, Dict, Any, List
from pathlib import Path
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RegexService:
    """正则匹配服务类"""
    
    def __init__(self):
        self.patterns: List[Dict[str, Any]] = []
        self._loaded = False
    
    def load_patterns(self):
        """从配置文件加载正则表达式模式"""
        if self._loaded:
            return
        
        config_path = Path(settings.REGEX_CONFIG_PATH)
        
        if not config_path.exists():
            logger.warning(f"Regex config file not found: {config_path}")
            # 创建默认配置文件
            self._create_default_config(config_path)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.patterns = config.get("patterns", [])
            
            logger.info(f"Loaded {len(self.patterns)} regex patterns")
            self._loaded = True
        except Exception as e:
            logger.error(f"Failed to load regex patterns: {e}")
            raise
    
    def match(self, text: str) -> Optional[Dict[str, Any]]:
        """
        使用正则表达式匹配文本
        
        Args:
            text: 待匹配的文本
        
        Returns:
            Dict包含intent, action, target, entities等字段，如果未匹配返回None
        """
        if not self._loaded:
            logger.warning("Regex patterns not loaded, cannot match")
            return None
        
        for pattern_config in self.patterns:
            pattern = pattern_config.get("pattern")
            if not pattern:
                continue
            
            try:
                match = re.search(pattern, text)
                if match:
                    result = self._extract_result(pattern_config, match, text)
                    logger.debug(f"Regex matched: {pattern} -> {result}")
                    return result
            except re.error as e:
                logger.error(f"Invalid regex pattern '{pattern}': {e}")
                continue
        
        return None
    
    def _extract_result(
        self,
        pattern_config: Dict[str, Any],
        match: re.Match,
        text: str
    ) -> Dict[str, Any]:
        """从匹配结果中提取结构化信息"""
        # 获取基础配置
        intent = pattern_config.get("intent", "unknown")
        action = pattern_config.get("action")
        target = pattern_config.get("target")
        confidence = pattern_config.get("confidence", 1.0)
        
        # 提取命名分组
        entities = {}
        if match.groupdict():
            entities = match.groupdict()
        
        # 提取所有分组
        groups = match.groups()
        if groups:
            group_names = pattern_config.get("group_names", [])
            for i, group_value in enumerate(groups):
                if group_value and i < len(group_names):
                    entities[group_names[i]] = group_value
        
        # 动态提取action和target（如果正则中有分组）
        if not action and "action" in entities:
            action = entities.get("action")
        if not target and "target" in entities:
            target = entities.get("target")
        
        return {
            "intent": intent,
            "action": action,
            "target": target,
            "confidence": confidence,
            "entities": entities if entities else None
        }
    
    def _create_default_config(self, config_path: Path):
        """创建默认的正则配置文件"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            "patterns": [
                {
                    "pattern": r"(打开|开启|启动)(?P<target>车窗|车门|天窗|空调|音乐|导航)",
                    "intent": "vehicle_control",
                    "action": "open",
                    "target": None,  # 从正则分组中提取
                    "confidence": 0.95,
                    "group_names": ["action", "target"]
                },
                {
                    "pattern": r"(关闭|停止|关闭)(?P<target>车窗|车门|天窗|空调|音乐|导航)",
                    "intent": "vehicle_control",
                    "action": "close",
                    "target": None,
                    "confidence": 0.95,
                    "group_names": ["action", "target"]
                }
            ]
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Created default regex config at {config_path}")

