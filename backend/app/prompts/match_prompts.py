import json
from typing import Any


def get_match_analysis_prompt(resume_data: dict[str, Any], jd_data: dict[str, Any]) -> str:
    resume_json = json.dumps(resume_data, ensure_ascii=False)[:5000]
    jd_json = json.dumps(jd_data, ensure_ascii=False)[:4000]
    return f"""你是大学生求职场景下的简历-JD 匹配分析专家。请基于结构化简历和结构化 JD 生成匹配度分析，并只返回一个合法 JSON 对象，不要返回 Markdown 代码块。

## 结构化简历
{resume_json}

## 结构化 JD
{jd_json}

JSON 字段必须完全使用以下结构：
{{
  "overall_score": 0,
  "dimension_scores": [
    {{
      "dimension": "技术栈",
      "score": 0,
      "max_score": 100,
      "weight": 0.35,
      "matched_keywords": ["已匹配关键词"],
      "missing_keywords": ["缺失关键词"]
    }},
    {{
      "dimension": "项目经历",
      "score": 0,
      "max_score": 100,
      "weight": 0.25,
      "matched_keywords": [],
      "missing_keywords": []
    }},
    {{
      "dimension": "教育背景",
      "score": 0,
      "max_score": 100,
      "weight": 0.15,
      "matched_keywords": [],
      "missing_keywords": []
    }},
    {{
      "dimension": "经验匹配",
      "score": 0,
      "max_score": 100,
      "weight": 0.25,
      "matched_keywords": [],
      "missing_keywords": []
    }}
  ],
  "matched_keywords": ["所有匹配关键词"],
  "missing_keywords": ["所有缺失关键词"],
  "weak_points": ["简历短板"],
  "suggestions": ["具体优化建议"],
  "match_level": "优秀/良好/一般/较差"
}}

要求：
1. 所有分数必须是 0-100 的整数。
2. 评分要保守，不能因为出现一个关键词就给过高分。
3. 建议必须能直接指导用户修改简历。
4. 不要编造候选人未体现的经历。"""
