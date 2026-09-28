from typing import Any


def calculate_job_ats_score(
    resume_analysis: dict[str, Any],
    match_result: dict[str, Any],
    jd_analysis: dict[str, Any],
    skill_gap: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate a job-specific ATS compatibility score.

    The score combines:
    - General resume ATS quality
    - Configured job skill match
    - Skills detected directly from the job description
    - Critical skill readiness
    """

    # ---------------------------------------------------------
    # 1. Resume ATS quality
    # ---------------------------------------------------------

    resume_scores = resume_analysis.get(
        "scores",
        {}
    )

    resume_ats_score = float(
        resume_scores.get(
            "ats_score",
            0
        )
    )

    # ---------------------------------------------------------
    # 2. Configured job skill match
    # ---------------------------------------------------------

    job_skill_match_score = float(
        match_result.get(
            "match_score",
            0
        )
    )

    # ---------------------------------------------------------
    # 3. JD keyword / skill coverage
    # ---------------------------------------------------------

    jd_skill_coverage = float(
        jd_analysis.get(
            "jd_skill_coverage",
            0
        )
    )

    # ---------------------------------------------------------
    # 4. Detailed skill coverage
    # ---------------------------------------------------------

    skill_coverage = float(
        skill_gap.get(
            "skill_coverage",
            0
        )
    )

    # ---------------------------------------------------------
    # 5. Weighted ATS calculation
    # ---------------------------------------------------------

    weights = {
        "resume_quality": 0.25,
        "job_skill_match": 0.35,
        "jd_skill_coverage": 0.25,
        "skill_readiness": 0.15,
    }

    weighted_resume_quality = (
        resume_ats_score
        * weights["resume_quality"]
    )

    weighted_job_match = (
        job_skill_match_score
        * weights["job_skill_match"]
    )

    weighted_jd_coverage = (
        jd_skill_coverage
        * weights["jd_skill_coverage"]
    )

    weighted_skill_readiness = (
        skill_coverage
        * weights["skill_readiness"]
    )

    job_ats_score = round(
        weighted_resume_quality
        + weighted_job_match
        + weighted_jd_coverage
        + weighted_skill_readiness,
        2
    )

    # ---------------------------------------------------------
    # 6. Rating
    # ---------------------------------------------------------

    if job_ats_score >= 85:
        rating = "EXCELLENT"

    elif job_ats_score >= 70:
        rating = "STRONG"

    elif job_ats_score >= 55:
        rating = "MODERATE"

    elif job_ats_score >= 40:
        rating = "WEAK"

    else:
        rating = "POOR"

    # ---------------------------------------------------------
    # 7. Critical missing skills
    # ---------------------------------------------------------

    missing_skills = skill_gap.get(
        "missing_skills",
        []
    ) or []

    critical_missing_skills = [
        skill.get("skill_name")
        for skill in missing_skills
        if str(
            skill.get(
                "importance",
                ""
            )
        ).upper() == "REQUIRED"
    ]

    # ---------------------------------------------------------
    # 8. Recommendations
    # ---------------------------------------------------------

    recommendations = []

    if critical_missing_skills:
        recommendations.append(
            "Prioritize these required skills: "
            + ", ".join(
                critical_missing_skills
            )
            + "."
        )

    if jd_skill_coverage < 70:
        recommendations.append(
            "Improve alignment with the terminology and "
            "technical requirements used in the job description."
        )

    if resume_ats_score < 80:
        recommendations.append(
            "Improve the resume structure, sections, keywords, "
            "and measurable achievements."
        )

    if job_ats_score >= 85:
        recommendations.append(
            "The resume has strong compatibility with this job. "
            "Focus on tailoring achievements and project evidence."
        )

    # ---------------------------------------------------------
    # 9. Return detailed score
    # ---------------------------------------------------------

    return {
        "job_ats_score": job_ats_score,
        "rating": rating,

        "score_breakdown": {
            "resume_ats_score": resume_ats_score,
            "job_skill_match_score": job_skill_match_score,
            "jd_skill_coverage": jd_skill_coverage,
            "skill_coverage": skill_coverage,
        },

        "weights": weights,

        "critical_missing_skills": (
            critical_missing_skills
        ),

        "recommendations": recommendations,
    }