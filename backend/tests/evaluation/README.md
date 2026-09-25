# Agent Evaluation

This folder contains offline evaluation cases for the resume diagnosis agent.

The runner disables remote LLM calls and validates the deterministic fallback
pipeline:

- job family profile detection
- multi-perspective diagnosis shape
- evidence chain output
- project deep-dive output
- expected score ranges
- keyword and gap coverage

Run from `backend/`:

```bash
python tests/evaluation/run_agent_eval.py
```

Print a full JSON report to stdout:

```bash
python tests/evaluation/run_agent_eval.py --json
```

Generate `reports/latest.json` and `reports/latest.md`:

```bash
python tests/evaluation/run_agent_eval.py --write-report
```

## RAG Retrieval Evaluation

The RAG runner builds a temporary SQLite vector store, seeds small knowledge
fixtures, and checks whether hybrid retrieval returns the expected source.

It reports:

- Hit@1
- Hit@K
- MRR
- top citation

Run from `backend/`:

```bash
python tests/evaluation/run_rag_eval.py --write-report
```

Generated reports:

- `reports/rag_latest.json`
- `reports/rag_latest.md`
