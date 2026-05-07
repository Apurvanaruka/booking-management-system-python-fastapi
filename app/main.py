from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
import uvicorn
from app.api.routes import (
    patient_router, doctor_router, appointment_router,
    auth_router, hospital_router, department_router,
    admin_router, booking_router,
)
from app.core.config import settings
from app.db.session import get_db
from app.api.deps import get_current_user, get_current_admin
from sqlalchemy import text

app = FastAPI(
    title="Healthcare Appointment System",
    description="API for managing Hospital Appointments — India",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Public routes (no auth required) ────────────────────────
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])

# ─── Protected routes ────────────────────────────────────────
app.include_router(
    hospital_router,
    prefix="/api/hospitals",
    tags=["Hospitals"],
    dependencies=[Depends(get_current_user)],
)

app.include_router(
    department_router,
    prefix="/api/departments",
    tags=["Departments"],
    dependencies=[Depends(get_current_user)],
)

app.include_router(
    patient_router,
    prefix="/api/patients",
    tags=["Patients"],
    dependencies=[Depends(get_current_user)],
)

app.include_router(
    doctor_router,
    prefix="/api/doctors",
    tags=["Doctors"],
    dependencies=[Depends(get_current_user)],
)

app.include_router(
    appointment_router,
    prefix="/api/appointments",
    tags=["Appointments"],
    dependencies=[Depends(get_current_user)],
)

app.include_router(
    admin_router,
    prefix="/api/admin",
    tags=["Admin Panel"],
    dependencies=[Depends(get_current_admin)],
)

app.include_router(
    booking_router,
    prefix="/api/booking",
    tags=["Patient Booking"],
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token with 'Bearer ' prefix"
        }
    }

    # Paths that don't need auth in Swagger
    public_paths = [
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/register-hospital",
        "/api/auth/send-otp",
        "/api/auth/verify-otp",
    ]

    for path, path_item in openapi_schema["paths"].items():
        if path in public_paths:
            continue

        for method in path_item.values():
            method.setdefault("security", [{"bearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Healthcare Appointment System API. Visit /docs for documentation."}

@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
