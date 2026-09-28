from typing import Any


SKILL_LEARNING_GUIDE = {
    "python": {
        "focus": [
            "Core Python",
            "Object-oriented programming",
            "File handling",
            "APIs and automation",
        ],
        "project": "Build a Python application that processes and analyses real-world data.",
    },
    "pandas": {
        "focus": [
            "DataFrames and Series",
            "Data cleaning",
            "Filtering and aggregation",
            "Missing-value handling",
            "GroupBy and merging datasets",
        ],
        "project": "Build an exploratory data analysis project using a real-world dataset.",
    },
    "numpy": {
        "focus": [
            "Arrays",
            "Vectorized operations",
            "Indexing and slicing",
            "Mathematical operations",
        ],
        "project": "Build a numerical data-analysis project using NumPy.",
    },
    "machine learning": {
        "focus": [
            "Data preprocessing",
            "Regression",
            "Classification",
            "Model evaluation",
            "Feature engineering",
        ],
        "project": "Build and evaluate a machine-learning prediction model.",
    },
    "sql": {
        "focus": [
            "Joins",
            "Subqueries",
            "Aggregations",
            "Window functions",
            "Database design",
        ],
        "project": "Build a database-backed analytics project using SQL.",
    },
    "fastapi": {
        "focus": [
            "REST APIs",
            "Request validation",
            "Authentication",
            "Database integration",
            "API documentation",
        ],
        "project": "Build and deploy a REST API using FastAPI.",
    },
    "django": {
        "focus": [
            "Models",
            "Views",
            "Templates",
            "Authentication",
            "REST APIs",
        ],
        "project": "Build a complete web application using Django.",
    },
    "react": {
        "focus": [
            "Components",
            "Props and state",
            "Hooks",
            "API integration",
            "Routing",
        ],
        "project": "Build a responsive frontend application using React.",
    },
    "javascript": {
        "focus": [
            "ES6+",
            "DOM manipulation",
            "Async programming",
            "Promises",
            "REST API integration",
        ],
        "project": "Build an interactive JavaScript web application.",
    },
    "docker": {
        "focus": [
            "Images",
            "Containers",
            "Dockerfiles",
            "Volumes",
            "Docker Compose",
        ],
        "project": "Containerize and run one of your existing applications using Docker.",
    },
    "git": {
        "focus": [
            "Commits",
            "Branches",
            "Merge workflows",
            "Pull requests",
            "Repository management",
        ],
        "project": "Maintain a professional GitHub repository using branches and pull requests.",
    },
}


def _normalise_skill_name(value: Any) -> str:
    return str(value or "").strip().lower()


def _priority_from_importance(importance: str) -> str:
    importance = str(importance or "").upper()

    if importance == "REQUIRED":
        return "CRITICAL"

    if importance == "HIGH":
        return "HIGH"

    return "MEDIUM"


def generate_career_advice(skill_gap: dict) -> dict:
    """
    Convert the skill-gap result into actionable career-development advice.

    This function does not modify the existing matching algorithm.
    It only uses its output.
    """

    missing_skills = skill_gap.get("missing_skills", []) or []
    matched_skills = skill_gap.get("matched_skills", []) or []

    improvement_plan = []

    for skill in missing_skills:
        skill_name = _normalise_skill_name(skill.get("skill_name"))
        importance = str(skill.get("importance", "MEDIUM")).upper()

        guide = SKILL_LEARNING_GUIDE.get(
            skill_name,
            {
                "focus": [
                    f"Learn the fundamentals of {skill_name}",
                    f"Practice {skill_name} through hands-on exercises",
                    f"Apply {skill_name} in a practical project",
                ],
                "project": (
                    f"Build a small practical project demonstrating {skill_name}."
                ),
            },
        )

        improvement_plan.append(
            {
                "skill_name": skill_name,
                "importance": importance,
                "priority": _priority_from_importance(importance),
                "why_improve": (
                    f"{skill_name} is currently missing from the resume "
                    f"and is marked {importance} for this job."
                ),
                "learning_focus": guide["focus"],
                "suggested_project": guide["project"],
            }
        )

    priority_order = {
        "CRITICAL": 1,
        "HIGH": 2,
        "MEDIUM": 3,
    }

    improvement_plan.sort(
        key=lambda item: priority_order.get(item["priority"], 4)
    )

    strengths = [
        {
            "skill_name": skill.get("skill_name"),
            "importance": skill.get("importance"),
            "proficiency_score": skill.get("proficiency_score"),
        }
        for skill in matched_skills
    ]

    if not improvement_plan:
        overall_advice = (
            "Your detected resume skills cover all configured skills for this job. "
            "Focus on demonstrating these skills through measurable projects, "
            "experience, and achievements."
        )
    else:
        critical_count = sum(
            1 for item in improvement_plan if item["priority"] == "CRITICAL"
        )

        if critical_count:
            overall_advice = (
                f"Prioritize the {critical_count} critical missing skill(s) first, "
                "then strengthen high-priority skills through practical projects."
            )
        else:
            overall_advice = (
                "Strengthen the missing skills in priority order and demonstrate "
                "them through practical projects."
            )

    return {
        "overall_advice": overall_advice,
        "strengths": strengths,
        "skills_to_improve": improvement_plan,
        "total_skills_to_improve": len(improvement_plan),
    }