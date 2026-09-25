import json

from app.prompts.interview_prompts import get_interview_questions_prompt, get_self_intro_prompt
from app.schemas.interview_schema import (
    QUESTION_TYPE_LABELS,
    InterviewQuestionsResult,
    QuestionItem,
)
from app.services.llm_service import llm_service


def generate_interview_questions(
    resume_data: dict,
    jd_data: dict,
    raw_text: str | None = None,
    rewrite_result: dict | None = None,
    question_types: list[str] | None = None
) -> InterviewQuestionsResult:
    if not resume_data or not jd_data:
        raise ValueError("简历数据和JD数据不能为空")

    if question_types is None:
        question_types = list(QUESTION_TYPE_LABELS.keys())

    # 优先使用大模型
    if llm_service.is_available():
        result = generate_with_llm(resume_data, jd_data, question_types)
        if result:
            return result

    # 降级到规则模板
    return generate_with_rules(resume_data, jd_data, question_types)


def generate_with_llm(
    resume_data: dict,
    jd_data: dict,
    question_types: list[str]
) -> InterviewQuestionsResult | None:
    """使用大模型生成面试问题（单次调用，包含自我介绍）"""
    prompt = get_interview_questions_prompt(resume_data, jd_data, question_types)

    messages = [
        {"role": "system", "content": "你是一位经验丰富的技术面试官。请严格按照JSON格式返回，不要添加任何额外说明。"},
        {"role": "user", "content": prompt}
    ]

    response = llm_service.chat(messages, temperature=0.7, max_tokens=2000)

    if response:
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            data = json.loads(response.strip())

            result = InterviewQuestionsResult()
            result.source = "ai"

            if "project_deep_dive" in data:
                result.project_deep_dive = [QuestionItem(**q) for q in data["project_deep_dive"]]
            if "tech_theory" in data:
                result.tech_theory = [QuestionItem(**q) for q in data["tech_theory"]]
            if "system_design" in data:
                result.system_design = [QuestionItem(**q) for q in data["system_design"]]
            if "project_difficulties" in data:
                result.project_difficulties = [QuestionItem(**q) for q in data["project_difficulties"]]
            if "hr_general" in data:
                result.hr_general = [QuestionItem(**q) for q in data["hr_general"]]
            if "self_intro" in data:
                result.self_intro = str(data["self_intro"])

            return result
        except (json.JSONDecodeError, Exception) as e:
            print(f"Parse LLM response error: {e}")

    return None


def generate_self_intro_with_llm(resume_data: dict, jd_data: dict) -> str | None:
    """使用大模型生成自我介绍建议"""
    prompt = get_self_intro_prompt(resume_data, jd_data)

    messages = [
        {"role": "system", "content": "你是一位职业规划师，请帮助优化自我介绍。"},
        {"role": "user", "content": prompt}
    ]

    return llm_service.chat(messages, temperature=0.7, max_tokens=1500)


def generate_self_intro_stream(resume_data: dict, jd_data: dict):
    """流式生成自我介绍建议，逐块 yield 文本"""
    prompt = get_self_intro_prompt(resume_data, jd_data)

    messages = [
        {"role": "system", "content": "你是一位职业规划师，请帮助优化自我介绍。"},
        {"role": "user", "content": prompt}
    ]

    yield from llm_service.chat_stream(messages, temperature=0.7, max_tokens=1500)


def generate_with_rules(
    resume_data: dict,
    jd_data: dict,
    question_types: list[str]
) -> InterviewQuestionsResult:
    """使用规则生成面试问题（兜底方案）"""
    projects = resume_data.get("projects", [])
    skills = extract_skills(resume_data)
    jd_skills = jd_data.get("required_skills", [])
    position_title = jd_data.get("position_title", "未知岗位")

    result = InterviewQuestionsResult()
    result.source = "rules"

    if "project_deep_dive" in question_types:
        result.project_deep_dive = generate_project_deep_questions(projects, jd_skills)

    if "tech_theory" in question_types:
        result.tech_theory = generate_tech_theory_questions(skills, jd_skills, position_title)

    if "system_design" in question_types:
        result.system_design = generate_system_design_questions(position_title, jd_skills)

    if "project_difficulties" in question_types:
        result.project_difficulties = generate_project_difficulty_questions(projects)

    if "hr_general" in question_types:
        result.hr_general = generate_hr_general_questions()

    if "self_intro" in question_types:
        result.self_intro = generate_self_intro_suggestion(resume_data, jd_data)

    return result


def extract_skills(resume_data: dict) -> list[str]:
    skills = []
    if resume_data.get("skills"):
        for skill_cat in resume_data["skills"]:
            if isinstance(skill_cat, dict) and "items" in skill_cat:
                skills.extend(skill_cat["items"])
    return skills


def generate_project_deep_questions(projects: list, jd_skills: list[str]) -> list[QuestionItem]:
    questions = []

    if not projects:
        projects = [{"name": "个人项目", "description": "负责开发", "technologies": []}]

    for proj in projects[:3]:
        proj_name = proj.get("name", "项目")
        proj_techs = proj.get("technologies", [])

        questions.append(QuestionItem(
            question=f"请介绍一下{proj_name}，你在项目中担任什么角色？",
            focus_point="项目整体把控、自我定位、表达能力",
            answer_guide="按STAR法则介绍：\n1. Situation: 项目背景\n2. Task: 我的职责\n3. Action: 具体做了什么\n4. Result: 项目成果",
            notes="突出个人贡献，使用'我'而非'我们'",
            difficulty="中等"
        ))

        questions.append(QuestionItem(
            question=f"{proj_name}中遇到的最大技术挑战是什么？如何解决的？",
            focus_point="问题解决能力、技术深度、思维过程",
            answer_guide="1. 描述挑战背景\n2. 分析原因\n3. 尝试的方案\n4. 最终解决方案\n5. 反思与总结",
            notes="避免把团队成果说成个人成果",
            difficulty="困难"
        ))

        if proj_techs:
            questions.append(QuestionItem(
                question=f"为什么在{proj_name}中选择{'/'.join(proj_techs[:2])}技术栈？",
                focus_point="技术选型能力、架构思维",
                answer_guide="从以下角度回答：\n1. 业务需求\n2. 技术优势\n3. 团队能力\n4. 未来扩展性",
                notes="了解技术的优缺点",
                difficulty="中等"
            ))

    return questions[:6]


def generate_tech_theory_questions(skills: list[str], jd_skills: list[str], position_title: str) -> list[QuestionItem]:
    questions = []

    tech_map = {
        "Python": ["Python的GIL是什么？如何避免？", "Python中的装饰器是什么？如何实现？"],
        "Django": ["Django的MTV模式是什么？", "Django如何进行数据库优化？"],
        "Flask": ["Flask和Django的区别是什么？", "Flask如何实现蓝图？"],
        "MySQL": ["MySQL的索引原理是什么？", "MySQL如何进行性能优化？"],
        "Redis": ["Redis的数据类型有哪些？", "Redis的持久化机制是什么？"],
        "Docker": ["Docker和虚拟机的区别？", "Dockerfile的常用指令有哪些？"],
        "Java": ["Java的垃圾回收机制？", "HashMap的底层实现原理？"],
        "JavaScript": ["JavaScript的事件循环机制？", "闭包是什么？有什么应用场景？"],
        "Vue": ["Vue的双向绑定原理？", "Vue3的Composition API和Vue2的区别？"],
        "React": ["React的生命周期？", "React的虚拟DOM原理？"],
        "Git": ["Git的常用命令？", "Git如何处理冲突？"]
    }

    target_skills = set(skills + jd_skills)

    for skill in target_skills:
        for question_template in tech_map.get(skill, []):
            questions.append(QuestionItem(
                question=question_template,
                focus_point=f"{skill}核心概念理解",
                answer_guide="1. 核心原理\n2. 实现机制\n3. 适用场景\n4. 优缺点",
                notes="结合项目经验回答",
                difficulty="中等"
            ))

    if not questions:
        questions.append(QuestionItem(
            question="请介绍一下你最擅长的技术栈？",
            focus_point="技术广度、专业深度",
            answer_guide="1. 技术栈介绍\n2. 项目应用\n3. 深度理解\n4. 持续学习",
            notes="选择最熟悉的领域深入",
            difficulty="简单"
        ))

    return questions[:6]


def generate_system_design_questions(position_title: str, jd_skills: list[str]) -> list[QuestionItem]:
    questions = []

    questions.append(QuestionItem(
        question="如何设计一个高并发的点赞系统？",
        focus_point="系统设计能力、架构思维、性能优化",
        answer_guide="1. 需求分析\n2. 整体架构\n3. 数据库设计\n4. 缓存策略\n5. 接口设计\n6. 扩展性考虑",
        notes="考虑读多写少的特点",
        difficulty="困难"
    ))

    questions.append(QuestionItem(
        question="如果系统出现性能瓶颈，你会如何排查和优化？",
        focus_point="问题诊断能力、性能优化经验",
        answer_guide="1. 定位瓶颈（CPU/内存/IO/网络）\n2. 分析日志和监控\n3. 数据库慢查询分析\n4. 代码层面优化\n5. 架构调整",
        notes="举例说明具体优化案例",
        difficulty="中等"
    ))

    if any(skill in position_title for skill in ["后端", "后端开发", "Java", "Python", "Go"]):
        questions.append(QuestionItem(
            question="如何设计一个接口幂等性方案？",
            focus_point="接口设计、数据一致性",
            answer_guide="1. 唯一ID方案\n2. 悲观锁/乐观锁\n3. 状态机控制\n4. 分布式锁",
            notes="结合具体业务场景",
            difficulty="中等"
        ))

    return questions[:4]


def generate_project_difficulty_questions(projects: list) -> list[QuestionItem]:
    questions = []

    if not projects:
        projects = [{"name": "个人项目", "description": "负责开发", "technologies": []}]

    for proj in projects[:2]:
        proj_name = proj.get("name", "项目")

        questions.append(QuestionItem(
            question=f"如果重新做{proj_name}，你会如何改进？",
            focus_point="复盘能力、学习能力、批判性思维",
            answer_guide="1. 当时的技术局限\n2. 现在的改进思路\n3. 学到的经验教训",
            notes="展示持续成长的心态",
            difficulty="中等"
        ))

        questions.append(QuestionItem(
            question=f"{proj_name}中最有成就感的一件事是什么？",
            focus_point="个人价值认同、成就动机",
            answer_guide="描述具体成果，最好量化：\n1. 背景\n2. 行动\n3. 结果（最好有数据）",
            notes="真实可信，避免过度夸张",
            difficulty="简单"
        ))

    return questions[:4]


def generate_hr_general_questions() -> list[QuestionItem]:
    questions = []

    questions.append(QuestionItem(
        question="请做一个简短的自我介绍？",
        focus_point="表达能力、自我认知、时间把控",
        answer_guide="1. 教育背景（1句）\n2. 技术栈（2-3句）\n3. 项目经验（3-4句）\n4. 求职动机（1句）\n建议控制在2分钟内",
        notes="突出与岗位匹配的优势",
        difficulty="简单"
    ))

    questions.append(QuestionItem(
        question="你为什么想加入我们公司？",
        focus_point="求职动机、对公司了解程度",
        answer_guide="1. 公司业务认可\n2. 技术栈匹配\n3. 职业发展\n4. 团队文化",
        notes="提前了解公司业务和技术栈",
        difficulty="简单"
    ))

    questions.append(QuestionItem(
        question="你的职业规划是什么？",
        focus_point="职业规划、自我认知、稳定性",
        answer_guide="分短期（1-2年）和长期（3-5年）：\n短期：技术深耕\n长期：技术管理/架构师",
        notes="避免说想创业或考研",
        difficulty="中等"
    ))

    questions.append(QuestionItem(
        question="你觉得自己最大的优点和缺点是什么？",
        focus_point="自我认知、诚信度",
        answer_guide="优点：结合岗位需求\n缺点：承认但展示改进措施",
        notes="缺点要真实且不影响工作",
        difficulty="中等"
    ))

    questions.append(QuestionItem(
        question="你在项目中与团队成员发生分歧怎么办？",
        focus_point="沟通协作、问题解决",
        answer_guide="1. 倾听对方观点\n2. 理性分析利弊\n3. 寻求共识\n4. 以团队目标为重",
        notes="展示成熟的工作态度",
        difficulty="中等"
    ))

    return questions[:5]


def generate_self_intro_suggestion(resume_data: dict, jd_data: dict) -> str:
    basic = resume_data.get("basic_info", {})
    skills = extract_skills(resume_data)
    projects = resume_data.get("projects", [])
    position_title = jd_data.get("position_title", "未知岗位")

    name = basic.get("name", "同学")
    school = basic.get("school", "")
    degree = basic.get("degree", "")
    major = basic.get("major", "")

    suggestion = f"""## 自我介绍优化建议

### 推荐模板（2分钟内）：
"大家好，我是{name}，{school}{degree}{major}在读。

我对后端开发有浓厚兴趣，主要掌握{', '.join(skills[:5])}等技术。

在校期间，我参与过{len(projects)}个项目开发，其中[最相关的项目]让我深入理解了[技术点]。

看到贵司正在招聘{position_title}，我认为我的技术背景和项目经验与该岗位高度匹配。期待能加入贵司学习成长，谢谢！"

### 优化要点：
1. 控制时长在90-120秒
2. 突出与岗位匹配的技能
3. 用具体数字说明成果（如：提升性能30%）
4. 结尾表达强烈求职意愿
5. 提前演练，注意语速和表情"""

    return suggestion
