import re
from typing import Any


def _normalize_text(text: str) -> str:
    """Normalize text for reliable keyword matching."""
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def analyze_job_description(
    resume_skills: list[str],
    job_description: str,
) -> dict[str, Any]:
    """
    Compare detected resume skills against a job description.

    This service does not modify the existing resume analysis.
    It only performs JD-specific skill matching.
    """

    normalized_jd = _normalize_text(job_description)

    normalized_resume_skills = sorted(
        {
            skill.strip().lower()
            for skill in resume_skills
            if skill and skill.strip()
        }
    )

    matched_skills = []
    unmatched_resume_skills = []

    for skill in normalized_resume_skills:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

        if re.search(pattern, normalized_jd, flags=re.IGNORECASE):
            matched_skills.append(skill)
        else:
            unmatched_resume_skills.append(skill)

    total_resume_skills = len(normalized_resume_skills)
    matched_skill_count = len(matched_skills)

    if total_resume_skills:
        resume_skill_relevance = round(
            (matched_skill_count / total_resume_skills) * 100,
            2,
        )
    else:
        resume_skill_relevance = 0.0

    return {
        "matched_resume_skills": matched_skills,
        "unmatched_resume_skills": unmatched_resume_skills,
        "matched_skill_count": matched_skill_count,
        "total_resume_skills": total_resume_skills,
        "resume_skill_relevance": resume_skill_relevance,
    }