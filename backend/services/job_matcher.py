from typing import Any


IMPORTANCE_WEIGHTS = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "REQUIRED": 4,
}


def normalize_skill_name(skill_name: str) -> str:
    """
    Normalize a skill name so resume skills and job skills
    can be compared consistently.
    """
    return skill_name.strip().lower()


def calculate_job_match(
    resume_skills: list[str],
    job_skills: list[dict[str, Any]]
) -> dict:
    """
    Compare resume skills against the skills required for a job.

    job_skills example:
    [
        {
            "skill_name": "Python",
            "importance": "REQUIRED"
        },
        {
            "skill_name": "Docker",
            "importance": "MEDIUM"
        }
    ]
    """

    normalized_resume_skills = {
        normalize_skill_name(skill)
        for skill in resume_skills
        if skill and skill.strip()
    }

    matched_skills = []
    missing_skills = []

    total_weight = 0
    matched_weight = 0

    for job_skill in job_skills:
        skill_name = job_skill["skill_name"].strip()

        importance = (
            job_skill.get("importance", "MEDIUM")
            .strip()
            .upper()
        )

        weight = IMPORTANCE_WEIGHTS.get(
            importance,
            IMPORTANCE_WEIGHTS["MEDIUM"]
        )

        normalized_job_skill = normalize_skill_name(skill_name)

        total_weight += weight

        skill_result = {
            "skill_name": skill_name,
            "importance": importance,
            "weight": weight,
        }

        if normalized_job_skill in normalized_resume_skills:
            matched_weight += weight
            matched_skills.append(skill_result)

        else:
            missing_skills.append(skill_result)

    if total_weight == 0:
        match_score = 0.0
    else:
        match_score = round(
            (matched_weight / total_weight) * 100,
            2
        )

    recommendations = []

    required_missing = [
        skill["skill_name"]
        for skill in missing_skills
        if skill["importance"] == "REQUIRED"
    ]

    high_missing = [
        skill["skill_name"]
        for skill in missing_skills
        if skill["importance"] == "HIGH"
    ]

    if required_missing:
        recommendations.append(
            "Prioritize learning or demonstrating the required skills: "
            + ", ".join(required_missing)
            + "."
        )

    if high_missing:
        recommendations.append(
            "Strengthen these high-priority skills: "
            + ", ".join(high_missing)
            + "."
        )

    if not missing_skills and job_skills:
        recommendations.append(
            "Your detected resume skills cover all skills "
            "listed for this job."
        )

    if not job_skills:
        recommendations.append(
            "No job skills are currently configured for this job."
        )

    return {
        "match_score": match_score,
        "matched_skill_count": len(matched_skills),
        "missing_skill_count": len(missing_skills),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "recommendations": recommendations,
        "calculation": {
            "matched_weight": matched_weight,
            "total_weight": total_weight,
        },
    }