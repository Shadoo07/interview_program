# Interview Notes

这份文档用于简历投递和面试讲解，可按需摘取。

## 项目一句话

Interview AI Agent 是一个面向大学生求职场景的 AI 简历与面试辅导 Web 应用，支持简历解析、JD 分析、匹配度评分、多视角诊断、简历改写、面试问题生成和知识库扩展。

## 简历项目描述

基于 Vue 3 + TypeScript + FastAPI 构建前后端分离的 AI 求职辅导系统。系统支持 PDF / DOCX / TXT 简历上传解析，能够提取教育背景、项目经历、技术栈、实习经历等结构化信息；支持目标岗位 JD 分析和多维度匹配度评分，从技术栈、项目经历、教育背景、经验匹配等维度生成关键词覆盖、短板分析和优化建议。后端通过 LangChain 封装 OpenAI-compatible 模型调用，默认接入 DeepSeek V4 Pro，并支持 DeepSeek Flash、Gemini、GPT、Qwen、GLM 等模型预设；JD 分析和匹配分析采用 LLM JSON 输出 + Pydantic 校验 + 规则兜底机制。系统还实现了 pgvector RAG、hybrid retrieval、rerank、citation 展示、知识库版本管理、结构化日志、健康检查、Docker Compose 一键启动和离线评测脚本。

## 技术栈

| 层次 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Vite、Pinia、Vue Router、Axios、Element Plus |
| 后端 | Python 3.11、FastAPI、Pydantic、SQLAlchemy、SQLite、PostgreSQL、pgvector |
| 文档解析 | PyMuPDF、python-docx |
| AI 能力 | LangChain、OpenAI-compatible API、Prompt 模板、JSON 结构化输出 |
| 测试 | Ruff、compileall、Vite build、Playwright E2E |
| 扩展 | RAG、Embedding、VectorStore、rerank、citation、知识库版本管理、Docker Compose |

## 个人职责

1. 设计前后端分离架构，完成 FastAPI 路由、服务层、Schema、数据库模型和 Vue 页面拆分。
2. 实现简历上传、PDF / DOCX / TXT 文本解析、结构化信息抽取和历史记录存储。
3. 封装统一 LLM 服务，支持多模型预设、模型连通性测试、异常处理和结果清洗。
4. 将 JD 分析和匹配分析升级为 LLM JSON 输出，并使用 Pydantic 校验和规则兜底保证稳定性。
5. 实现简历改写、面试题生成、知识库上传、语义 chunk、Embedding、pgvector/SQLite 双路径检索和 Agent RAG 注入。
6. 增加 hybrid retrieval、rerank、citation 展示、知识库版本管理和 RAG 命中率评测。
7. 补充 Playwright E2E、Agent Evaluation、RAG Evaluation、Docker Compose 和结构化日志能力。

## 项目亮点

- **稳定性设计**：LLM 不可用时自动回退规则逻辑，保证无 Key 环境也能演示核心流程。
- **结构化输出**：JD 和匹配分析使用 JSON Prompt + Pydantic 校验，降低前后端字段错配风险。
- **模型可切换**：通过 `LLM_MODEL_PRESET` 切换 DeepSeek、Gemini、GPT、Qwen、GLM 等模型。
- **RAG 质量优化**：知识库文档上传、语义 chunk、Embedding、pgvector、hybrid retrieval、rerank 和 citation 已打通。
- **工程化验证**：后端静态检查、前端构建、Agent Evaluation、RAG Evaluation 和浏览器 E2E 测试形成基础质量闭环。
- **可观测性**：结构化日志记录 HTTP、LLM 和 RAG 调用状态，健康检查接口方便本地部署和排障。

## 面试讲解路线

1. 从用户痛点讲起：大学生简历表达、岗位匹配和面试准备效率低。
2. 展示主流程：上传简历 -> 解析 -> 输入 JD -> 匹配评分 -> 改写/面试题。
3. 讲后端分层：routers / services / schemas / models / prompts / utils。
4. 讲 LLM 工程化：模型预设、连通性测试、JSON 输出、Pydantic 校验、规则兜底。
5. 讲 RAG 质量：chunk 策略、向量召回、关键词召回、rerank、citation、Hit@K 和 MRR。
6. 讲部署和可靠性：Docker Compose、健康检查、结构化日志、模型失败兜底。

## 可量化表达

- 完成 15+ RESTful API，覆盖简历、JD、匹配、诊断、改写、面试题、历史和知识库。
- 支持 3 种简历文件格式解析。
- 支持 6 种简历改写模式和 6 类面试准备问题。
- 支持 6 个模型预设，默认 DeepSeek V4 Pro。
- 支持 pgvector RAG、知识库版本管理和 citation 展示。
- Agent 评测 5/5 passed，RAG 样例评测 Hit@1=1.00、Hit@3=1.00、MRR=1.00。
- 使用 Playwright 覆盖浏览器端核心 E2E 流程。
