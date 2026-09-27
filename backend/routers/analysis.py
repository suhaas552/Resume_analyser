from fastapi import APIRouter, Depends, HTTPException, status

from database import get_db_connection
from routers.auth import get_current_user
from services.resume_analyser import analyse_resume


router = APIRouter(
    prefix="/analysis",
    tags=["Resume Analysis"]
)


@router.post("/{resume_id}")
def analyse_uploaded_resume(
    resume_id: int,
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

        # Find the resume and ensure it belongs to
        # the currently authenticated user.
        cursor.execute(
            """
            SELECT
                resume_id,
                user_id,
                original_filename,
                extracted_text,
                upload_status
            FROM resumes
            WHERE resume_id = %s
              AND user_id = %s
            """,
            (
                resume_id,
                current_user["user_id"]
            )
        )

        resume = cursor.fetchone()

        if resume is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )

        if resume["upload_status"] != "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume processing is not completed"
            )

        if not resume["extracted_text"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No extracted resume text is available"
            )

        # Run our resume analysis engine.
        analysis = analyse_resume(
            resume["extracted_text"]
        )

        return {
            "message": "Resume analysed successfully",
            "resume": {
                "resume_id": resume["resume_id"],
                "original_filename": resume["original_filename"]
            },
            "analysis": analysis
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume analysis failed: {error}"
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection.is_connected():
            connection.close()