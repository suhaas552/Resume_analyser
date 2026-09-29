from fastapi import FastAPI

from database import get_db_connection
from routers.auth import router as auth_router
from routers.resumes import router as resumes_router
from routers.analysis import router as analysis_router
from routers.jobs import router as jobs_router
from routers.history import router as history_router
from routers.dashboard import router as dashboard_router

# ---------------------------------------------------------
# Create FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="Resume Analyser API",
    description=(
        "Backend API for analysing resumes, skills, education, "
        "experience, career opportunities, job matching, "
        "ATS scoring, resume optimization, and analysis history."
    ),
    version="1.0.0"
)


# ---------------------------------------------------------
# Register API routers
# ---------------------------------------------------------

app.include_router(auth_router)
app.include_router(resumes_router)
app.include_router(analysis_router)
app.include_router(jobs_router)
app.include_router(history_router)
app.include_router(dashboard_router)

# ---------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Resume Analyser API is running",
        "status": "success"
    }


# ---------------------------------------------------------
# Database health endpoint
# ---------------------------------------------------------

@app.get("/health/database")
def database_health():
    connection = get_db_connection()

    if connection is None:
        return {
            "status": "error",
            "database": "Not connected"
        }

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT DATABASE(), VERSION();"
        )

        database_name, mysql_version = cursor.fetchone()

        return {
            "status": "success",
            "database": database_name,
            "mysql_version": mysql_version
        }

    finally:
        if cursor is not None:
            cursor.close()

        if connection.is_connected():
            connection.close()