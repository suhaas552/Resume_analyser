import json

from fastapi import APIRouter, Depends, HTTPException, status

from database import get_db_connection
from routers.auth import get_current_user
from services.resume_analyser import analyse_resume
from services.resume_optimizer import optimize_resume
from services.resume_rewriter import generate_resume_rewrite_suggestions

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

        # ---------------------------------------------------------
        # 1. Find resume and verify ownership
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # 2. Analyse resume
        # ---------------------------------------------------------
        analysis = analyse_resume(
            resume["extracted_text"]
        )

        # ---------------------------------------------------------
        # Generate resume optimization report
        # ---------------------------------------------------------

        optimization = optimize_resume(
        resume_text=resume["extracted_text"],
        analysis=analysis
        )

        # ---------------------------------------------------------
        # Generate resume rewrite suggestions
        # ---------------------------------------------------------

        rewrite_suggestions = generate_resume_rewrite_suggestions(
        analysis=analysis
        )

        scores = analysis["scores"]

        strengths_json = json.dumps(
            analysis["strengths"],
            ensure_ascii=False
        )

        weaknesses_json = json.dumps(
            analysis["weaknesses"],
            ensure_ascii=False
        )

        suggestions_json = json.dumps(
            analysis["suggestions"],
            ensure_ascii=False
        )

        # ---------------------------------------------------------
        # 3. Check whether analysis already exists
        # ---------------------------------------------------------
        cursor.execute(
            """
            SELECT analysis_id
            FROM resume_analyses
            WHERE resume_id = %s
            """,
            (resume_id,)
        )

        existing_analysis = cursor.fetchone()

        # ---------------------------------------------------------
        # 4. Update existing analysis OR insert new analysis
        # ---------------------------------------------------------
        if existing_analysis:

            cursor.execute(
                """
                UPDATE resume_analyses
                SET
                    overall_score = %s,
                    ats_score = %s,
                    skills_score = %s,
                    education_score = %s,
                    experience_score = %s,
                    project_score = %s,
                    strengths = %s,
                    weaknesses = %s,
                    suggestions = %s,
                    analysis_summary = %s
                WHERE resume_id = %s
                """,
                (
                    scores["overall_score"],
                    scores["ats_score"],
                    scores["skills_score"],
                    scores["education_score"],
                    scores["experience_score"],
                    scores["project_score"],
                    strengths_json,
                    weaknesses_json,
                    suggestions_json,
                    analysis["analysis_summary"],
                    resume_id
                )
            )

            analysis_id = existing_analysis["analysis_id"]
            database_action = "updated"

        else:

            cursor.execute(
                """
                INSERT INTO resume_analyses (
                    resume_id,
                    overall_score,
                    ats_score,
                    skills_score,
                    education_score,
                    experience_score,
                    project_score,
                    strengths,
                    weaknesses,
                    suggestions,
                    analysis_summary
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                """,
                (
                    resume_id,
                    scores["overall_score"],
                    scores["ats_score"],
                    scores["skills_score"],
                    scores["education_score"],
                    scores["experience_score"],
                    scores["project_score"],
                    strengths_json,
                    weaknesses_json,
                    suggestions_json,
                    analysis["analysis_summary"]
                )
            )

            analysis_id = cursor.lastrowid
            database_action = "created"

        # ---------------------------------------------------------
        # 5. Synchronize detected resume skills
        # ---------------------------------------------------------

        # Remove old resume-skill relationships so re-analysis
        # always reflects the latest detected skills.
        cursor.execute(
            """
            DELETE FROM resume_skills
            WHERE resume_id = %s
            """,
            (resume_id,)
        )

        saved_resume_skills = []

        detected_skills = analysis.get("skills", [])

        for detected_skill in detected_skills:

            skill_name = detected_skill.strip().lower()

            if not skill_name:
                continue

            # Check whether the skill already exists globally.
            cursor.execute(
                """
                SELECT
                    skill_id,
                    skill_name
                FROM skills
                WHERE LOWER(skill_name) = %s
                LIMIT 1
                """,
                (skill_name,)
            )

            existing_skill = cursor.fetchone()

            if existing_skill:
                skill_id = existing_skill["skill_id"]
                stored_skill_name = existing_skill["skill_name"]

            else:
                # Create the skill if it doesn't already exist.
                cursor.execute(
                    """
                    INSERT INTO skills (
                        skill_name,
                        category
                    )
                    VALUES (%s, %s)
                    """,
                    (
                        skill_name,
                        "Resume Detected"
                    )
                )

                skill_id = cursor.lastrowid
                stored_skill_name = skill_name

            # Count how many times the skill appears in resume text.
            occurrence_count = (
                resume["extracted_text"]
                .lower()
                .count(skill_name)
            )

            if occurrence_count < 1:
                occurrence_count = 1

            # Basic proficiency score.
            #
            # We are not claiming this represents actual candidate
            # proficiency. It simply records detection confidence /
            # occurrence information for the current rule-based engine.
            proficiency_score = min(
                100,
                50 + ((occurrence_count - 1) * 10)
            )

            cursor.execute(
                """
                INSERT INTO resume_skills (
                    resume_id,
                    skill_id,
                    proficiency_score,
                    occurrence_count
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    resume_id,
                    skill_id,
                    proficiency_score,
                    occurrence_count
                )
            )

            saved_resume_skills.append(
                {
                    "skill_id": skill_id,
                    "skill_name": stored_skill_name,
                    "proficiency_score": proficiency_score,
                    "occurrence_count": occurrence_count
                }
            )

        # ---------------------------------------------------------
        # 6. Commit ALL changes together
        # ---------------------------------------------------------
        connection.commit()

        # ---------------------------------------------------------
        # 7. Return analysis
        # ---------------------------------------------------------
        return {
            "message": "Resume analysed successfully",
            "database_action": database_action,
            "analysis_id": analysis_id,
            "resume": {
                "resume_id": resume["resume_id"],
                "original_filename": resume["original_filename"]
            },
            "saved_resume_skills": saved_resume_skills,
            "analysis": analysis,
            "optimization": optimization,
            "rewrite_suggestions": rewrite_suggestions  
        }

    except HTTPException:

        if connection is not None:
            connection.rollback()

        raise

    except Exception as error:

        if connection is not None:
            connection.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume analysis failed: {error}"
        )

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()