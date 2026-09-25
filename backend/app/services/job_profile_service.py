from __future__ import annotations

from copy import deepcopy
from typing import Any

JOB_FAMILY_PROFILES: dict[str, dict[str, Any]] = {
    "backend": {
        "title": "后端开发",
        "aliases": ["后端", "backend", "server", "服务端", "api", "接口", "分布式"],
        "core_skills": ["Python", "Java", "Go", "SQL", "MySQL", "Redis", "RESTful API", "Linux"],
        "preferred_skills": ["Docker", "Kubernetes", "Kafka", "RabbitMQ", "Nginx", "CI/CD", "微服务"],
        "project_evidence_requirements": [
            "清楚说明接口设计、数据模型、鉴权、异常处理和日志监控",
            "给出数据库索引、缓存、异步队列或性能优化的真实案例",
            "能解释并发、事务一致性、幂等、限流和降级等工程问题",
        ],
        "interview_focus": ["接口设计", "数据库优化", "缓存策略", "并发与一致性", "线上问题排查"],
        "resume_keywords": ["接口", "数据库", "缓存", "并发", "性能优化", "部署", "日志", "监控"],
        "risk_signals": ["只写 CRUD 没有业务复杂度", "没有性能或稳定性指标", "无法说明技术选型原因"],
        "scoring_weights": {"skills": 0.3, "projects": 0.35, "engineering": 0.25, "communication": 0.1},
    },
    "frontend": {
        "title": "前端开发",
        "aliases": ["前端", "frontend", "web", "vue", "react", "页面", "组件"],
        "core_skills": ["JavaScript", "TypeScript", "Vue", "React", "HTML", "CSS", "HTTP"],
        "preferred_skills": ["Vite", "Webpack", "Pinia", "Redux", "Element Plus", "Tailwind CSS", "性能优化"],
        "project_evidence_requirements": [
            "说明组件拆分、状态管理、路由、接口联调和错误处理",
            "给出首屏加载、包体积、渲染性能或交互体验优化证据",
            "能解释复杂表单、权限、图表、响应式布局等前端工程问题",
        ],
        "interview_focus": ["组件设计", "状态管理", "浏览器原理", "工程化", "性能优化"],
        "resume_keywords": ["组件", "状态管理", "路由", "联调", "响应式", "性能优化", "工程化"],
        "risk_signals": ["只写页面实现没有工程思考", "没有复杂交互或性能指标", "无法解释框架原理"],
        "scoring_weights": {"skills": 0.3, "projects": 0.3, "engineering": 0.25, "communication": 0.15},
    },
    "ai_application": {
        "title": "AI 应用开发",
        "aliases": ["ai应用", "ai application", "llm", "大模型", "rag", "agent", "prompt", "embedding"],
        "core_skills": ["Python", "FastAPI", "LLM", "RAG", "Prompt Engineering", "Embedding", "Vector DB"],
        "preferred_skills": ["LangChain", "LangGraph", "OpenAI-compatible API", "pgvector", "Milvus", "知识库"],
        "project_evidence_requirements": [
            "说明模型调用、提示词设计、结构化输出、异常兜底和成本控制",
            "给出 RAG 的切分、召回、重排、引用证据和质量评估方法",
            "能解释幻觉控制、权限边界、数据安全和多模型切换策略",
        ],
        "interview_focus": ["Prompt 设计", "RAG 召回质量", "Agent 流程编排", "结构化输出", "模型可靠性"],
        "resume_keywords": ["大模型", "Agent", "RAG", "知识库", "向量检索", "结构化输出", "模型评测"],
        "risk_signals": ["只写调用 API 没有业务闭环", "没有评测或兜底机制", "无法说明 RAG 准确率来源"],
        "scoring_weights": {"skills": 0.25, "projects": 0.35, "engineering": 0.25, "evaluation": 0.15},
    },
    "java_backend": {
        "title": "Java 开发",
        "aliases": ["java", "spring", "spring boot", "jvm", "mybatis"],
        "core_skills": ["Java", "Spring Boot", "MyBatis", "MySQL", "Redis", "JVM"],
        "preferred_skills": ["Spring Cloud", "Kafka", "RocketMQ", "Docker", "Nacos", "Sentinel"],
        "project_evidence_requirements": [
            "说明分层架构、事务、缓存、消息队列和接口幂等设计",
            "给出 JVM、SQL、Redis 或接口性能优化案例",
            "能解释 Spring 生态、并发集合、线程池和线上排查经验",
        ],
        "interview_focus": ["Java 基础", "Spring 原理", "数据库", "Redis", "并发编程"],
        "resume_keywords": ["Spring Boot", "接口", "事务", "缓存", "消息队列", "线程池", "JVM"],
        "risk_signals": ["项目像课程作业且缺少业务链路", "没有并发或事务场景", "八股与项目无法对应"],
        "scoring_weights": {"skills": 0.3, "projects": 0.35, "engineering": 0.25, "communication": 0.1},
    },
    "python_backend": {
        "title": "Python 开发",
        "aliases": ["python", "fastapi", "django", "flask", "pydantic"],
        "core_skills": ["Python", "FastAPI", "Django", "SQLAlchemy", "MySQL", "Redis"],
        "preferred_skills": ["Celery", "Pytest", "Docker", "Pydantic", "AsyncIO", "LangChain"],
        "project_evidence_requirements": [
            "说明接口、数据模型、异步任务、依赖注入和异常处理",
            "给出测试、性能优化、部署或可观测性证据",
            "能解释 Python 语言特性、异步、ORM 和工程规范",
        ],
        "interview_focus": ["Python 语言", "Web 框架", "ORM", "异步任务", "测试与部署"],
        "resume_keywords": ["FastAPI", "Django", "接口", "ORM", "异步", "测试", "部署"],
        "risk_signals": ["只会脚本没有 Web 工程经验", "缺少测试和部署说明", "不了解框架边界"],
        "scoring_weights": {"skills": 0.3, "projects": 0.35, "engineering": 0.25, "communication": 0.1},
    },
    "algorithm": {
        "title": "算法工程",
        "aliases": ["算法", "algorithm", "机器学习", "深度学习", "nlp", "cv", "推荐"],
        "core_skills": ["Python", "数据结构", "机器学习", "PyTorch", "NumPy", "Pandas"],
        "preferred_skills": ["Transformer", "BERT", "推荐系统", "特征工程", "模型部署", "A/B Test"],
        "project_evidence_requirements": [
            "说明数据来源、特征处理、模型选择、训练验证和评估指标",
            "给出准确率、召回率、AUC、延迟或业务指标提升",
            "能解释 baseline、消融实验、过拟合处理和模型上线方式",
        ],
        "interview_focus": ["算法基础", "模型评估", "特征工程", "实验设计", "模型部署"],
        "resume_keywords": ["模型", "特征", "训练", "评估", "准确率", "召回率", "AUC", "实验"],
        "risk_signals": ["只有调包没有实验设计", "没有指标和数据集说明", "无法解释模型选择"],
        "scoring_weights": {"skills": 0.25, "projects": 0.35, "algorithm": 0.3, "communication": 0.1},
    },
    "product_ops": {
        "title": "产品/运营",
        "aliases": ["产品", "运营", "product", "operation", "用户增长", "需求", "数据分析"],
        "core_skills": ["需求分析", "用户研究", "竞品分析", "数据分析", "PRD", "沟通协作"],
        "preferred_skills": ["SQL", "A/B Test", "增长模型", "埋点分析", "Axure", "Figma"],
        "project_evidence_requirements": [
            "说明用户问题、目标指标、方案设计、协作推进和结果复盘",
            "给出增长、转化、留存、活跃或效率提升等量化结果",
            "能解释需求优先级、数据口径和跨团队沟通取舍",
        ],
        "interview_focus": ["需求分析", "数据洞察", "产品思维", "沟通推进", "复盘能力"],
        "resume_keywords": ["需求", "用户", "转化", "留存", "增长", "复盘", "数据分析"],
        "risk_signals": ["只写活动执行没有目标和结果", "缺少数据口径", "无法说明个人推动作用"],
        "scoring_weights": {"skills": 0.2, "projects": 0.35, "business": 0.3, "communication": 0.15},
    },
}


def build_job_profile(jd_content: str, resume_text: str = "") -> dict[str, Any]:
    combined_text = f"{jd_content}\n{resume_text[:1200]}".lower()
    family_id, raw_score, matched = _detect_family(combined_text)
    base_profile = deepcopy(JOB_FAMILY_PROFILES[family_id])
    confidence = _score_to_confidence(raw_score)

    return {
        "family_id": family_id,
        "title": base_profile["title"],
        "confidence": confidence,
        "core_skills": base_profile["core_skills"],
        "preferred_skills": base_profile["preferred_skills"],
        "project_evidence_requirements": base_profile["project_evidence_requirements"],
        "interview_focus": base_profile["interview_focus"],
        "resume_keywords": base_profile["resume_keywords"],
        "risk_signals": base_profile["risk_signals"],
        "scoring_weights": base_profile["scoring_weights"],
        "matched_signals": matched[:12],
    }


def _detect_family(text: str) -> tuple[str, int, list[str]]:
    best_family = "backend"
    best_score = -1
    best_matched: list[str] = []

    for family_id, profile in JOB_FAMILY_PROFILES.items():
        score = 0
        matched = []
        for alias in profile["aliases"]:
            if alias.lower() in text:
                score += 6
                matched.append(alias)
        for skill in profile["core_skills"]:
            if skill.lower() in text:
                score += 4
                matched.append(skill)
        for skill in profile["preferred_skills"]:
            if skill.lower() in text:
                score += 2
                matched.append(skill)
        for keyword in profile["resume_keywords"]:
            if keyword.lower() in text:
                score += 1
                matched.append(keyword)

        if score > best_score:
            best_family = family_id
            best_score = score
            best_matched = list(dict.fromkeys(matched))

    return best_family, max(best_score, 0), best_matched


def _score_to_confidence(score: int) -> float:
    if score <= 0:
        return 0.35
    return round(min(0.95, 0.45 + score / 60), 2)
