# NXZ NLU Service

自然语言理解服务，用于意图识别和标准化数据返回。

## 功能特性

- 🚀 基于 FastAPI 的高性能 Web 服务
- 🤖 支持小模型推理进行意图识别
- 📝 支持正则表达式匹配（优先级可配置）
- 🔄 模型+正则混合策略
- 📊 标准化的 JSON 响应格式
- 🔧 灵活的配置管理
- 📝 自动生成 API 文档

## 项目结构

```
NXZ_NLU/
├── app/                        # 应用主目录
│   ├── main.py                 # FastAPI应用入口
│   ├── api/                    # API路由层
│   ├── core/                   # 核心配置和模型
│   ├── services/               # 业务逻辑层
│   ├── models/                 # 模型处理相关
│   └── utils/                  # 工具函数
├── configs/                    # 配置文件目录
├── model_files/                # 模型文件存储（不上传git）
├── tests/                      # 测试目录
└── logs/                       # 日志目录
```

## 快速开始

### 1. 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装开发依赖（可选）
pip install -r requirements-dev.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，配置模型路径等参数
```

### 3. 配置模型和正则规则

- **正则规则**: 编辑 `configs/regex_patterns.json`
- **意图映射**: 编辑 `configs/intent_mappings.json`
- **模型配置**: 编辑 `configs/model_config.json`

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

### 意图识别

```bash
curl -X POST "http://localhost:8000/api/v1/nlu/intent" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "打开车窗",
       "context": {},
       "session_id": "session_123"
     }'
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "intent": "vehicle_control",
    "action": "open",
    "target": "window",
    "confidence": 0.95,
    "entities": {
      "action": "打开",
      "target": "车窗"
    },
    "raw_text": "打开车窗",
    "method": "regex"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 配置说明

### 环境变量

主要配置项说明：

- `MODEL_PATH`: 模型文件存储路径
- `MODEL_NAME`: 模型名称（如果使用模型）
- `REGEX_PRIORITY`: 是否优先使用正则匹配（默认True）
- `CONFIDENCE_THRESHOLD`: 置信度阈值（默认0.5）

详细配置见 `.env.example`

### 正则规则配置

在 `configs/regex_patterns.json` 中添加正则表达式规则：

```json
{
  "pattern": "(打开|开启)(?P<target>车窗|车门)",
  "intent": "vehicle_control",
  "action": "open",
  "confidence": 0.95
}
```

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

## 许可证

[待指定]

## 贡献

欢迎提交 Issue 和 Pull Request！

