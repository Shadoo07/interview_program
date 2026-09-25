def get_resume_rewrite_prompt(
    resume_data: dict,
    jd_data: dict,
    raw_text: str,
    rewrite_mode: str
) -> str:
    mode_names = {
        "big_company_intern": "大厂实习投递版",
        "backend_developer": "后端开发岗位版",
        "ai_developer": "AI应用开发岗位版",
        "project_enhance": "项目经历强化版",
        "hr_friendly": "HR初筛友好版",
        "one_page": "简洁一页版"
    }

    mode_name = mode_names.get(rewrite_mode, "默认版本")

    return f"""你是一位专业的简历优化专家。请根据以下信息，生成一份{mode_name}的简历。

## 原始简历信息
{raw_text[:1500]}

## 目标岗位
{jd_data.get('position_title', '软件开发工程师')}

## 岗位要求
{', '.join(jd_data.get('required_skills', []))}

## 改写要求
1. 突出与目标岗位匹配的技能和经验
2. 使用量化数据描述成果
3. 优化语言表达，使其更专业
4. 保持真实，不编造经历

请生成改写后的简历内容（Markdown格式）："""


def get_resume_analysis_prompt(resume_text: str) -> str:
    return f"""请分析以下简历内容，提取关键信息：

{resume_text[:1500]}

请按以下格式返回JSON：
{{
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1", "不足2"],
  "suggestions": ["建议1", "建议2"]
}}"""
