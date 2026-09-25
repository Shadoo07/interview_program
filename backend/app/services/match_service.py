
from pydantic import ValidationError

from app.prompts.match_prompts import get_match_analysis_prompt
from app.schemas.match_schema import DimensionScore, MatchAnalysisResult
from app.services.llm_service import llm_service
from app.utils.json_utils import clamp_score, extract_json_object


def analyze_match(resume_data: dict, jd_data: dict) -> MatchAnalysisResult:
    if not resume_data or not jd_data:
        raise ValueError("简历数据和JD数据不能为空")

    if llm_service.is_available():
        result = analyze_match_with_llm(resume_data, jd_data)
        if result:
            return result

    return analyze_match_with_rules(resume_data, jd_data)


def analyze_match_with_llm(resume_data: dict, jd_data: dict) -> MatchAnalysisResult | None:
    prompt = get_match_analysis_prompt(resume_data, jd_data)
    response = llm_service.chat(
        [
            {"role": "system", "content": "你是简历与岗位匹配度分析专家，只输出合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=2200,
    )
    if not response:
        return None

    try:
        data = extract_json_object(response)
        data = normalize_match_payload(data)
        return MatchAnalysisResult.model_validate(data)
    except (ValueError, ValidationError) as exc:
        print(f"Parse match LLM response error: {exc}")
        return None


def normalize_match_payload(data: dict) -> dict:
    data["overall_score"] = clamp_score(data.get("overall_score"))
    dimensions = data.get("dimension_scores", [])
    if isinstance(dimensions, dict):
        dimensions = [
            {"dimension": name, "score": score}
            for name, score in dimensions.items()
        ]

    default_weights = {
        "技术栈": 0.35,
        "项目经历": 0.25,
        "教育背景": 0.15,
        "经验匹配": 0.25,
    }
    normalized_dimensions = []
    for item in dimensions if isinstance(dimensions, list) else []:
        if not isinstance(item, dict):
            continue
        dimension = str(item.get("dimension", "其他"))
        normalized_dimensions.append({
            "dimension": dimension,
            "score": clamp_score(item.get("score")),
            "max_score": 100,
            "weight": float(item.get("weight") or default_weights.get(dimension, 0.25)),
            "matched_keywords": item.get("matched_keywords") if isinstance(item.get("matched_keywords"), list) else [],
            "missing_keywords": item.get("missing_keywords") if isinstance(item.get("missing_keywords"), list) else [],
        })
    data["dimension_scores"] = normalized_dimensions

    for key in ["matched_keywords", "missing_keywords", "weak_points", "suggestions"]:
        if not isinstance(data.get(key), list):
            data[key] = []
    if data.get("match_level") not in ["优秀", "良好", "一般", "较差"]:
        data["match_level"] = get_match_level(data["overall_score"])
    return data


def analyze_match_with_rules(resume_data: dict, jd_data: dict) -> MatchAnalysisResult:
    dimension_scores = []

    tech_score, tech_matched, tech_missing = calculate_tech_match(resume_data, jd_data)
    project_score, project_matched, project_missing = calculate_project_match(resume_data, jd_data)
    education_score, edu_matched, edu_missing = calculate_education_match(resume_data, jd_data)
    experience_score, exp_matched, exp_missing = calculate_experience_match(resume_data, jd_data)

    dimension_scores.append(DimensionScore(
        dimension="技术栈",
        score=tech_score,
        weight=0.35,
        matched_keywords=tech_matched,
        missing_keywords=tech_missing
    ))

    dimension_scores.append(DimensionScore(
        dimension="项目经历",
        score=project_score,
        weight=0.25,
        matched_keywords=project_matched,
        missing_keywords=project_missing
    ))

    dimension_scores.append(DimensionScore(
        dimension="教育背景",
        score=education_score,
        weight=0.15,
        matched_keywords=edu_matched,
        missing_keywords=edu_missing
    ))

    dimension_scores.append(DimensionScore(
        dimension="经验匹配",
        score=experience_score,
        weight=0.25,
        matched_keywords=exp_matched,
        missing_keywords=exp_missing
    ))

    overall_score = calculate_overall_score(dimension_scores)
    all_matched = [kw for dim in dimension_scores for kw in dim.matched_keywords]
    all_missing = [kw for dim in dimension_scores for kw in dim.missing_keywords]

    weak_points = generate_weak_points(dimension_scores, all_missing)
    suggestions = generate_suggestions(dimension_scores, all_missing)
    match_level = get_match_level(overall_score)

    return MatchAnalysisResult(
        overall_score=overall_score,
        dimension_scores=dimension_scores,
        matched_keywords=all_matched,
        missing_keywords=all_missing,
        weak_points=weak_points,
        suggestions=suggestions,
        match_level=match_level
    )


def calculate_tech_match(resume_data: dict, jd_data: dict) -> tuple[int, list[str], list[str]]:
    resume_skills = extract_resume_skills(resume_data)
    jd_skills = jd_data.get('required_skills', []) + jd_data.get('nice_to_have_skills', [])

    if not jd_skills:
        return 70, [], []

    matched = []
    missing = []

    for skill in jd_skills:
        if any(skill.lower() in rs.lower() for rs in resume_skills):
            matched.append(skill)
        else:
            missing.append(skill)

    score = int((len(matched) / len(jd_skills)) * 100) if jd_skills else 0
    return score, matched, missing


def extract_resume_skills(resume_data: dict) -> list[str]:
    skills = []

    if 'skills' in resume_data:
        for skill_item in resume_data['skills']:
            if isinstance(skill_item, dict) and 'items' in skill_item:
                skills.extend(skill_item['items'])

    if 'projects' in resume_data:
        for project in resume_data['projects']:
            if isinstance(project, dict) and 'technologies' in project:
                skills.extend(project['technologies'])

    return skills


def calculate_project_match(resume_data: dict, jd_data: dict) -> tuple[int, list[str], list[str]]:
    projects = resume_data.get('projects', [])
    responsibilities = jd_data.get('responsibilities', [])

    if not responsibilities or not projects:
        return 60, [], []

    matched = []
    missing = []
    project_descriptions = []

    for project in projects:
        if isinstance(project, dict):
            desc = project.get('description', '')
            role = project.get('role', '')
            project_descriptions.append(f"{role} {desc}")

    project_text = ' '.join(project_descriptions).lower()

    for responsibility in responsibilities:
        keywords = extract_keywords(responsibility)
        found = False
        for keyword in keywords[:3]:
            if keyword.lower() in project_text:
                matched.append(keyword)
                found = True
                break
        if not found:
            missing.append(responsibility[:20] + '...' if len(responsibility) > 20 else responsibility)

    score = min(100, int((len(matched) / len(responsibilities)) * 100) + 30)
    return min(100, score), matched, missing


def extract_keywords(text: str) -> list[str]:
    keywords = []
    tech_keywords = ['开发', '设计', '实现', '构建', '优化', '维护', '搭建', '迭代', '部署', '测试', '架构']
    for kw in tech_keywords:
        if kw in text:
            keywords.append(kw)
    return keywords if keywords else [text[:10]]


def calculate_education_match(resume_data: dict, jd_data: dict) -> tuple[int, list[str], list[str]]:
    resume_degree = get_resume_degree(resume_data)
    jd_education = jd_data.get('education_requirement', '')

    if not jd_education:
        return 80, [], []

    degree_order = {'博士': 4, '硕士': 3, '本科': 2, '大专': 1}
    resume_level = degree_order.get(resume_degree, 0)
    jd_level = degree_order.get(jd_education, 0)

    if resume_level >= jd_level:
        return 100, [resume_degree], []
    elif resume_level > 0:
        return 60, [resume_degree], [jd_education]
    else:
        return 40, [], [jd_education]


def get_resume_degree(resume_data: dict) -> str:
    if resume_data.get('basic_info'):
        degree = resume_data['basic_info'].get('degree', '')
        if degree:
            return degree

    if 'education' in resume_data:
        for edu in resume_data['education']:
            if isinstance(edu, dict) and 'degree' in edu:
                return edu['degree']

    return ''


def calculate_experience_match(resume_data: dict, jd_data: dict) -> tuple[int, list[str], list[str]]:
    resume_exp = calculate_resume_experience(resume_data)
    jd_exp = jd_data.get('experience_requirement', '')

    if not jd_exp:
        return 70, [], []

    jd_years = extract_experience_years(jd_exp)

    if resume_exp >= jd_years:
        return 100, [f"{resume_exp}年经验"], []
    elif resume_exp >= jd_years * 0.6:
        return 70, [f"{resume_exp}年经验"], [f"需要{jd_years}年经验"]
    elif resume_exp > 0:
        return 40, [f"{resume_exp}年经验"], [f"需要{jd_years}年经验"]
    else:
        return 20, [], [f"需要{jd_years}年经验"]


def calculate_resume_experience(resume_data: dict) -> int:
    exp = 0

    if 'internships' in resume_data:
        exp += len(resume_data['internships'])

    if 'projects' in resume_data:
        project_count = len(resume_data['projects'])
        exp += min(project_count, 3)

    return exp


def extract_experience_years(exp_text: str) -> int:
    import re
    match = re.search(r'(\d+)年', exp_text)
    if match:
        return int(match.group(1))
    if '应届' in exp_text:
        return 0
    if '不限' in exp_text:
        return 0
    return 3


def calculate_overall_score(dimension_scores: list[DimensionScore]) -> int:
    total = 0.0
    total_weight = 0.0

    for dim in dimension_scores:
        total += dim.score * dim.weight
        total_weight += dim.weight

    return int(total / total_weight) if total_weight > 0 else 0


def generate_weak_points(dimension_scores: list[DimensionScore], missing_keywords: list[str]) -> list[str]:
    weak_points = []

    for dim in dimension_scores:
        if dim.score < 60:
            weak_points.append(f"{dim.dimension}匹配度较低 ({dim.score}分)")

    if len(missing_keywords) > 3:
        weak_points.append(f"缺少{len(missing_keywords)}个关键技能/要求")

    return weak_points[:5]


def generate_suggestions(dimension_scores: list[DimensionScore], missing_keywords: list[str]) -> list[str]:
    suggestions = []

    for dim in dimension_scores:
        if dim.score < 60:
            suggestions.append(f"建议补充{dim.dimension}相关经历，重点关注: {', '.join(dim.missing_keywords[:3])}")

    if missing_keywords:
        suggestions.append(f"建议学习以下技能: {', '.join(missing_keywords[:5])}")

    suggestions.append("建议在简历中突出与JD匹配的关键词")
    suggestions.append("建议量化项目成果，增加说服力")

    return suggestions[:6]


def get_match_level(score: int) -> str:
    if score >= 80:
        return "优秀"
    elif score >= 60:
        return "良好"
    elif score >= 40:
        return "一般"
    else:
        return "较差"
