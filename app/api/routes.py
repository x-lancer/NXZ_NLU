"""
API路由定义
"""
from fastapi import APIRouter, HTTPException, Depends
from app.core.schemas import IntentRequest, IntentResponse, ErrorResponse
from app.services.nlu_service import NLUService
from app.api.dependencies import get_nlu_service

router = APIRouter(tags=["NLU"])


@router.post(
    "/nlu/intent",
    response_model=IntentResponse,
    summary="意图识别",
    description="接收自然语言文本，返回标准化的意图识别结果"
)
async def recognize_intent(
    request: IntentRequest,
    nlu_service: NLUService = Depends(get_nlu_service)
):
    """
    意图识别API端点
    
    - **text**: 待识别的文本
    - **context**: 可选的上下文信息
    - **session_id**: 可选的会话ID
    """
    try:
        result = await nlu_service.recognize(
            text=request.text,
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

