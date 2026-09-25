# Agent Evaluation Report

- Generated at: `2026-04-30T17:54:25.707960+00:00`
- Pass rate: **5/5** (100%)
- Failed cases: **0**

## Quality Dimensions

- `job_family_detection`
- `multi_perspective_diagnosis`
- `evidence_chain_output`
- `project_deep_dive_output`
- `score_range_guardrail`
- `keyword_and_gap_coverage`

## Case Results

| Case | Status | Job Family | Score | Project Deep Dives | Failed Checks |
| --- | --- | --- | ---: | ---: | --- |
| ai_application_strong | PASS | ai_application | 76 | 1 | - |
| backend_missing_metrics | PASS | java_backend | 74 | 1 | - |
| frontend_project | PASS | frontend | 74 | 1 | - |
| algorithm_weak_evidence | PASS | algorithm | 58 | 1 | - |
| product_ops | PASS | product_ops | 67 | 1 | - |

## Notes

The evaluation disables remote LLM calls and validates the deterministic fallback path, so it can run locally or in CI without API keys.
