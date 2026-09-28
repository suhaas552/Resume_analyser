import re
from typing import Any


# Skills that the JD analyzer knows how to identify.
# We can later move this into the database.
JD_SKILL_KEYWORDS = {
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
    "rest api",
    "restful api",

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

    # DevOps / Cloud
    "git",
    "github",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "linux",
    "nginx",
    "ci/cd",

    # General technical
    "data structures",
    "algorithms",
    "object oriented programming",
    "oop",
    "microservices",
    "api development",
}


def _normalize_text(text: str) -> str:
    """
    Normalize text for reliable keyword matching.
    """

    return re.sub(
        r"\s+",
        " ",
        (text or "").lower()
    ).strip()


def _contains_skill(
    text: str,
    skill: str
) -> bool:
    """
    Check whether a skill occurs as a standalone keyword
    or phrase inside text.
    """

    pattern = (
        r"(?<!\w)"
        + re.escape(skill.lower())
        + r"(?!\w)"
    )

    return bool(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )
    )


def _extract_jd_skills(
    job_description: str
) -> list[str]:
    """
    Detect known technical skills mentioned in the
    job description.
    """

    normalized_jd = _normalize_text(job_description)

    detected_skills = []

    for skill in JD_SKILL_KEYWORDS:

        if _contains_skill(
            normalized_jd,
            skill
        ):
            detected_skills.append(skill)

    return sorted(
        detected_skills,
        key=str.lower
    )


def _calculate_match_level(
    coverage_score: float
) -> str:
    """
    Convert JD skill coverage into a simple readiness level.
    """

    if coverage_score >= 80:
        return "STRONG"

    if coverage_score >= 60:
        return "GOOD"

    if coverage_score >= 40:
        return "MODERATE"

    return "LOW"


def analyze_job_description(
    resume_skills: list[str],
    job_description: str,
) -> dict[str, Any]:
    """
    Compare resume skills against skills detected directly
    from a job description.

    The main score represents JD requirement coverage:

        matched JD skills / total detected JD skills

    This is more meaningful than measuring how many resume
    skills happen to appear in the job description.
    """

    normalized_jd = _normalize_text(
        job_description
    )

    normalized_resume_skills = sorted(
        {
            skill.strip().lower()
            for skill in resume_skills
            if skill and skill.strip()
        }
    )

    resume_skill_set = set(
        normalized_resume_skills
    )

    # ---------------------------------------------------------
    # 1. Detect skills requested by the JD
    # ---------------------------------------------------------

    jd_skills = _extract_jd_skills(
        normalized_jd
    )

    # ---------------------------------------------------------
    # 2. Compare JD requirements with resume
    # ---------------------------------------------------------

    matched_jd_skills = []
    missing_jd_skills = []

    for skill in jd_skills:

        if skill in resume_skill_set:
            matched_jd_skills.append(skill)

        else:
            missing_jd_skills.append(skill)

    # ---------------------------------------------------------
    # 3. Calculate JD coverage
    # ---------------------------------------------------------

    total_jd_skills = len(jd_skills)
    matched_jd_skill_count = len(
        matched_jd_skills
    )

    if total_jd_skills:

        jd_skill_coverage = round(
            (
                matched_jd_skill_count
                / total_jd_skills
            )
            * 100,
            2
        )

    else:
        jd_skill_coverage = 0.0

    # ---------------------------------------------------------
    # 4. Keep previous resume-relevance calculation
    # ---------------------------------------------------------

    matched_resume_skills = []
    unmatched_resume_skills = []

    for skill in normalized_resume_skills:

        if _contains_skill(
            normalized_jd,
            skill
        ):
            matched_resume_skills.append(
                skill
            )

        else:
            unmatched_resume_skills.append(
                skill
            )

    total_resume_skills = len(
        normalized_resume_skills
    )

    matched_skill_count = len(
        matched_resume_skills
    )

    if total_resume_skills:

        resume_skill_relevance = round(
            (
                matched_skill_count
                / total_resume_skills
            )
            * 100,
            2
        )

    else:
        resume_skill_relevance = 0.0

    # ---------------------------------------------------------
    # 5. Recommendations
    # ---------------------------------------------------------

    recommendations = []

    if missing_jd_skills:

        recommendations.append(
            "Consider learning or demonstrating these "
            "skills requested by the job description: "
            + ", ".join(missing_jd_skills)
            + "."
        )

    if matched_jd_skills:

        recommendations.append(
            "Highlight these matching skills prominently "
            "in the resume: "
            + ", ".join(matched_jd_skills)
            + "."
        )

    if not jd_skills:

        recommendations.append(
            "No recognizable technical skills were detected "
            "in the job description. Review the job description "
            "manually or expand the skill dictionary."
        )

    # ---------------------------------------------------------
    # 6. Return detailed JD analysis
    # ---------------------------------------------------------

    return {
        "jd_skills": jd_skills,

        "matched_jd_skills": matched_jd_skills,

        "missing_jd_skills": missing_jd_skills,

        "total_jd_skills": total_jd_skills,

        "matched_jd_skill_count": (
            matched_jd_skill_count
        ),

        "missing_jd_skill_count": len(
            missing_jd_skills
        ),

        "jd_skill_coverage": (
            jd_skill_coverage
        ),

        "match_level": _calculate_match_level(
            jd_skill_coverage
        ),

        # Previous fields are retained for compatibility.
        "matched_resume_skills": (
            matched_resume_skills
        ),

        "unmatched_resume_skills": (
            unmatched_resume_skills
        ),

        "matched_skill_count": (
            matched_skill_count
        ),

        "total_resume_skills": (
            total_resume_skills
        ),

        "resume_skill_relevance": (
            resume_skill_relevance
        ),

        "recommendations": recommendations,
    }