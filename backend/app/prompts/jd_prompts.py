def get_jd_analysis_prompt(jd_content: str) -> str:
    return f"""请分析以下岗位描述，提取关键信息：

{jd_content[:1500]}

请按以下格式返回JSON：
{{
  "position_title": "岗位名称",
  "position_type": "岗位类型",
  "required_skills": ["技能1", "技能2"],
  "responsibilities": ["职责1", "职责2"],
  "requirements": ["要求1", "要求2"],
  "nice_to_have": ["加分项1", "加分项2"],
  "experience_requirement": "经验要求",
  "education_requirement": "学历要求",
  "summary": "岗位总结"
}}"""


def get_jd_structured_prompt(jd_content: str) -> str:
    return f"""你是资深招聘分析专家。请分析以下岗位 JD，并只返回一个合法 JSON 对象，不要返回 Markdown 代码块。

## 岗位 JD
{jd_content[:4000]}

JSON 字段必须完全使用以下结构：
{{
  "position_title": "岗位名称，无法判断时填未知岗位",
  "position_type": "后端开发/前端开发/AI应用开发/Java开发/Python开发/算法工程/产品经理/运营/测试开发/其他",
  "required_skills": ["核心必备技能关键词"],
  "nice_to_have_skills": ["加分技能关键词"],
  "responsibilities": ["岗位职责，逐条列出"],
  "requirements": ["任职要求，逐条列出"],
  "plus_points": ["加分项，逐条列出"],
  "experience_requirement": "经验要求，没有则为空字符串",
  "education_requirement": "学历要求，没有则为空字符串",
  "summary": "用 2-3 句话总结岗位对候选人的核心要求"
}}

要求：
1. 技能关键词要短，优先输出技术名或能力名。
2. 不要编造 JD 中没有暗示的硬性要求。
3. 所有数组字段即使为空也必须返回 []。"""
