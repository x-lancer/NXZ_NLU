"""
NLU核心服务
编排领域划分、模型预测和正则匹配，实现两阶段意图识别
"""
from typing import Optional, Dict, Any
from app.core.schemas import IntentData, DomainData
from app.core.config import settings
from app.services.model_service import ModelService
from app.services.domain_service import DomainService
from app.services.regex_service import RegexService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NLUService:
    """NLU核心服务类"""
    
    def __init__(self):
        self.domain_service: Optional[DomainService] = None
        self.model_service: Optional[ModelService] = None
        self.regex_service: Optional[RegexService] = None
        self._initialized = False
    
    def initialize(self):
        """初始化服务，加载模型和正则规则"""
        if self._initialized:
            return
        
        logger.info("Initializing NLU Service...")
        
        # 初始化领域划分服务
        try:
            self.domain_service = DomainService()
            self.domain_service.load_model()
            logger.info("Domain service initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize domain service: {e}")
        
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
    
    async def classify_domain(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DomainData:
        """
        领域划分
        
        Args:
            text: 待分类的文本
            context: 上下文信息
        
        Returns:
            DomainData: 领域划分结果
        """
        if not self._initialized:
            raise RuntimeError("NLU Service not initialized")
        
        logger.info(f"Classifying domain for text: {text}")
        
        if not self.domain_service:
            logger.warning("Domain service not available, returning default domain")
            return DomainData(
                domain="通用",
                confidence=0.0,
                raw_text=text,
                method="none"
            )
        
        domain_result = await self.domain_service.classify_domain(text, context)
        
        if domain_result:
            return DomainData(
                domain=domain_result.get("domain", "通用"),
                confidence=domain_result.get("confidence", 0.0),
                raw_text=text,
                method="model"
            )
        else:
            return DomainData(
                domain="通用",
                confidence=0.0,
                raw_text=text,
                method="none"
            )
    
    async def recognize(
        self,
        text: str,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> IntentData:
        """
        识别意图（两阶段流程：先领域划分，再意图识别）
        
        Args:
            text: 待识别的文本
            domain: 可选的领域（如果提供则跳过领域划分）
            context: 上下文信息
            session_id: 会话ID
        
        Returns:
            IntentData: 意图识别结果
        """
        if not self._initialized:
            raise RuntimeError("NLU Service not initialized")
        
        logger.info(f"Recognizing intent for text: {text}")
        
        # 阶段1: 领域划分（如果未提供领域）
        detected_domain = domain
        if not detected_domain and self.domain_service:
            domain_result = await self.domain_service.classify_domain(text, context)
            if domain_result:
                detected_domain = domain_result.get("domain", "通用")
                logger.info(f"Detected domain: {detected_domain}")
        elif not detected_domain:
            detected_domain = "通用"
            logger.info(f"Using default domain: {detected_domain}")
        
        # 策略1: 如果启用了正则优先，先尝试正则匹配（在指定领域下）
        if settings.REGEX_PRIORITY and self.regex_service:
            regex_result = self.regex_service.match(text, domain=detected_domain)
            if regex_result and regex_result.get("confidence", 0) >= settings.CONFIDENCE_THRESHOLD:
                logger.info(f"Regex match found: {regex_result}")
                return IntentData(
                    intent=regex_result.get("intent", "unknown"),
                    domain=detected_domain,
                    action=regex_result.get("action"),
                    target=regex_result.get("target"),
                    confidence=regex_result.get("confidence", 0.0),
                    entities=regex_result.get("entities"),
                    raw_text=text,
                    method="regex"
                )
        
        # 策略2: 使用模型预测（在指定领域下）
        if self.model_service:
            model_result = await self.model_service.predict(text, domain=detected_domain, context=context)
            if model_result and model_result.get("confidence", 0) >= settings.CONFIDENCE_THRESHOLD:
                logger.info(f"Model prediction: {model_result}")
                return IntentData(
                    intent=model_result.get("intent", "unknown"),
                    domain=detected_domain,
                    action=model_result.get("action"),
                    target=model_result.get("target"),
                    confidence=model_result.get("confidence", 0.0),
                    entities=model_result.get("entities"),
                    raw_text=text,
                    method="model"
                )
        
        # 策略3: 如果正则未启用优先，但模型失败，再尝试正则（在指定领域下）
        if not settings.REGEX_PRIORITY and self.regex_service:
            regex_result = self.regex_service.match(text, domain=detected_domain)
            if regex_result:
                logger.info(f"Fallback regex match: {regex_result}")
                return IntentData(
                    intent=regex_result.get("intent", "unknown"),
                    domain=detected_domain,
                    action=regex_result.get("action"),
                    target=regex_result.get("target"),
                    confidence=regex_result.get("confidence", 0.0),
                    entities=regex_result.get("entities"),
                    raw_text=text,
                    method="regex"
                )
        
        # 默认返回未知意图
        logger.warning(f"No valid intent found for text: {text}")
        return IntentData(
            intent="unknown",
            domain=detected_domain,
            confidence=0.0,
            raw_text=text,
            method="none"
        )

