# NXZ NLU Service

**逆行者语义识别服务** - 自然语言理解服务，用于意图识别和标准化数据返回。

> **NXZ** = **逆行者**（Ni Xing Zhe）  
> **NLU** = Natural Language Understanding（自然语言理解）

NXZ NLU 是一个高性能的自然语言理解服务，专注于语义识别和意图解析，为智能交互系统提供准确、快速的意图识别能力。

## 功能特性

- 🚀 基于 FastAPI 的高性能 Web 服务
- 🎯 **两阶段架构**：领域划分 → 意图识别
- 🤖 **基于 MiniLM 的轻量级模型**（支持多语言）
  - 领域划分：识别文本所属领域（车控、导航、音乐、电话、系统、通用、闲聊）
  - 意图识别：在对应领域下进行意图解析
- 📝 支持正则表达式匹配（优先级可配置）
- 🔄 模型+正则混合策略
- 📊 标准化的 JSON 响应格式
- 🔧 灵活的配置管理
- 📝 自动生成 API 文档
- ⚡ 内置缓存机制，提升推理性能

## 关于项目

NXZ NLU（逆行者语义识别服务）是一个基于深度学习的自然语言理解服务，采用两阶段架构（领域划分 + 意图识别），为智能交互系统提供准确的语义识别能力。

### 项目特点

- 🎯 **精准识别**：两阶段架构确保领域和意图的准确识别
- 🚀 **高性能**：基于 MiniLM 轻量级模型，推理速度快
- 🔧 **易扩展**：模块化设计，支持按领域组织规则和配置
- 📊 **标准化**：统一的 JSON 响应格式，便于集成

## 项目结构

```
NXZ_NLU/
├── app/                        # 应用主目录
│   ├── main.py                 # FastAPI应用入口
│   ├── api/                    # API路由层
│   ├── core/                   # 核心配置和模型
│   ├── services/               # 业务逻辑层
│   │   ├── domain_service.py   # 领域划分服务
│   │   ├── model_service.py    # 模型服务（MiniLM）
│   │   ├── nlu_service.py      # NLU核心服务
│   │   └── regex_service.py    # 正则匹配服务
│   ├── models/                 # 模型处理相关
│   └── utils/                  # 工具函数
├── configs/                    # 配置文件目录
│   ├── regex/                  # 领域正则规则目录
│   │   ├── 车控.json
│   │   ├── 导航.json
│   │   └── ...
│   ├── domain_examples.json    # 领域示例配置
│   ├── intent_examples.json    # 意图示例配置
│   └── ...
├── model_files/                # 模型文件存储（不上传git）
├── tests/                      # 测试目录
└── logs/                       # 日志目录
```

## 快速开始

### 1. 安装依赖

```bash
# 安装所有依赖（包括开发依赖）
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，配置模型路径等参数
```

### 3. 配置模型和正则规则

- **领域示例**: 编辑 `configs/domain_examples.json`（用于领域划分）
- **正则规则**: 编辑 `configs/regex_patterns.json`
- **意图映射**: 编辑 `configs/intent_mappings.json`
- **意图示例**: 编辑 `configs/intent_examples.json`（用于意图识别）
- **模型配置**: 编辑 `configs/model_config.json`

#### MiniLM 模型配置

项目默认使用 `paraphrase-multilingual-MiniLM-L12-v2` 模型，这是一个轻量级的多语言文本嵌入模型。

**模型特点：**
- 模型大小：约 420MB
- 支持多语言（包括中文）
- 推理速度快，适合生产环境
- 通过文本嵌入和相似度匹配实现意图识别

**配置方式：**

1. **使用默认模型**（自动从 HuggingFace 下载）：
   ```bash
   # 在 .env 文件中设置（可选，默认已配置）
   MODEL_NAME=paraphrase-multilingual-MiniLM-L12-v2
   ```

2. **使用本地模型**：
   ```bash
   # 将模型下载到 model_files 目录，然后在 .env 中设置
   MODEL_NAME=./model_files/your-model-name
   ```

3. **配置意图示例**：
   编辑 `configs/intent_examples.json`，为每个意图添加示例文本。模型会通过计算输入文本与这些示例的相似度来识别意图。

### 4. 运行服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 使用示例

### 1. 领域划分

```bash
curl -X POST "http://localhost:8000/api/v1/nlu/domain" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "打开车窗",
       "context": {},
       "session_id": "session_123"
     }'
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "domain": "车控",
    "confidence": 0.92,
    "raw_text": "打开车窗",
    "method": "model"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. 意图识别（两阶段流程）

```bash
curl -X POST "http://localhost:8000/api/v1/nlu/intent" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "打开车窗",
       "context": {},
       "session_id": "session_123"
     }'
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "intent": "vehicle_control",
    "domain": "车控",
    "action": "open",
    "target": "window",
    "confidence": 0.95,
    "entities": {
      "action": "打开",
      "target": "车窗"
    },
    "raw_text": "打开车窗",
    "method": "model"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 3. 直接指定领域进行意图识别

如果已经知道领域，可以直接指定，跳过领域划分阶段：

```bash
curl -X POST "http://localhost:8000/api/v1/nlu/intent" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "打开车窗",
       "domain": "车控",
       "context": {},
       "session_id": "session_123"
     }'
```

## 配置说明

### 环境变量

主要配置项说明：

- `MODEL_PATH`: 模型文件存储路径（默认：`./model_files`）
- `MODEL_NAME`: 模型名称（默认：`paraphrase-multilingual-MiniLM-L12-v2`）
- `MODEL_DEVICE`: 模型运行设备，`cpu` 或 `cuda`（默认：`cpu`）
- `USE_GPU`: 是否使用GPU（默认：`False`）
- `REGEX_PRIORITY`: 是否优先使用正则匹配（默认：`True`）
- `CONFIDENCE_THRESHOLD`: 置信度阈值（默认：`0.5`）
- `SIMILARITY_THRESHOLD`: MiniLM 相似度阈值（默认：`0.6`）
- `DOMAIN_EXAMPLES_PATH`: 领域示例配置文件路径（默认：`./configs/domain_examples.json`）
- `INTENT_EXAMPLES_PATH`: 意图示例配置文件路径（默认：`./configs/intent_examples.json`）
- `REGEX_DOMAIN_DIR`: 领域正则规则目录路径（默认：`./configs/regex`）
- `MAX_SEQUENCE_LENGTH`: 最大序列长度（默认：`128`）

详细配置见 `.env.example`

### 支持的领域

系统支持以下7个领域：

1. **车控** - 车辆控制相关指令（如：打开车窗、关闭空调）
2. **导航** - 导航相关指令（如：导航到北京、查看路况）
3. **音乐** - 音乐播放相关指令（如：播放音乐、下一首）
4. **电话** - 电话相关指令（如：打电话给张三、接听电话）
5. **系统** - 系统设置相关指令（如：打开蓝牙、查看系统版本）
6. **通用** - 通用查询和操作（如：今天天气怎么样、现在几点了）
7. **闲聊** - 闲聊对话（如：你好、讲个笑话）

### 正则规则配置

#### 按领域组织的规则文件（推荐）

正则规则现在按领域组织，每个领域有独立的配置文件：

```
configs/
├── regex_patterns.json          # 通用规则（可选，向后兼容）
└── regex/                       # 领域规则目录
    ├── 车控.json
    ├── 导航.json
    ├── 音乐.json
    ├── 电话.json
    ├── 系统.json
    ├── 通用.json
    └── 闲聊.json
```

**优势：**
- 🚀 **性能优化**：在已知领域的情况下，只匹配该领域的规则，减少匹配次数
- 📝 **易于维护**：每个领域的规则独立管理，互不干扰
- 👥 **团队协作**：不同团队可以并行维护不同领域的规则
- 🔧 **灵活扩展**：新增领域只需添加新文件

**配置示例（车控领域）：**

编辑 `configs/regex/车控.json`：

```json
{
  "domain": "车控",
  "description": "车辆控制相关规则",
  "patterns": [
    {
      "pattern": "(打开|开启|启动)(?P<target>车窗|车门|天窗|空调)",
      "intent": "vehicle_control",
      "action": "open",
      "target": null,
      "confidence": 0.95,
      "group_names": ["action", "target"]
    }
  ]
}
```

**匹配策略：**

1. 如果指定了领域，优先匹配该领域的规则
2. 然后匹配通用规则（`regex_patterns.json`）
3. 如果未指定领域，会尝试匹配所有领域的规则

**向后兼容：**

系统仍然支持旧的单文件格式（`configs/regex_patterns.json`），作为通用规则使用。

## 架构说明

### 两阶段流程

系统采用两阶段架构进行意图识别：

1. **阶段一：领域划分**
   - 使用 MiniLM 模型对输入文本进行领域分类
   - 识别文本所属的领域（车控、导航、音乐等）
   - 支持7个预定义领域

2. **阶段二：意图识别**
   - 在已识别的领域下进行意图解析
   - 使用 MiniLM 模型计算与领域内意图示例的相似度
   - 提取动作（action）和目标（target）等实体信息

### MiniLM 工作原理

MiniLM 模型通过以下步骤进行识别：

1. **文本嵌入**：将输入文本转换为高维向量（嵌入向量）
2. **相似度计算**：计算输入文本与示例的平均嵌入向量的余弦相似度
3. **匹配**：选择相似度最高的结果，如果相似度低于阈值则返回默认值

### 添加新意图

1. **编辑意图示例文件** (`configs/intent_examples.json`)：
   ```json
   {
     "intent_examples": {
       "your_new_intent": {
         "description": "新意图描述",
         "examples": [
           "示例文本1",
           "示例文本2",
           "示例文本3"
         ]
       }
     }
   }
   ```

2. **添加更多示例**：为每个意图提供 5-10 个典型示例，可以提高识别准确率

3. **调整相似度阈值**：如果识别不准确，可以在 `.env` 中调整 `SIMILARITY_THRESHOLD`（范围 0-1）

### 性能优化建议

1. **使用 GPU**（如果可用）：
   ```bash
   USE_GPU=True
   MODEL_DEVICE=cuda
   ```

2. **缓存机制**：模型服务内置了缓存机制，相同文本的重复请求会直接返回缓存结果

3. **批量处理**：对于大量文本，可以考虑批量编码以提高效率

4. **模型量化**（可选）：可以使用 ONNX Runtime 进行模型量化，进一步减少内存占用和提升速度

### 模型选择

项目默认使用 `paraphrase-multilingual-MiniLM-L12-v2`，你也可以选择其他 MiniLM 变体：

- `paraphrase-multilingual-MiniLM-L12-v2`：多语言，平衡性能和准确率（推荐）
- `paraphrase-MiniLM-L6-v2`：英文专用，更小更快
- `all-MiniLM-L6-v2`：通用模型，适合多种任务

## 开发指南

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black app/
```

### 添加新模型

1. 在 `app/services/model_service.py` 中实现模型加载和推理逻辑
2. 在 `.env` 中配置模型路径和名称
3. 确保模型输出格式符合 `IntentData` 结构

## 部署

### Docker 部署（待完善）

```bash
docker build -t nxz-nlu-service .
docker run -p 8000:8000 nxz-nlu-service
```

## 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解每个版本的详细变更记录。

## 许可证

[待指定]

## 贡献

欢迎提交 Issue 和 Pull Request！

