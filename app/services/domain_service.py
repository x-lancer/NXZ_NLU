"""
领域划分服务
基于 MiniLM 的轻量级领域分类服务
"""
import os
import json
import hashlib
from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_supported_domains() -> List[str]:
    """
    从配置文件读取支持的领域列表
    
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


class DomainService:
    """领域划分服务类"""
    
    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
        self.domain_examples: Dict[str, List[str]] = {}
        self.domain_embeddings: Dict[str, np.ndarray] = {}
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self._prediction_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_size_limit = 1000
        self._loaded = False
    
    def load_model(self):
        """加载 MiniLM 模型和领域示例"""
        if self._loaded:
            return
        
        try:
            # 使用与意图识别相同的模型
            model_name = settings.MODEL_NAME or "paraphrase-multilingual-MiniLM-L12-v2"
            
            # 检查是否是本地路径
            if os.path.exists(model_name) or os.path.isabs(model_name):
                logger.info(f"Loading domain model from local path: {model_name}")
                self.model = SentenceTransformer(model_name, device=settings.MODEL_DEVICE)
            else:
                logger.info(f"Loading domain model from HuggingFace: {model_name}")
                self.model = SentenceTransformer(model_name, device=settings.MODEL_DEVICE)
            
            logger.info(f"Domain model loaded successfully on device: {settings.MODEL_DEVICE}")
            
            # 加载领域示例
            self._load_domain_examples()
            
            # 预计算领域示例的嵌入向量
            self._precompute_embeddings()
            
            self._loaded = True
            logger.info("Domain service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to load domain model: {e}", exc_info=True)
            logger.warning("Domain service will not be available")
    
    def _load_domain_examples(self):
        """从配置文件加载领域示例"""
        config_path = Path(settings.DOMAIN_EXAMPLES_PATH)
        
        if not config_path.exists():
            logger.warning(f"Domain examples file not found: {config_path}")
            logger.info("Creating default domain examples file...")
            self._create_default_domain_examples(config_path)
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                domain_examples = config.get("domain_examples", {})
                
                # 提取每个领域的示例文本
                for domain, domain_data in domain_examples.items():
                    examples = domain_data.get("examples", [])
                    if examples:
                        self.domain_examples[domain] = examples
                
                logger.info(f"Loaded domain examples for {len(self.domain_examples)} domains")
                total_examples = sum(len(examples) for examples in self.domain_examples.values())
                logger.info(f"Total domain examples: {total_examples}")
                
        except Exception as e:
            logger.error(f"Failed to load domain examples: {e}", exc_info=True)
            raise
    
    def _precompute_embeddings(self):
        """预计算所有领域示例的嵌入向量"""
        if not self.model:
            return
        
        logger.info("Precomputing domain embeddings...")
        
        for domain, examples in self.domain_examples.items():
            if examples:
                # 批量编码所有示例
                embeddings = self.model.encode(
                    examples,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    normalize_embeddings=True
                )
                # 计算平均嵌入向量
                self.domain_embeddings[domain] = np.mean(embeddings, axis=0)
                logger.debug(f"Precomputed embedding for domain: {domain} ({len(examples)} examples)")
        
        logger.info(f"Precomputed embeddings for {len(self.domain_embeddings)} domains")
    
    def _create_default_domain_examples(self, config_path: Path):
        """创建默认的领域示例配置文件"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            "domain_examples": {
                "车控": {
                    "description": "车辆控制相关指令",
                    "examples": [
                        "打开车窗",
                        "关闭车门",
                        "开启空调",
                        "调高温度",
                        "打开天窗",
                        "关闭音乐",
                        "启动导航",
                        "调整座椅"
                    ]
                },
                "导航": {
                    "description": "导航相关指令",
                    "examples": [
                        "导航到北京",
                        "去最近的加油站",
                        "显示路线",
                        "避开高速",
                        "重新规划路线",
                        "查看路况",
                        "导航回家"
                    ]
                },
                "音乐": {
                    "description": "音乐播放相关指令",
                    "examples": [
                        "播放音乐",
                        "下一首",
                        "上一首",
                        "暂停播放",
                        "调大音量",
                        "播放周杰伦的歌",
                        "随机播放"
                    ]
                },
                "电话": {
                    "description": "电话相关指令",
                    "examples": [
                        "打电话给张三",
                        "拨打10086",
                        "接听电话",
                        "挂断电话",
                        "查看通话记录",
                        "回拨"
                    ]
                },
                "系统": {
                    "description": "系统设置相关指令",
                    "examples": [
                        "打开蓝牙",
                        "关闭WiFi",
                        "调整屏幕亮度",
                        "查看系统版本",
                        "恢复出厂设置",
                        "查看存储空间"
                    ]
                },
                "通用": {
                    "description": "通用查询和操作",
                    "examples": [
                        "今天天气怎么样",
                        "现在几点了",
                        "查询油价",
                        "查看新闻",
                        "设置提醒"
                    ]
                },
                "闲聊": {
                    "description": "闲聊对话",
                    "examples": [
                        "你好",
                        "在干嘛",
                        "讲个笑话",
                        "今天心情不错",
                        "谢谢",
                        "再见"
                    ]
                }
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Created default domain examples file at {config_path}")
        # 重新加载
        self._load_domain_examples()
    
    async def classify_domain(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        对文本进行领域分类
        
        Args:
            text: 待分类的文本
            context: 上下文信息（暂未使用）
        
        Returns:
            Dict包含domain, confidence等字段
        """
        if not self._loaded or not self.model:
            logger.warning("Domain model not loaded, cannot classify domain")
            return None
        
        if not self.domain_embeddings:
            logger.warning("No domain embeddings available")
            return None
        
        try:
            # 检查缓存
            text_hash = self._hash_text(text)
            if text_hash in self._prediction_cache:
                logger.debug(f"Using cached domain prediction for text: {text[:20]}...")
                return self._prediction_cache[text_hash]
            
            # 检查嵌入缓存
            if text_hash in self._embedding_cache:
                text_embedding = self._embedding_cache[text_hash]
                logger.debug(f"Using cached embedding for text: {text[:20]}...")
            else:
                # 编码输入文本
                text_embedding = self.model.encode(
                    text,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                # 缓存嵌入
                if len(self._embedding_cache) < self._cache_size_limit:
                    self._embedding_cache[text_hash] = text_embedding
            
            # 计算与所有领域的相似度
            similarities = {}
            for domain, domain_embedding in self.domain_embeddings.items():
                # 使用余弦相似度
                similarity = float(np.dot(text_embedding, domain_embedding))
                similarities[domain] = similarity
            
            # 找到最相似的领域
            best_domain = max(similarities.items(), key=lambda x: x[1])
            domain_name, confidence = best_domain
            
            # 智能领域选择逻辑：
            # 1. 如果最相似的领域是"通用"且置信度低于阈值，保持为"通用"
            # 2. 如果最相似的领域不是"通用"：
            #    - 如果相似度高于阈值，直接返回
            #    - 如果相似度低于阈值，但明显高于"通用"领域的相似度，仍返回该领域
            #    - 否则，考虑使用"通用"领域
            general_similarity = similarities.get("通用", 0.0)
            
            if domain_name == "通用":
                # 最相似的领域本身就是"通用"
                logger.debug(f"Best match is '通用' (confidence: {confidence:.3f})")
            elif confidence >= settings.SIMILARITY_THRESHOLD:
                # 相似度高于阈值，直接返回最相似的领域
                logger.debug(f"Domain '{domain_name}' confidence ({confidence:.3f}) above threshold")
            elif confidence > general_similarity + 0.1:
                # 最相似的领域虽然不是"通用"，且相似度低于阈值，但明显高于"通用"相似度（差值>0.1）
                # 仍然返回最相似的领域
                logger.info(
                    f"Domain '{domain_name}' similarity ({confidence:.3f}) below threshold "
                    f"({settings.SIMILARITY_THRESHOLD}), but higher than '通用' ({general_similarity:.3f}), using it"
                )
            else:
                # 最相似的领域相似度不够高，且与"通用"接近，使用"通用"
                domain_name = "通用"
                confidence = general_similarity
                logger.info(
                    f"Best domain '{best_domain[0]}' similarity ({best_domain[1]:.3f}) too low, "
                    f"using default domain '通用' ({general_similarity:.3f})"
                )
            
            logger.debug(f"Classified domain: {domain_name} (confidence: {confidence:.3f})")
            
            result = {
                "domain": domain_name,
                "confidence": float(confidence),
                "similarities": {k: float(v) for k, v in similarities.items()}
            }
            
            # 缓存结果
            if len(self._prediction_cache) < self._cache_size_limit:
                self._prediction_cache[text_hash] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Domain classification failed: {e}", exc_info=True)
            return None
    
    def _hash_text(self, text: str) -> str:
        """生成文本的哈希值用于缓存"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def clear_cache(self):
        """清空缓存"""
        self._embedding_cache.clear()
        self._prediction_cache.clear()
        logger.info("Domain service cache cleared")
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        if not self._loaded:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "model_name": settings.MODEL_NAME,
            "device": settings.MODEL_DEVICE,
            "domain_count": len(self.domain_examples),
            "total_examples": sum(len(examples) for examples in self.domain_examples.values()),
            "supported_domains": list(self.domain_examples.keys()),
            "cache_size": {
                "embeddings": len(self._embedding_cache),
                "predictions": len(self._prediction_cache)
            }
        }

