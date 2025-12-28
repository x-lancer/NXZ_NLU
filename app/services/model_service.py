"""
模型服务
基于 MiniLM 的轻量级意图识别模型服务
使用 sentence-transformers 进行文本嵌入和相似度匹配
"""
import os
import json
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.utils.logger import get_logger
from app.utils.helpers import build_semantic_dict, filter_none_values
from app.services.vocabulary_manager import VocabularyManager

logger = get_logger(__name__)


class ModelService:
    """基于 MiniLM 的模型服务类"""
    
    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
        self.intent_examples: Dict[str, Dict[str, List[str]]] = {}  # {domain: {intent: [examples]}}
        self.intent_embeddings: Dict[str, Dict[str, np.ndarray]] = {}  # {domain: {intent: embedding}}
        self.vocab_manager: Optional[VocabularyManager] = None  # 词汇组管理器（用于实体提取和alias映射）
        self._embedding_cache: Dict[str, np.ndarray] = {}  # 文本嵌入缓存
        self._prediction_cache: Dict[str, Dict[str, Any]] = {}  # 预测结果缓存
        self._cache_size_limit = 1000  # 缓存大小限制
        self._loaded = False
    
    def load_model(self):
        """加载 MiniLM 模型和意图示例"""
        if self._loaded:
            return
        
        try:
            # 加载 MiniLM 模型
            model_name = settings.MODEL_NAME or "paraphrase-multilingual-MiniLM-L12-v2"
            
            # 检查是否是本地路径
            if os.path.exists(model_name) or os.path.isabs(model_name):
                logger.info(f"Loading model from local path: {model_name}")
                self.model = SentenceTransformer(model_name, device=settings.MODEL_DEVICE)
            else:
                logger.info(f"Loading model from HuggingFace: {model_name}")
                self.model = SentenceTransformer(model_name, device=settings.MODEL_DEVICE)
            
            logger.info(f"Model loaded successfully on device: {settings.MODEL_DEVICE}")
            
            # 加载词汇组管理器（用于实体提取和alias映射）
            try:
                self.vocab_manager = VocabularyManager()
                self.vocab_manager.load_vocabularies()
                logger.info("Vocabulary manager loaded for model service")
            except Exception as e:
                logger.warning(f"Failed to load vocabulary manager: {e}, entity extraction may be limited")
                self.vocab_manager = None
            
            # 加载意图示例
            self._load_intent_examples()
            
            # 预计算意图示例的嵌入向量（用于加速推理）
            self._precompute_embeddings()
            
            self._loaded = True
            logger.info("Model service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            # 不抛出异常，允许服务在没有模型的情况下运行（仅使用正则）
            logger.warning("Model service will not be available, falling back to regex only")
    
    def _load_intent_examples(self):
        """从配置文件加载意图示例"""
        config_path = Path(settings.INTENT_EXAMPLES_PATH)
        
        if not config_path.exists():
            logger.warning(f"Intent examples file not found: {config_path}")
            logger.info("Creating default intent examples file...")
            self._create_default_intent_examples(config_path)
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                intent_examples = config.get("intent_examples", {})
                
                # 提取每个意图的示例文本
                for intent, intent_data in intent_examples.items():
                    examples = intent_data.get("examples", [])
                    if examples:
                        self.intent_examples[intent] = examples
                
                logger.info(f"Loaded intent examples for {len(self.intent_examples)} intents")
                total_examples = sum(len(examples) for examples in self.intent_examples.values())
                logger.info(f"Total examples: {total_examples}")
                
        except Exception as e:
            logger.error(f"Failed to load intent examples: {e}", exc_info=True)
            raise
    
    def _precompute_embeddings(self):
        """预计算所有意图示例的嵌入向量"""
        if not self.model:
            return
        
        logger.info("Precomputing intent embeddings...")
        
        for intent, examples in self.intent_examples.items():
            if examples:
                # 批量编码所有示例
                embeddings = self.model.encode(
                    examples,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    normalize_embeddings=True  # 归一化以便使用余弦相似度
                )
                # 计算平均嵌入向量（或使用其他聚合方法）
                self.intent_embeddings[intent] = np.mean(embeddings, axis=0)
                logger.debug(f"Precomputed embedding for intent: {intent} ({len(examples)} examples)")
        
        logger.info(f"Precomputed embeddings for {len(self.intent_embeddings)} intents")
    
    def _create_default_intent_examples(self, config_path: Path):
        """创建默认的意图示例配置文件"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            "intent_examples": {
                "vehicle_control": {
                    "description": "车辆控制意图",
                    "examples": [
                        "打开车窗",
                        "开启车门",
                        "关闭天窗",
                        "停止空调",
                        "启动音乐"
                    ]
                },
                "vehicle_query": {
                    "description": "车辆查询意图",
                    "examples": [
                        "查询天气",
                        "查看路况",
                        "显示油量",
                        "查看电量"
                    ]
                }
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Created default intent examples file at {config_path}")
        # 重新加载
        self._load_intent_examples()
    
    async def predict(
        self,
        text: str,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        使用 MiniLM 模型进行意图预测
        
        通过计算输入文本与意图示例的相似度来确定意图
        
        Args:
            text: 待预测的文本
            domain: 所属领域（如果提供，只在该领域下进行意图识别）
            context: 上下文信息（暂未使用）
        
        Returns:
            Dict包含intent, confidence, entities等字段
        """
        if not self._loaded or not self.model:
            logger.warning("Model not loaded, cannot make prediction")
            return None
        
        if not self.intent_embeddings:
            logger.warning("No intent embeddings available")
            return None
        
        try:
            # 构建缓存键（包含领域信息）
            cache_key = f"{text}_{domain}" if domain else text
            text_hash = self._hash_text(cache_key)
            
            if text_hash in self._prediction_cache:
                logger.debug(f"Using cached prediction for text: {text[:20]}...")
                return self._prediction_cache[text_hash]
            
            # 检查嵌入缓存（文本嵌入不依赖领域）
            text_only_hash = self._hash_text(text)
            if text_only_hash in self._embedding_cache:
                text_embedding = self._embedding_cache[text_only_hash]
                logger.debug(f"Using cached embedding for text: {text[:20]}...")
            else:
                # 编码输入文本
                text_embedding = self.model.encode(
                    text,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                # 缓存嵌入（限制缓存大小）
                if len(self._embedding_cache) < self._cache_size_limit:
                    self._embedding_cache[text_only_hash] = text_embedding
            
            # 根据领域过滤意图嵌入
            intent_embeddings_to_use = self.intent_embeddings
            if domain:
                # 如果指定了领域，只在该领域下查找意图
                # 注意：当前实现中，意图示例是扁平的，未来可以按领域组织
                logger.debug(f"Filtering intents for domain: {domain}")
                # 暂时使用所有意图，后续可以优化为按领域过滤
            
            # 计算与所有意图的相似度
            similarities = {}
            for intent, intent_embedding in intent_embeddings_to_use.items():
                # 使用余弦相似度
                similarity = float(np.dot(text_embedding, intent_embedding))
                similarities[intent] = similarity
            
            # 找到最相似的意图
            if not similarities:
                logger.warning("No intent embeddings available for comparison")
                return None
                
            best_intent = max(similarities.items(), key=lambda x: x[1])
            intent_name, confidence = best_intent
            
            # 如果置信度低于阈值，返回 unknown
            if confidence < settings.SIMILARITY_THRESHOLD:
                intent_name = "unknown"
                confidence = 0.0
            
            logger.debug(f"Predicted intent: {intent_name} (confidence: {confidence:.3f})")
            
            # 提取实体（action, target, position, value）
            entities = self._extract_entities(text, intent_name)
            
            # 构建semantic对象（与正则匹配保持一致的结构）
            semantic = None
            if entities:
                # 从entities中获取中文原始文本，然后映射为alias
                action_text = entities.get("action")
                target_text = entities.get("target")
                position_text = entities.get("position")
                value_text = entities.get("value")
                
                # 将中文文本映射为alias（用于semantic字段）
                action = None
                target = None
                position = None
                value = value_text  # value通常不需要映射
                
                if action_text and self.vocab_manager:
                    action = self.vocab_manager.get_alias_by_item(action_text)
                if target_text and self.vocab_manager:
                    target = self.vocab_manager.get_alias_by_item(target_text)
                if position_text and self.vocab_manager:
                    position = self.vocab_manager.get_alias_by_item(position_text)
                
                # 使用统一的工具函数构建semantic对象，自动过滤None值
                semantic = build_semantic_dict(
                    action=action,
                    target=target,
                    position=position,
                    value=value
                )
            
            # 过滤entities中的None值
            filtered_entities = filter_none_values(entities)
            
            result = {
                "intent": intent_name,
                "semantic": semantic,
                "confidence": float(confidence),
                "entities": filtered_entities,
                "raw_text": text,  # 添加原始文本
                "similarities": {k: float(v) for k, v in similarities.items()}  # 用于调试
            }
            
            # 缓存结果（限制缓存大小）
            if len(self._prediction_cache) < self._cache_size_limit:
                self._prediction_cache[text_hash] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Model prediction failed: {e}", exc_info=True)
            return None
    
    def _extract_entities(self, text: str, intent: str) -> Dict[str, Any]:
        """
        从文本中提取实体（action, target, position, value）
        
        使用vocabulary_groups.json中的词汇组进行匹配，并使用alias机制统一输出格式
        与正则匹配的实体提取逻辑保持一致
        """
        entities = {}
        
        if not self.vocab_manager:
            logger.debug("Vocabulary manager not available, cannot extract entities")
            return None
        
        # 定义需要提取的实体类型及其对应的词汇组前缀
        entity_types = {
            "action": ["action_"],
            "target": ["target_"],
            "position": ["position_"],
            "value": []  # value通常不是从词汇组中提取，而是从文本中直接提取数值等
        }
        
        # 遍历所有词汇组，匹配文本中的实体
        for group_id, group_data in self.vocab_manager.groups.items():
            items = group_data.get("items", [])
            alias = group_data.get("alias")
            
            if not items or not alias:
                continue
            
            # 确定实体类型
            entity_type = None
            for et, prefixes in entity_types.items():
                if any(group_id.startswith(prefix) for prefix in prefixes):
                    entity_type = et
                    break
            
            if not entity_type:
                continue
            
            # 如果该实体类型已经提取到了，跳过（避免覆盖）
            if entity_type in entities:
                continue
            
            # 匹配文本中的词汇（按长度降序，确保长词优先匹配）
            sorted_items = sorted(items, key=len, reverse=True)
            for item in sorted_items:
                if item in text:
                    # entities中只保留中文原始文本（与正则匹配保持一致）
                    entities[entity_type] = item
                    break
        
        # 提取value（通常是数值、时间等，这里简化处理，可以根据需要扩展）
        # 可以添加数值提取逻辑，例如使用正则表达式提取数字等
        
        return entities if entities else None
    
    def _hash_text(self, text: str) -> str:
        """生成文本的哈希值用于缓存"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def clear_cache(self):
        """清空缓存"""
        self._embedding_cache.clear()
        self._prediction_cache.clear()
        logger.info("Model service cache cleared")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        if not self._loaded:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "model_name": settings.MODEL_NAME,
            "device": settings.MODEL_DEVICE,
            "intent_count": len(self.intent_examples),
            "total_examples": sum(len(examples) for examples in self.intent_examples.values()),
            "cache_size": {
                "embeddings": len(self._embedding_cache),
                "predictions": len(self._prediction_cache)
            }
        }
