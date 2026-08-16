from __future__ import annotations

from typing import Any, Generator

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.database.models import Business
from app.ingestion.service import IngestionService
from app.ingestion.validator import validate_zip_package

app = FastAPI(title="Blueprint BI API")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/v1/whatsapp/imports")
async def upload_whatsapp_import(
    business_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if file.filename is None or not file.filename.strip():
        raise HTTPException(status_code=400, detail={"errors": ["A WhatsApp ZIP file is required."]})

    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail={"errors": ["Only ZIP archive uploads are supported for WhatsApp imports."]},
        )

    payload = await file.read()
    validation = validate_zip_package(payload)
    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"errors": validation.errors, "warnings": validation.warnings},
        )

    business = db.get(Business, business_id)
    if business is None:
        raise HTTPException(
            status_code=404,
            detail={"errors": [f"Business {business_id} was not found."]},
        )

    result = IngestionService(db.bind).import_package(
        business_id=business_id,
        file_bytes=payload,
        import_name=file.filename,
    )

    response = {
        "import_batch_id": result.import_batch_id,
        "status": result.status,
        "is_successful": result.is_successful,
        "errors": result.errors,
        "warnings": result.warnings,
    }

    if result.status == "failed":
        raise HTTPException(status_code=400, detail=response)

    return response
