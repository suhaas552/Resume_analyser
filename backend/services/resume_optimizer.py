import re
from typing import Any


STRONG_ACTION_VERBS = {
    "achieved",
    "automated",
    "built",
    "created",
    "designed",
    "developed",
    "implemented",
    "improved",
    "increased",
    "led",
    "managed",
    "optimized",
    "reduced",
    "resolved",
    "saved",
    "streamlined",
}


WEAK_PHRASES = {
    "responsible for",
    "worked on",
    "helped with",
    "participated in",
    "involved in",
    "hard working",
    "hardworking",
    "team player",
    "quick learner",
}


def _contains_number(text: str) -> bool:
    """Check whether resume content contains measurable numbers."""
    return bool(re.search(r"\d", text))


def _calculate_keyword_density(
    text: str,
    skills: list[str]
) -> dict[str, int]:
    """Count occurrences of detected skills in resume text."""

    text_lower = text.lower()
    result = {}

    for skill in skills:
        normalized_skill = skill.strip().lower()

        if not normalized_skill:
            continue

        count = text_lower.count(normalized_skill)

        if count > 0:
            result[normalized_skill] = count

    return result


def optimize_resume(
    resume_text: str,
    analysis: dict[str, Any]
) -> dict[str, Any]:
    """
    Analyse a resume for ATS and content-improvement opportunities.

    This function provides suggestions only. It does not overwrite
    the candidate's original resume.
    """

    text = resume_text.strip()
    text_lower = text.lower()

    sections = analysis.get("sections", {}) or {}
    skills = analysis.get("skills", []) or []
    scores = analysis.get("scores", {}) or {}

    issues = []
    recommendations = []

    # ---------------------------------------------------------
    # 1. Contact information
    # ---------------------------------------------------------

    if not analysis.get("email"):
        issues.append(
            {
                "category": "CONTACT",
                "severity": "HIGH",
                "issue": "Email address was not detected.",
            }
        )

        recommendations.append(
            "Add a professional email address near the top of the resume."
        )

    if not analysis.get("phone"):
        issues.append(
            {
                "category": "CONTACT",
                "severity": "HIGH",
                "issue": "Phone number was not detected.",
            }
        )

        recommendations.append(
            "Add a valid phone number near the contact information."
        )

    # ---------------------------------------------------------
    # 2. Important resume sections
    # ---------------------------------------------------------

    important_sections = {
        "education": "Education",
        "experience": "Experience",
        "skills": "Skills",
        "projects": "Projects",
    }

    for section_key, section_name in important_sections.items():

        if not sections.get(section_key):

            severity = (
                "HIGH"
                if section_key in {"experience", "skills"}
                else "MEDIUM"
            )

            issues.append(
                {
                    "category": "SECTION",
                    "severity": severity,
                    "issue": f"{section_name} section was not detected.",
                }
            )

            recommendations.append(
                f"Add a clearly labelled {section_name} section."
            )

    # ---------------------------------------------------------
    # 3. Quantifiable achievements
    # ---------------------------------------------------------

    experience_text = sections.get("experience", "")

    if experience_text and not _contains_number(experience_text):

        issues.append(
            {
                "category": "IMPACT",
                "severity": "HIGH",
                "issue": (
                    "Work experience contains few or no "
                    "quantifiable achievements."
                ),
            }
        )

        recommendations.append(
            "Add measurable results to experience bullets, such as "
            "percentages, time saved, users served, revenue, accuracy, "
            "performance improvements, or scale."
        )

    # ---------------------------------------------------------
    # 4. Projects
    # ---------------------------------------------------------

    projects_text = sections.get("projects", "")

    if not projects_text:

        recommendations.append(
            "Add relevant academic or personal projects that demonstrate "
            "your technical skills."
        )

    elif not _contains_number(projects_text):

        recommendations.append(
            "Strengthen project descriptions with measurable outcomes, "
            "dataset sizes, performance results, users, features, or scale."
        )

    # ---------------------------------------------------------
    # 5. Weak phrases
    # ---------------------------------------------------------

    detected_weak_phrases = sorted(
        phrase
        for phrase in WEAK_PHRASES
        if phrase in text_lower
    )

    for phrase in detected_weak_phrases:

        issues.append(
            {
                "category": "WORDING",
                "severity": "MEDIUM",
                "issue": f"Weak or generic phrase detected: '{phrase}'.",
            }
        )

    if detected_weak_phrases:

        recommendations.append(
            "Replace passive or generic phrases with specific action verbs "
            "and explain the result of your work."
        )

    # ---------------------------------------------------------
    # 6. Action verbs
    # ---------------------------------------------------------

    detected_action_verbs = sorted(
        verb
        for verb in STRONG_ACTION_VERBS
        if re.search(
            rf"\b{re.escape(verb)}\b",
            text_lower
        )
    )

    if len(detected_action_verbs) < 3:

        issues.append(
            {
                "category": "WORDING",
                "severity": "MEDIUM",
                "issue": (
                    "The resume uses relatively few strong "
                    "achievement-oriented action verbs."
                ),
            }
        )

        recommendations.append(
            "Start experience and project bullets with strong verbs such as "
            "developed, implemented, optimized, automated, improved, "
            "reduced, or built."
        )

    # ---------------------------------------------------------
    # 7. Skill keyword usage
    # ---------------------------------------------------------

    keyword_density = _calculate_keyword_density(
        text,
        skills
    )

    if len(skills) < 5:

        issues.append(
            {
                "category": "ATS_KEYWORDS",
                "severity": "MEDIUM",
                "issue": (
                    "Only a small number of recognizable skills "
                    "were detected."
                ),
            }
        )

        recommendations.append(
            "Include relevant technical keywords naturally in the Skills, "
            "Projects, and Experience sections."
        )

    # ---------------------------------------------------------
    # 8. Resume length
    # ---------------------------------------------------------

    word_count = len(text.split())

    if word_count < 200:

        issues.append(
            {
                "category": "CONTENT",
                "severity": "MEDIUM",
                "issue": "The resume may contain too little detail.",
            }
        )

        recommendations.append(
            "Add more evidence of projects, experience, achievements, "
            "technical skills, and measurable outcomes."
        )

    elif word_count > 1200:

        issues.append(
            {
                "category": "CONTENT",
                "severity": "MEDIUM",
                "issue": "The resume may be overly long.",
            }
        )

        recommendations.append(
            "Remove repetitive or low-value content and prioritize "
            "information relevant to the target role."
        )

    # ---------------------------------------------------------
    # 9. Remove duplicate recommendations
    # ---------------------------------------------------------

    recommendations = list(
        dict.fromkeys(recommendations)
    )

    # ---------------------------------------------------------
    # 10. Improvement priority
    # ---------------------------------------------------------

    severity_weight = {
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
    }

    issues.sort(
        key=lambda item: severity_weight.get(
            item["severity"],
            0
        ),
        reverse=True
    )

    # ---------------------------------------------------------
    # 11. Return optimization report
    # ---------------------------------------------------------

    return {
        "current_scores": scores,
        "word_count": word_count,
        "detected_skill_count": len(skills),
        "keyword_density": keyword_density,
        "detected_action_verbs": detected_action_verbs,
        "weak_phrases": detected_weak_phrases,
        "issues": issues,
        "recommendations": recommendations,
        "total_issues": len(issues),
    }