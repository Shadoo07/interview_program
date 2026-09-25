import re

from app.schemas.resume_schema import (
    AwardEntry,
    BasicInfo,
    EducationEntry,
    FileUploadData,
    InternshipEntry,
    ProjectEntry,
    ResumeParseData,
    ResumeStructureResponse,
    SkillEntry,
    SummaryEntry,
)
from app.utils import file_parser, file_storage


def upload_resume(file_content: bytes, filename: str) -> FileUploadData:
    file_info = file_storage.save_upload_file(file_content, filename)
    return FileUploadData(**file_info)


def parse_resume(file_id: str) -> ResumeParseData:
    file_path = file_storage.get_upload_file_path(file_id)
    file_info = file_storage.get_upload_file_path(file_id)

    try:
        raw_text = file_parser.parse_file(file_path, file_info.suffix.lower() if hasattr(file_info, 'suffix') else "")
    except Exception:
        raw_text = file_parser.parse_file_content(file_storage.get_upload_file_path(file_id).read_bytes(), file_id)

    return ResumeParseData(
        file_id=file_id,
        raw_text=raw_text
    )


def structure_resume(raw_text: str) -> ResumeStructureResponse:
    basic_info = extract_basic_info(raw_text)
    education = extract_education(raw_text)
    projects = extract_projects(raw_text)
    skills = extract_skills(raw_text)
    internships = extract_internships(raw_text)
    awards = extract_awards(raw_text)
    summary = extract_summary(raw_text)

    return ResumeStructureResponse(
        basic_info=basic_info,
        education=education,
        projects=projects,
        skills=skills,
        internships=internships,
        awards=awards,
        summary=summary
    )


def extract_basic_info(text: str) -> BasicInfo:
    name = None
    phone = None
    email = None
    school = None
    major = None
    degree = None

    phone_pattern = r'1[3-9]\d{9}'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        phone = phone_match.group()

    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    email_match = re.search(email_pattern, text)
    if email_match:
        email = email_match.group()

    lines = text.split('\n')
    for line in lines[:10]:
        line = line.strip()
        if not name and 2 <= len(line) <= 20 and re.match(r'^[\u4e00-\u9fa5a-zA-Z\s]+$', line):
            if any(keyword in line for keyword in ['大学', '学院', 'School', 'University']):
                school = line
            elif not any(keyword in line for keyword in ['简历', 'Resume', '电话', '邮箱', 'Email']):
                name = line

    universities = ['大学', '学院', 'University', 'college', 'school']
    for line in lines[:20]:
        line_lower = line.lower()
        if any(uni in line_lower for uni in universities):
            school = line.strip()
            break

    majors = ['专业', 'Major', '计算机', '软件', '电子', '机械', '数学', '物理']
    for line in lines[:30]:
        line_stripped = line.strip()
        if any(m in line_stripped for m in majors):
            major = line_stripped
            break

    degrees = ['本科', '硕士', '博士', 'Bachelor', 'Master', 'PhD', '研究生']
    for line in lines[:20]:
        line_stripped = line.strip()
        if any(d in line_stripped for d in degrees):
            degree = line_stripped
            break

    return BasicInfo(
        name=name,
        phone=phone,
        email=email,
        school=school,
        major=major,
        degree=degree
    )


def extract_education(text: str) -> list:
    education_entries = []
    lines = text.split('\n')

    education_keywords = ['教育', 'Education', '学习', '本科', '硕士', '博士', 'Bachelor', 'Master']

    in_education_section = False
    current_entry_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if any(keyword in line for keyword in education_keywords):
            in_education_section = True
            continue

        if in_education_section:
            if len(line) < 5 and any(keyword in line for keyword in ['项目', 'Project', '工作', 'Intern', '实习', '技能', 'Skill', '获奖', 'Award']):
                in_education_section = False
                continue

            current_entry_lines.append(line)

            if len(current_entry_lines) >= 3:
                education_text = ' '.join(current_entry_lines)
                entry = EducationEntry(
                    school=extract_school_from_text(education_text),
                    major=extract_major_from_text(education_text),
                    degree=extract_degree_from_text(education_text),
                    duration=extract_duration_from_text(education_text),
                    description=education_text
                )
                education_entries.append(entry)
                current_entry_lines = []
                in_education_section = False

    return education_entries


def extract_projects(text: str) -> list:
    project_entries = []
    lines = text.split('\n')

    project_keywords = ['项目', 'Project', '项目经历', '项目经验']

    in_project_section = False
    current_project = {}
    project_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if any(keyword in line for keyword in project_keywords):
            in_project_section = True
            continue

        if in_project_section:
            if len(line) < 5 and any(keyword in line for keyword in ['教育', 'Education', '实习', 'Intern', '技能', 'Skill', '获奖', 'Award', '工作', 'Work']):
                if current_project.get('name'):
                    project_entries.append(ProjectEntry(
                        name=current_project.get('name', ''),
                        description=' '.join(project_lines) if project_lines else current_project.get('description', ''),
                        technologies=current_project.get('technologies', []),
                        highlights=current_project.get('highlights', [])
                    ))
                current_project = {}
                project_lines = []
                in_project_section = False
                continue

            if '：' in line or ':' in line:
                parts = line.split('：') if '：' in line else line.split(':')
                key = parts[0].strip()
                value = '：'.join(parts[1:]) if '：' in line else ':'.join(parts[1:])

                if any(k in key for k in ['名称', '名字', 'Name', '项目名']):
                    current_project['name'] = value
                elif any(k in key for k in ['技术', 'Tech', '框架', 'Framework']):
                    current_project['technologies'] = [t.strip() for t in re.split(r'[,，、]', value) if t.strip()]
                elif any(k in key for k in ['时间', 'Duration', '期间']):
                    current_project['duration'] = value
            else:
                project_lines.append(line)

    if current_project.get('name'):
        project_entries.append(ProjectEntry(
            name=current_project.get('name', ''),
            description=' '.join(project_lines) if project_lines else current_project.get('description', ''),
            technologies=current_project.get('technologies', []),
            highlights=current_project.get('highlights', [])
        ))

    return project_entries


def extract_skills(text: str) -> list:
    skill_entries = []
    lines = text.split('\n')

    skill_keywords = ['技能', 'Skill', '技术栈', '技术', '掌握', '熟悉']

    current_category = None
    current_skills = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if any(keyword in line for keyword in skill_keywords):
            if current_category and current_skills:
                skill_entries.append(SkillEntry(category=current_category, items=current_skills))
            current_category = '技术技能'
            current_skills = []
            continue

        if any(keyword in line for keyword in ['项目', 'Project', '教育', 'Education', '实习', 'Intern', '获奖', 'Award']):
            if current_category and current_skills:
                skill_entries.append(SkillEntry(category=current_category, items=current_skills))
            current_category = None
            current_skills = []
            continue

        if current_category is not None:
            skills = re.split(r'[,，、\n]', line)
            for skill in skills:
                skill = skill.strip()
                if skill and len(skill) < 30:
                    current_skills.append(skill)

    if current_category and current_skills:
        skill_entries.append(SkillEntry(category=current_category, items=current_skills))

    return skill_entries


def extract_internships(text: str) -> list:
    internship_entries = []
    lines = text.split('\n')

    internship_keywords = ['实习', 'Intern', '工作', 'Work', '经历']

    in_intern_section = False
    current_intern = {}
    intern_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if any(keyword in line for keyword in internship_keywords):
            in_intern_section = True
            continue

        if in_intern_section:
            if len(line) < 5 and any(keyword in line for keyword in ['项目', 'Project', '教育', 'Education', '技能', 'Skill', '获奖', 'Award']):
                if current_intern.get('company'):
                    internship_entries.append(InternshipEntry(
                        company=current_intern.get('company', ''),
                        position=current_intern.get('position'),
                        duration=current_intern.get('duration'),
                        description=' '.join(intern_lines) if intern_lines else current_intern.get('description', ''),
                        achievements=current_intern.get('achievements', [])
                    ))
                current_intern = {}
                intern_lines = []
                in_intern_section = False
                continue

            if '：' in line or ':' in line:
                parts = line.split('：') if '：' in line else line.split(':')
                key = parts[0].strip()
                value = '：'.join(parts[1:]) if '：' in line else ':'.join(parts[1:])

                if any(k in key for k in ['公司', 'Company']):
                    current_intern['company'] = value
                elif any(k in key for k in ['职位', 'Position', '岗位']):
                    current_intern['position'] = value
                elif any(k in key for k in ['时间', 'Duration', '期间']):
                    current_intern['duration'] = value
            else:
                intern_lines.append(line)

    if current_intern.get('company'):
        internship_entries.append(InternshipEntry(
            company=current_intern.get('company', ''),
            position=current_intern.get('position'),
            duration=current_intern.get('duration'),
            description=' '.join(intern_lines) if intern_lines else current_intern.get('description', ''),
            achievements=current_intern.get('achievements', [])
        ))

    return internship_entries


def extract_awards(text: str) -> list:
    award_entries = []
    lines = text.split('\n')

    award_keywords = ['获奖', 'Award', '荣誉', '证书', 'Cert', '奖学金']

    in_award_section = False
    current_award_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if any(keyword in line for keyword in award_keywords):
            in_award_section = True
            if current_award_lines:
                award_text = ' '.join(current_award_lines)
                award_entries.append(AwardEntry(
                    name=award_text,
                    description=award_text
                ))
                current_award_lines = []
            continue

        if in_award_section:
            if len(line) < 5 and any(keyword in line for keyword in ['项目', 'Project', '教育', 'Education', '实习', 'Intern', '技能', 'Skill']):
                in_award_section = False
                continue

            current_award_lines.append(line)

    if current_award_lines:
        award_text = ' '.join(current_award_lines)
        award_entries.append(AwardEntry(
            name=award_text,
            description=award_text
        ))

    return award_entries


def extract_summary(text: str) -> SummaryEntry | None:
    lines = text.split('\n')

    summary_keywords = ['总结', 'Summary', '个人', '简介', 'About', 'Objective']

    for line in lines:
        line = line.strip()
        if any(keyword in line for keyword in summary_keywords):
            if len(line) > 10:
                return SummaryEntry(content=line)
            continue

        if 50 < len(line) < 500 and not any(
            keyword in line for keyword in ['项目', '教育', '实习', '技能', '获奖', '电话', '邮箱']
        ):
            return SummaryEntry(content=line)

    return None


def extract_school_from_text(text: str) -> str | None:
    universities = ['大学', '学院', 'University', 'college', ' institute']
    for uni in universities:
        if uni.lower() in text.lower():
            match = re.search(rf'([\u4e00-\u9fa5a-zA-Z\s]+{uni}[\u4e00-\u9fa5a-zA-Z\s]*)', text)
            if match:
                return match.group().strip()
    return None


def extract_major_from_text(text: str) -> str | None:
    majors = ['专业', 'Major', '计算机', '软件', '电子', '机械', '数学', '物理']
    for major in majors:
        if major in text:
            return text
    return None


def extract_degree_from_text(text: str) -> str | None:
    degrees = ['本科', '硕士', '博士', 'Bachelor', 'Master', 'PhD', '研究生']
    for degree in degrees:
        if degree in text:
            return degree
    return None


def extract_duration_from_text(text: str) -> str | None:
    duration_pattern = r'(\d{4})\s*[-~]\s*(\d{4}|\d{2}|至今|present|Now)'
    match = re.search(duration_pattern, text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return None
