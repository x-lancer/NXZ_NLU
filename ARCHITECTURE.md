# 项目架构说明

## 整体架构

本项目采用分层架构设计，清晰的职责划分便于维护和扩展。

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  (app/main.py)                          │
└─────────────────────────────────────────┘
              │
              ├──────────────────┬──────────────────┐
              │                  │                  │
    ┌─────────▼─────────┐ ┌─────▼──────┐ ┌────────▼────────┐
    │   API Routes      │ │  Schemas   │ │   Dependencies  │
    │  (routes.py)      │ │ (schemas)  │ │ (dependencies)  │
    └─────────┬─────────┘ └────────────┘ └─────────────────┘
              │
              │
    ┌─────────▼─────────┐
    │   NLU Service     │
    │ (nlu_service.py)  │
    └─────────┬─────────┘
              │
       ┌──────┴──────┐
       │             │
┌──────▼──────┐ ┌───▼──────────┐
│   Regex     │ │   Model      │
│  Service    │ │   Service    │
└─────────────┘ └──────────────┘
```

## 目录说明

### app/
应用主目录，包含所有业务代码。

#### app/main.py
- FastAPI 应用入口
- 中间件配置（CORS等）
- 启动/关闭事件处理
- 健康检查端点

#### app/api/
API 路由层，处理 HTTP 请求。

- **routes.py**: API 端点定义
- **dependencies.py**: 依赖注入，管理服务实例

#### app/core/
核心配置和数据模型。

- **config.py**: 使用 Pydantic Settings 管理配置
- **schemas.py**: Pydantic 数据模型（请求/响应）

#### app/services/
业务逻辑层，核心服务实现。

- **nlu_service.py**: NLU 核心服务，编排模型和正则
- **model_service.py**: 模型加载和推理服务
- **regex_service.py**: 正则表达式匹配服务

#### app/models/
模型相关封装（可选扩展）。

- **intent_classifier.py**: 意图分类器封装

#### app/utils/
工具函数和辅助模块。

- **logger.py**: 日志配置
- **exceptions.py**: 自定义异常类

### configs/
配置文件目录。

- **regex_patterns.json**: 正则表达式规则配置
- **intent_mappings.json**: 意图映射和标准化输出模板
- **model_config.json**: 模型相关配置

### tests/
测试目录。

- **test_api.py**: API 端点测试
- **test_regex.py**: 正则匹配服务测试

## 数据流

### 请求流程

1. **客户端请求** → FastAPI 接收 HTTP 请求
2. **路由层** → `routes.py` 解析请求参数
3. **依赖注入** → `dependencies.py` 注入 NLU 服务实例
4. **服务层** → `nlu_service.py` 处理意图识别
   - 优先使用正则匹配（如果启用）
   - 回退到模型预测
   - 可选的结果融合
5. **返回结果** → 标准化的 JSON 响应

### 初始化流程

1. 应用启动 → `startup_event()` 触发
2. 初始化 NLU 服务 → `initialize_nlu_service()`
3. 加载正则规则 → `RegexService.load_patterns()`
4. 加载模型 → `ModelService.load_model()`
5. 服务就绪 → 接收请求

## 设计模式

### 1. 依赖注入
- 使用 FastAPI 的 `Depends()` 进行依赖注入
- 单例模式管理服务实例

### 2. 策略模式
- 正则匹配和模型预测作为不同策略
- 可通过配置切换优先级

### 3. 分层架构
- API 层：处理 HTTP 请求
- 服务层：业务逻辑
- 数据层：模型和配置

## 扩展点

### 1. 添加新的识别方法
在 `NLUService.recognize()` 中添加新的策略分支。

### 2. 支持新的意图类型
- 在 `configs/intent_mappings.json` 中添加新意图
- 在 `configs/regex_patterns.json` 中添加对应规则

### 3. 集成新的模型
在 `ModelService.load_model()` 和 `ModelService.predict()` 中实现模型加载和推理逻辑。

### 4. 结果融合策略
在 `NLUService.recognize()` 中实现多种结果的融合逻辑（加权平均、投票等）。

## 配置管理

使用 Pydantic Settings 管理配置，支持：
- 环境变量覆盖
- 配置文件读取
- 类型验证
- 默认值设置

配置优先级：环境变量 > .env 文件 > 代码默认值

## 日志系统

- 结构化日志输出
- 支持控制台和文件双输出
- 日志轮转（10MB，保留5个文件）
- 可配置日志级别

## 错误处理

- 统一的异常处理
- 自定义异常类
- 友好的错误响应格式
- 详细的错误日志记录

