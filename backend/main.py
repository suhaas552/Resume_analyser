from fastapi import FastAPI

from database import get_db_connection
from routers.auth import router as auth_router
from routers.resumes import router as resumes_router


app = FastAPI(
    title="Resume Analyser API",
    description="Backend API for analysing resumes, skills, education, experience, and career opportunities.",
    version="1.0.0"
)


app.include_router(auth_router)
app.include_router(resumes_router)


@app.get("/")
def root():
    return {
        "message": "Resume Analyser API is running",
        "status": "success"
    }


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
        cursor.execute("SELECT DATABASE(), VERSION();")

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