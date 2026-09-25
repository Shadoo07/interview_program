# API Reference

所有接口返回统一结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

## Health

### GET `/api/health/check`

服务健康检查。

### GET `/api/health/llm-config`

查看当前模型配置，不返回完整 API Key。

### GET `/api/health/llm-models`

返回可选模型预设。

### GET `/api/health/llm-test`

实际调用一次模型，返回是否成功、耗时和错误提示。

## Resume

### POST `/api/resume/upload`

上传简历文件。支持 `pdf`、`docx`、`txt`。

请求类型：`multipart/form-data`

字段：

| name | type | required |
| --- | --- | --- |
| file | File | yes |

### POST `/api/resume/parse`

根据 `file_id` 提取原始文本。

```json
{
  "file_id": "20260430120000_xxxxxxxx.pdf"
}
```

### POST `/api/resume/structure`

将原始简历文本解析为结构化字段。

```json
{
  "raw_text": "简历原始文本"
}
```

### POST `/api/resume/rewrite`

按指定模式生成优化后的 Markdown 简历。

```json
{
  "resume_data": {},
  "jd_data": {},
  "raw_text": "简历原始文本",
  "rewrite_mode": "backend_developer"
}
```

可选 `rewrite_mode`：

- `big_company_intern`
- `backend_developer`
- `ai_developer`
- `project_enhance`
- `hr_friendly`
- `one_page`

## JD

### POST `/api/jd/analyze`

分析岗位 JD。服务优先使用 LLM JSON 输出，失败时规则兜底。

```json
{
  "jd_content": "岗位描述文本"
}
```

## Match

### POST `/api/match/analyze`

分析简历与 JD 的匹配度。

```json
{
  "resume_data": {},
  "jd_data": {}
}
```

返回包含：

- `overall_score`
- `dimension_scores`
- `matched_keywords`
- `missing_keywords`
- `weak_points`
- `suggestions`
- `match_level`

## Agent

### POST `/api/agent/diagnose`

生成多视角简历诊断。

```json
{
  "resume_text": "简历文本",
  "jd_content": "岗位描述"
}
```

## Interview

### POST `/api/interview/questions`

生成面试问题和回答提示。

```json
{
  "resume_data": {},
  "jd_data": {},
  "raw_text": "简历原始文本"
}
```

## History

### GET `/api/history/list`

获取历史记录列表。

### GET `/api/history/{id}`

获取历史记录详情。

### DELETE `/api/history/{id}`

删除历史记录。

## Knowledge

### POST `/api/knowledge/upload`

上传知识库文档。

### GET `/api/knowledge/list`

获取知识库文档列表。

### POST `/api/knowledge/search`

Hybrid 检索知识库片段，支持向量召回、关键词召回、rerank、岗位族加权和版本过滤。

```json
{
  "keyword": "AI 应用开发 RAG 项目追问",
  "top_k": 5,
  "use_vector": true,
  "rerank": true,
  "role_family": "ai_application",
  "version": "v2"
}
```

返回结果包含 `citation`、`retrieval_score`、`rerank_score`、`section_title`、`version` 等字段，可直接用于前端引用来源展示。

### GET `/api/knowledge/versions`

按 `version + source_type + role_family + status` 聚合知识库版本，返回文档数量、chunk 数和最近创建时间。

### PATCH `/api/knowledge/{id}`

更新知识库文档元数据，支持 `source_type`、`tags`、`role_family`、`version`、`status`，用于知识库审核和版本管理。

### DELETE `/api/knowledge/{id}`

删除知识库文档。
