# Contributing

欢迎提交 issue、建议和 pull request。

## 本地开发

后端：

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
python run.py
```

前端：

```bash
cd frontend
npm install
npm run dev
```

完整本地启动：

```bash
docker compose up --build
```

## 提交前检查

```bash
cd backend
python -m ruff check app tests
python -m compileall app tests
python tests/evaluation/run_agent_eval.py
python tests/evaluation/run_rag_eval.py

cd ../frontend
npm run build
```

## 注意事项

- 不要提交 `.env`、数据库文件、上传文件、日志或真实 API Key。
- 新接口需要补充 Pydantic Schema 和 API 文档。
- 涉及 LLM 输出的功能需要保留结构化校验、异常处理和规则兜底。
- 涉及 RAG 的改动建议同步更新 RAG 评测样例和报告。
