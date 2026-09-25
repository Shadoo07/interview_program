# Architecture

## 设计目标

Interview AI Agent 采用前后端分离架构，目标是让大学生在一个连续流程中完成简历解析、岗位理解、匹配分析、简历改写和面试准备。

系统设计重点：

- API 层与业务逻辑分离，便于测试和后续扩展。
- LLM 调用集中封装，避免模型供应商耦合到业务代码。
- Schema 先行，方便数据库存储、版本对比、RAG 检索和前端类型对接。
- 本地规则兜底，保证没有模型 Key 时也可以演示基础功能。
- RAG 链路可观测、可评测，支持从命中率和引用来源角度持续优化质量。

## 后端分层

```text
app/
├── main.py
├── core/
│   ├── config.py          # 环境变量配置
│   └── model_presets.py   # 多模型预设
├── routers/               # FastAPI 路由
├── services/              # 业务逻辑
├── schemas/               # Pydantic 请求/响应模型
├── models/                # SQLAlchemy 数据模型
├── prompts/               # Prompt 模板
└── utils/                 # 文件解析、JSON 清洗、文档切分
```

## LLM 调用链路

```mermaid
sequenceDiagram
  participant Web as Vue Frontend
  participant API as FastAPI Router
  participant Service as Domain Service
  participant LLM as LLMService
  participant Model as OpenAI-compatible Model

  Web->>API: POST /api/jd/analyze
  API->>Service: analyze_jd(jd_content)
  Service->>LLM: chat(prompt)
  LLM->>Model: LangChain invoke()
  Model-->>LLM: JSON text
  LLM-->>Service: cleaned text
  Service->>Service: extract_json_object + Pydantic validate
  alt valid JSON
    Service-->>API: structured result
  else invalid or unavailable
    Service->>Service: rules fallback
    Service-->>API: fallback result
  end
  API-->>Web: { code, message, data }
```

## 数据模型

- `HistoryRecord`: 保存一次完整分析链路，包括简历、JD、匹配结果、诊断、改写和面试题。
- `KnowledgeDocument`: 知识库文档元信息，包含来源类型、标签、岗位族、版本、审核状态和内容哈希。
- `KnowledgeChunk`: 文档切分片段，包含 section、字符位置、token 数、内容哈希和 SQLite 本地向量 fallback。
- `knowledge_embeddings`: PostgreSQL + pgvector 模式下的向量索引表，支持 HNSW cosine 检索。

## RAG 链路

```mermaid
flowchart LR
  Upload["上传岗位资料 / 八股题库 / 项目追问"] --> Parse["PDF/DOCX/TXT 解析"]
  Parse --> Chunk["语义 Chunk\n标题/段落/句子窗口"]
  Chunk --> Embed["EmbeddingService\nRemote or Hash Fallback"]
  Embed --> Vector["pgvector / SQLite VectorStore"]
  Query["JD + 简历 + 岗位族"] --> Recall["Hybrid Recall\nVector + Keyword"]
  Vector --> Recall
  Recall --> Rerank["Rerank\n关键词覆盖/短语/元数据"]
  Rerank --> Cite["Citation\nsource/section/chunk/version"]
  Cite --> Agent["Agent Prompt 注入"]
```

RAG 第一版已经打通上传、解析、切分、embedding、向量存储、hybrid retrieval、rerank、citation 和 Agent 诊断注入。Docker Compose 默认启动 PostgreSQL + pgvector；无远程 embedding Key 时会使用 deterministic hash embedding 兜底，便于本地演示和评测。

## 可观测性

- HTTP 请求日志：`request_id`、方法、路径、状态码、耗时。
- LLM 调用统计：调用次数、成功/失败、fallback、最近错误和延迟。
- RAG 调用统计：检索次数、结果数、失败原因和最近引用来源。
- 健康检查：`/api/health/check`、`/api/health/ready`、`/api/health/observability`。

## 测试策略

- 后端：`ruff` 做静态检查，`compileall` 做语法检查。
- 前端：`vue-tsc && vite build` 做类型和构建检查。
- E2E：Playwright 覆盖上传简历、解析、JD 分析和匹配分析主流程。
- Agent Evaluation：覆盖岗位族识别、多视角诊断、项目深挖、证据链和兜底稳定性。
- RAG Evaluation：覆盖 Hit@1、Hit@K、MRR 和 citation 展示。
