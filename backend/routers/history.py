import json

from fastapi import APIRouter, Depends, HTTPException, status

from database import get_db_connection
from routers.auth import get_current_user


router = APIRouter(
    prefix="/history",
    tags=["History"]
)


# =========================================================
# 1. Resume Analysis History
# =========================================================

@router.get("/analyses")
def get_analysis_history(
    current_user: dict = Depends(get_current_user)
):
    connection = get_db_connection()

    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                ra.analysis_id,
                ra.resume_id,
                r.original_filename,
                ra.overall_score,
                ra.ats_score,
                ra.skills_score,
                ra.education_score,
                ra.experience_score,
                ra.project_score,
                ra.analysis_summary
            FROM resume_analyses ra
            JOIN resumes r
                ON ra.resume_id = r.resume_id
            WHERE r.user_id = %s
            ORDER BY ra.analysis_id DESC
            """,
            (current_user["user_id"],)
        )

        rows = cursor.fetchall()

        return {
            "total_analyses": len(rows),
            "analyses": rows
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analysis history: {exc}"
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# =========================================================
# 2. Job Match History
# =========================================================

@router.get("/job-matches")
def get_job_match_history(
    current_user: dict = Depends(get_current_user)
):
    connection = get_db_connection()

    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                jm.match_id,
                jm.resume_id,
                jm.job_id,
                r.original_filename,
                jd.job_title,
                jd.company_name,
                jd.location,
                jd.experience_required,
                jm.match_score,
                jm.matched_skills,
                jm.missing_skills,
                jm.recommendations
            FROM job_matches jm
            JOIN resumes r
                ON jm.resume_id = r.resume_id
            JOIN job_descriptions jd
                ON jm.job_id = jd.job_id
            WHERE r.user_id = %s
              AND jd.user_id = %s
            ORDER BY jm.match_id DESC
            """,
            (
                current_user["user_id"],
                current_user["user_id"]
            )
        )

        rows = cursor.fetchall()

        # -------------------------------------------------
        # Convert stored JSON strings into Python lists
        # -------------------------------------------------

        for row in rows:
            for field in (
                "matched_skills",
                "missing_skills",
                "recommendations"
            ):
                value = row.get(field)

                if isinstance(value, str):
                    try:
                        row[field] = json.loads(value)

                    except json.JSONDecodeError:
                        row[field] = []

                elif value is None:
                    row[field] = []

        return {
            "total_matches": len(rows),
            "matches": rows
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job match history: {exc}"
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()