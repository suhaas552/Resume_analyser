import re
from typing import Any


# ---------------------------------------------------------
# Weak phrases and stronger alternatives
# ---------------------------------------------------------

WEAK_TO_STRONG_PHRASES = {
    "responsible for": "managed",
    "worked on": "developed",
    "helped with": "contributed to",
    "participated in": "contributed to",
    "involved in": "implemented",
}


# ---------------------------------------------------------
# Strong resume action verbs
# ---------------------------------------------------------

ACTION_VERBS = [
    "Developed",
    "Built",
    "Implemented",
    "Designed",
    "Optimized",
    "Automated",
    "Improved",
    "Created",
    "Engineered",
    "Delivered",
    "Established",
    "Configured",
    "Containerized",
    "Maintained",
    "Integrated",
]


# ---------------------------------------------------------
# Text helpers
# ---------------------------------------------------------

def _clean_text(text: str) -> str:
    """
    Normalize unnecessary whitespace without changing
    the meaning of the original resume text.
    """

    return re.sub(
        r"\s+",
        " ",
        (text or "")
    ).strip()


def _contains_metric(text: str) -> bool:
    """
    Detect whether a resume statement contains
    measurable evidence.
    """

    metric_patterns = [
        r"\d+%",
        r"\d+\+",
        r"\b\d[\d,]*\s*(?:users|customers|requests|records|projects|apis|events|developers)\b",
        r"\b\d[\d,]*\s*(?:ms|milliseconds|seconds|minutes|hours|days)\b",
        r"\b\d[\d,]*\s+requests\s+per\s+second\b",
        r"\$\s*\d[\d,]*",
    ]

    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )
        for pattern in metric_patterns
    )


def _replace_weak_phrases(
    text: str
) -> tuple[str, list[str]]:
    """
    Replace common weak resume phrases with stronger wording.
    """

    rewritten = text
    replacements = []

    for weak_phrase, strong_phrase in WEAK_TO_STRONG_PHRASES.items():

        pattern = re.compile(
            re.escape(weak_phrase),
            flags=re.IGNORECASE
        )

        if pattern.search(rewritten):

            rewritten = pattern.sub(
                strong_phrase,
                rewritten
            )

            replacements.append(
                f"Replaced '{weak_phrase}' with "
                f"'{strong_phrase}'."
            )

    return rewritten, replacements


# ---------------------------------------------------------
# PDF line reconstruction
# ---------------------------------------------------------

def _reconstruct_lines(
    section_text: str
) -> list[str]:
    """
    Reconstruct sentences that were split across multiple
    lines during PDF text extraction.

    Example:

    Designed and developed 12+ microservices...
    throughput by 35%.

    becomes one complete statement before analysis.
    """

    raw_lines = [
        line.strip(" •-\t")
        for line in section_text.splitlines()
        if line.strip()
    ]

    if not raw_lines:
        return []

    lines = []
    current_line = ""

    for line in raw_lines:

        if not current_line:
            current_line = line
            continue

        # If the current text does not end like a complete
        # sentence, assume the PDF wrapped the same statement
        # onto another line.
        if not re.search(
            r"[.!?]$",
            current_line
        ):
            current_line += " " + line

        else:
            lines.append(
                _clean_text(current_line)
            )

            current_line = line

    if current_line:
        lines.append(
            _clean_text(current_line)
        )

    return lines


# ---------------------------------------------------------
# Individual statement analysis
# ---------------------------------------------------------

def _analyse_bullet(
    bullet: str
) -> dict[str, Any]:

    original = _clean_text(
        bullet
    )

    rewritten, replacements = _replace_weak_phrases(
        original
    )

    has_metric = _contains_metric(
        rewritten
    )

    suggestions = []

    if not has_metric:
        suggestions.append(
            "Add a measurable result where truthful, such as "
            "performance improvement, users served, time saved, "
            "accuracy, scale, or percentage change."
        )

    words = rewritten.split()

    first_word = (
        words[0].lower()
        if words
        else ""
    )

    known_action_verbs = {
        verb.lower()
        for verb in ACTION_VERBS
    }

    if (
        first_word
        and first_word not in known_action_verbs
    ):
        suggestions.append(
            "Consider starting this bullet with a stronger "
            "achievement-oriented action verb."
        )

    return {
        "original": original,
        "suggested_rewrite": rewritten,
        "has_metric": has_metric,
        "changes": replacements,
        "suggestions": suggestions,
    }


# ---------------------------------------------------------
# Main Resume Rewrite Service
# ---------------------------------------------------------

def generate_resume_rewrite_suggestions(
    analysis: dict[str, Any]
) -> dict[str, Any]:
    """
    Generate safe resume rewrite suggestions using the
    already-parsed resume analysis.

    The service does NOT invent:
    - achievements
    - percentages
    - employers
    - technologies
    - experience
    - project results

    Missing metrics are suggested rather than fabricated.
    """

    sections = analysis.get(
        "sections",
        {}
    ) or {}

    section_results = {}

    target_sections = [
        "experience",
        "projects",
        "achievements",
    ]

    total_lines = 0
    lines_needing_metrics = 0
    lines_with_metrics = 0
    lines_with_rewrites = 0

    # -----------------------------------------------------
    # Analyse each supported resume section
    # -----------------------------------------------------

    for section_name in target_sections:

        section_text = sections.get(
            section_name,
            ""
        )

        if not section_text:
            continue

        # Reconstruct PDF-wrapped statements before
        # analysing them.
        lines = _reconstruct_lines(
            section_text
        )

        analysed_lines = []

        for line in lines:

            result = _analyse_bullet(
                line
            )

            analysed_lines.append(
                result
            )

            total_lines += 1

            if result["has_metric"]:
                lines_with_metrics += 1
            else:
                lines_needing_metrics += 1

            if result["changes"]:
                lines_with_rewrites += 1

        section_results[
            section_name
        ] = analysed_lines

    # -----------------------------------------------------
    # General recommendations
    # -----------------------------------------------------

    general_recommendations = []

    if lines_needing_metrics:

        general_recommendations.append(
            f"{lines_needing_metrics} resume lines could "
            "potentially be strengthened with truthful "
            "measurable evidence."
        )

    if lines_with_rewrites:

        general_recommendations.append(
            f"{lines_with_rewrites} resume lines contain "
            "wording that can be made more achievement-oriented."
        )

    if not section_results:

        general_recommendations.append(
            "No experience, project, or achievement content "
            "was available for rewrite analysis."
        )

    # -----------------------------------------------------
    # Return rewrite report
    # -----------------------------------------------------

    return {
        "sections": section_results,

        "statistics": {
            "total_lines_analyzed": total_lines,
            "lines_with_metrics": lines_with_metrics,
            "lines_needing_metrics": lines_needing_metrics,
            "lines_with_rewrites": lines_with_rewrites,
        },

        "general_recommendations": (
            general_recommendations
        ),

        "note": (
            "Rewrite suggestions preserve the supplied "
            "information. Metrics and achievements should "
            "only be added when they are factually accurate."
        ),
    }