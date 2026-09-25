def get_interview_questions_prompt(
    resume_data: dict,
    jd_data: dict,
    question_types: list
) -> str:
    position = jd_data.get('position_title', '软件开发工程师')
    skills = jd_data.get('required_skills', [])
    projects = resume_data.get('projects', [])

    project_info = ""
    for p in projects[:3]:
        project_info += f"- {p.get('name', '项目')}: {p.get('description', '')[:100]}\n"

    return f"""你是一位经验丰富的技术面试官。请根据候选人的简历和目标岗位，生成面试问题。

## 目标岗位
{position}

## 岗位技能要求
{', '.join(skills[:10]) if skills else '通用技能'}

## 候选人项目经历
{project_info if project_info else '暂无项目信息'}

请生成以下类型的面试问题，严格以JSON格式返回（不要markdown代码块）：

{{
  "project_deep_dive": [
    {{"question": "...", "focus_point": "...", "answer_guide": "...", "notes": "...", "difficulty": "中等"}}
  ],
  "tech_theory": [
    {{"question": "...", "focus_point": "...", "answer_guide": "...", "notes": "...", "difficulty": "中等"}}
  ],
  "system_design": [
    {{"question": "...", "focus_point": "...", "answer_guide": "...", "notes": "...", "difficulty": "困难"}}
  ],
  "project_difficulties": [
    {{"question": "...", "focus_point": "...", "answer_guide": "...", "notes": "...", "difficulty": "中等"}}
  ],
  "hr_general": [
    {{"question": "...", "focus_point": "...", "answer_guide": "...", "notes": "...", "difficulty": "简单"}}
  ],
  "self_intro": "针对该岗位的自我介绍建议（Markdown格式，包含模板和要点）"
}}

要求：
1. 每类生成2-3个问题，内容精简
2. 问题要有针对性，结合候选人真实背景
3. 难度递进：简单→中等→困难
4. 参考回答要具体可操作，50字以内"""


def get_self_intro_prompt(resume_data: dict, jd_data: dict) -> str:
    position = jd_data.get('position_title', '软件开发工程师')
    name = resume_data.get('basic_info', {}).get('name', '候选人')

    return f"""请为候选人{name}生成一份针对{position}岗位的自我介绍优化建议。

请包含：
1. 推荐的自我介绍模板（2分钟版本）
2. 需要突出的重点
3. 表达技巧建议
4. 常见问题应对

以Markdown格式返回。"""
