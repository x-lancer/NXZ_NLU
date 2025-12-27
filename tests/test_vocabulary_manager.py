"""
词汇组管理器测试
"""
import pytest
from app.services.vocabulary_manager import VocabularyManager
from pathlib import Path


def test_vocabulary_manager_load():
    """测试词汇组管理器加载"""
    manager = VocabularyManager()
    manager.load_vocabularies()
    
    assert manager._loaded is True
    assert len(manager.groups) > 0
    assert "action_open" in manager.groups


def test_get_group():
    """测试获取词汇组"""
    manager = VocabularyManager()
    manager.load_vocabularies()
    
    items = manager.get_group("action_open")
    assert items is not None
    assert "打开" in items
    assert "开启" in items


def test_get_group_pattern():
    """测试获取词汇组正则模式"""
    manager = VocabularyManager()
    manager.load_vocabularies()
    
    pattern = manager.get_group_pattern("action_open")
    assert pattern is not None
    assert "打开" in pattern or "\\u6253\\u5f00" in pattern  # 转义后的字符


def test_expand_pattern():
    """测试展开模式模板"""
    manager = VocabularyManager()
    manager.load_vocabularies()
    
    # 测试简单展开
    template = "{{action_open}}{{target_window}}"
    expanded = manager.expand_pattern(template)
    
    assert expanded != template
    assert "(" in expanded  # 应该包含分组
    assert ")" in expanded


def test_expand_pattern_with_named_group():
    """测试包含命名分组的模式展开"""
    manager = VocabularyManager()
    manager.load_vocabularies()
    
    template = "{{action_open}}(?P<target>{{target_window}})"
    expanded = manager.expand_pattern(template)
    
    assert "(?P<target>" in expanded
    assert "打开" in expanded or "开启" in expanded


def test_expand_pattern_backward_compatible():
    """测试向后兼容性（不使用词汇组的模式）"""
    manager = VocabularyManager()
    manager.load_vocabularies()
    
    # 没有词汇组引用的模式应该保持不变
    template = "(打开|开启)(车窗|车门)"
    expanded = manager.expand_pattern(template)
    
    assert expanded == template


def test_alias():
    """测试别名功能"""
    manager = VocabularyManager()
    manager.load_vocabularies()
    
    # 使用别名获取组
    items_by_alias = manager.get_group("打开")  # 通过别名
    items_by_id = manager.get_group("action_open")  # 通过ID
    
    assert items_by_alias == items_by_id


def test_integration_regex_service():
    """测试与RegexService的集成"""
    from app.services.regex_service import RegexService
    
    service = RegexService()
    service.load_patterns()
    
    assert service.vocab_manager is not None
    assert service.vocab_manager._loaded is True


def test_match_with_vocabulary_groups():
    """测试使用词汇组的规则匹配"""
    from app.services.regex_service import RegexService
    
    service = RegexService()
    service.load_patterns()
    
    # 测试匹配
    result = service.match("打开主驾驶车窗", domain="车控")
    
    if result:
        assert result["intent"] == "vehicle_control"
        assert result["action"] == "open"

