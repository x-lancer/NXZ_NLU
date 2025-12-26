"""
API路由定义
"""
from fastapi import APIRouter, HTTPException, Depends
from app.core.schemas import (
    IntentRequest, IntentResponse, 
    DomainResponse, ErrorResponse
)
from app.services.nlu_service import NLUService
from app.api.dependencies import get_nlu_service

router = APIRouter(tags=["NLU"])


@router.post(
    "/nlu/domain",
    response_model=DomainResponse,
    summary="领域划分",
    description="接收自然语言文本，返回所属领域"
)
async def classify_domain(
    request: IntentRequest,
    nlu_service: NLUService = Depends(get_nlu_service)
):
    """
    领域划分API端点
    
    - **text**: 待分类的文本
    - **context**: 可选的上下文信息
    - **session_id**: 可选的会话ID
    """
    try:
        result = await nlu_service.classify_domain(
            text=request.text,
            context=request.context
        )
        return DomainResponse(
            success=True,
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"领域划分失败: {str(e)}"
        )


@router.post(
    "/nlu/intent",
    response_model=IntentResponse,
    summary="意图识别",
    description="接收自然语言文本，先进行领域划分，再在对应领域下进行意图识别"
)
async def recognize_intent(
    request: IntentRequest,
    nlu_service: NLUService = Depends(get_nlu_service)
):
    """
    意图识别API端点（两阶段流程）
    
    - **text**: 待识别的文本
    - **domain**: 可选的领域（如果提供则跳过领域划分）
    - **context**: 可选的上下文信息
    - **session_id**: 可选的会话ID
    
    流程：
    1. 如果未提供 domain，先进行领域划分
    2. 在对应领域下进行意图识别
    """
    try:
        result = await nlu_service.recognize(
            text=request.text,
            domain=request.domain,
            context=request.context,
            session_id=request.session_id
        )
        return IntentResponse(
            success=True,
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"意图识别失败: {str(e)}"
        )

