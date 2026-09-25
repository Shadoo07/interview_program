"""Offline quality checks for the resume diagnosis agent.

The evaluation intentionally disables remote LLM calls so it can run in CI,
local demos, and interview walkthroughs without API keys.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services import agent_service  # noqa: E402

DEFAULT_CASES_PATH = Path(__file__).resolve().parent / "cases" / "agent_eval_cases.json"
DEFAULT_REPORT_DIR = Path(__file__).resolve().parent / "reports"


def load_cases(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise TypeError("Evaluation cases must be a JSON array")
    return data


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    original_is_available = agent_service.llm_service.is_available
    agent_service.llm_service.is_available = lambda: False
    try:
        result = agent_service.diagnose_resume(case["resume_text"], case["jd_content"])
    finally:
        agent_service.llm_service.is_available = original_is_available

    checks = {
        "source_is_rules": result.get("source") == "rules",
        "has_job_profile": bool(result.get("job_profile")),
        "job_family_matches": check_job_family(result, case),
        "has_perspectives": len(result.get("perspectives") or []) >= 3,
        "has_evidence_chains": bool(result.get("evidence_chains")),
        "has_validation": bool(result.get("validation")),
        "has_project_deep_dive": check_project_deep_dive(result, case),
        "score_in_expected_range": check_score_range(result, case),
        "expected_keywords_present": check_expected_keywords(result, case),
        "expected_gap_keywords_present": check_gap_keywords(result, case),
    }
    passed = all(checks.values())
    return {
        "id": case["id"],
        "title": case.get("title", case["id"]),
        "passed": passed,
        "checks": checks,
        "expected": {
            "family_ids": case.get("expected_family_ids", []),
            "min_overall_score": case.get("min_overall_score"),
            "max_overall_score": case.get("max_overall_score"),
            "keywords": case.get("expected_keywords", []),
            "gap_keywords": case.get("expected_gap_keywords", []),
        },
        "summary": summarize_result(result),
    }


def check_job_family(result: dict[str, Any], case: dict[str, Any]) -> bool:
    expected = set(case.get("expected_family_ids") or [])
    if not expected:
        return True
    actual = (result.get("job_profile") or {}).get("family_id")
    return actual in expected


def check_project_deep_dive(result: dict[str, Any], case: dict[str, Any]) -> bool:
    if not case.get("requires_project_deep_dive", False):
        return True
    dives = result.get("project_deep_dives") or []
    if not dives:
        return False
    return all(item.get("likely_followups") and item.get("evidence_gaps") for item in dives)


def check_score_range(result: dict[str, Any], case: dict[str, Any]) -> bool:
    score = int(result.get("overall_score") or 0)
    min_score = case.get("min_overall_score")
    max_score = case.get("max_overall_score")
    above_min = min_score is None or score >= int(min_score)
    below_max = max_score is None or score <= int(max_score)
    return above_min and below_max


def check_expected_keywords(result: dict[str, Any], case: dict[str, Any]) -> bool:
    keywords = case.get("expected_keywords") or []
    if not keywords:
        return True
    haystack = json.dumps(result, ensure_ascii=False).lower()
    return all(keyword.lower() in haystack for keyword in keywords)


def check_gap_keywords(result: dict[str, Any], case: dict[str, Any]) -> bool:
    keywords = case.get("expected_gap_keywords") or []
    if not keywords:
        return True
    weak_text = json.dumps(
        {
            "weaknesses": result.get("weaknesses", []),
            "improvements": result.get("improvements", []),
            "project_deep_dives": result.get("project_deep_dives", []),
        },
        ensure_ascii=False,
    )
    return any(keyword in weak_text for keyword in keywords)


def summarize_result(result: dict[str, Any]) -> dict[str, Any]:
    profile = result.get("job_profile") or {}
    return {
        "source": result.get("source"),
        "overall_score": result.get("overall_score"),
        "job_family": profile.get("family_id"),
        "job_title": profile.get("title"),
        "project_deep_dives": len(result.get("project_deep_dives") or []),
        "perspectives": len(result.get("perspectives") or []),
        "evidence_chains": len(result.get("evidence_chains") or []),
    }


def print_report(results: list[dict[str, Any]]) -> None:
    total = len(results)
    passed = sum(1 for item in results if item["passed"])
    print(f"Agent evaluation: {passed}/{total} passed")
    for item in results:
        status = "PASS" if item["passed"] else "FAIL"
        summary = item["summary"]
        print(
            f"- [{status}] {item['id']} | family={summary['job_family']} "
            f"score={summary['overall_score']} projects={summary['project_deep_dives']}"
        )
        if not item["passed"]:
            failed_checks = [name for name, ok in item["checks"].items() if not ok]
            print(f"  failed checks: {', '.join(failed_checks)}")


def build_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for item in results if item["passed"])
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total, 4) if total else 0,
        },
        "quality_dimensions": [
            "job_family_detection",
            "multi_perspective_diagnosis",
            "evidence_chain_output",
            "project_deep_dive_output",
            "score_range_guardrail",
            "keyword_and_gap_coverage",
        ],
        "cases": results,
    }


def write_reports(report: dict[str, Any], report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "latest.json"
    markdown_path = report_dir / "latest.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown_report(report), encoding="utf-8")
    print(f"Reports written: {json_path} and {markdown_path}")


def render_markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Agent Evaluation Report",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Pass rate: **{summary['passed']}/{summary['total']}** ({summary['pass_rate']:.0%})",
        f"- Failed cases: **{summary['failed']}**",
        "",
        "## Quality Dimensions",
        "",
    ]
    lines.extend(f"- `{dimension}`" for dimension in report["quality_dimensions"])
    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Case | Status | Job Family | Score | Project Deep Dives | Failed Checks |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for item in report["cases"]:
        status = "PASS" if item["passed"] else "FAIL"
        summary_item = item["summary"]
        failed_checks = [name for name, ok in item["checks"].items() if not ok]
        lines.append(
            "| {case} | {status} | {family} | {score} | {projects} | {failed} |".format(
                case=item["id"],
                status=status,
                family=summary_item.get("job_family") or "-",
                score=summary_item.get("overall_score") or "-",
                projects=summary_item.get("project_deep_dives") or 0,
                failed=", ".join(failed_checks) if failed_checks else "-",
            )
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "The evaluation disables remote LLM calls and validates the deterministic fallback path, "
            "so it can run locally or in CI without API keys.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline agent evaluation cases.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH, help="Path to evaluation case JSON file")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    parser.add_argument("--write-report", action="store_true", help="Write latest.json and latest.md reports")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR, help="Directory for generated reports")
    args = parser.parse_args()

    cases = load_cases(args.cases)
    results = [evaluate_case(case) for case in cases]
    report = build_report(results)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(results)
    if args.write_report:
        write_reports(report, args.report_dir)
    return 0 if all(item["passed"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
