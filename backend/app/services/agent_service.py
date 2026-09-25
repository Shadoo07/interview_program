from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.prompts.agent_prompts import (
    PERSPECTIVES,
    RUBRIC_VERSION,
    get_diagnosis_summary_prompt,
    get_diagnosis_validation_prompt,
    get_perspective_diagnosis_prompt,
    get_project_deep_dive_prompt,
)
from app.schemas.agent import (
    DiagnoseResult,
    PerspectiveDiagnosis,
    ProjectDeepDive,
    ValidationResult,
)
from app.services.job_profile_service import build_job_profile
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.utils.json_utils import clamp_score, extract_json_object

KEY_SKILLS = [
    "Python",
    "Java",
    "Go",
    "JavaScript",
    "TypeScript",
    "Vue",
    "React",
    "MySQL",
    "PostgreSQL",
    "Redis",
    "Docker",
    "FastAPI",
    "Spring Boot",
    "RAG",
    "LLM",
    "LangChain",
]

PROJECT_STOP_MARKERS = ["教育经历", "实习经历", "工作经历", "技能", "获奖", "证书", "自我评价", "Education", "Experience"]


def diagnose_resume(resume_text: str, jd_content: str, db: Session | None = None) -> dict[str, Any]:
    """
    Diagnose a resume against a target JD.

    Pipeline:
    job-family profile -> project deep dive -> perspective agents ->
    coordinator summary -> consistency validation.
    """
    initial_profile = build_job_profile(jd_content, resume_text)
    rag_references = retrieve_rag_references(db, resume_text, jd_content, initial_profile.get("family_id", ""))
    rag_context = format_rag_references(rag_references)
    jd_with_context = f"{jd_content}\n\n{rag_context}" if rag_context else jd_content

    job_profile = build_job_profile(jd_with_context, resume_text)
    projects = extract_project_candidates(resume_text)

    if llm_service.is_available():
        result = diagnose_with_llm(resume_text, jd_with_context, job_profile, projects, rag_references)
        if result:
            result["source"] = "ai"
            return result

    result = diagnose_with_rules(resume_text, jd_with_context, job_profile, projects, rag_references)
    result["source"] = "rules"
    return result


def diagnose_with_llm(
    resume_text: str,
    jd_content: str,
    job_profile: dict[str, Any],
    projects: list[dict[str, Any]],
    rag_references: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    project_deep_dives = deep_dive_projects_with_llm(projects, job_profile, resume_text, jd_content)
    if not project_deep_dives:
        project_deep_dives = deep_dive_projects_with_rules(projects, job_profile, resume_text)

    from concurrent.futures import ThreadPoolExecutor, as_completed

    perspectives = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(
                diagnose_perspective_with_llm,
                role_id, resume_text, jd_content, job_profile, project_deep_dives,
            ): role_id
            for role_id in PERSPECTIVES
        }
        for future in as_completed(futures):
            perspective = future.result()
            if perspective:
                perspectives.append(perspective)

    if not perspectives:
        return None

    summary = summarize_diagnosis_with_llm(resume_text, jd_content, perspectives, job_profile, project_deep_dives)
    if not summary:
        summary = synthesize_summary_from_perspectives(perspectives, job_profile, project_deep_dives)

    try:
        normalized = normalize_diagnosis_payload(summary, perspectives, job_profile, project_deep_dives, rag_references or [])
        result = DiagnoseResult.model_validate(normalized)
        validation = validate_diagnosis_with_llm(result.model_dump(), resume_text, jd_content)
        result.validation = ValidationResult.model_validate(validation)
        return result.model_dump()
    except ValidationError as exc:
        print(f"Validate diagnosis result error: {exc}")
        return None


def deep_dive_projects_with_llm(
    projects: list[dict[str, Any]],
    job_profile: dict[str, Any],
    resume_text: str,
    jd_content: str,
) -> list[dict[str, Any]]:
    prompt = get_project_deep_dive_prompt(projects, job_profile, resume_text, jd_content)
    response = llm_service.chat(
        [
            {"role": "system", "content": "你是项目深挖面试官。只输出合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.25,
        max_tokens=2200,
    )
    if not response:
        return []

    try:
        data = extract_json_object(response)
        return normalize_project_deep_dives(data.get("project_deep_dives"))
    except (ValueError, ValidationError) as exc:
        print(f"Parse project deep dive error: {exc}")
        return []


def diagnose_perspective_with_llm(
    role_id: str,
    resume_text: str,
    jd_content: str,
    job_profile: dict[str, Any],
    project_deep_dives: list[dict[str, Any]],
) -> dict[str, Any] | None:
    prompt = get_perspective_diagnosis_prompt(role_id, resume_text, jd_content, job_profile, project_deep_dives)
    response = llm_service.chat(
        [
            {"role": "system", "content": "你是简历诊断子 Agent。只输出合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.25,
        max_tokens=1600,
    )
    if not response:
        return None

    try:
        data = extract_json_object(response)
        data["score"] = clamp_score(data.get("score"), default=60)
        perspective = PerspectiveDiagnosis.model_validate(data)
        return perspective.model_dump()
    except (ValueError, ValidationError) as exc:
        print(f"Parse perspective diagnosis error ({role_id}): {exc}")
        return None


def summarize_diagnosis_with_llm(
    resume_text: str,
    jd_content: str,
    perspectives: list[dict[str, Any]],
    job_profile: dict[str, Any],
    project_deep_dives: list[dict[str, Any]],
) -> dict[str, Any] | None:
    prompt = get_diagnosis_summary_prompt(resume_text, jd_content, perspectives, job_profile, project_deep_dives)
    response = llm_service.chat(
        [
            {"role": "system", "content": "你是简历诊断总控 Agent。只输出合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=2600,
    )
    if not response:
        return None

    try:
        return extract_json_object(response)
    except ValueError as exc:
        print(f"Parse diagnosis summary error: {exc}")
        return None


def validate_diagnosis_with_llm(
    result_json: dict[str, Any],
    resume_text: str,
    jd_content: str,
) -> dict[str, Any]:
    prompt = get_diagnosis_validation_prompt(result_json, resume_text, jd_content)
    response = llm_service.chat(
        [
            {"role": "system", "content": "你是 AI 诊断结果质量校验器。只输出合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=700,
    )
    if not response:
        return {"passed": False, "issues": ["二次校验未返回结果"], "fixed": False}

    try:
        data = extract_json_object(response)
        return {
            "passed": bool(data.get("passed", False)),
            "issues": normalize_string_list(data.get("issues")),
            "fixed": bool(data.get("fixed", False)),
        }
    except ValueError as exc:
        return {"passed": False, "issues": [f"二次校验解析失败：{exc}"], "fixed": False}


def normalize_diagnosis_payload(
    data: dict[str, Any],
    perspectives: list[dict[str, Any]],
    job_profile: dict[str, Any],
    project_deep_dives: list[dict[str, Any]],
    rag_references: list[dict[str, Any]],
) -> dict[str, Any]:
    data = dict(data or {})
    data["rubric_version"] = data.get("rubric_version") or RUBRIC_VERSION
    data["overall_score"] = clamp_score(data.get("overall_score"), default=average_score(perspectives))
    data["overall_assessment"] = data.get("overall_assessment") or (
        "已完成岗位画像、多视角诊断和项目深挖，建议优先补强岗位关键词、项目证据和面试追问准备。"
    )
    data["strengths"] = normalize_items(data.get("strengths"), "point", "detail")
    data["weaknesses"] = normalize_items(data.get("weaknesses"), "point", "detail")
    data["improvements"] = normalize_improvements(data.get("improvements"))
    data["career_advice"] = str(data.get("career_advice") or "")
    data["interview_tips"] = normalize_string_list(data.get("interview_tips"))
    data["perspectives"] = data.get("perspectives") or perspectives
    data["evidence_chains"] = normalize_evidence(data.get("evidence_chains")) or collect_perspective_evidence(perspectives)
    data["job_profile"] = data.get("job_profile") or job_profile
    data["project_deep_dives"] = data.get("project_deep_dives") or project_deep_dives
    data["rag_references"] = data.get("rag_references") or rag_references
    return data


def synthesize_summary_from_perspectives(
    perspectives: list[dict[str, Any]],
    job_profile: dict[str, Any],
    project_deep_dives: list[dict[str, Any]],
) -> dict[str, Any]:
    risks = []
    suggestions = []
    for item in perspectives:
        risks.extend(normalize_string_list(item.get("risks")))
        suggestions.extend(normalize_string_list(item.get("suggestions")))
    for item in project_deep_dives:
        risks.extend(normalize_string_list(item.get("evidence_gaps")))
        suggestions.extend(normalize_string_list(item.get("rewrite_suggestions")))

    return {
        "overall_score": average_score(perspectives),
        "overall_assessment": (
            f"已识别目标方向为{job_profile.get('title', '目标岗位')}，并基于岗位画像、三视角诊断和项目深挖完成分析。"
            "整体建议围绕岗位关键词、项目证据和追问准备优先优化。"
        ),
        "strengths": [
            {
                "point": "岗位画像明确",
                "detail": f"系统已识别核心能力要求：{', '.join(job_profile.get('core_skills', [])[:5])}。",
            }
        ],
        "weaknesses": [{"point": "待补强风险", "detail": risk} for risk in risks[:3]],
        "improvements": [
            {"area": "简历优化", "suggestion": suggestion, "priority": "中"}
            for suggestion in suggestions[:4]
        ],
        "career_advice": "优先选择与岗位画像最相关的项目放在前面，并补充能证明工程能力、技术深度和结果指标的证据。",
        "interview_tips": [
            "围绕每个项目准备架构、难点、指标和个人贡献",
            "将岗位画像中的核心技能映射到真实项目案例",
            "提前准备项目失败复盘和技术取舍解释",
        ],
    }


def diagnose_with_rules(
    resume_text: str,
    jd_content: str,
    job_profile: dict[str, Any] | None = None,
    projects: list[dict[str, Any]] | None = None,
    rag_references: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rag_references = rag_references or []
    job_profile = job_profile or build_job_profile(jd_content, resume_text)
    projects = projects or extract_project_candidates(resume_text)
    project_deep_dives = deep_dive_projects_with_rules(projects, job_profile, resume_text)

    found_skills = [skill for skill in KEY_SKILLS if skill.lower() in resume_text.lower()]
    profile_skills = job_profile.get("core_skills", []) + job_profile.get("preferred_skills", [])
    missing_skills = [skill for skill in profile_skills if skill.lower() not in resume_text.lower()]
    has_project = bool(projects)
    has_metrics = has_metric_signal(resume_text)

    strengths = []
    weaknesses = []
    if len(resume_text) > 500:
        strengths.append({"point": "内容信息较完整", "detail": "简历文本较充足，有利于提取教育、项目和技能信息。"})
    else:
        weaknesses.append({"point": "简历内容偏短", "detail": "建议补充项目背景、个人职责、技术方案和结果数据。"})

    strengths.append(
        {
            "point": "岗位方向已识别",
            "detail": f"目标岗位更接近{job_profile.get('title')}，核心关注：{', '.join(job_profile.get('interview_focus', [])[:4])}。",
        }
    )

    if found_skills:
        strengths.append({"point": "技术关键词明确", "detail": f"简历中出现了 {', '.join(found_skills[:6])} 等技术关键词。"})
    else:
        weaknesses.append({"point": "技术栈不够明确", "detail": "建议单独列出语言、框架、数据库、工程工具和 AI/RAG 相关能力。"})

    if has_project:
        strengths.append({"point": "包含项目经历", "detail": "简历中有项目相关描述，可继续强化技术难点和个人贡献。"})
    else:
        weaknesses.append({"point": "项目经历不足", "detail": "建议增加与目标岗位相关的 1-2 个项目，并写清楚技术选型和结果。"})

    if missing_skills:
        weaknesses.append(
            {
                "point": "岗位画像关键词覆盖不足",
                "detail": f"画像要求但简历中不明显的关键词包括：{', '.join(missing_skills[:6])}。",
            }
        )

    if not has_metrics:
        weaknesses.append({"point": "缺少量化结果", "detail": "项目描述中缺少性能、效率、规模、用户量或业务结果等量化证据。"})

    improvements = [
        {
            "area": "岗位画像对齐",
            "suggestion": f"围绕{job_profile.get('title')}能力画像补齐：{', '.join(job_profile.get('resume_keywords', [])[:5])}。",
            "priority": "高",
        },
        {
            "area": "项目证据链补强",
            "suggestion": "每段项目经历按“背景-职责-技术方案-结果指标-复盘”重写，避免只罗列技术名词。",
            "priority": "高",
        },
        {
            "area": "面试追问准备",
            "suggestion": "为每个项目准备架构选择、难点定位、性能优化、失败复盘和个人贡献五类追问答案。",
            "priority": "中",
        },
    ]

    perspectives = build_rule_perspectives(found_skills, missing_skills, has_project, has_metrics, job_profile)
    evidence = collect_perspective_evidence(perspectives)
    evidence.append(
        {
            "claim": "岗位画像识别",
            "evidence": f"匹配信号：{', '.join(job_profile.get('matched_signals', [])[:8]) or '证据不足'}",
            "source": "profile",
        }
    )
    score = average_score(perspectives)

    return {
        "overall_assessment": (
            f"简历已按{job_profile.get('title')}岗位画像完成诊断。建议继续围绕岗位关键词覆盖、项目技术深度、"
            "量化结果和面试追问证据进行优化。"
        ),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvements": improvements,
        "career_advice": "投递前优先选择与目标岗位最相关的项目放在前面，并补充能证明能力画像要求的技术细节和结果指标。",
        "interview_tips": [
            "准备项目架构图和核心链路说明",
            "复盘项目中的技术难点、取舍和失败点",
            "将岗位画像中的核心技能对应到自己的项目案例",
        ],
        "rubric_version": RUBRIC_VERSION,
        "overall_score": score,
        "perspectives": perspectives,
        "evidence_chains": evidence[:6],
        "validation": {"passed": True, "issues": ["当前为规则兜底结果，未经过远程 LLM 二次校验。"], "fixed": False},
        "job_profile": job_profile,
        "project_deep_dives": project_deep_dives,
        "rag_references": rag_references,
    }


def retrieve_rag_references(
    db: Session | None,
    resume_text: str,
    jd_content: str,
    role_family: str = "",
) -> list[dict[str, Any]]:
    if db is None:
        return []
    query = f"{jd_content}\n{resume_text[:1000]}"
    try:
        return rag_service.retrieve_knowledge(db, query, top_k=4, role_family=role_family)
    except Exception as exc:
        print(f"RAG retrieval skipped: {exc}")
        return []


def format_rag_references(references: list[dict[str, Any]]) -> str:
    if not references:
        return ""
    lines = ["RAG 检索上下文："]
    for index, item in enumerate(references, 1):
        lines.append(
            f"[{index}] citation={item.get('citation')} 文档={item.get('document_name')} "
            f"类型={item.get('source_type')} 方向={item.get('role_family')} "
            f"版本={item.get('version')} 分数={item.get('score')}\n{item.get('content')}"
        )
    return "\n\n".join(lines)


def extract_project_candidates(resume_text: str) -> list[dict[str, Any]]:
    lines = [clean_line(line) for line in resume_text.splitlines()]
    lines = [line for line in lines if line]
    projects = []
    current: dict[str, Any] | None = None

    for line in lines:
        if current and is_stop_marker(line):
            projects.append(enrich_project(current))
            current = None
            continue

        if looks_like_project_title(line):
            if current:
                projects.append(enrich_project(current))
            current = {"name": clean_project_name(line), "description": "", "technologies": []}
            continue

        if current and len(current["description"]) < 1400:
            current["description"] = f"{current['description']} {line}".strip()

    if current:
        projects.append(enrich_project(current))

    if projects:
        return projects[:5]

    snippet = find_project_like_snippet(resume_text)
    if snippet:
        return [enrich_project({"name": "简历项目线索", "description": snippet, "technologies": []})]
    return []


def deep_dive_projects_with_rules(
    projects: list[dict[str, Any]],
    job_profile: dict[str, Any],
    resume_text: str,
) -> list[dict[str, Any]]:
    if not projects:
        return [
            ProjectDeepDive(
                project_name="未识别到明确项目",
                relevance_score=30,
                role_assessment="简历中缺少清晰项目标题或项目段落，面试官难以判断候选人的真实贡献。",
                technical_depth="证据不足，无法判断技术深度。",
                evidence_gaps=["补充至少一个与目标岗位相关的项目", "写清楚个人职责、技术方案和结果指标"],
                likely_followups=["你最能代表岗位能力的项目是什么？", "你在项目中具体负责哪一部分？"],
                answer_strategy=["优先选择一个与岗位画像最相关的项目", "按背景、任务、行动、结果组织回答"],
                rewrite_suggestions=["新增“项目经历”模块，并把最相关项目放在第一位"],
                risk_level="high",
            ).model_dump()
        ]

    result = []
    profile_skills = job_profile.get("core_skills", []) + job_profile.get("preferred_skills", [])
    for project in projects[:3]:
        desc = f"{project.get('name', '')} {project.get('description', '')}"
        matched_skills = [skill for skill in profile_skills if skill.lower() in desc.lower()]
        has_role = any(token in desc for token in ["负责", "主导", "实现", "设计", "优化", "参与", "owner", "built", "designed"])
        has_metrics = has_metric_signal(desc)
        score = 45 + len(matched_skills) * 7 + (12 if has_role else 0) + (12 if has_metrics else 0)

        gaps = []
        if not matched_skills:
            gaps.append("项目描述没有明显覆盖岗位画像中的核心技能")
        if not has_role:
            gaps.append("缺少个人职责和贡献边界")
        if not has_metrics:
            gaps.append("缺少量化结果，例如性能、效率、规模、准确率或业务指标")
        for requirement in job_profile.get("project_evidence_requirements", [])[:2]:
            gaps.append(f"建议补充证据：{requirement}")

        relevance = clamp_score(score, default=60)
        risk_level = "low" if relevance >= 80 and len(gaps) <= 2 else "medium"
        if relevance < 60 or len(gaps) >= 4:
            risk_level = "high"

        followups = [
            f"{project.get('name', '该项目')}中你最核心的个人贡献是什么？",
            "你为什么选择当前技术方案？有没有比较过其他方案？",
        ]
        followups.extend(
            [f"请展开说明项目中与{focus}相关的设计、取舍和结果。" for focus in job_profile.get("interview_focus", [])[:3]]
        )

        result.append(
            ProjectDeepDive(
                project_name=project.get("name") or "项目经历",
                relevance_score=relevance,
                role_assessment="有个人贡献线索。" if has_role else "个人职责边界不够清晰。",
                technical_depth=(
                    f"已体现 {', '.join(matched_skills[:5])} 等岗位相关技术。"
                    if matched_skills
                    else "技术深度证据不足，需要补充方案、难点和取舍。"
                ),
                evidence_gaps=gaps[:5],
                likely_followups=followups[:6],
                answer_strategy=[
                    "先用一句话说明项目目标和业务价值",
                    "再说明个人负责的模块、技术方案和关键难点",
                    "最后用量化结果或复盘说明项目效果",
                ],
                rewrite_suggestions=[
                    "把技术名词改成“使用什么技术解决什么问题，产生什么结果”",
                    "补充个人贡献边界，减少“参与”“协助”等弱表达",
                    "增加可验证指标或至少给出规模、复杂度、约束条件",
                ],
                risk_level=risk_level,
            ).model_dump()
        )
    return result


def build_rule_perspectives(
    found_skills: list[str],
    missing_skills: list[str],
    has_project: bool,
    has_metrics: bool,
    job_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    profile_confidence = int(float(job_profile.get("confidence", 0.5)) * 10)
    hr_score = 70 + min(len(found_skills), 5) * 3 - min(len(missing_skills), 4) * 4 + profile_confidence
    tech_score = 62 + (12 if has_project else -8) + min(len(found_skills), 6) * 2 - min(len(missing_skills), 4) * 3
    editor_score = 76 if has_metrics else 64

    return [
        {
            "role": "HR 初筛官",
            "score": clamp_score(hr_score, default=70),
            "summary": "从初筛角度看，岗位画像匹配度、关键词覆盖和信息完整度决定通过率。",
            "evidence": [
                {
                    "claim": "岗位画像",
                    "evidence": f"识别方向：{job_profile.get('title')}，置信度：{job_profile.get('confidence')}",
                    "source": "profile",
                },
                {"claim": "技术关键词覆盖", "evidence": f"已识别关键词：{', '.join(found_skills) or '证据不足'}", "source": "resume"},
            ],
            "risks": ["岗位画像关键词覆盖不足会影响机器筛选和 HR 初筛"] if missing_skills else [],
            "suggestions": ["在技能栈和项目经历中自然补齐岗位画像高频关键词"],
        },
        {
            "role": "技术面试官",
            "score": clamp_score(tech_score, default=68),
            "summary": "从技术面试角度看，需要证明项目真实深度、个人工程贡献和追问可解释性。",
            "evidence": [
                {"claim": "项目经历", "evidence": "简历包含项目描述" if has_project else "项目经历证据不足", "source": "resume"},
                {
                    "claim": "技术深度要求",
                    "evidence": f"岗位关注：{', '.join(job_profile.get('interview_focus', [])[:4])}",
                    "source": "profile",
                },
            ],
            "risks": ["项目缺少技术难点时，容易在追问中暴露准备不足"] if has_project else ["缺少可追问项目会降低技术面评价"],
            "suggestions": ["补充项目架构、核心模块、难点解决、技术取舍和结果指标"],
        },
        {
            "role": "简历编辑专家",
            "score": clamp_score(editor_score, default=65),
            "summary": "从表达角度看，量化结果、动作动词和岗位关键词能显著提升专业度。",
            "evidence": [
                {"claim": "量化表达", "evidence": "已出现量化或优化表达" if has_metrics else "量化结果证据不足", "source": "resume"},
            ],
            "risks": [] if has_metrics else ["缺少结果指标会让项目贡献显得泛泛而谈"],
            "suggestions": ["使用动作动词、岗位关键词和数据指标重写项目 bullet"],
        },
    ]


def normalize_project_deep_dives(items: Any) -> list[dict[str, Any]]:
    normalized = []
    if not isinstance(items, list):
        return normalized
    for item in items:
        if not isinstance(item, dict):
            continue
        item["relevance_score"] = clamp_score(item.get("relevance_score"), default=60)
        item["evidence_gaps"] = normalize_string_list(item.get("evidence_gaps"))
        item["likely_followups"] = normalize_string_list(item.get("likely_followups"))
        item["answer_strategy"] = normalize_string_list(item.get("answer_strategy"))
        item["rewrite_suggestions"] = normalize_string_list(item.get("rewrite_suggestions"))
        risk_level = str(item.get("risk_level") or "medium").lower()
        item["risk_level"] = risk_level if risk_level in {"low", "medium", "high"} else "medium"
        normalized.append(ProjectDeepDive.model_validate(item).model_dump())
    return normalized


def enrich_project(project: dict[str, Any]) -> dict[str, Any]:
    description = str(project.get("description") or "")
    project["description"] = description[:1400]
    project["technologies"] = extract_known_skills(f"{project.get('name', '')} {description}")
    return project


def clean_line(line: str) -> str:
    return line.strip().strip("-*•·| \t")


def looks_like_project_title(line: str) -> bool:
    lower = line.lower()
    if len(line) > 90:
        return False
    return "项目" in line or "project" in lower


def clean_project_name(line: str) -> str:
    name = line.replace("项目经历", "").replace("项目经验", "").replace("Projects", "").replace("Project", "")
    name = name.strip(" ：:-|")
    return name or "项目经历"


def is_stop_marker(line: str) -> bool:
    return len(line) <= 30 and any(marker.lower() in line.lower() for marker in PROJECT_STOP_MARKERS)


def find_project_like_snippet(resume_text: str) -> str:
    lower = resume_text.lower()
    for marker in ["项目", "project", "系统", "平台", "应用"]:
        index = lower.find(marker.lower())
        if index >= 0:
            return resume_text[max(0, index - 120): index + 800].strip()
    return ""


def extract_known_skills(text: str) -> list[str]:
    return [skill for skill in KEY_SKILLS if skill.lower() in text.lower()]


def has_metric_signal(text: str) -> bool:
    metric_tokens = ["%", "提升", "降低", "优化", "用户", "QPS", "ms", "准确率", "召回率", "AUC", "并发", "响应"]
    return any(token in text for token in metric_tokens)


def average_score(perspectives: list[dict[str, Any]]) -> int:
    if not perspectives:
        return 65
    scores = [clamp_score(item.get("score"), default=65) for item in perspectives]
    return round(sum(scores) / len(scores))


def normalize_items(items: Any, key_a: str, key_b: str) -> list[dict[str, str]]:
    normalized = []
    if not isinstance(items, list):
        return normalized
    for item in items:
        if isinstance(item, dict):
            normalized.append({key_a: str(item.get(key_a) or ""), key_b: str(item.get(key_b) or "")})
        elif item:
            normalized.append({key_a: str(item), key_b: ""})
    return normalized


def normalize_improvements(items: Any) -> list[dict[str, str]]:
    normalized = []
    if not isinstance(items, list):
        return normalized
    for item in items:
        if not isinstance(item, dict):
            continue
        priority = str(item.get("priority") or "中")
        if priority not in {"高", "中", "低"}:
            priority = "中"
        normalized.append(
            {
                "area": str(item.get("area") or "简历优化"),
                "suggestion": str(item.get("suggestion") or ""),
                "priority": priority,
            }
        )
    return normalized


def normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize_evidence(items: Any) -> list[dict[str, str]]:
    normalized = []
    if not isinstance(items, list):
        return normalized
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "claim": str(item.get("claim") or ""),
                "evidence": str(item.get("evidence") or "证据不足"),
                "source": str(item.get("source") or "inference"),
            }
        )
    return normalized


def collect_perspective_evidence(perspectives: list[dict[str, Any]]) -> list[dict[str, str]]:
    evidence = []
    for perspective in perspectives:
        evidence.extend(normalize_evidence(perspective.get("evidence")))
    return evidence[:6]
