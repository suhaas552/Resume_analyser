from fastapi import APIRouter, Depends, HTTPException, status

from database import get_db_connection
from routers.auth import get_current_user


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/summary")
def get_dashboard_summary(
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

        user_id = current_user["user_id"]

        # -------------------------------------------------
        # 1. Total resumes
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS total_resumes
            FROM resumes
            WHERE user_id = %s
            """,
            (user_id,)
        )

        total_resumes = cursor.fetchone()["total_resumes"]

        # -------------------------------------------------
        # 2. Total analyses
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS total_analyses
            FROM resume_analyses ra
            JOIN resumes r
                ON ra.resume_id = r.resume_id
            WHERE r.user_id = %s
            """,
            (user_id,)
        )

        total_analyses = cursor.fetchone()["total_analyses"]

        # -------------------------------------------------
        # 3. Total jobs
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS total_jobs
            FROM job_descriptions
            WHERE user_id = %s
            """,
            (user_id,)
        )

        total_jobs = cursor.fetchone()["total_jobs"]

        # -------------------------------------------------
        # 4. Total job matches
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS total_matches
            FROM job_matches jm
            JOIN resumes r
                ON jm.resume_id = r.resume_id
            JOIN job_descriptions jd
                ON jm.job_id = jd.job_id
            WHERE r.user_id = %s
              AND jd.user_id = %s
            """,
            (user_id, user_id)
        )

        total_matches = cursor.fetchone()["total_matches"]

        # -------------------------------------------------
        # 5. Average ATS score
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT AVG(ra.ats_score) AS average_ats_score
            FROM resume_analyses ra
            JOIN resumes r
                ON ra.resume_id = r.resume_id
            WHERE r.user_id = %s
            """,
            (user_id,)
        )

        average_ats_row = cursor.fetchone()

        average_ats_score = (
            round(float(average_ats_row["average_ats_score"]), 2)
            if average_ats_row["average_ats_score"] is not None
            else 0.0
        )

        # -------------------------------------------------
        # 6. Average job-match score
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT AVG(jm.match_score) AS average_match_score
            FROM job_matches jm
            JOIN resumes r
                ON jm.resume_id = r.resume_id
            JOIN job_descriptions jd
                ON jm.job_id = jd.job_id
            WHERE r.user_id = %s
              AND jd.user_id = %s
            """,
            (user_id, user_id)
        )

        average_match_row = cursor.fetchone()

        average_match_score = (
            round(float(average_match_row["average_match_score"]), 2)
            if average_match_row["average_match_score"] is not None
            else 0.0
        )

        # -------------------------------------------------
        # 7. Best job match
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                jm.match_id,
                jm.resume_id,
                jm.job_id,
                r.original_filename,
                jd.job_title,
                jd.company_name,
                jm.match_score
            FROM job_matches jm
            JOIN resumes r
                ON jm.resume_id = r.resume_id
            JOIN job_descriptions jd
                ON jm.job_id = jd.job_id
            WHERE r.user_id = %s
              AND jd.user_id = %s
            ORDER BY jm.match_score DESC, jm.match_id DESC
            LIMIT 1
            """,
            (user_id, user_id)
        )

        best_job_match = cursor.fetchone()

        # -------------------------------------------------
        # 8. Recent analyses
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                ra.analysis_id,
                ra.resume_id,
                r.original_filename,
                ra.overall_score,
                ra.ats_score
            FROM resume_analyses ra
            JOIN resumes r
                ON ra.resume_id = r.resume_id
            WHERE r.user_id = %s
            ORDER BY ra.analysis_id DESC
            LIMIT 5
            """,
            (user_id,)
        )

        recent_analyses = cursor.fetchall()

        # -------------------------------------------------
        # Final dashboard response
        # -------------------------------------------------

        return {
            "statistics": {
                "total_resumes": total_resumes,
                "total_analyses": total_analyses,
                "total_jobs": total_jobs,
                "total_matches": total_matches,
                "average_ats_score": average_ats_score,
                "average_match_score": average_match_score
            },
            "best_job_match": best_job_match,
            "recent_analyses": recent_analyses
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard summary: {exc}"
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()