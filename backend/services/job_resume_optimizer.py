from typing import Any


def optimize_resume_for_job(
    resume_analysis: dict[str, Any],
    jd_analysis: dict[str, Any],
    skill_gap: dict[str, Any],
    job_ats: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate job-specific resume optimization recommendations.

    This service does not invent skills, experience, projects,
    achievements, or metrics. It only recommends improvements
    based on existing resume and job-analysis data.
    """

    sections = resume_analysis.get("sections", {}) or {}

    matched_jd_skills = jd_analysis.get(
        "matched_jd_skills",
        []
    ) or []

    missing_jd_skills = jd_analysis.get(
        "missing_jd_skills",
        []
    ) or []

    missing_job_skills = skill_gap.get(
        "missing_skills",
        []
    ) or []

    priority_skills = skill_gap.get(
        "priority_skills_to_learn",
        []
    ) or []

    job_ats_score = float(
        job_ats.get(
            "job_ats_score",
            0
        )
    )

    # -----------------------------------------------------
    # 1. Skills to emphasize
    # -----------------------------------------------------

    skills_to_emphasize = sorted(
        set(matched_jd_skills)
    )

    # -----------------------------------------------------
    # 2. Missing skills
    # -----------------------------------------------------

    missing_skills = []

    for skill in missing_job_skills:

        skill_name = skill.get("skill_name")

        if skill_name:
            missing_skills.append(
                {
                    "skill_name": skill_name,
                    "importance": skill.get(
                        "importance"
                    ),
                    "priority_score": skill.get(
                        "priority_score"
                    ),
                }
            )

    # -----------------------------------------------------
    # 3. Section-specific recommendations
    # -----------------------------------------------------

    section_recommendations = {}

    if skills_to_emphasize:

        section_recommendations["skills"] = [
            (
                "Make matching job skills easy to locate in the "
                "Skills section: "
                + ", ".join(skills_to_emphasize)
                + "."
            )
        ]

    if sections.get("experience"):

        section_recommendations["experience"] = [
            (
                "Prioritize experience bullets that demonstrate "
                "skills and responsibilities relevant to this job."
            ),
            (
                "Use measurable outcomes where they are factually "
                "supported."
            ),
        ]

    if sections.get("projects"):

        section_recommendations["projects"] = [
            (
                "Place the most job-relevant projects first."
            ),
            (
                "Clearly show the technologies used and the "
                "problem solved by each relevant project."
            ),
        ]

    else:

        section_recommendations["projects"] = [
            (
                "Consider adding a relevant project that "
                "demonstrates the target job's required skills."
            )
        ]

    # -----------------------------------------------------
    # 4. Keyword recommendations
    # -----------------------------------------------------

    keyword_recommendations = []

    if skills_to_emphasize:

        keyword_recommendations.append(
            {
                "type": "MATCHED",
                "keywords": skills_to_emphasize,
                "recommendation": (
                    "These keywords already match the job. "
                    "Keep them visible in relevant resume sections."
                ),
            }
        )

    if missing_jd_skills:

        keyword_recommendations.append(
            {
                "type": "MISSING",
                "keywords": missing_jd_skills,
                "recommendation": (
                    "Only add these job-description keywords if "
                    "they truthfully reflect your skills or experience."
                ),
            }
        )

    # -----------------------------------------------------
    # 5. Optimization priorities
    # -----------------------------------------------------

    optimization_priorities = []

    for skill_name in priority_skills:

        optimization_priorities.append(
            {
                "priority": "HIGH",
                "area": "SKILL_GAP",
                "item": skill_name,
                "action": (
                    f"Learn or demonstrate {skill_name} through "
                    "coursework, projects, or real experience."
                ),
            }
        )

    if job_ats_score < 70:

        optimization_priorities.append(
            {
                "priority": "HIGH",
                "area": "JOB_ALIGNMENT",
                "item": "ATS compatibility",
                "action": (
                    "Tailor the resume more closely to the target "
                    "job while keeping all claims factually accurate."
                ),
            }
        )

    # -----------------------------------------------------
    # 6. Summary
    # -----------------------------------------------------

    if job_ats_score >= 85:
        summary = (
            "The resume is strongly aligned with this job. "
            "Focus on emphasizing the most relevant evidence."
        )

    elif job_ats_score >= 70:
        summary = (
            "The resume has good alignment with this job, but "
            "some targeted improvements could strengthen it."
        )

    elif job_ats_score >= 50:
        summary = (
            "The resume has moderate alignment with this job. "
            "Address important skill gaps and improve targeting."
        )

    else:
        summary = (
            "The resume currently has limited alignment with "
            "this job. Prioritize the major skill gaps before "
            "tailoring the resume."
        )

    return {
        "job_ats_score": job_ats_score,
        "summary": summary,
        "skills_to_emphasize": skills_to_emphasize,
        "missing_skills": missing_skills,
        "keyword_recommendations": keyword_recommendations,
        "section_recommendations": section_recommendations,
        "optimization_priorities": optimization_priorities,
        "safety_note": (
            "Only include skills, achievements, metrics, and "
            "experience that are factually true."
        ),
    }