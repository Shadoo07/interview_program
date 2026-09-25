import re

from pydantic import ValidationError

from app.prompts.jd_prompts import get_jd_structured_prompt
from app.schemas.jd_schema import JDAnalysisResult
from app.services.llm_service import llm_service
from app.utils.json_utils import extract_json_object

BACKEND_SKILLS = [
    'Python', 'Java', 'Go', 'Golang', 'Rust', 'C++', 'C#', '.NET',
    'Node.js', 'NodeJS', 'Express', 'Spring', 'Spring Boot', 'Django', 'Flask',
    'MySQL', 'PostgreSQL', 'Redis', 'MongoDB', 'SQL', 'SQLite', 'Oracle',
    'Docker', 'Kubernetes', 'K8s', 'DevOps', 'CI/CD', 'Jenkins',
    'RESTful', 'gRPC', 'MQ', 'RabbitMQ', 'Kafka', '消息队列',
    'Linux', 'Nginx', '分布式', '微服务', '高并发', '缓存', '数据库'
]

FRONTEND_SKILLS = [
    'JavaScript', 'TypeScript', 'Vue', 'React', 'Angular', 'Vue3', 'React Native',
    'HTML', 'CSS', 'SCSS', 'Sass', 'Less',
    'Webpack', 'Vite', 'Rollup', 'Parcel',
    'Element Plus', 'Ant Design', 'Tailwind CSS', 'Bootstrap',
    'Axios', 'Fetch', 'HTTP', 'WebSocket',
    'SPA', 'SSR', 'SEO', '性能优化', '响应式'
]

AI_SKILLS = [
    '机器学习', '深度学习', 'AI', '大模型', 'LLM', 'GPT',
    'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn',
    'NLP', '自然语言处理', '计算机视觉', 'CV',
    '推荐系统', '数据挖掘', '数据分析', '数据科学',
    'Pandas', 'NumPy', 'Matplotlib', 'Jupyter',
    'Transformer', 'BERT', 'GPT', 'Embedding', '向量数据库'
]

FULLSTACK_SKILLS = BACKEND_SKILLS + FRONTEND_SKILLS

POSITION_TYPES = {
    '后端开发': ['后端', 'backend', 'server', '服务端', 'API', 'Spring', 'Django', 'Go', 'Java'],
    '前端开发': ['前端', 'frontend', '前端开发', 'Vue', 'React', 'JavaScript', 'TypeScript'],
    'AI应用开发': ['AI', '人工智能', '机器学习', '深度学习', 'LLM', '大模型', 'NLP'],
    'Java开发': ['Java', 'JDK', 'Spring', 'Spring Boot'],
    'Python开发': ['Python', 'Django', 'Flask', 'FastAPI'],
    '算法工程': ['算法', 'Algorithm', '推荐', 'NLP', 'CV', '机器学习'],
    '产品经理': ['产品', 'PM', 'Product', '需求', '设计'],
    '运营': ['运营', 'Operation', '增长', '用户'],
    '测试开发': ['测试', 'QA', 'Test', '自动化测试']
}

RESPONSIBILITY_KEYWORDS = [
    '负责', '负责开发', '负责设计', '参与', '主导', '开发', '设计', '维护',
    '优化', '实现', '搭建', '构建', '改造', '迭代', '上线', '部署'
]

REQUIREMENT_KEYWORDS = [
    '要求', '学历', '本科', '硕士', '博士', '经验', '年', '熟悉', '掌握',
    '了解', '精通', '熟练', '良好', '优秀', '扎实', '深入'
]

PLUS_POINTS_KEYWORDS = [
    '加分', '优先', '良好', '优秀', '更佳', '相关', '额外', '熟悉'
]


def analyze_jd(jd_content: str) -> JDAnalysisResult:
    if not jd_content or len(jd_content.strip()) < 10:
        raise ValueError("JD内容不能为空或过短")

    if llm_service.is_available():
        result = analyze_jd_with_llm(jd_content)
        if result:
            return result

    return analyze_jd_with_rules(jd_content)


def analyze_jd_with_llm(jd_content: str) -> JDAnalysisResult | None:
    prompt = get_jd_structured_prompt(jd_content)
    response = llm_service.chat(
        [
            {"role": "system", "content": "你是招聘 JD 结构化分析专家，只输出合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=1800,
    )
    if not response:
        return None

    try:
        data = extract_json_object(response)
        if "nice_to_have" in data and "nice_to_have_skills" not in data:
            data["nice_to_have_skills"] = data.pop("nice_to_have")
        data.setdefault("position_title", "未知岗位")
        data.setdefault("position_type", "其他")
        for key in [
            "required_skills",
            "nice_to_have_skills",
            "responsibilities",
            "requirements",
            "plus_points",
        ]:
            if not isinstance(data.get(key), list):
                data[key] = []
        data.setdefault("experience_requirement", "")
        data.setdefault("education_requirement", "")
        data.setdefault("summary", "")
        return JDAnalysisResult.model_validate(data)
    except (ValueError, ValidationError) as exc:
        print(f"Parse JD LLM response error: {exc}")
        return None


def analyze_jd_with_rules(jd_content: str) -> JDAnalysisResult:
    lines = jd_content.split('\n')
    position_title = extract_position_title(jd_content)
    position_type = classify_position_type(jd_content)
    required_skills, nice_to_have_skills = extract_skills(jd_content)
    responsibilities = extract_responsibilities(lines)
    requirements = extract_requirements(lines)
    plus_points = extract_plus_points(lines)
    experience_requirement = extract_experience(jd_content)
    education_requirement = extract_education(jd_content)
    summary = generate_summary(position_title, position_type, required_skills, responsibilities)

    return JDAnalysisResult(
        position_title=position_title,
        position_type=position_type,
        required_skills=required_skills,
        nice_to_have_skills=nice_to_have_skills,
        responsibilities=responsibilities,
        requirements=requirements,
        plus_points=plus_points,
        experience_requirement=experience_requirement,
        education_requirement=education_requirement,
        summary=summary
    )


def extract_position_title(jd_content: str) -> str:
    lines = jd_content.split('\n')
    for line in lines[:10]:
        line = line.strip()
        if line and len(line) < 50:
            if any(title in line for title in ['招聘', '岗位', '职责', '要求', 'Description']):
                continue
            if len(line) >= 2:
                return line
    return "未知岗位"


def classify_position_type(jd_content: str) -> str:
    jd_lower = jd_content.lower()
    for position_type, keywords in POSITION_TYPES.items():
        for keyword in keywords:
            if keyword.lower() in jd_lower or keyword in jd_content:
                return position_type
    return "其他"


def extract_skills(jd_content: str) -> tuple[list[str], list[str]]:
    required = []
    nice_to_have = []
    all_skills = FULLSTACK_SKILLS + AI_SKILLS

    for skill in all_skills:
        pattern = re.compile(re.escape(skill), re.IGNORECASE)
        if pattern.search(jd_content):
            if any(word in jd_content for word in ['熟悉', '了解', '加分', '优先']):
                nice_to_have.append(skill)
            else:
                required.append(skill)

    return required, nice_to_have


def extract_responsibilities(lines: list[str]) -> list[str]:
    responsibilities = []
    in_responsibility_section = False

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        if any(keyword in line_stripped for keyword in ['职责', 'Responsibility', '工作内容', '负责']):
            in_responsibility_section = True
            continue

        if in_responsibility_section:
            if len(line_stripped) < 5 and any(keyword in line_stripped for keyword in ['要求', '任职', '学历', '经验', '技能']):
                break

            if any(keyword in line_stripped for keyword in RESPONSIBILITY_KEYWORDS):
                responsibilities.append(line_stripped)

            if len(responsibilities) >= 10:
                break

    return responsibilities[:10]


def extract_requirements(lines: list[str]) -> list[str]:
    requirements = []
    in_requirement_section = False

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        if any(keyword in line_stripped for keyword in ['要求', '任职', 'Qualification', 'Requirement']):
            in_requirement_section = True
            continue

        if in_requirement_section:
            if len(line_stripped) < 5 and any(keyword in line_stripped for keyword in ['职责', '加分', '福利', '薪资']):
                break

            if any(keyword in line_stripped for keyword in REQUIREMENT_KEYWORDS):
                requirements.append(line_stripped)

            if len(requirements) >= 10:
                break

    return requirements[:10]


def extract_plus_points(lines: list[str]) -> list[str]:
    plus_points = []

    for line in lines:
        line_stripped = line.strip()
        if len(line_stripped) > 5 and any(keyword in line_stripped for keyword in PLUS_POINTS_KEYWORDS):
            plus_points.append(line_stripped)

    return plus_points[:5]


def extract_experience(jd_content: str) -> str:
    experience_patterns = [
        r'(\d+)[-~年]经验',
        r'(\d+)[-~年]工作经验',
        r'经验[-~：:]?(\d+)[年]',
        r'(\d+)-(\d+)年',
        r'应届', '应届生', '不限经验', '1年', '2年', '3年', '5年'
    ]

    for pattern in experience_patterns:
        match = re.search(pattern, jd_content)
        if match:
            return match.group()

    return ""


def extract_education(jd_content: str) -> str:
    education_keywords = ['本科', '硕士', '博士', '大专', '学历', '应届']
    for keyword in education_keywords:
        if keyword in jd_content:
            return keyword
    return ""


def generate_summary(position_title: str, position_type: str, skills: list[str], responsibilities: list[str]) -> str:
    summary = f"该岗位为{position_type}方向的{position_title}。"
    if skills:
        summary += f"核心技能要求包括：{', '.join(skills[:5])}等。"
    if responsibilities:
        summary += f"主要职责涉及：{', '.join([r[:20] for r in responsibilities[:3]])}等方面。"
    return summary
