"""
正则匹配服务
负责加载正则表达式规则并进行匹配
支持按领域组织的规则文件和可复用的词汇组
"""
import json
import re
from typing import Optional, Dict, Any, List
from pathlib import Path
from app.core.config import settings
from app.utils.logger import get_logger
from app.utils.helpers import build_semantic_dict, filter_none_values
from app.services.vocabulary_manager import VocabularyManager

logger = get_logger(__name__)


def _get_supported_domains() -> List[str]:
    """
    从配置文件读取支持的领域列表（用于正则服务）
    
    Returns:
        领域名称列表，按配置文件中的顺序返回
    """
    config_path = Path(settings.DOMAIN_EXAMPLES_PATH)
    
    if not config_path.exists():
        logger.warning(f"Domain examples file not found: {config_path}")
        return []
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            domain_examples = config.get("domain_examples", {})
            # 返回所有定义的领域名称列表
            return list(domain_examples.keys())
    except Exception as e:
        logger.error(f"Failed to load domain list from config: {e}", exc_info=True)
        return []


class RegexService:
    """正则匹配服务类"""
    
    def __init__(self):
        self.domain_patterns: Dict[str, List[Dict[str, Any]]] = {}  # 按领域组织的规则
        self.common_patterns: List[Dict[str, Any]] = []  # 通用规则（向后兼容）
        self.vocab_manager: Optional[VocabularyManager] = None  # 词汇组管理器
        self._loaded = False
    
    def load_patterns(self):
        """从配置文件加载正则表达式模式"""
        if self._loaded:
            return
        
        logger.info("Loading regex patterns...")
        
        # 0. 加载词汇组管理器（必须在加载模式之前）
        try:
            self.vocab_manager = VocabularyManager()
            self.vocab_manager.load_vocabularies()
            logger.info("Vocabulary manager loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load vocabulary manager: {e}, continuing without vocabulary groups")
            self.vocab_manager = None
        
        # 1. 加载领域特定的规则文件
        self._load_domain_patterns()
        
        # 2. 加载通用规则文件（向后兼容）
        self._load_common_patterns()
        
        # 统计信息
        total_patterns = sum(len(patterns) for patterns in self.domain_patterns.values())
        total_patterns += len(self.common_patterns)
        
        logger.info(f"Loaded {total_patterns} regex patterns")
        logger.info(f"  - Domain-specific: {len(self.domain_patterns)} domains, {sum(len(p) for p in self.domain_patterns.values())} patterns")
        logger.info(f"  - Common patterns: {len(self.common_patterns)} patterns")
        
        self._loaded = True
    
    def _load_domain_patterns(self):
        """加载领域特定的规则文件"""
        domain_dir = Path(settings.REGEX_DOMAIN_DIR)
        
        if not domain_dir.exists():
            logger.info(f"Domain regex directory not found: {domain_dir}, creating default files...")
            self._create_default_domain_configs(domain_dir)
            return
        
        supported_domains = _get_supported_domains()
        for domain in supported_domains:
            domain_file = domain_dir / f"{domain}.json"
            
            if domain_file.exists():
                try:
                    with open(domain_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        patterns = config.get("patterns", [])
                        
                        if patterns:
                            # 展开词汇组引用
                            expanded_patterns = self._expand_patterns(patterns)
                            # 为每个规则添加文件级别的domain（如果规则本身没有domain字段）
                            for pattern_config in expanded_patterns:
                                if "domain" not in pattern_config:
                                    pattern_config["domain"] = domain
                            self.domain_patterns[domain] = expanded_patterns
                            logger.debug(f"Loaded {len(expanded_patterns)} patterns for domain: {domain}")
                except Exception as e:
                    logger.error(f"Failed to load regex patterns for domain '{domain}': {e}")
                    continue
            else:
                logger.debug(f"No regex file found for domain: {domain}")
    
    def _load_common_patterns(self):
        """加载通用规则文件（向后兼容）"""
        config_path = Path(settings.REGEX_CONFIG_PATH)
        
        if not config_path.exists():
            logger.debug(f"Common regex config file not found: {config_path}")
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                patterns = config.get("patterns", [])
                
                if patterns:
                    # 展开词汇组引用
                    self.common_patterns = self._expand_patterns(patterns)
                    logger.info(f"Loaded {len(self.common_patterns)} common patterns from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load common regex patterns: {e}")
    
    def _expand_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        展开模式中的词汇组引用
        
        Args:
            patterns: 原始模式配置列表
            
        Returns:
            展开后的模式配置列表
        """
        if not self.vocab_manager:
            # 如果没有词汇组管理器，直接返回原始模式（向后兼容）
            return patterns
        
        expanded = []
        for pattern_config in patterns:
            expanded_config = pattern_config.copy()
            original_pattern = pattern_config.get("pattern", "")
            
            if original_pattern:
                # 展开词汇组引用
                expanded_pattern = self.vocab_manager.expand_pattern(original_pattern)
                expanded_config["pattern"] = expanded_pattern
                
                # 记录原始模式（用于调试）
                if expanded_pattern != original_pattern:
                    expanded_config["_original_pattern"] = original_pattern
                    logger.debug(f"Expanded pattern: {original_pattern[:100]}... -> {expanded_pattern[:200]}...")
                
                # 验证展开后的正则表达式是否有效
                try:
                    re.compile(expanded_pattern)
                except re.error as e:
                    logger.error(f"Invalid expanded regex pattern: {expanded_pattern[:200]}... Error: {e}")
            
            expanded.append(expanded_config)
        
        return expanded
    
    def match(
        self, 
        text: str, 
        domain: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        使用正则表达式匹配文本
        
        Args:
            text: 待匹配的文本
            domain: 可选的领域
                - None: 全局正则匹配（只匹配通用规则，来自 regex_patterns.json）
                - 指定领域: 只匹配该领域的规则（来自 configs/regex/{domain}.json）
        
        Returns:
            Dict包含intent, action, target, entities, domain等字段，如果未匹配返回None
        """
        if not self._loaded:
            logger.warning("Regex patterns not loaded, cannot match")
            return None
        
        # 策略1: 全局正则匹配（domain=None）- 只匹配通用规则
        if domain is None:
            # 只匹配通用规则（不遍历领域规则）
            if self.common_patterns:
                result = self._match_patterns(text, self.common_patterns)
                if result:
                    # 优先使用规则配置中的domain，如果没有则使用"通用"
                    if not result.get("domain"):
                        result["domain"] = "通用"
                    logger.debug(f"Matched common pattern (global regex), domain={result.get('domain')}")
                    return result
            
            # 全局正则只匹配通用规则，不匹配领域规则
            return None
        
        # 策略2: 指定领域匹配
        if domain in self.domain_patterns:
            result = self._match_patterns(text, self.domain_patterns[domain])
            if result:
                # 优先使用规则配置中的domain，如果没有则使用传入的domain
                if not result.get("domain"):
                    result["domain"] = domain
                semantic = result.get('semantic', {})
                logger.info(f"Matched pattern in domain '{result.get('domain', domain)}': intent={result.get('intent')}, action={semantic.get('action') if isinstance(semantic, dict) else None}, target={semantic.get('target') if isinstance(semantic, dict) else None}")
                return result
            else:
                logger.debug(f"No pattern matched in domain '{domain}' for text: {text}")
        
        # 如果指定领域匹配失败，尝试通用规则（兜底）
        if self.common_patterns:
            result = self._match_patterns(text, self.common_patterns)
            if result:
                # 优先使用规则配置中的domain，如果没有则使用"通用"
                if not result.get("domain"):
                    result["domain"] = "通用"
                logger.debug(f"Matched common pattern (fallback), domain={result.get('domain')}")
                return result
        
        return None
    
    def _match_patterns(
        self, 
        text: str, 
        patterns: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        在给定的规则列表中匹配文本
        
        Args:
            text: 待匹配的文本
            patterns: 规则列表
        
        Returns:
            匹配结果，包含intent, action, target, entities等字段
        """
        for pattern_config in patterns:
            pattern = pattern_config.get("pattern")
            if not pattern:
                continue
            
            try:
                # 编译正则表达式以提高性能（可以考虑缓存）
                match = re.search(pattern, text)
                if match:
                    result = self._extract_result(pattern_config, match, text)
                    semantic = result.get('semantic', {})
                    logger.info(f"Regex matched: pattern={pattern[:100]}..., text={text}, intent={result.get('intent')}, action={semantic.get('action') if isinstance(semantic, dict) else None}, target={semantic.get('target') if isinstance(semantic, dict) else None}")
                    return result
                else:
                    # 只在调试模式下记录未匹配的规则，避免日志过多
                    logger.debug(f"Regex not matched: pattern={pattern[:100]}..., text={text}")
            except re.error as e:
                logger.error(f"Invalid regex pattern '{pattern[:100]}...': {e}")
                continue
        
        return None
    
    def _extract_result(
        self,
        pattern_config: Dict[str, Any],
        match: re.Match,
        text: str
    ) -> Dict[str, Any]:
        """
        从匹配结果中提取结构化信息
        
        Args:
            pattern_config: 规则配置
            match: 正则匹配对象
            text: 原始文本
        
        Returns:
            包含intent, action, target, position, value, confidence, entities, raw_text等字段的字典
        """
        # 获取基础配置
        intent = pattern_config.get("intent", "unknown")
        action = pattern_config.get("action")  # 从配置中读取action（如"open"）
        target = pattern_config.get("target")  # 从配置中读取target（通常是null，从正则中提取）
        domain = pattern_config.get("domain")  # 从配置中读取domain（如果规则中有定义）
        confidence = pattern_config.get("confidence", 1.0)
        
        # 提取命名分组
        entities = {}
        if match.groupdict():
            entities = match.groupdict()
        
        # 提取所有分组（包括非命名分组）
        groups = match.groups()
        if groups:
            group_names = pattern_config.get("group_names", [])
            for i, group_value in enumerate(groups):
                if group_value and i < len(group_names):
                    # 只有当entities中没有该key时才添加（避免覆盖命名分组）
                    if group_names[i] not in entities:
                        entities[group_names[i]] = group_value
        
        # 动态提取target、position、value（如果正则中有分组）
        # action从配置中读取，不需要从entities中提取
        if not target and "target" in entities:
            target = entities.get("target")
            # 将中文target映射为alias（如果vocab_manager可用）
            if target and self.vocab_manager:
                alias = self.vocab_manager.get_alias_by_item(target)
                if alias:
                    target = alias
        
        position = entities.get("position")  # 方位（可选）
        # 将中文position映射为alias（如果vocab_manager可用）
        if position and self.vocab_manager:
            alias = self.vocab_manager.get_alias_by_item(position)
            if alias:
                position = alias
        
        value = entities.get("value")  # 值（可选）
        # 将中文value映射为alias（如果vocab_manager可用）
        if value and self.vocab_manager:
            alias = self.vocab_manager.get_alias_by_item(value)
            if alias:
                value = alias
        
        logger.debug(f"Extracted result: intent={intent}, action={action}, target={target}, position={position}, entities={entities}")
        
        # 构建semantic对象（使用统一的工具函数，自动过滤None值）
        semantic = build_semantic_dict(
            action=action,
            target=target,
            position=position,
            value=value
        )
        
        # 过滤entities中的None值
        filtered_entities = filter_none_values(entities)
        
        return {
            "intent": intent,
            "domain": domain,  # 使用配置中的domain值（如果规则中有定义）
            "semantic": semantic,  # 已经是过滤后的结果，可能为None
            "confidence": confidence,
            "entities": filtered_entities,  # 已经是过滤后的结果，可能为None
            "raw_text": text  # 添加原始文本
        }
    
    def _create_default_domain_configs(self, domain_dir: Path):
        """创建默认的领域规则文件（从配置文件读取领域列表）"""
        domain_dir.mkdir(parents=True, exist_ok=True)
        
        # 从配置文件读取领域列表和描述
        supported_domains = _get_supported_domains()
        if not supported_domains:
            logger.warning("No domains found in config, cannot create default regex configs")
            return
        
        # 读取领域描述
        config_path = Path(settings.DOMAIN_EXAMPLES_PATH)
        domain_descriptions = {}
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    domain_examples = config.get("domain_examples", {})
                    for domain, domain_data in domain_examples.items():
                        domain_descriptions[domain] = domain_data.get("description", f"{domain}相关规则")
        except Exception as e:
            logger.warning(f"Failed to read domain descriptions: {e}")
        
        # 为每个领域创建默认配置文件
        for domain in supported_domains:
            domain_file = domain_dir / f"{domain}.json"
            
            # 如果文件已存在，跳过
            if domain_file.exists():
                logger.debug(f"Regex config file already exists for domain '{domain}', skipping")
                continue
            
            # 创建默认配置（空的patterns数组）
            default_config = {
                "domain": domain,
                "description": domain_descriptions.get(domain, f"{domain}相关规则"),
                "patterns": []
            }
            
            with open(domain_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            logger.info(f"Created default regex config for domain '{domain}' at {domain_file}")
