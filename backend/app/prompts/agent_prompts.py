import json
from typing import Any

RUBRIC_VERSION = "resume-diagnosis-v2"

DIAGNOSIS_RUBRIC = """
评分 Rubric：
- 90-100：简历证据充分，项目与 JD 高度一致，表达清晰且可直接用于投递。
- 75-89：整体匹配，存在表达、量化或关键词覆盖不足，可通过局部优化提升。
- 60-74：部分匹配，但项目深度、技术证据或岗位关键词存在明显缺口。
- 0-59：岗位匹配较弱，简历缺少关键经历或内容可信度不足。

证据链要求：
- 每个重要结论必须绑定简历、JD 或岗位画像中的可见信息。
- 不得编造学校、公司、项目指标、获奖或技术细节。
- 证据不足时明确写“证据不足”，并给出补充建议。
"""

PERSPECTIVES = {
    "hr": {
        "role": "HR 初筛官",
        "focus": "排版清晰度、教育背景、岗位基本要求、关键词覆盖、初筛通过概率。",
    },
    "tech": {
        "role": "技术面试官",
        "focus": "项目技术深度、技术栈真实性、项目难点表达、追问风险、工程能力证据。",
    },
    "editor": {
        "role": "简历编辑专家",
        "focus": "表达专业度、动作动词、量化结果、个人贡献、大厂实习投递友好度。",
    },
}


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def get_perspective_diagnosis_prompt(
    role_id: str,
    resume_text: str,
    jd_content: str,
    job_profile: dict[str, Any] | None = None,
    project_deep_dives: list[dict[str, Any]] | None = None,
) -> str:
    perspective = PERSPECTIVES[role_id]
    profile_text = _json(job_profile or {})
    project_text = _json(project_deep_dives or [])
    return f"""
你是{perspective["role"]}，请只从该视角诊断候选人的简历与目标岗位。

关注重点：{perspective["focus"]}

{DIAGNOSIS_RUBRIC}

岗位族能力画像：
{profile_text}

项目深挖初步结论：
{project_text}

简历内容：
{resume_text[:3500]}

目标 JD：
{jd_content[:2500]}

请只返回合法 JSON，不要 Markdown，不要解释：
{{
  "role": "{perspective["role"]}",
  "score": 0,
  "summary": "该视角下 2-3 句话总结",
  "evidence": [
    {{"claim": "结论", "evidence": "来自简历、JD 或岗位画像的具体依据；没有依据写证据不足", "source": "resume|jd|profile|inference"}}
  ],
  "risks": ["可能影响通过率或面试表现的风险"],
  "suggestions": ["可直接执行的优化建议"]
}}
"""


def get_project_deep_dive_prompt(
    projects: list[dict[str, Any]],
    job_profile: dict[str, Any],
    resume_text: str,
    jd_content: str,
) -> str:
    return f"""
你是项目深挖 Agent，目标是判断候选人简历中的项目是否能经得住目标岗位面试追问。

岗位族能力画像：
{_json(job_profile)}

候选项目：
{_json(projects)}

简历原文：
{resume_text[:3500]}

目标 JD：
{jd_content[:2500]}

请对最多 3 个最相关项目做深挖。要求：
1. relevance_score 根据岗位画像和 JD 要求评分。
2. evidence_gaps 必须指出简历中缺失的证据，不要编造。
3. likely_followups 要像真实面试官追问，围绕架构、难点、指标、个人贡献、失败复盘。
4. answer_strategy 给出回答组织策略，不要写完整背诵稿。
5. rewrite_suggestions 给出可直接改简历的方向。
6. risk_level 只能是 low、medium、high。

只返回合法 JSON，不要 Markdown：
{{
  "project_deep_dives": [
    {{
      "project_name": "项目名称",
      "relevance_score": 0,
      "role_assessment": "候选人在项目中的角色与贡献判断",
      "technical_depth": "项目技术深度判断",
      "evidence_gaps": ["缺失证据"],
      "likely_followups": ["高概率追问"],
      "answer_strategy": ["回答策略"],
      "rewrite_suggestions": ["简历改写建议"],
      "risk_level": "low|medium|high"
    }}
  ]
}}
"""


def get_diagnosis_summary_prompt(
    resume_text: str,
    jd_content: str,
    perspective_results: list[dict[str, Any]],
    job_profile: dict[str, Any] | None = None,
    project_deep_dives: list[dict[str, Any]] | None = None,
) -> str:
    return f"""
你是简历诊断总控 Agent。请整合岗位族能力画像、项目深挖结论，以及 HR 初筛官、技术面试官、简历编辑专家三个视角，输出最终诊断。

{DIAGNOSIS_RUBRIC}

岗位族能力画像：
{_json(job_profile or {})}

项目深挖结论：
{_json(project_deep_dives or [])}

简历内容：
{resume_text[:3500]}

目标 JD：
{jd_content[:2500]}

三个视角的结构化诊断：
{_json(perspective_results)}

请遵循以下原则：
1. 总分必须能由岗位画像、项目深挖和三个视角的 score 推导，不能脱离证据链。
2. strengths、weaknesses、improvements 必须具体、可执行。
3. evidence_chains 只保留最关键的 3-6 条证据。
4. priority 只能是“高”“中”“低”。
5. 只返回合法 JSON，不要 Markdown。

返回 JSON：
{{
  "overall_score": 0,
  "overall_assessment": "整体评价，2-3 句话",
  "strengths": [
    {{"point": "优势点", "detail": "基于证据的说明"}}
  ],
  "weaknesses": [
    {{"point": "不足点", "detail": "基于证据的说明"}}
  ],
  "improvements": [
    {{"area": "改进领域", "suggestion": "具体改写或准备建议", "priority": "高|中|低"}}
  ],
  "career_advice": "后续投递和能力补强建议",
  "interview_tips": ["面试准备建议"],
  "evidence_chains": [
    {{"claim": "最终诊断结论", "evidence": "支撑该结论的具体依据", "source": "resume|jd|profile|inference"}}
  ]
}}
"""


def get_diagnosis_validation_prompt(result_json: dict[str, Any], resume_text: str, jd_content: str) -> str:
    result_text = _json(result_json)
    return f"""
你是 AI 输出质量校验器。请检查以下简历诊断结果是否存在问题：
- 是否编造了简历/JD 中没有的事实。
- 分数是否与证据相符。
- 岗位画像是否与 JD 相符。
- 项目深挖是否有具体追问和证据缺口。
- 建议是否具体、可执行。
- JSON 字段是否符合语义。
- 是否有明显自相矛盾。

简历内容：
{resume_text[:3000]}

目标 JD：
{jd_content[:2200]}

待校验诊断：
{result_text}

只返回合法 JSON，不要 Markdown：
{{
  "passed": true,
  "issues": ["发现的问题；没有问题返回空数组"],
  "fixed": false
}}
"""


def get_diagnose_prompt(resume_text: str, jd_content: str) -> str:
    """Backward-compatible prompt for older callers."""
    return get_diagnosis_summary_prompt(resume_text, jd_content, [])
