import asyncio
import io
import zipfile
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.database.connection import SessionLocal
from app.database.models import Business, Conversation, ImportBatch, Message, Participant, WhatsAppIdentity
from app.ingestion.service import IngestionService
from app.ingestion.validator import temporary_zip_workspace
from app.main import upload_whatsapp_import


def _make_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, future=True)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    return engine


def test_temporary_zip_workspace_extracts_and_removes_files():
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("chat.txt", "2024-01-02, 09:15 - Nethmi: Hi there\n")

    with temporary_zip_workspace(payload.getvalue()) as (temp_dir, warnings):
        assert Path(temp_dir, "chat.txt").exists()
        assert warnings == []

    assert not any(Path(temp_dir).exists() for temp_dir in [Path(temp_dir)])


def test_service_tracks_partial_import_success_and_failure():
    engine = _make_engine()
    SessionLocal.configure(bind=engine)

    with SessionLocal() as session:
        session.add(Business(name="Good Bakery", slug="good-bakery"))
        session.commit()
        business_id = session.query(Business).first().id

    service = IngestionService(engine)

    valid = io.BytesIO()
    with zipfile.ZipFile(valid, "w") as archive:
        archive.writestr("chat.txt", "2024-01-02, 09:15 - Nethmi: Hello\n")

    invalid = io.BytesIO()
    with zipfile.ZipFile(invalid, "w") as archive:
        archive.writestr("bad.txt", "not a valid message\n")

    batch_one = service.import_package(business_id, valid.getvalue(), import_name="valid")
    batch_two = service.import_package(business_id, invalid.getvalue(), import_name="invalid")

    with SessionLocal() as session:
        assert batch_one.is_successful is True
        assert batch_two.is_successful is False
        assert session.query(Message).count() == 1
        assert session.query(ImportBatch).count() >= 2


def test_identity_isolation_and_partial_transaction_are_safe():
    engine = _make_engine()
    SessionLocal.configure(bind=engine)

    with SessionLocal() as session:
        session.add(Business(name="Bakery B", slug="bakery-b"))
        session.commit()
        business_id = session.query(Business).first().id

    service = IngestionService(engine)
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("chat.txt", "2024-01-02, 09:15 - Alice: Hello\n2024-01-02, 09:16 - Alice: Hello\n")

    result = service.import_package(business_id, payload.getvalue(), import_name="chat-identity")
    assert result.is_successful is True

    with SessionLocal() as session:
        identities = session.execute(select(WhatsAppIdentity)).scalars().all()
        participants = session.execute(select(Participant)).scalars().all()
        assert len(identities) == 1
        assert len(participants) == 1
        assert session.query(Message).count() == 2


def test_repeated_import_reuses_existing_conversation_for_same_business():
    engine = _make_engine()
    SessionLocal.configure(bind=engine)

    with SessionLocal() as session:
        session.add(Business(name="Bakery C", slug="bakery-c"))
        session.commit()
        business_id = session.query(Business).first().id

    service = IngestionService(engine)

    first_export = io.BytesIO()
    with zipfile.ZipFile(first_export, "w") as archive:
        archive.writestr("chat.txt", "2024-01-02, 09:15 - Nethmi: Hello\n")

    second_export = io.BytesIO()
    with zipfile.ZipFile(second_export, "w") as archive:
        archive.writestr("chat.txt", "2024-01-02, 09:15 - Nethmi: Hello\n2024-01-02, 09:16 - Nethmi: Need a cake\n")

    first_result = service.import_package(business_id, first_export.getvalue(), import_name="chat-repeat-1")
    second_result = service.import_package(business_id, second_export.getvalue(), import_name="chat-repeat-2")

    assert first_result.is_successful is True
    assert second_result.is_successful is True

    with SessionLocal() as session:
        conversations = session.query(Conversation).all()
        messages = session.query(Message).all()
        assert len(conversations) == 1
        assert len(messages) == 2


def _patch_main_db(monkeypatch, engine):
    import app.main as main_module
    from app.database.connection import session_scope as connection_session_scope

    @contextmanager
    def test_session_scope():
        with connection_session_scope(bind=engine) as session:
            yield session

    monkeypatch.setattr(main_module, "engine", engine)
    monkeypatch.setattr(main_module, "session_scope", test_session_scope)


def test_upload_api_accepts_valid_zip_and_returns_import_result(monkeypatch):
    engine = _make_engine()
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    _patch_main_db(monkeypatch, engine)

    with factory() as session:
        session.add(Business(name="Upload Bakery", slug="upload-bakery"))
        session.commit()

    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("chat.txt", "2024-01-02, 09:15 - Nethmi: Hello from upload\n")

    file_obj = UploadFile(filename="chat.zip", file=io.BytesIO(payload.getvalue()))
    result = asyncio.run(upload_whatsapp_import(business_id=1, file=file_obj))

    assert result["status"] in {"completed", "partial"}
    assert result["is_successful"] is True
    assert result["import_batch_id"] is not None


def test_upload_api_rejects_invalid_or_missing_upload(monkeypatch):
    engine = _make_engine()
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    _patch_main_db(monkeypatch, engine)

    with factory() as session:
        session.add(Business(name="Reject Bakery", slug="reject-bakery"))
        session.commit()

    invalid_file = UploadFile(filename="bad.txt", file=io.BytesIO(b"not a zip"))
    with pytest.raises(HTTPException, match="Only ZIP archive uploads are supported"):
        asyncio.run(upload_whatsapp_import(business_id=1, file=invalid_file))

    with pytest.raises(HTTPException):
        asyncio.run(upload_whatsapp_import(business_id=999, file=UploadFile(filename="chat.zip", file=io.BytesIO(b"not a zip"))))
