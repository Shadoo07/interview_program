# Roadmap

## 已完成

- FastAPI 后端基础框架与 Vue 3 + Vite 前端。
- PDF / DOCX / TXT 简历上传、解析和结构化抽取。
- JD 分析、匹配度评分、多视角诊断、简历改写和面试问题生成。
- LangChain + OpenAI-compatible LLM 封装，默认 DeepSeek V4 Pro，支持多模型预设。
- LLM JSON 输出、Pydantic 校验、规则兜底和模型连通性测试。
- 历史记录存储和知识库管理基础接口。
- PostgreSQL + pgvector、Embedding 封装、知识库种子导入和 Agent RAG 注入。
- Hybrid retrieval、chunk 优化、rerank、citation 和知识库版本管理。
- 后端结构化日志、健康检查、就绪检查和 LLM/RAG 观测快照。
- Docker Compose 一键启动：frontend + backend + postgres/pgvector。
- Agent Evaluation 和 RAG Retrieval Evaluation。
- 前端构建 chunk 拆分优化。
- SSE 流式输出：简历改写和面试自我介绍支持 token 级实时流式生成。
- 诊断管线并行化：三视角 Agent 并行执行，延迟降低 30%+。

## 短期优化

- 在前端知识库页面展示 citation、rerank score、版本过滤器和审核状态。
- 增加更多真实岗位 JD、八股题库和项目追问样例，扩大 RAG 评测集。
- 为简历上传、知识库上传和模型连通性测试补充更多异常态提示。
- 增加 GitHub Actions 构建缓存和测试报告上传。

## 中期优化

- 引入 Alembic 管理数据库迁移。
- 增加用户账号、管理员权限和知识库管理员角色。
- 增加历史分析版本对比和简历版本 diff。
- 增加模板化 PDF 简历导出和面试准备报告导出。
- 增加 query rewrite、cross-encoder rerank 或 LLM rerank。

## 长期方向

- 面试模拟对话 Agent：围绕项目经历持续追问，并根据回答质量给反馈。
- 岗位投递看板：记录岗位、JD、简历版本、投递状态和准备进度。
- 多语言简历与英文面试准备。
- 知识库质量平台：批量导入、审核流、版本发布、评测趋势和回滚。
