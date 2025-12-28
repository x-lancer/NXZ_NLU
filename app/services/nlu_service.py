"""
NLU核心服务
编排领域划分、模型预测和正则匹配，实现三层并行意图识别
"""
import asyncio
from typing import Optional, Dict, Any
from app.core.schemas import IntentData, DomainData
from app.core.config import settings
from app.services.model_service import ModelService
from app.services.domain_service import DomainService
from app.services.regex_service import RegexService
from app.utils.logger import get_logger
from app.utils.helpers import filter_none_values

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
        识别意图（三层并行架构）
        
        并行路径：
        1. 全局正则匹配（最快路径）
        2. 领域划分 → 特定域正则（中等路径）
        3. 领域划分 → 模型预测（兜底路径）
        
        Args:
            text: 待识别的文本
            domain: 可选的领域（如果提供则跳过领域划分，直接进入意图识别）
            context: 上下文信息
            session_id: 会话ID
        
        Returns:
            IntentData: 意图识别结果
        """
        if not self._initialized:
            raise RuntimeError("NLU Service not initialized")
        
        logger.info(f"Recognizing intent for text: {text}")
        
        # 如果已提供领域，直接进入意图识别阶段（并行执行特定域正则和模型预测）
        if domain:
            return await self._recognize_intent_with_domain(text, domain, context)
        
        # 第一层并行：全局正则 + 领域划分
        return await self._recognize_parallel(text, context)
    
    async def _recognize_parallel(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> IntentData:
        """
        并行识别意图（三层并行架构的核心逻辑）
        """
        # 创建第一层并行任务
        global_regex_task = None
        domain_task = None
        
        if self.regex_service:
            global_regex_task = asyncio.create_task(
                asyncio.to_thread(self.regex_service.match, text, domain=None)
            )
        
        if self.domain_service:
            domain_task = asyncio.create_task(
                self.domain_service.classify_domain(text, context)
            )
        
        # 等待第一层第一个完成
        tasks = []
        if global_regex_task:
            tasks.append(global_regex_task)
        if domain_task:
            tasks.append(domain_task)
        
        if not tasks:
            # 没有可用的服务
            return IntentData(
                intent="unknown",
                domain="通用",
                confidence=0.0,
                raw_text=text,
                method="none"
            )
        
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # 检查全局正则是否完成
        if global_regex_task and global_regex_task in done:
            try:
                regex_result = await global_regex_task
                if regex_result and regex_result.get("confidence", 0) >= settings.CONFIDENCE_THRESHOLD:
                    logger.info(
                        f"Global regex match found: intent={regex_result.get('intent')}, "
                        f"domain={regex_result.get('domain')}, confidence={regex_result.get('confidence'):.3f}"
                    )
                    # 取消领域划分任务（节省资源）
                    if domain_task and domain_task not in done:
                        domain_task.cancel()
                        try:
                            await domain_task  # 等待取消完成
                        except asyncio.CancelledError:
                            pass
                    
                    return self._build_intent_data(
                        regex_result,
                        domain=regex_result.get("domain", "通用"),
                        method="regex_global"
                    )
            except Exception as e:
                logger.error(f"Global regex task failed: {e}", exc_info=True)
        
        # 检查领域划分是否完成
        if domain_task and domain_task in done:
            try:
                domain_result = await domain_task
                detected_domain = "通用"
                if domain_result:
                    detected_domain = domain_result.get("domain", "通用")
                    logger.info(f"Domain classified: {detected_domain}")
                
                # 第二层并行：特定域正则 + 模型预测
                return await self._recognize_intent_parallel(
                    text, detected_domain, context
                )
            except Exception as e:
                logger.error(f"Domain classification task failed: {e}")
                detected_domain = "通用"
                # 即使失败，也继续尝试意图识别
                return await self._recognize_intent_parallel(text, detected_domain, context)
        
        # 如果都还没完成（理论上不应该发生），等待全部完成
        if pending:
            await asyncio.wait(pending)
            # 再次尝试处理
            if global_regex_task and global_regex_task.done():
                regex_result = global_regex_task.result()
                if regex_result and regex_result.get("confidence", 0) >= settings.CONFIDENCE_THRESHOLD:
                    return self._build_intent_data(
                        regex_result,
                        domain=regex_result.get("domain", "通用"),
                        method="regex_global"
                    )
            
            if domain_task and domain_task.done():
                domain_result = domain_task.result()
                detected_domain = domain_result.get("domain", "通用") if domain_result else "通用"
                return await self._recognize_intent_parallel(text, detected_domain, context)
        
        # 默认返回未知意图
        logger.warning(f"No valid intent found for text: {text}")
        return IntentData(
            intent="unknown",
            domain="通用",
            confidence=0.0,
            raw_text=text,
            method="none"
        )
    
    async def _recognize_intent_parallel(
        self,
        text: str,
        domain: str,
        context: Optional[Dict[str, Any]] = None
    ) -> IntentData:
        """
        第二层并行：特定域正则 + 模型预测
        
        Args:
            text: 待识别的文本
            domain: 已识别的领域
            context: 上下文信息
        
        Returns:
            IntentData: 意图识别结果
        """
        # 创建第二层并行任务
        domain_regex_task = None
        model_task = None
        
        if self.regex_service:
            domain_regex_task = asyncio.create_task(
                asyncio.to_thread(self.regex_service.match, text, domain=domain)
            )
        
        if self.model_service:
            model_task = asyncio.create_task(
                self.model_service.predict(text, domain=domain, context=context)
            )
        
        tasks = []
        if domain_regex_task:
            tasks.append(domain_regex_task)
        if model_task:
            tasks.append(model_task)
        
        if not tasks:
            # 没有可用的服务
            return IntentData(
                intent="unknown",
                domain=domain,
                confidence=0.0,
                raw_text=text,
                method="none"
            )
        
        # 等待第二层第一个完成
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # 检查特定域正则是否完成
        if domain_regex_task and domain_regex_task in done:
            try:
                regex_result = await domain_regex_task
                if regex_result and regex_result.get("confidence", 0) >= settings.CONFIDENCE_THRESHOLD:
                    logger.info(
                        f"Domain-specific regex match found: intent={regex_result.get('intent')}, "
                        f"domain={domain}, confidence={regex_result.get('confidence'):.3f}"
                    )
                    # 取消模型预测任务（节省资源）
                    if model_task and model_task not in done:
                        model_task.cancel()
                        try:
                            await model_task  # 等待取消完成
                        except asyncio.CancelledError:
                            pass
                    
                    return self._build_intent_data(
                        regex_result,
                        domain=domain,
                        method="regex_domain_specific"
                    )
            except Exception as e:
                logger.error(f"Domain regex task failed: {e}", exc_info=True)
        
        # 检查模型预测是否完成
        if model_task and model_task in done:
            try:
                model_result = await model_task
                if model_result and model_result.get("confidence", 0) >= settings.CONFIDENCE_THRESHOLD:
                    logger.info(
                        f"Model prediction: intent={model_result.get('intent')}, "
                        f"domain={domain}, confidence={model_result.get('confidence'):.3f}"
                    )
                    # 取消特定域正则任务（节省资源）
                    if domain_regex_task and domain_regex_task not in done:
                        domain_regex_task.cancel()
                        try:
                            await domain_regex_task  # 等待取消完成
                        except asyncio.CancelledError:
                            pass
                    
                    return self._build_intent_data(
                        model_result,
                        domain=domain,
                        method="model"
                    )
            except Exception as e:
                logger.error(f"Model prediction task failed: {e}", exc_info=True)
        
        # 如果都失败，等待另一个完成（用于日志记录）
        if pending:
            await asyncio.wait(pending)
            # 再次检查是否有结果（可能置信度较低）
            if domain_regex_task and domain_regex_task.done():
                regex_result = domain_regex_task.result()
                if regex_result:
                    logger.debug(f"Domain regex matched but confidence too low: {regex_result.get('confidence', 0)}")
                    return self._build_intent_data(
                        regex_result,
                        domain=domain,
                        method="regex_domain_specific"
                    )
            
            if model_task and model_task.done():
                model_result = model_task.result()
                if model_result:
                    logger.debug(f"Model predicted but confidence too low: {model_result.get('confidence', 0)}")
                    return self._build_intent_data(
                        model_result,
                        domain=domain,
                        method="model"
                    )
        
        # 默认返回未知意图
        logger.warning(f"No valid intent found for text: {text} in domain: {domain}")
        return IntentData(
            intent="unknown",
            domain=domain,
            confidence=0.0,
            raw_text=text,
            method="none"
        )
    
    async def _recognize_intent_with_domain(
        self,
        text: str,
        domain: str,
        context: Optional[Dict[str, Any]] = None
    ) -> IntentData:
        """
        在已知领域的情况下识别意图（第二层并行）
        
        Args:
            text: 待识别的文本
            domain: 已知的领域
            context: 上下文信息
        
        Returns:
            IntentData: 意图识别结果
        """
        return await self._recognize_intent_parallel(text, domain, context)
    
    def _build_intent_data(
        self,
        result: Dict[str, Any],
        domain: Optional[str] = None,
        method: str = "unknown"
    ) -> IntentData:
        """
        构建IntentData对象
        
        Args:
            result: 匹配/预测结果字典
            domain: 领域（如果result中没有）
            method: 识别方法
        
        Returns:
            IntentData: 意图识别结果
        """
        # 构建semantic对象（统一格式：所有方法都返回semantic对象）
        semantic_data = None
        semantic_dict = result.get("semantic")
        if semantic_dict:
            # 使用统一的工具函数过滤None值
            filtered_semantic_dict = filter_none_values(semantic_dict)
            if filtered_semantic_dict:  # 只有当过滤后字典不为空时才创建对象
                from app.core.schemas import SemanticData
                semantic_data = SemanticData(**filtered_semantic_dict)
        
        # 过滤entities中的None值（使用统一的工具函数）
        entities = filter_none_values(result.get("entities"))
        
        return IntentData(
            intent=result.get("intent", "unknown"),
            domain=result.get("domain") or domain or "通用",
            semantic=semantic_data,
            confidence=result.get("confidence", 0.0),
            entities=entities,
            raw_text=result.get("raw_text", ""),
            method=method
        )

