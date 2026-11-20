from contextlib import asynccontextmanager

from fastapi import FastAPI

from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Облік часу відновлення сервісів",
    description="Web API для збереження та аналізу вимірювань часу відновлення сервісів (в хвилинах).",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(categories.router)
app.include_router(records.router)


@app.get("/ping", tags=["System"])
def ping():
    """Перевірка доступності сервісу."""
    return {"status": "ok"}


@app.get("/student", tags=["System"])
def get_student():
    """Відомості про студента."""
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }
