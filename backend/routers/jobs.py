import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from database import get_db_connection
from routers.auth import get_current_user
from services.skill_gap_analyzer import analyse_skill_gap
from services.job_matcher import calculate_job_match
from services.job_recommender import recommend_jobs
from services.career_advisor import generate_career_advice
from services.jd_analyzer import analyze_job_description

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


class JobSkillInput(BaseModel):
    skill_name: str = Field(min_length=1, max_length=100)
    importance: str = "MEDIUM"


class JobCreateRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=200)
    company_name: Optional[str] = Field(default=None, max_length=200)
    job_description: str = Field(min_length=1)
    experience_required: Optional[str] = Field(
        default=None,
        max_length=100
    )
    location: Optional[str] = Field(
        default=None,
        max_length=150
    )
    skills: list[JobSkillInput] = []


# =========================================================
# CREATE JOB
# =========================================================

@router.post("", status_code=status.HTTP_201_CREATED)
def create_job(
    job_data: JobCreateRequest,
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
            INSERT INTO job_descriptions (
                user_id,
                job_title,
                company_name,
                job_description,
                experience_required,
                location
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                current_user["user_id"],
                job_data.job_title.strip(),
                job_data.company_name.strip()
                if job_data.company_name else None,
                job_data.job_description.strip(),
                job_data.experience_required.strip()
                if job_data.experience_required else None,
                job_data.location.strip()
                if job_data.location else None,
            )
        )

        job_id = cursor.lastrowid
        saved_skills = []

        allowed_importance = {
            "LOW",
            "MEDIUM",
            "HIGH",
            "REQUIRED"
        }

        for skill_data in job_data.skills:

            skill_name = skill_data.skill_name.strip().lower()
            importance = skill_data.importance.strip().upper()

            if not skill_name:
                continue

            if importance not in allowed_importance:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Invalid importance '{importance}' for "
                        f"skill '{skill_name}'. "
                        "Use LOW, MEDIUM, HIGH, or REQUIRED."
                    )
                )

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
                        "General"
                    )
                )

                skill_id = cursor.lastrowid
                stored_skill_name = skill_name

            cursor.execute(
                """
                SELECT job_skill_id
                FROM job_skills
                WHERE job_id = %s
                  AND skill_id = %s
                LIMIT 1
                """,
                (
                    job_id,
                    skill_id
                )
            )

            existing_job_skill = cursor.fetchone()

            if existing_job_skill is None:

                cursor.execute(
                    """
                    INSERT INTO job_skills (
                        job_id,
                        skill_id,
                        importance
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (
                        job_id,
                        skill_id,
                        importance
                    )
                )

                saved_skills.append(
                    {
                        "skill_id": skill_id,
                        "skill_name": stored_skill_name,
                        "importance": importance
                    }
                )

        connection.commit()

        return {
            "message": "Job description created successfully",
            "job": {
                "job_id": job_id,
                "job_title": job_data.job_title,
                "company_name": job_data.company_name,
                "job_description": job_data.job_description,
                "experience_required": job_data.experience_required,
                "location": job_data.location,
                "skills": saved_skills
            }
        }

    except HTTPException:
        connection.rollback()
        raise

    except Exception as error:

        connection.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job description: {error}"
        )

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# =========================================================
# MATCH RESUME WITH JOB
# =========================================================

# =========================================================
# RECOMMEND JOBS FOR A RESUME
# =========================================================

@router.get("/recommendations/{resume_id}")
def get_job_recommendations(
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

        # -----------------------------------------------------
        # 1. Verify that the resume belongs to the current user
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT
                resume_id,
                original_filename
            FROM resumes
            WHERE resume_id = %s
              AND user_id = %s
            LIMIT 1
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

        # -----------------------------------------------------
        # 2. Get resume skills
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT
                s.skill_id,
                s.skill_name,
                rs.proficiency_score,
                rs.occurrence_count
            FROM resume_skills rs
            JOIN skills s
                ON rs.skill_id = s.skill_id
            WHERE rs.resume_id = %s
            ORDER BY s.skill_name
            """,
            (resume_id,)
        )

        resume_skill_rows = cursor.fetchall()

        if not resume_skill_rows:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "No analysed skills were found for this resume. "
                    "Analyse the resume before requesting recommendations."
                )
            )

        # -----------------------------------------------------
        # 3. Get all jobs belonging to the current user
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT
                job_id,
                job_title,
                company_name,
                experience_required,
                location
            FROM job_descriptions
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (current_user["user_id"],)
        )

        job_rows = cursor.fetchall()

        if not job_rows:
            return {
                "message": "No jobs are available for recommendation",
                "resume": {
                    "resume_id": resume["resume_id"],
                    "original_filename": resume["original_filename"]
                },
                "total_jobs": 0,
                "recommendations": []
            }

        # -----------------------------------------------------
        # 4. Get skills for every job
        # -----------------------------------------------------

        jobs = []

        for job in job_rows:

            cursor.execute(
                """
                SELECT
                    s.skill_id,
                    s.skill_name,
                    js.importance
                FROM job_skills js
                JOIN skills s
                    ON js.skill_id = s.skill_id
                WHERE js.job_id = %s
                ORDER BY s.skill_name
                """,
                (job["job_id"],)
            )

            job_skill_rows = cursor.fetchall()

            jobs.append(
                {
                    "job_id": job["job_id"],
                    "job_title": job["job_title"],
                    "company_name": job["company_name"],
                    "experience_required": job[
                        "experience_required"
                    ],
                    "location": job["location"],
                    "skills": job_skill_rows
                }
            )

        # -----------------------------------------------------
        # 5. Rank jobs using the recommendation engine
        # -----------------------------------------------------

        recommendations = recommend_jobs(
            resume_skills=resume_skill_rows,
            jobs=jobs
        )

        # -----------------------------------------------------
        # 6. Return ranked recommendations
        # -----------------------------------------------------

        return {
            "message": "Job recommendations generated successfully",
            "resume": {
                "resume_id": resume["resume_id"],
                "original_filename": resume["original_filename"]
            },
            "total_jobs": len(recommendations),
            "recommendations": recommendations
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate job recommendations: {error}"
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

@router.post(
    "/{job_id}/match/{resume_id}",
    status_code=status.HTTP_200_OK
)
def match_resume_with_job(
    job_id: int,
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

        # -----------------------------------------------------
        # 1. Verify resume
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT
                resume_id,
                original_filename
            FROM resumes
            WHERE resume_id = %s
              AND user_id = %s
            LIMIT 1
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

        # -----------------------------------------------------
        # 2. Verify job
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT
                job_id,
                job_title,
                company_name,
                job_description,
                experience_required,
                location
            FROM job_descriptions
            WHERE job_id = %s
              AND user_id = %s
            LIMIT 1
            """,
            (
                job_id,
                current_user["user_id"]
            )
        )

        job = cursor.fetchone()

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )

        # -----------------------------------------------------
        # 3. Get resume skills
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT
                s.skill_id,
                s.skill_name,
                rs.proficiency_score,
                rs.occurrence_count
            FROM resume_skills rs
            JOIN skills s
                ON rs.skill_id = s.skill_id
            WHERE rs.resume_id = %s
            ORDER BY s.skill_name
            """,
            (resume_id,)
        )

        resume_skill_rows = cursor.fetchall()

        resume_skills = [
            row["skill_name"]
            for row in resume_skill_rows
        ]

        # -----------------------------------------------------
        # 4. Get required job skills
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT
                s.skill_id,
                s.skill_name,
                js.importance
            FROM job_skills js
            JOIN skills s
                ON js.skill_id = s.skill_id
            WHERE js.job_id = %s
            ORDER BY s.skill_name
            """,
            (job_id,)
        )

        job_skill_rows = cursor.fetchall()

        if not job_skill_rows:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="This job does not have any configured skills"
            )

        # -----------------------------------------------------
        # 5. Calculate match
        # -----------------------------------------------------

        match_result = calculate_job_match(
            resume_skills=resume_skills,
            job_skills=job_skill_rows
        )
        # -----------------------------------------------------
        # 5A. Perform detailed skill-gap analysis
        # -----------------------------------------------------

        skill_gap_result = analyse_skill_gap(
        resume_skills=resume_skill_rows,
        job_skills=job_skill_rows
        )

        # -----------------------------------------------------
        # 5B. Generate career improvement advice
        # -----------------------------------------------------

        career_advice = generate_career_advice(
        skill_gap=skill_gap_result
        )
        # -----------------------------------------------------
        # 5C. Analyse resume against the job description
        # -----------------------------------------------------

        jd_analysis = analyze_job_description(
        resume_skills=resume_skills,
        job_description=job["job_description"]
        )

        matched_skills_json = json.dumps(
            match_result["matched_skills"],
            ensure_ascii=False
        )

        missing_skills_json = json.dumps(
            match_result["missing_skills"],
            ensure_ascii=False
        )

        recommendations_json = json.dumps(
            match_result["recommendations"],
            ensure_ascii=False
        )

        # -----------------------------------------------------
        # 6. Check existing match
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT match_id
            FROM job_matches
            WHERE resume_id = %s
              AND job_id = %s
            LIMIT 1
            """,
            (
                resume_id,
                job_id
            )
        )

        existing_match = cursor.fetchone()

        # -----------------------------------------------------
        # 7. Update or create match
        # -----------------------------------------------------

        if existing_match:

            cursor.execute(
                """
                UPDATE job_matches
                SET
                    match_score = %s,
                    matched_skills = %s,
                    missing_skills = %s,
                    recommendations = %s
                WHERE match_id = %s
                """,
                (
                    match_result["match_score"],
                    matched_skills_json,
                    missing_skills_json,
                    recommendations_json,
                    existing_match["match_id"]
                )
            )

            match_id = existing_match["match_id"]
            database_action = "updated"

        else:

            cursor.execute(
                """
                INSERT INTO job_matches (
                    resume_id,
                    job_id,
                    match_score,
                    matched_skills,
                    missing_skills,
                    recommendations
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    resume_id,
                    job_id,
                    match_result["match_score"],
                    matched_skills_json,
                    missing_skills_json,
                    recommendations_json
                )
            )

            match_id = cursor.lastrowid
            database_action = "created"

        connection.commit()

        # -----------------------------------------------------
        # 8. Return result
        # -----------------------------------------------------

        return {
            "message": "Resume matched with job successfully",
            "database_action": database_action,
            "match_id": match_id,
            "resume": {
                "resume_id": resume["resume_id"],
                "original_filename": resume["original_filename"]
            },
            "job": {
                "job_id": job["job_id"],
                "job_title": job["job_title"],
                "company_name": job["company_name"],
                "experience_required": job["experience_required"],
                "location": job["location"]
            },
            "resume_skills": resume_skill_rows,
            "job_skills": job_skill_rows,
            "match": match_result,
            "skill_gap": skill_gap_result,
            "career_advice": career_advice,
            "jd_analysis": jd_analysis
        }

    except HTTPException:

        connection.rollback()
        raise

    except Exception as error:

        connection.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match resume with job: {error}"
        )

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()