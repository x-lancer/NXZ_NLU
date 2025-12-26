"""
自定义异常类
"""


class NLUServiceError(Exception):
    """NLU服务基础异常"""
    pass


class ModelLoadError(NLUServiceError):
    """模型加载失败异常"""
    pass


class RegexPatternError(NLUServiceError):
    """正则表达式错误异常"""
    pass


class ConfigError(NLUServiceError):
    """配置错误异常"""
    pass

