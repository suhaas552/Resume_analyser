import re
from typing import Optional


SKILL_KEYWORDS = {
    # Programming
    "python", "java", "c", "c++", "c#", "javascript",
    "typescript", "php", "kotlin", "swift", "dart",

    # Web / Backend
    "html", "css", "react", "angular", "vue", "node.js",
    "express", "fastapi", "django", "flask", "spring boot",

    # Databases
    "sql", "mysql", "postgresql", "mongodb", "oracle", "redis",

    # Data / AI
    "numpy", "pandas", "matplotlib", "seaborn",
    "machine learning", "deep learning", "data analysis",
    "data science", "tensorflow", "pytorch", "scikit-learn",
    "power bi", "tableau", "excel",

    # Development tools
    "git", "github", "docker", "kubernetes",
    "aws", "azure", "gcp", "linux",

    # Warehouse / Logistics
    "inventory management", "warehouse management",
    "logistics", "supply chain", "packing", "picking",
    "shipping", "kanban", "5s", "kaizen",

    # General
    "project management", "communication", "leadership",
    "problem solving", "teamwork", "mathematics",
}


SECTION_NAMES = {
    "education": [
        "education",
        "academic background",
        "academic qualifications",
        "qualifications",
    ],
    "experience": [
        "experience",
        "employment history",
        "work experience",
        "professional experience",
        "employment",
    ],
    "projects": [
        "projects",
        "academic projects",
        "personal projects",
        "project experience",
    ],
    "skills": [
        "skills",
        "technical skills",
        "core skills",
        "key skills",
        "competencies",
    ],
    "certifications": [
        "certifications",
        "certificates",
        "courses",
        "training",
    ],
    "achievements": [
        "achievements",
        "awards",
        "accomplishments",
    ],
    "languages": [
        "languages",
        "language proficiency",
    ],
}


def clean_text(text: str) -> str:
    """Clean extracted resume text while preserving line structure."""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    lines = []

    for line in text.split("\n"):
        cleaned_line = re.sub(r"[ \t]+", " ", line).strip()

        if cleaned_line:
            lines.append(cleaned_line)

    return "\n".join(lines)


def extract_email(text: str) -> Optional[str]:
    """Extract the first email address."""

    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    match = re.search(pattern, text)

    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extract a likely phone number."""

    pattern = r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"

    matches = re.findall(pattern, text)

    for match in matches:
        digits = re.sub(r"\D", "", match)

        if 10 <= len(digits) <= 15:
            return match.strip()

    return None


def extract_name(text: str) -> Optional[str]:
    """Estimate the candidate name from the beginning of the resume."""

    ignored = {
        "resume",
        "curriculum vitae",
        "cv",
        "profile",
        "summary",
        "professional summary",
        "objective",
    }

    lines = text.split("\n")[:10]

    for line in lines:
        candidate = line.strip()

        if not candidate:
            continue

        if candidate.lower() in ignored:
            continue

        if "@" in candidate:
            continue

        if re.search(r"\d", candidate):
            continue

        words = candidate.split()

        if 2 <= len(words) <= 5 and len(candidate) <= 80:
            return candidate

    return None


def extract_skills(text: str) -> list[str]:
    """Find known skills mentioned anywhere in the resume."""

    text_lower = text.lower()
    detected = []

    for skill in SKILL_KEYWORDS:
        pattern = rf"(?<!\w){re.escape(skill)}(?!\w)"

        if re.search(pattern, text_lower):
            detected.append(skill)

    return sorted(detected, key=str.lower)


def extract_sections(text: str) -> dict:
    """Detect common resume sections."""

    lines = text.split("\n")
    heading_lookup = {}

    for section, headings in SECTION_NAMES.items():
        for heading in headings:
            heading_lookup[heading.lower()] = section

    sections = {}
    current_section = None

    for line in lines:
        stripped = line.strip()
        normalized = stripped.lower().rstrip(":")

        if normalized in heading_lookup:
            current_section = heading_lookup[normalized]

            if current_section not in sections:
                sections[current_section] = []

            continue

        if current_section:
            sections[current_section].append(stripped)

    return {
        section: "\n".join(content).strip()
        for section, content in sections.items()
        if content
    }


def calculate_ats_score(
    name: Optional[str],
    email: Optional[str],
    phone: Optional[str],
    sections: dict
) -> float:
    """Calculate basic ATS-readiness score out of 100."""

    score = 0

    if name:
        score += 15

    if email:
        score += 15

    if phone:
        score += 10

    if sections.get("skills"):
        score += 15

    if sections.get("education"):
        score += 15

    if sections.get("experience"):
        score += 15

    if sections.get("projects"):
        score += 10

    if sections.get("certifications"):
        score += 5

    return min(float(score), 100.0)


def calculate_skills_score(skills: list[str]) -> float:
    """Calculate skill-content score."""

    count = len(skills)

    if count >= 10:
        return 100.0
    if count >= 8:
        return 90.0
    if count >= 6:
        return 80.0
    if count >= 4:
        return 65.0
    if count >= 2:
        return 45.0
    if count == 1:
        return 25.0

    return 0.0


def calculate_education_score(sections: dict) -> float:
    """Calculate education section score."""

    education = sections.get("education", "")

    if not education:
        return 0.0

    word_count = len(education.split())

    if word_count >= 20:
        return 100.0
    if word_count >= 10:
        return 80.0
    if word_count >= 5:
        return 60.0

    return 40.0


def calculate_experience_score(sections: dict) -> float:
    """Calculate experience section score."""

    experience = sections.get("experience", "")

    if not experience:
        return 0.0

    word_count = len(experience.split())

    if word_count >= 100:
        return 100.0
    if word_count >= 60:
        return 90.0
    if word_count >= 30:
        return 75.0
    if word_count >= 15:
        return 60.0

    return 40.0


def calculate_project_score(sections: dict) -> float:
    """Calculate projects section score."""

    projects = sections.get("projects", "")

    if not projects:
        return 0.0

    word_count = len(projects.split())

    if word_count >= 60:
        return 100.0
    if word_count >= 30:
        return 85.0
    if word_count >= 15:
        return 70.0

    return 50.0


def build_feedback(
    email: Optional[str],
    phone: Optional[str],
    skills: list[str],
    sections: dict
) -> tuple[list[str], list[str], list[str]]:
    """Generate strengths, weaknesses and suggestions."""

    strengths = []
    weaknesses = []
    suggestions = []

    if email and phone:
        strengths.append("Contact information is clearly available.")
    else:
        weaknesses.append("Contact information is incomplete.")
        suggestions.append(
            "Include a professional email address and phone number."
        )

    if len(skills) >= 6:
        strengths.append(
            "Resume contains a good range of identifiable skills."
        )
    else:
        weaknesses.append(
            "The resume contains relatively few identifiable skills."
        )
        suggestions.append(
            "Add relevant technical and professional skills."
        )

    if sections.get("experience"):
        strengths.append("Work experience is clearly presented.")
    else:
        weaknesses.append("A clear work experience section was not detected.")
        suggestions.append(
            "Add an experience or internship section where applicable."
        )

    if sections.get("education"):
        strengths.append("Education information is included.")
    else:
        weaknesses.append("Education section was not detected.")
        suggestions.append(
            "Add a clearly labelled Education section."
        )

    if sections.get("projects"):
        strengths.append("Projects are included in the resume.")
    else:
        weaknesses.append("A dedicated projects section was not detected.")
        suggestions.append(
            "Add relevant academic or personal projects with technologies "
            "used and measurable outcomes."
        )

    if sections.get("certifications"):
        strengths.append(
            "Certifications or additional training are included."
        )
    else:
        suggestions.append(
            "Add relevant certifications or training if available."
        )

    return strengths, weaknesses, suggestions


def analyse_resume(text: str) -> dict:
    """Analyse a resume and generate structured data and scores."""

    cleaned_text = clean_text(text)

    sections = extract_sections(cleaned_text)
    skills = extract_skills(cleaned_text)

    name = extract_name(cleaned_text)
    email = extract_email(cleaned_text)
    phone = extract_phone(cleaned_text)

    ats_score = calculate_ats_score(
        name,
        email,
        phone,
        sections
    )

    skills_score = calculate_skills_score(skills)
    education_score = calculate_education_score(sections)
    experience_score = calculate_experience_score(sections)
    project_score = calculate_project_score(sections)

    # Weighted general resume score.
    overall_score = round(
        (ats_score * 0.30)
        + (skills_score * 0.25)
        + (education_score * 0.15)
        + (experience_score * 0.20)
        + (project_score * 0.10),
        2
    )

    strengths, weaknesses, suggestions = build_feedback(
        email,
        phone,
        skills,
        sections
    )

    if overall_score >= 80:
        summary = (
            "The resume has strong overall structure and content. "
            "Further improvements can focus on tailoring it to specific jobs."
        )
    elif overall_score >= 60:
        summary = (
            "The resume has a reasonable foundation but several areas "
            "can be improved to strengthen its overall quality."
        )
    elif overall_score >= 40:
        summary = (
            "The resume contains useful information but needs significant "
            "improvements in structure, content, or completeness."
        )
    else:
        summary = (
            "The resume requires substantial improvement before it is "
            "ready for effective job applications."
        )

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "sections": sections,

        "scores": {
            "overall_score": overall_score,
            "ats_score": ats_score,
            "skills_score": skills_score,
            "education_score": education_score,
            "experience_score": experience_score,
            "project_score": project_score,
        },

        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "analysis_summary": summary,

        "statistics": {
            "character_count": len(cleaned_text),
            "word_count": len(cleaned_text.split()),
            "detected_skill_count": len(skills),
            "detected_section_count": len(sections),
        },
    }