# 更新日志

所有显著的变更都将记录在此文件中。

本项目的版本遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/) 规范。

## [0.0.4] - 2025-12-27

### 重大变更
- **语义字段统一** - 将 `action`, `target`, `position`, `value` 字段统一包装到 `semantic` 对象中
- **Alias 机制统一** - 正则匹配和模型推测统一使用 `vocabulary_groups.json` 的 alias 机制，确保输出格式一致

### 新增
- **SemanticData 模型** - 新增 `SemanticData` 类，统一语义字段结构
- **Alias 字段支持** - 在 `vocabulary_groups.json` 中为每个词汇组添加 `alias` 字段，用于标准化输出
- **执行耗时统计** - API 响应中添加 `elapsed_time` 字段，记录服务执行耗时
- **Domain 字段支持** - 正则规则配置中添加 `domain` 字段，匹配时自动设置正确的领域

### 变更
- **响应格式重构**：
  - `IntentData` 模型重构，语义字段统一到 `semantic` 对象中
  - `entities` 字段只保留中文原始文本，移除英文 alias 和 `_text` 后缀字段
- **正则服务优化**：
  - `_extract_result()` 方法使用 alias 机制，将中文词汇映射为英文标识符
  - 支持从规则配置中读取 `domain` 字段
- **模型服务重构**：
  - `_extract_entities()` 方法重构，使用 `vocabulary_groups.json` 的词汇组和 alias 机制
  - 统一实体提取逻辑，支持提取 `action`, `target`, `position`, `value` 四个字段
  - 移除对 `intent_mappings.json` 的依赖
- **词汇组系统优化**：
  - 删除 `aliases` 字段（简写引用功能），简化配置
  - 优化 `item_to_alias` 映射逻辑，确保更具体的组优先
- **API 响应增强**：
  - 添加 `elapsed_time` 字段，记录服务执行耗时（秒）
  - 改进错误处理，返回更详细的错误信息

### 删除
- **向后兼容代码** - 移除 `nlu_service.py` 中兼容旧格式的代码
- **Aliases 字段** - 从 `vocabulary_groups.json` 中删除 `aliases` 字段

### 技术细节
- 统一使用 `VocabularyManager.get_alias_by_item()` 进行中文到英文的映射
- `semantic` 对象使用英文 alias，`entities` 对象保留中文原始文本
- 正则匹配和模型推测的语义字段结构完全一致

## [0.0.3] - 2025-12-27

### 重大变更
- **架构重构：三层并行架构** - 从串行两阶段架构重构为三层并行架构，性能提升2-6倍
- **并行执行** - 全局正则、领域划分、特定域正则、模型预测并行执行，最快结果优先返回
- **任务自动取消** - 成功时自动取消未完成任务，节省资源

### 新增
- **词汇组系统** - 支持正则规则中的词汇组复用，通过 `{{group_name}}` 语法引用
  - `VocabularyManager` - 词汇组管理器，负责加载和展开词汇组
  - `configs/vocabulary_groups.json` - 词汇组配置文件
  - 支持别名（aliases）机制，简化词汇组引用
- **全领域正则匹配** - `RegexService.match()` 支持 `domain=None` 时的全领域匹配
- **并行执行支持** - `NLUService` 实现三层并行执行逻辑
- **文档**：
  - `docs/REFACTORING_SUMMARY.md` - 重构总结文档
  - `docs/FLOW_ANALYSIS_CORRECTED.md` - 三层并行架构分析
  - `docs/VOCABULARY_GROUPS.md` - 词汇组使用文档
  - `docs/ARCHITECTURE_VOCABULARY_GROUPS.md` - 词汇组架构文档

### 变更
- **NLUService 重构**：
  - `recognize()` 方法重构，实现三层并行架构
  - 新增 `_recognize_parallel()` - 第一层并行逻辑
  - 新增 `_recognize_intent_parallel()` - 第二层并行逻辑
  - 新增 `_build_intent_data()` - 统一的结果构建方法
- **RegexService 重构**：
  - `match()` 方法支持全领域匹配和返回领域信息
  - 优化匹配逻辑，明确区分全领域和指定领域匹配
  - `_extract_result()` 方法返回结果包含 `raw_text` 字段
- **ModelService 优化**：
  - `predict()` 方法返回结果包含 `raw_text` 字段
- **配置优化**：
  - 移除 `REGEX_PRIORITY` 配置项（并行架构不再需要）
  - 新增 `PARALLEL_EXECUTION` 配置项（预留，未来可用于开关）
  - 统一使用 `CONFIDENCE_THRESHOLD` 作为置信度阈值
- **项目版本**：从 `0.0.2` 更新到 `0.0.3`

### 删除
- **过时文档**：
  - `docs/FLOW_ANALYSIS.md` - 原始流程分析文档（已被 CORRECTED 版本替代）
  - `docs/FLOW_ANALYSIS_ADVANCED.md` - 高级流程分析（内容已整合）
  - `docs/FLOW_ANALYSIS_PARALLEL.md` - 并行流程分析（内容已整合）

### 性能提升
- **全局正则快速路径**：性能提升 **6倍**（60ms → 10ms）
- **特定域正则路径**：性能提升 **1.7倍**（55ms → 32ms）
- **模型预测路径**：性能提升 **1.6倍**（80ms → 50ms）
- **整体性能**：平均提升 **2-6倍**，取决于最快路径

### 技术细节
- 使用 `asyncio.wait()` 和 `asyncio.create_task()` 实现并行执行
- 使用 `asyncio.to_thread()` 将同步正则匹配转换为异步任务
- 完善的异常处理和任务取消逻辑
- 详细的日志记录，包括性能指标和路径选择

## [0.0.2] - 2025-12-27

### 新增
- **两阶段 NLU 架构**: 引入领域划分 (Domain Classification) 和意图识别 (Intent Recognition) 的两阶段处理流程
- **领域划分服务**: 新增 `app/services/domain_service.py`，实现基于 MiniLM 的领域划分功能
- **领域划分 API**: 新增 `/api/v1/nlu/domain` 端点，支持单独进行领域划分
- **领域示例配置**: 新增 `configs/domain_examples.json`，包含 7 个领域的示例文本（车控、导航、音乐、电话、系统、通用、闲聊）
- **意图示例配置**: 新增 `configs/intent_examples.json`，用于存储意图示例文本，支持 MiniLM 相似度匹配
- **领域正则规则**: 新增 `configs/regex/` 目录，按领域拆分正则规则文件
  - `configs/regex/车控.json` - 车控领域规则
  - `configs/regex/导航.json` - 导航领域规则
  - `configs/regex/音乐.json` - 音乐领域规则
  - `configs/regex/电话.json` - 电话领域规则
  - `configs/regex/系统.json` - 系统领域规则
  - `configs/regex/通用.json` - 通用领域规则
  - `configs/regex/闲聊.json` - 闲聊领域规则
- **MiniLM 模型集成**:
  - 在 `requirements.txt` 中添加 `sentence-transformers`, `torch`, `transformers` 依赖
  - `app/services/model_service.py` 重构，实现基于 MiniLM 的文本嵌入和相似度匹配进行意图识别
  - 支持文本嵌入缓存和预测结果缓存机制
- **数据模型扩展**:
  - `app/core/schemas.py` 新增 `DomainData` 和 `DomainResponse` 模型
  - `IntentData` 和 `IntentRequest` 新增 `domain` 字段，支持领域信息

### 变更
- **项目版本**: 将项目版本从 `0.0.1` 更新到 `0.0.2` (在 `app/__init__.py` 和 `app/core/config.py` 中)
- **依赖文件合并**: `requirements-dev.txt` 合并到 `requirements.txt` 并删除 `requirements-dev.txt`
- **NLU 服务重构**: `app/services/nlu_service.py` 重构，整合领域划分和意图识别流程，支持两阶段处理
- **正则服务重构**: `app/services/regex_service.py` 重构，支持从 `configs/regex/` 目录按领域加载规则文件，同时保持向后兼容
- **意图识别 API**: `/api/v1/nlu/intent` 端点更新，支持可选的 `domain` 参数，实现领域感知的意图识别
- **配置管理**: `app/core/config.py` 新增配置项：
  - `DOMAIN_EXAMPLES_PATH`: 领域示例配置文件路径
  - `REGEX_DOMAIN_DIR`: 领域正则表达式配置文件目录路径
  - `SIMILARITY_THRESHOLD`: MiniLM 相似度阈值
- **模型配置**: `configs/model_config.json` 更新，支持 MiniLM 相关配置
- **项目描述**: `app/main.py` 更新 FastAPI 应用描述，说明为"逆行者语义识别服务"
- **README 更新**: 更新 `README.md`，添加项目名称解释（NXZ = 逆行者）、两阶段架构说明、MiniLM 使用指南、领域正则规则说明等

### 删除
- **文档文件**: 删除 `ARCHITECTURE.md` 和 `GIT_ENCODING_SETUP.md`（内容已整合到 README）

### 技术细节
- **模型加载**: 优化模型加载逻辑，支持本地路径和 HuggingFace 下载
- **实体提取**: 改进 `ModelService` 中的实体提取逻辑，结合 `intent_examples.json` 和 `intent_mappings.json`
- **日志**: 增强日志输出，提供更详细的服务初始化和预测信息
- **性能优化**: 实现文本嵌入和预测结果缓存，提升推理性能

## [0.0.1] - 2025-12-27

### 新增
- **项目初始化**: 创建 NXZ NLU Service 项目基础结构
- **FastAPI 框架**: 基于 FastAPI 的高性能 Web 服务框架
- **核心服务**:
  - `app/services/nlu_service.py` - NLU 核心服务
  - `app/services/model_service.py` - 模型服务（初始版本）
  - `app/services/regex_service.py` - 正则匹配服务
- **API 端点**: `/api/v1/nlu/intent` - 意图识别 API
- **配置管理**:
  - `app/core/config.py` - 应用配置管理
  - `app/core/schemas.py` - 数据模型定义
  - `configs/intent_mappings.json` - 意图映射配置
  - `configs/regex_patterns.json` - 正则表达式规则配置
  - `configs/model_config.json` - 模型配置
- **项目文档**:
  - `README.md` - 项目说明文档
  - `ARCHITECTURE.md` - 架构文档
  - `GIT_ENCODING_SETUP.md` - Git 编码设置文档
- **开发工具**:
  - `requirements.txt` 和 `requirements-dev.txt` - 依赖管理
  - `run.py` 和 `run.bat` - 启动脚本
  - `.gitignore` - Git 忽略文件配置
- **测试框架**: 基础测试文件（`tests/test_api.py`, `tests/test_regex.py`）
- **日志系统**: `app/utils/logger.py` - 日志工具
- **异常处理**: `app/utils/exceptions.py` - 异常定义

### 功能特性
- 支持正则表达式匹配进行意图识别
- 标准化的 JSON 响应格式
- 灵活的配置管理
- 自动生成 API 文档（Swagger/ReDoc）

[0.0.2]: https://github.com/yourusername/NXZ_NLU/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/yourusername/NXZ_NLU/releases/tag/v0.0.1

