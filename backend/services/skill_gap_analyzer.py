from typing import Any


IMPORTANCE_PRIORITY = {
    "REQUIRED": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


def analyse_skill_gap(
    resume_skills: list[dict[str, Any]],
    job_skills: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Analyse the skill gap between a candidate's resume
    and a job description.

    Returns:
    - matched skills
    - missing skills
    - priority skills to learn
    - candidate strengths
    - learning recommendations
    - readiness level
    """

    # ---------------------------------------------------------
    # 1. Normalize resume skills
    # ---------------------------------------------------------

    resume_skill_map = {}

    for skill in resume_skills:

        skill_name = str(
            skill.get("skill_name", "")
        ).strip().lower()

        if not skill_name:
            continue

        resume_skill_map[skill_name] = {
            "skill_name": skill_name,
            "proficiency_score": float(
                skill.get("proficiency_score", 0) or 0
            ),
            "occurrence_count": int(
                skill.get("occurrence_count", 0) or 0
            ),
        }

    # ---------------------------------------------------------
    # 2. Compare resume skills with job skills
    # ---------------------------------------------------------

    matched_skills = []
    missing_skills = []

    for job_skill in job_skills:

        skill_name = str(
            job_skill.get("skill_name", "")
        ).strip().lower()

        if not skill_name:
            continue

        importance = str(
            job_skill.get("importance", "MEDIUM")
        ).strip().upper()

        if importance not in IMPORTANCE_PRIORITY:
            importance = "MEDIUM"

        if skill_name in resume_skill_map:

            resume_skill = resume_skill_map[skill_name]

            matched_skills.append(
                {
                    "skill_name": skill_name,
                    "importance": importance,
                    "proficiency_score":
                        resume_skill["proficiency_score"],
                    "occurrence_count":
                        resume_skill["occurrence_count"],
                }
            )

        else:

            missing_skills.append(
                {
                    "skill_name": skill_name,
                    "importance": importance,
                    "priority_score":
                        IMPORTANCE_PRIORITY[importance],
                }
            )

    # ---------------------------------------------------------
    # 3. Sort missing skills by importance
    # ---------------------------------------------------------

    missing_skills.sort(
        key=lambda skill: skill["priority_score"],
        reverse=True,
    )

    # ---------------------------------------------------------
    # 4. Determine priority skills to learn
    # ---------------------------------------------------------

    priority_skills = [
        skill["skill_name"]
        for skill in missing_skills
        if skill["importance"] in {"REQUIRED", "HIGH"}
    ]

    # ---------------------------------------------------------
    # 5. Determine strongest matching skills
    # ---------------------------------------------------------

    strongest_skills = sorted(
        matched_skills,
        key=lambda skill: (
            IMPORTANCE_PRIORITY.get(
                skill["importance"],
                0,
            ),
            skill["proficiency_score"],
            skill["occurrence_count"],
        ),
        reverse=True,
    )

    strongest_skills = strongest_skills[:5]

    # ---------------------------------------------------------
    # 6. Calculate skill coverage
    # ---------------------------------------------------------

    total_job_skills = len(job_skills)
    total_matched_skills = len(matched_skills)

    if total_job_skills == 0:
        skill_coverage = 0.0

    else:
        skill_coverage = round(
            (
                total_matched_skills
                / total_job_skills
            )
            * 100,
            2,
        )

    # ---------------------------------------------------------
    # 7. Determine readiness level
    # ---------------------------------------------------------

    required_missing = [
        skill
        for skill in missing_skills
        if skill["importance"] == "REQUIRED"
    ]

    high_missing = [
        skill
        for skill in missing_skills
        if skill["importance"] == "HIGH"
    ]

    if not job_skills:
        readiness_level = "UNKNOWN"

    elif not missing_skills:
        readiness_level = "STRONG"

    elif required_missing:
        readiness_level = "NEEDS_IMPROVEMENT"

    elif high_missing:
        readiness_level = "MODERATE"

    elif skill_coverage >= 75:
        readiness_level = "STRONG"

    elif skill_coverage >= 50:
        readiness_level = "MODERATE"

    else:
        readiness_level = "NEEDS_IMPROVEMENT"

    # ---------------------------------------------------------
    # 8. Generate recommendations
    # ---------------------------------------------------------

    recommendations = []

    if required_missing:

        required_names = [
            skill["skill_name"]
            for skill in required_missing
        ]

        recommendations.append(
            "Highest priority: learn or demonstrate the "
            "required skills: "
            + ", ".join(required_names)
            + "."
        )

    if high_missing:

        high_names = [
            skill["skill_name"]
            for skill in high_missing
        ]

        recommendations.append(
            "Strengthen these high-priority skills: "
            + ", ".join(high_names)
            + "."
        )

    medium_missing = [
        skill["skill_name"]
        for skill in missing_skills
        if skill["importance"] == "MEDIUM"
    ]

    if medium_missing:

        recommendations.append(
            "Improve these additional skills to increase "
            "job compatibility: "
            + ", ".join(medium_missing)
            + "."
        )

    if not missing_skills and job_skills:

        recommendations.append(
            "Your detected resume skills cover all "
            "skills configured for this job."
        )

    if not job_skills:

        recommendations.append(
            "No skills are configured for this job, "
            "so a skill-gap analysis cannot be calculated."
        )

    # ---------------------------------------------------------
    # 9. Return complete skill-gap analysis
    # ---------------------------------------------------------

    return {
        "skill_coverage": skill_coverage,
        "readiness_level": readiness_level,
        "total_job_skills": total_job_skills,
        "matched_skill_count": len(matched_skills),
        "missing_skill_count": len(missing_skills),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "priority_skills_to_learn": priority_skills,
        "strongest_matching_skills": strongest_skills,
        "recommendations": recommendations,
    }