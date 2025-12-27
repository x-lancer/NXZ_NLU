# 可复用词汇组系统使用指南

## 概述

可复用词汇组系统允许您定义常用的词汇集合，并在正则表达式规则中引用这些词汇组，从而实现：
- **复用性**：一次定义，多处使用
- **可维护性**：修改词汇组定义，所有使用该组的地方自动更新
- **可读性**：使用有意义的组名，规则更易理解
- **一致性**：确保相同概念使用相同的词汇

## 架构设计

### 核心组件

1. **VocabularyManager** (`app/services/vocabulary_manager.py`)
   - 负责加载和管理词汇组定义
   - 提供词汇组展开功能
   - 支持别名和缓存

2. **RegexService** (`app/services/regex_service.py`)
   - 集成词汇组管理器
   - 在加载规则时自动展开词汇组引用
   - 保持向后兼容（原有规则仍可正常使用）

3. **配置文件** (`configs/vocabulary_groups.json`)
   - JSON格式的词汇组定义
   - 支持嵌套引用和别名

## 配置文件格式

### 基本结构

```json
{
  "description": "可复用的正则词汇组定义",
  "version": "1.0",
  "groups": {
    "group_id": {
      "name": "组名称",
      "description": "组描述",
      "items": ["词汇1", "词汇2", "词汇3"]
    }
  },
  "aliases": {
    "别名": "group_id"
  }
}
```

### 示例配置

```json
{
  "groups": {
    "action_open": {
      "name": "打开动作",
      "description": "表示打开、开启的动作词汇",
      "items": ["打开", "开启", "启动", "开"]
    },
    "target_window": {
      "name": "车窗",
      "description": "车窗相关的词汇",
      "items": ["车窗", "车窗玻璃", "窗户玻璃", "窗户"]
    },
    "position_driver": {
      "name": "主驾驶位置",
      "description": "主驾驶相关的词汇",
      "items": ["主驾驶", "主驾", "主驾驶位置", "驾驶位"]
    }
  },
  "aliases": {
    "打开": "action_open",
    "车窗": "target_window",
    "主驾": "position_driver"
  }
}
```

## 在规则中使用词汇组

### 语法格式

在正则表达式模式中使用 `{{group_id}}` 来引用词汇组：

```json
{
  "pattern": "{{action_open}}{{position_driver}}{{target_window}}",
  "intent": "vehicle_control",
  "action": "open"
}
```

### 展开结果

上面的规则会被展开为：

```
(打开|开启|启动|开)(主驾驶|主驾|主驾驶位置|驾驶位)(车窗|车窗玻璃|窗户玻璃|窗户)
```

### 高级用法

#### 1. 与命名分组结合

```json
{
  "pattern": "{{action_open}}(?P<target>{{target_window}})",
  "intent": "vehicle_control"
}
```

#### 2. 可选分组

```json
{
  "pattern": "{{action_open}}(?:{{position_driver}})?{{target_window}}",
  "intent": "vehicle_control"
}
```

#### 3. 混合使用

```json
{
  "pattern": "({{action_open}}|{{action_close}})(?P<target>{{target_window}}|{{target_door}})",
  "intent": "vehicle_control"
}
```

#### 4. 使用别名

```json
{
  "pattern": "{{打开}}{{主驾}}{{车窗}}",
  "intent": "vehicle_control"
}
```

## 实际示例

### 示例1：车控规则

**词汇组定义：**
```json
{
  "action_open": {
    "items": ["打开", "开启", "启动"]
  },
  "target_window": {
    "items": ["车窗", "车窗玻璃", "窗户玻璃"]
  },
  "position_driver": {
    "items": ["主驾驶", "主驾", "主驾驶位置"]
  }
}
```

**规则定义：**
```json
{
  "pattern": "{{action_open}}(?:{{position_driver}})?{{target_window}}",
  "intent": "vehicle_control",
  "action": "open"
}
```

**输入文本：** `打开主驾驶车窗`

**匹配结果：**
- `action`: "打开"
- `target`: "主驾驶车窗"
- `intent`: "vehicle_control"

### 示例2：完整的车控规则

```json
{
  "patterns": [
    {
      "pattern": "{{action_open}}(?P<target>(?:{{position_all}})?(?:{{target_window}}|{{target_door}}|{{target_sunroof}}))",
      "intent": "vehicle_control",
      "action": "open",
      "confidence": 0.95
    },
    {
      "pattern": "{{action_close}}(?P<target>(?:{{position_all}})?(?:{{target_window}}|{{target_door}}|{{target_sunroof}}))",
      "intent": "vehicle_control",
      "action": "close",
      "confidence": 0.95
    }
  ]
}
```

## 性能优化

### 1. 编译缓存

词汇组管理器会自动缓存展开后的正则表达式，避免重复计算。

### 2. 模式排序

词汇按长度降序排列，确保长词优先匹配（避免"主驾"匹配到"主驾驶"的一部分）。

### 3. 特殊字符转义

默认情况下，词汇组中的特殊字符会被自动转义，确保正则表达式正确。

## 最佳实践

### 1. 命名规范

- 使用有意义的组ID：`action_open` 而不是 `a1`
- 使用下划线分隔单词：`target_window` 而不是 `targetWindow`
- 保持一致性：所有动作用 `action_` 前缀，所有目标用 `target_` 前缀

### 2. 词汇组织

- **粒度适中**：不要太大（难以维护），也不要太小（失去复用价值）
- **语义清晰**：每个组代表一个明确的语义概念
- **避免重复**：相同概念的词汇只定义一次

### 3. 规则设计

- **优先使用词汇组**：对于常用词汇，尽量使用词汇组而不是硬编码
- **保持简洁**：规则模板应该易于阅读和理解
- **文档化**：为复杂的词汇组添加清晰的描述

### 4. 维护建议

- **版本控制**：将词汇组定义纳入版本控制
- **测试覆盖**：添加测试确保词汇组正确展开
- **定期审查**：定期检查是否有重复或过时的词汇组

## 向后兼容

系统完全向后兼容：
- 如果规则中没有使用 `{{group_id}}` 语法，规则会原样使用
- 如果词汇组管理器加载失败，系统会继续工作（仅记录警告）
- 原有的正则表达式规则无需修改即可继续使用

## 扩展性

### 自定义词汇组

只需在 `configs/vocabulary_groups.json` 中添加新的组定义即可：

```json
{
  "groups": {
    "custom_action": {
      "name": "自定义动作",
      "items": ["自定义词1", "自定义词2"]
    }
  }
}
```

### 动态加载

词汇组在服务启动时加载，修改配置文件后需要重启服务。未来可以考虑支持热重载。

## 故障排查

### 问题1：词汇组未展开

**症状**：规则中的 `{{group_id}}` 没有被替换

**可能原因**：
1. 词汇组ID不存在
2. 词汇组管理器加载失败

**解决方法**：
- 检查 `configs/vocabulary_groups.json` 文件是否存在
- 检查日志中的错误信息
- 确认词汇组ID拼写正确

### 问题2：匹配失败

**症状**：使用词汇组的规则无法匹配预期文本

**可能原因**：
1. 词汇组中没有包含需要的词汇
2. 正则表达式展开后格式错误

**解决方法**：
- 检查展开后的正则表达式（查看日志中的debug信息）
- 验证词汇组中是否包含所有需要的词汇
- 使用正则表达式测试工具验证展开后的模式

## 总结

可复用词汇组系统提供了：
- ✅ 代码复用：一次定义，多处使用
- ✅ 易于维护：集中管理词汇，修改更方便
- ✅ 提高可读性：使用语义化的组名
- ✅ 向后兼容：不影响现有规则
- ✅ 性能优化：编译缓存，高效展开

这使得正则表达式规则的编写和维护变得更加高效和可维护。

