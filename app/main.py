from fastapi import FastAPI

from app.config import get_settings
from app.database import init_db
from app.routers import auth, billing, clinical, operations, residents, users

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

if settings.auto_create_schema:
    init_db()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(residents.router)
app.include_router(clinical.router)
app.include_router(billing.router)
app.include_router(operations.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": settings.app_name, "docs": "/docs"}
