"""
配置管理模块
使用Pydantic Settings管理应用配置
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # 项目基本信息
    PROJECT_NAME: str = "NXZ NLU Service"
    VERSION: str = "0.0.2"
    API_V1_PREFIX: str = "/api/v1"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = Field(
        default=["*"],
        description="允许的跨域源"
    )
    
    # 模型配置
    MODEL_PATH: str = Field(
        default="./model_files",
        description="模型文件路径"
    )
    MODEL_NAME: str = Field(
        default="paraphrase-multilingual-MiniLM-L12-v2",
        description="模型名称（MiniLM模型名称或本地路径）"
    )
    USE_GPU: bool = Field(
        default=False,
        description="是否使用GPU"
    )
    MODEL_DEVICE: str = Field(
        default="cpu",
        description="模型运行设备：cpu/cuda"
    )
    # MiniLM 特定配置
    INTENT_EXAMPLES_PATH: str = Field(
        default="./configs/intent_examples.json",
        description="意图示例配置文件路径（用于相似度匹配）"
    )
    DOMAIN_EXAMPLES_PATH: str = Field(
        default="./configs/domain_examples.json",
        description="领域示例配置文件路径（用于领域划分）"
    )
    SIMILARITY_THRESHOLD: float = Field(
        default=0.6,
        description="相似度阈值（0-1之间）"
    )
    MAX_SEQUENCE_LENGTH: int = Field(
        default=128,
        description="最大序列长度"
    )
    
    # 配置文件路径
    REGEX_CONFIG_PATH: str = Field(
        default="./configs/regex_patterns.json",
        description="正则表达式配置文件路径（通用规则，向后兼容）"
    )
    REGEX_DOMAIN_DIR: str = Field(
        default="./configs/regex",
        description="领域正则规则目录路径（按领域组织的规则文件）"
    )
    INTENT_CONFIG_PATH: str = Field(
        default="./configs/intent_mappings.json",
        description="意图映射配置文件路径"
    )
    MODEL_CONFIG_PATH: str = Field(
        default="./configs/model_config.json",
        description="模型配置文件路径"
    )
    
    # NLU服务配置
    REGEX_PRIORITY: bool = Field(
        default=True,
        description="是否优先使用正则匹配"
    )
    CONFIDENCE_THRESHOLD: float = Field(
        default=0.5,
        description="模型置信度阈值"
    )
    
    # 日志配置
    LOG_LEVEL: str = Field(
        default="INFO",
        description="日志级别"
    )
    LOG_DIR: str = Field(
        default="./logs",
        description="日志目录"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

