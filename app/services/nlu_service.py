"""
NLU核心服务
编排模型预测和正则匹配，实现意图识别
"""
from typing import Optional, Dict, Any
from app.core.schemas import IntentData
from app.core.config import settings
from app.services.model_service import ModelService
from app.services.regex_service import RegexService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NLUService:
    """NLU核心服务类"""
    
    def __init__(self):
        self.model_service: Optional[ModelService] = None
        self.regex_service: Optional[RegexService] = None
        self._initialized = False
    
    def initialize(self):
        """初始化服务，加载模型和正则规则"""
        if self._initialized:
            return
        
        logger.info("Initializing NLU Service...")
        
        # 初始化正则服务
        try:
            self.regex_service = RegexService()
            self.regex_service.load_patterns()
            logger.info("Regex service initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize regex service: {e}")
        
        # 初始化模型服务
        try:
            self.model_service = ModelService()
            self.model_service.load_model()
            logger.info("Model service initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize model service: {e}")
        
        self._initialized = True
        logger.info("NLU Service initialized successfully")
    
    async def recognize(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> IntentData:
        """
        识别意图
        
        Args:
            text: 待识别的文本
            context: 上下文信息
            session_id: 会话ID
        
        Returns:
            IntentData: 意图识别结果
        """
        if not self._initialized:
            raise RuntimeError("NLU Service not initialized")
        
        logger.info(f"Recognizing intent for text: {text}")
        
        # 策略1: 如果启用了正则优先，先尝试正则匹配
        if settings.REGEX_PRIORITY and self.regex_service:
            regex_result = self.regex_service.match(text)
            if regex_result and regex_result.get("confidence", 0) >= settings.CONFIDENCE_THRESHOLD:
                logger.info(f"Regex match found: {regex_result}")
                return IntentData(
                    intent=regex_result.get("intent", "unknown"),
                    action=regex_result.get("action"),
                    target=regex_result.get("target"),
                    confidence=regex_result.get("confidence", 0.0),
                    entities=regex_result.get("entities"),
                    raw_text=text,
                    method="regex"
                )
        
        # 策略2: 使用模型预测
        if self.model_service:
            model_result = await self.model_service.predict(text, context)
            if model_result and model_result.get("confidence", 0) >= settings.CONFIDENCE_THRESHOLD:
                logger.info(f"Model prediction: {model_result}")
                return IntentData(
                    intent=model_result.get("intent", "unknown"),
                    action=model_result.get("action"),
                    target=model_result.get("target"),
                    confidence=model_result.get("confidence", 0.0),
                    entities=model_result.get("entities"),
                    raw_text=text,
                    method="model"
                )
        
        # 策略3: 如果正则未启用优先，但模型失败，再尝试正则
        if not settings.REGEX_PRIORITY and self.regex_service:
            regex_result = self.regex_service.match(text)
            if regex_result:
                logger.info(f"Fallback regex match: {regex_result}")
                return IntentData(
                    intent=regex_result.get("intent", "unknown"),
                    action=regex_result.get("action"),
                    target=regex_result.get("target"),
                    confidence=regex_result.get("confidence", 0.0),
                    entities=regex_result.get("entities"),
                    raw_text=text,
                    method="regex"
                )
        
        # 策略4: 结果融合（如果两者都有结果）
        # TODO: 实现结果融合逻辑
        
        # 默认返回未知意图
        logger.warning(f"No valid intent found for text: {text}")
        return IntentData(
            intent="unknown",
            confidence=0.0,
            raw_text=text,
            method="none"
        )

