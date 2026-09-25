
from app.prompts.resume_prompts import get_resume_rewrite_prompt
from app.schemas.rewrite_schema import ResumeRewriteResult
from app.services.llm_service import llm_service


def rewrite_resume(
    resume_data: dict,
    jd_data: dict,
    raw_text: str,
    rewrite_mode: str,
    match_result: dict | None = None,
    diagnose_result: dict | None = None
) -> ResumeRewriteResult:
    if not resume_data or not jd_data:
        raise ValueError("简历数据和JD数据不能为空")

    original_analysis = analyze_original_resume(resume_data, jd_data, match_result)

    # 优先使用大模型
    if llm_service.is_available():
        result = rewrite_with_llm(resume_data, jd_data, raw_text, rewrite_mode, original_analysis)
        if result:
            return result

    # 降级到规则模板
    content, reasons, project_text = rewrite_with_rules(resume_data, jd_data, rewrite_mode)
    notes = generate_notes(rewrite_mode)

    return ResumeRewriteResult(
        original_analysis=original_analysis,
        rewritten_content=content,
        rewrite_reasons=reasons,
        project_experience_text=project_text,
        notes=notes
    )


def rewrite_with_llm(
    resume_data: dict,
    jd_data: dict,
    raw_text: str,
    rewrite_mode: str,
    original_analysis: str
) -> ResumeRewriteResult | None:
    """使用大模型进行简历改写"""
    prompt = get_resume_rewrite_prompt(resume_data, jd_data, raw_text, rewrite_mode)

    messages = [
        {"role": "system", "content": "你是一位专业的简历优化专家，请根据用户需求改写简历。"},
        {"role": "user", "content": prompt}
    ]

    response = llm_service.chat(messages, temperature=0.7, max_tokens=3000)

    if response:
        reasons = [
            "基于AI分析，针对目标岗位优化",
            "突出与岗位匹配的技能和经验",
            "优化语言表达，提升专业度",
            "保持真实，不编造经历"
        ]

        notes = [
            "此简历由AI生成，请根据实际情况调整",
            "建议保留真实的项目经历和技能",
            "如有实习经历请补充具体工作内容"
        ]

        return ResumeRewriteResult(
            original_analysis=original_analysis,
            rewritten_content=response,
            rewrite_reasons=reasons,
            project_experience_text="请查看改写后的简历内容",
            notes=notes
        )

    return None


def rewrite_with_llm_stream(
    resume_data: dict,
    jd_data: dict,
    raw_text: str,
    rewrite_mode: str,
    original_analysis: str
):
    """流式使用大模型进行简历改写，逐块 yield 文本内容"""
    prompt = get_resume_rewrite_prompt(resume_data, jd_data, raw_text, rewrite_mode)

    messages = [
        {"role": "system", "content": "你是一位专业的简历优化专家，请根据用户需求改写简历。"},
        {"role": "user", "content": prompt}
    ]

    yield from llm_service.chat_stream(messages, temperature=0.7, max_tokens=3000)


def rewrite_with_rules(resume_data: dict, jd_data: dict, rewrite_mode: str) -> tuple:
    """使用规则模板进行简历改写（兜底方案）"""
    if rewrite_mode == "big_company_intern":
        return big_company_intern_mode(resume_data, jd_data)
    elif rewrite_mode == "backend_developer":
        return backend_developer_mode(resume_data, jd_data)
    elif rewrite_mode == "ai_developer":
        return ai_developer_mode(resume_data, jd_data)
    elif rewrite_mode == "project_enhance":
        return project_enhance_mode(resume_data, jd_data)
    elif rewrite_mode == "hr_friendly":
        return hr_friendly_mode(resume_data, jd_data)
    elif rewrite_mode == "one_page":
        return one_page_mode(resume_data, jd_data)
    else:
        return default_mode(resume_data, jd_data)


def analyze_original_resume(resume_data: dict, jd_data: dict, match_result: dict) -> str:
    analysis = "【原始简历分析】\n\n"

    basic = resume_data.get("basic_info", {})
    if basic.get("name"):
        analysis += f"- 候选人：{basic['name']}\n"
    if basic.get("degree"):
        analysis += f"- 学历：{basic['degree']}\n"

    skills = []
    if resume_data.get("skills"):
        for skill_cat in resume_data["skills"]:
            if isinstance(skill_cat, dict) and "items" in skill_cat:
                skills.extend(skill_cat["items"])
    if skills:
        analysis += f"- 现有技能：{', '.join(skills[:5])}\n"

    projects = resume_data.get("projects", [])
    analysis += f"- 项目数量：{len(projects)}个\n"

    jd_title = jd_data.get("position_title", "未知岗位")
    analysis += f"\n【目标岗位】\n- {jd_title}\n"

    if match_result:
        score = match_result.get("overall_score", 0)
        analysis += f"\n【匹配度】\n- 综合评分：{score}分\n"
        if match_result.get("weak_points"):
            analysis += "- 短板：" + "; ".join(match_result["weak_points"][:3]) + "\n"

    return analysis


def big_company_intern_mode(resume_data: dict, jd_data: dict) -> tuple:
    basic = resume_data.get("basic_info", {})
    projects = resume_data.get("projects", [])
    internships = resume_data.get("internships", [])

    content = f"""# {basic.get('name', 'XXX')} - 简历

## 基本信息
- 姓名：{basic.get('name', 'XXX')}
- 电话：{basic.get('phone', 'XXX')}
- 邮箱：{basic.get('email', 'XXX')}
- 学校：{basic.get('school', 'XXX')}
- 专业：{basic.get('major', 'XXX')}
- 学历：{basic.get('degree', '本科')}

## 求职意向
- 目标岗位：{jd_data.get('position_title', '软件开发工程师')}
- 期望城市：{basic.get('city', '北京/上海/深圳')}
- 实习时间：6个月以上

## 教育背景
"""

    for edu in resume_data.get("education", []):
        content += f"- {edu.get('school', 'XXX大学')} | {edu.get('major', 'XXX专业')} | {edu.get('degree', '本科')}\n"
        content += f"  {edu.get('duration', '')}\n"

    content += "\n## 专业技能\n"
    content += format_skills(resume_data)

    content += "\n## 实习经历\n"
    for intern in internships[:2]:
        content += f"- **{intern.get('company', 'XXX公司')}** | {intern.get('position', '实习生')}\n"
        content += f"  {intern.get('duration', '')}\n"
        content += f"  {intern.get('description', '负责日常开发工作')}\n\n"

    content += "## 项目经历\n"
    for proj in projects[:3]:
        content += f"### {proj.get('name', 'XXX项目')}\n"
        content += f"- **项目描述**：{proj.get('description', '项目描述')}\n"
        content += f"- **技术栈**：{', '.join(proj.get('technologies', []))}\n"
        content += f"- **个人职责**：{proj.get('role', '参与开发')}\n"
        content += "- **量化成果**：提升效率XX%，优化性能XX%\n\n"

    reasons = [
        "突出实习经历和项目成果，符合大厂招聘偏好",
        "强调量化成果和技术栈匹配度",
        "优化排版结构，便于HR快速浏览",
        "增加求职意向明确性"
    ]

    project_text = ""
    for proj in projects[:3]:
        project_text += f"{proj.get('name', 'XXX项目')}：{proj.get('description', '')}。技术栈：{', '.join(proj.get('technologies', []))}。\n"

    return content, reasons, project_text


def backend_developer_mode(resume_data: dict, jd_data: dict) -> tuple:
    basic = resume_data.get("basic_info", {})
    projects = resume_data.get("projects", [])

    content = f"""# {basic.get('name', 'XXX')} - 后端开发工程师

## 基本信息
- 姓名：{basic.get('name', 'XXX')} | 电话：{basic.get('phone', 'XXX')} | 邮箱：{basic.get('email', 'XXX')}
- 学历：{basic.get('degree', '本科')} | 学校：{basic.get('school', 'XXX大学')}
- 工作年限：{basic.get('experience', '3年以上')}

## 专业技能
"""
    content += format_skills(resume_data)

    jd_skills = jd_data.get("required_skills", [])
    if jd_skills:
        content += "\n### 岗位匹配技能\n"
        content += f"- 符合要求：{', '.join(jd_skills[:5])}\n"

    content += "\n## 项目经验\n"
    for proj in projects[:4]:
        content += f"### {proj.get('name', 'XXX项目')}\n"
        content += f"- **技术架构**：{', '.join(proj.get('technologies', []))}\n"
        content += f"- **核心模块**：{proj.get('description', '负责后端开发')}\n"
        content += "- **性能优化**：接口响应时间优化XX%，QPS提升至XX\n\n"

    content += "\n## 实习/工作经历\n"
    for intern in resume_data.get("internships", [])[:2]:
        content += f"- **{intern.get('company', 'XXX公司')}** | {intern.get('position', '后端开发')}\n"
        content += f"  {intern.get('duration', '')}\n\n"

    reasons = [
        "突出后端技术栈和架构能力",
        "强调性能优化经验",
        "匹配JD技能要求进行高亮",
        "结构化展示项目复杂度"
    ]

    project_text = ""
    for proj in projects[:3]:
        project_text += f"【{proj.get('name', 'XXX项目')}】技术栈：{', '.join(proj.get('technologies', []))}。负责：{proj.get('description', '')}。\n"

    return content, reasons, project_text


def ai_developer_mode(resume_data: dict, jd_data: dict) -> tuple:
    basic = resume_data.get("basic_info", {})
    projects = resume_data.get("projects", [])

    content = f"""# {basic.get('name', 'XXX')} - AI应用开发工程师

## 基本信息
- 姓名：{basic.get('name', 'XXX')} | 邮箱：{basic.get('email', 'XXX')}
- 学历：{basic.get('degree', '硕士')} | 专业：{basic.get('major', '计算机科学')}

## AI技能栈
- 机器学习框架：PyTorch, TensorFlow, scikit-learn
- NLP技术：BERT, Transformers, 文本分类
- 深度学习：CNN, RNN, Attention机制

## 专业技能
"""
    content += format_skills(resume_data)

    content += "\n## AI项目经验\n"
    ai_projects = [p for p in projects if contains_ai_keywords(p)]
    for proj in ai_projects[:3] or projects[:3]:
        content += f"### {proj.get('name', 'XXX项目')}\n"
        content += f"- **任务目标**：{proj.get('description', 'AI模型开发')}\n"
        content += f"- **技术方案**：使用{', '.join(proj.get('technologies', ['PyTorch']))}实现\n\n"

    reasons = [
        "突出AI相关技能和项目",
        "强调模型效果和技术创新",
        "符合AI岗位的技术评估标准",
        "结构化展示学术背景"
    ]

    project_text = ""
    for proj in ai_projects[:3] or projects[:3]:
        project_text += f"【{proj.get('name', 'XXX项目')}】{proj.get('description', '')}。技术：{', '.join(proj.get('technologies', []))}。\n"

    return content, reasons, project_text


def project_enhance_mode(resume_data: dict, jd_data: dict) -> tuple:
    basic = resume_data.get("basic_info", {})
    projects = resume_data.get("projects", [])

    content = f"""# {basic.get('name', 'XXX')} - 项目经验强化版

## 基本信息
- 姓名：{basic.get('name', 'XXX')} | 电话：{basic.get('phone', 'XXX')} | 邮箱：{basic.get('email', 'XXX')}

## 项目经历（详细版）
"""
    for proj in projects[:4]:
        content += f"---\n\n## {proj.get('name', 'XXX项目')}\n\n"
        content += "### 项目概述\n"
        content += f"{proj.get('description', '项目描述')}\n\n"
        content += "### 技术架构\n"
        content += f"- 技术栈：{', '.join(proj.get('technologies', []))}\n\n"
        content += "### 个人职责\n"
        content += f"- {proj.get('role', '核心开发')}\n\n"
        content += "### 量化成果\n"
        content += "- 性能提升：接口响应时间优化XX%\n\n"

    content += "## 专业技能\n"
    content += format_skills(resume_data)

    reasons = [
        "详细展开项目经历，突出技术深度",
        "强调个人职责和技术贡献",
        "加入量化成果展示",
        "便于面试官深入了解项目细节"
    ]

    project_text = ""
    for proj in projects[:3]:
        project_text += f"【项目名称】{proj.get('name', 'XXX项目')}\n【项目描述】{proj.get('description', '')}\n【技术栈】{', '.join(proj.get('technologies', []))}\n\n"

    return content, reasons, project_text


def hr_friendly_mode(resume_data: dict, jd_data: dict) -> tuple:
    basic = resume_data.get("basic_info", {})
    projects = resume_data.get("projects", [])

    content = f"""# {basic.get('name', 'XXX')}

📍 {basic.get('phone', 'XXX')} | 📧 {basic.get('email', 'XXX')} | 🏫 {basic.get('school', 'XXX大学')}

## 💡 核心优势
"""
    skills = []
    if resume_data.get("skills"):
        for skill_cat in resume_data["skills"]:
            if isinstance(skill_cat, dict) and "items" in skill_cat:
                skills.extend(skill_cat["items"])
    content += f"- 技能匹配：{', '.join(skills[:6])}\n"

    jd_title = jd_data.get("position_title", "XXX岗位")
    content += f"- 目标岗位：{jd_title}\n"

    content += "\n## 📚 教育背景\n"
    for edu in resume_data.get("education", [])[:2]:
        content += f"- {edu.get('school', 'XXX大学')} | {edu.get('major', 'XXX专业')} | {edu.get('degree', '本科')}\n"

    content += "\n## 💼 实习经历\n"
    for intern in resume_data.get("internships", [])[:2]:
        content += f"- **{intern.get('company', 'XXX公司')}** | {intern.get('position', '实习生')}\n"

    content += "\n## 🚀 项目亮点\n"
    for proj in projects[:3]:
        content += f"- **{proj.get('name', 'XXX项目')}**\n"
        content += f"  技术：{', '.join(proj.get('technologies', []))}\n"

    reasons = [
        "使用符号标签，提升视觉吸引力",
        "突出核心优势，便于HR快速筛选",
        "精简内容，控制在一页内",
        "关键词前置，优化ATS扫描"
    ]

    project_text = ""
    for proj in projects[:3]:
        project_text += f"{proj.get('name', 'XXX')}：{', '.join(proj.get('technologies', []))}。\n"

    return content, reasons, project_text


def one_page_mode(resume_data: dict, jd_data: dict) -> tuple:
    basic = resume_data.get("basic_info", {})
    projects = resume_data.get("projects", [])

    content = f"""# {basic.get('name', 'XXX')}

**联系方式** | {basic.get('phone', 'XXX')} | {basic.get('email', 'XXX')} | {basic.get('school', 'XXX大学')}

---

## 求职意向
{jd_data.get('position_title', '软件开发工程师')} | {basic.get('city', '北京')}

## 教育背景
"""
    for edu in resume_data.get("education", [])[:2]:
        content += f"{edu.get('school', 'XXX')} | {edu.get('major', 'XXX')} | {edu.get('degree', '本科')}\n"

    content += "\n## 专业技能\n"
    skills = []
    if resume_data.get("skills"):
        for skill_cat in resume_data["skills"]:
            if isinstance(skill_cat, dict) and "items" in skill_cat:
                skills.extend(skill_cat["items"])
    content += f"{', '.join(skills[:10])}\n"

    content += "\n## 项目经验\n"
    for proj in projects[:2]:
        content += f"- **{proj.get('name', 'XXX')}**：{proj.get('description', '')[:50]}... | {', '.join(proj.get('technologies', []))}\n"

    reasons = [
        "精简内容至一页，适合快速浏览",
        "突出关键信息，去除冗余",
        "清晰的分栏布局",
        "便于打印和线下投递"
    ]

    project_text = ""
    for proj in projects[:2]:
        project_text += f"{proj.get('name', 'XXX')}：{proj.get('description', '')[:50]} | {', '.join(proj.get('technologies', []))}\n"

    return content, reasons, project_text


def default_mode(resume_data: dict, jd_data: dict) -> tuple:
    basic = resume_data.get("basic_info", {})

    content = f"""# {basic.get('name', 'XXX')} 的简历

## 基本信息
- 姓名：{basic.get('name', 'XXX')}
- 电话：{basic.get('phone', 'XXX')}
- 邮箱：{basic.get('email', 'XXX')}
- 学历：{basic.get('degree', '本科')}

## 教育背景
"""
    for edu in resume_data.get("education", []):
        content += f"- {edu.get('school', 'XXX')} | {edu.get('major', 'XXX')}\n"

    content += "\n## 专业技能\n"
    content += format_skills(resume_data)

    content += "\n## 项目经历\n"
    for proj in resume_data.get("projects", []):
        content += f"- {proj.get('name', 'XXX')}：{proj.get('description', '')}\n"

    reasons = ["使用默认模板生成简历"]
    project_text = ""

    return content, reasons, project_text


def format_skills(resume_data: dict) -> str:
    skills = resume_data.get("skills", [])
    result = ""
    for skill_cat in skills:
        if isinstance(skill_cat, dict):
            category = skill_cat.get("category", "其他")
            items = skill_cat.get("items", [])
            result += f"- **{category}**：{', '.join(items)}\n"
    return result


def contains_ai_keywords(project: dict) -> bool:
    ai_keywords = ['AI', '机器学习', '深度学习', 'NLP', '神经网络', 'PyTorch', 'TensorFlow']
    desc = project.get('description', '')
    techs = project.get('technologies', [])
    text = desc + ' ' + ' '.join(techs)
    return any(keyword.lower() in text.lower() for keyword in ai_keywords)


def generate_notes(rewrite_mode: str) -> list[str]:
    notes = [
        "请根据实际情况调整简历内容",
        "建议保留真实的项目经历和技能",
        "如有实习经历请补充具体工作内容"
    ]

    if rewrite_mode == "one_page":
        notes.append("此版本为一页精简版，适合快速投递")
    elif rewrite_mode == "big_company_intern":
        notes.append("建议突出与目标公司业务相关的项目")
    elif rewrite_mode == "ai_developer":
        notes.append("如有论文发表或竞赛获奖请补充")

    return notes
