"""
正则匹配服务测试
"""
import pytest
from app.services.regex_service import RegexService


def test_regex_service_load():
    """测试正则服务加载"""
    service = RegexService()
    service.load_patterns()
    assert service._loaded is True


def test_regex_match():
    """测试正则匹配"""
    service = RegexService()
    service.load_patterns()
    
    result = service.match("打开车窗")
    assert result is not None
    assert result["intent"] == "vehicle_control"
    assert result["action"] == "open"

