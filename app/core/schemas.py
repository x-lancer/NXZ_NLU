"""
Pydantic数据模型定义
定义API请求和响应的数据结构
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class IntentRequest(BaseModel):
    """意图识别请求模型"""
    text: str = Field(..., description="待识别的文本内容", min_length=1)
    domain: Optional[str] = Field(
        default=None,
        description="可选的领域（如果提供则跳过领域划分，直接进行意图识别）"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="可选的上下文信息"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="会话ID，用于多轮对话"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "打开车窗",
                "domain": None,
                "context": {},
                "session_id": "session_123"
            }
        }


class Entity(BaseModel):
    """实体信息"""
    type: str = Field(..., description="实体类型")
    value: str = Field(..., description="实体值")
    start: Optional[int] = Field(None, description="实体在文本中的起始位置")
    end: Optional[int] = Field(None, description="实体在文本中的结束位置")


class DomainData(BaseModel):
    """领域划分结果数据"""
    domain: str = Field(..., description="识别的领域")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    raw_text: str = Field(..., description="原始文本")
    method: Optional[str] = Field(None, description="识别方法：model")


class DomainResponse(BaseModel):
    """领域划分响应模型"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[DomainData] = Field(None, description="领域划分结果数据")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    elapsed_time: Optional[float] = Field(None, description="服务执行耗时（秒）")


class SemanticData(BaseModel):
    """语义信息数据"""
    model_config = ConfigDict(exclude_none=True)
    
    action: Optional[str] = Field(None, description="动作")
    target: Optional[str] = Field(None, description="操作目标")
    position: Optional[str] = Field(None, description="方位（不一定有）")
    value: Optional[str] = Field(None, description="值（不一定有）")
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """重写序列化方法，确保排除 None 值"""
        # 确保 exclude_none=True 被应用
        kwargs.setdefault('exclude_none', True)
        data = super().model_dump(**kwargs)
        # 再次过滤 None 值（双重保障）
        return {k: v for k, v in data.items() if v is not None}


class IntentData(BaseModel):
    """意图识别结果数据"""
    intent: str = Field(..., description="识别的意图")
    domain: Optional[str] = Field(None, description="所属领域")
    semantic: Optional[SemanticData] = Field(None, description="语义信息（action、target、position、value）")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    entities: Optional[Dict[str, Any]] = Field(None, description="提取的实体信息")
    raw_text: str = Field(..., description="原始文本")
    method: Optional[str] = Field(None, description="识别方法：regex/model/hybrid")


class IntentResponse(BaseModel):
    """意图识别响应模型"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[IntentData] = Field(None, description="识别结果数据")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    elapsed_time: Optional[float] = Field(None, description="服务执行耗时（秒）")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "intent": "vehicle_control",
                    "domain": "车控",
                "semantic": {
                    "action": "open",
                    "target": "window",
                    "position": "driver"
                },
                    "confidence": 0.95,
                    "entities": {
                        "action": "打开",
                        "object": "车窗"
                    },
                    "raw_text": "打开车窗",
                    "method": "regex"
                },
                "error": None,
                "timestamp": "2024-01-01T12:00:00Z",
                "elapsed_time": 0.0123
            }
        }


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error: str = Field(..., description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

