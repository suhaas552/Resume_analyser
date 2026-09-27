import re
from typing import Optional


# Common technical and professional skills.
# We can expand this list later or move it into the database.
SKILL_KEYWORDS = {
    # Programming
    "python",
    "java",
    "c",
    "c++",
    "c#",
    "javascript",
    "typescript",
    "php",
    "kotlin",
    "swift",
    "dart",

    # Web / Backend
    "html",
    "css",
    "react",
    "angular",
    "vue",
    "node.js",
    "express",
    "fastapi",
    "django",
    "flask",
    "spring boot",

    # Databases
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "oracle",
    "redis",

    # Data / AI
    "numpy",
    "pandas",
    "matplotlib",
    "seaborn",
    "machine learning",
    "deep learning",
    "data analysis",
    "data science",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "power bi",
    "tableau",
    "excel",

    # Development tools
    "git",
    "github",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "linux",

    # Warehouse / Logistics
    "inventory management",
    "warehouse management",
    "logistics",
    "supply chain",
    "packing",
    "picking",
    "shipping",
    "kanban",
    "5s",
    "kaizen",

    # General
    "project management",
    "communication",
    "leadership",
    "problem solving",
    "teamwork",
    "mathematics",
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
    """
    Estimate the candidate name from the beginning of the resume.

    This intentionally uses conservative rules so headings such as
    'Resume' or 'Curriculum Vitae' are not returned as names.
    """

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
    """
    Detect common resume sections using headings.

    Returns the text belonging to each detected section.
    """

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


def analyse_resume(text: str) -> dict:
    """
    Convert extracted resume text into basic structured information.
    """

    cleaned_text = clean_text(text)

    sections = extract_sections(cleaned_text)

    return {
        "name": extract_name(cleaned_text),
        "email": extract_email(cleaned_text),
        "phone": extract_phone(cleaned_text),
        "skills": extract_skills(cleaned_text),
        "sections": sections,
        "statistics": {
            "character_count": len(cleaned_text),
            "word_count": len(cleaned_text.split()),
            "detected_skill_count": len(extract_skills(cleaned_text)),
            "detected_section_count": len(sections),
        },
    }