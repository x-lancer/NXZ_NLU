"""
依赖注入模块
用于在应用启动时初始化服务，并在请求时注入依赖
"""
from app.services.nlu_service import NLUService


# 使用单例模式管理NLU服务实例
_nlu_service_instance: NLUService = None


def initialize_nlu_service() -> NLUService:
    """初始化NLU服务（在应用启动时调用）"""
    global _nlu_service_instance
    if _nlu_service_instance is None:
        _nlu_service_instance = NLUService()
        _nlu_service_instance.initialize()
    return _nlu_service_instance


def get_nlu_service() -> NLUService:
    """获取NLU服务实例（依赖注入）"""
    if _nlu_service_instance is None:
        raise RuntimeError("NLU服务未初始化，请先调用initialize_nlu_service()")
    return _nlu_service_instance

