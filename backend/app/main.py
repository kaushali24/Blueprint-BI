from __future__ import annotations

from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import OperationalError

from app.database.connection import engine, session_scope
from app.database.models import Business
from app.coordinator import ImportCoordinator
from app.ingestion.validator import validate_zip_package

app = FastAPI(title="Blueprint BI API")


@app.post("/api/v1/whatsapp/imports")
async def upload_whatsapp_import(
    business_id: int = Form(...),
    file: UploadFile = File(...),
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

    try:
        with session_scope() as session:
            business = session.get(Business, business_id)
            if business is None:
                raise HTTPException(
                    status_code=404,
                    detail={"errors": [f"Business {business_id} was not found."]},
                )

        result = ImportCoordinator(engine).process_import(
            business_id=business_id,
            file_bytes=payload,
            import_name=file.filename,
        )
    except OperationalError as exc:
        if "database is locked" in str(exc).lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "errors": [
                        "The database is locked by another application. "
                        "Close DB Browser or other SQLite tools, stop duplicate backend processes, "
                        "then retry the import."
                    ]
                },
            ) from exc
        raise

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
