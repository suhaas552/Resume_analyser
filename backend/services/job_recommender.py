from typing import Any

from services.job_matcher import calculate_job_match
from services.skill_gap_analyzer import analyse_skill_gap


def recommend_jobs(
    resume_skills: list[dict[str, Any]],
    jobs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Compare a resume against multiple jobs and rank the jobs
    according to how well the resume matches their required skills.
    """

    resume_skill_names = [
        skill["skill_name"]
        for skill in resume_skills
        if skill.get("skill_name")
    ]

    recommendations = []

    for job in jobs:
        job_skills = job.get("skills", [])

        # Basic weighted job match
        match_result = calculate_job_match(
            resume_skills=resume_skill_names,
            job_skills=job_skills
        )

        # Detailed skill-gap analysis
        skill_gap_result = analyse_skill_gap(
            resume_skills=resume_skills,
            job_skills=job_skills
        )

        recommendation = {
            "job_id": job["job_id"],
            "job_title": job["job_title"],
            "company_name": job.get("company_name"),
            "experience_required": job.get("experience_required"),
            "location": job.get("location"),

            "match_score": match_result["match_score"],

            "skill_coverage": skill_gap_result["skill_coverage"],
            "readiness_level": skill_gap_result["readiness_level"],

            "matched_skill_count": skill_gap_result[
                "matched_skill_count"
            ],

            "missing_skill_count": skill_gap_result[
                "missing_skill_count"
            ],

            "matched_skills": skill_gap_result[
                "matched_skills"
            ],

            "missing_skills": skill_gap_result[
                "missing_skills"
            ],

            "recommendations": skill_gap_result[
                "recommendations"
            ],
        }

        recommendations.append(recommendation)

    # Highest matching jobs should appear first
    recommendations.sort(
        key=lambda job: (
            job["match_score"],
            job["skill_coverage"]
        ),
        reverse=True
    )

    # Add ranking after sorting
    for index, recommendation in enumerate(
        recommendations,
        start=1
    ):
        recommendation["rank"] = index

    return recommendations