import io
import zipfile
from datetime import datetime

from sqlalchemy import create_engine, event

from app.database import Base
from app.database.connection import SessionLocal
from app.database.models import Business, Message
from app.ingestion import parse_whatsapp_chat_text, validate_zip_package
from app.ingestion.service import IngestionService


def _make_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, future=True)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    return engine


def test_validate_zip_package_accepts_supported_chat_export():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("chat.txt", "2024-01-02, 09:15 - Nethmi: Hi there\n")

    validation = validate_zip_package(buffer.getvalue())

    assert validation.is_valid is True
    assert validation.supported_files
    assert validation.errors == []


def test_parse_whatsapp_chat_text_extracts_messages_and_participants():
    lines = "2024-01-02, 09:15 - Nethmi: Hi there\n2024-01-02, 09:16 - Bakery: Hello!"

    records = parse_whatsapp_chat_text(lines)

    assert len(records) == 2
    assert records[0]["sender"] == "Nethmi"
    assert records[0]["content"] == "Hi there"
    assert isinstance(records[0]["timestamp"], datetime)
    assert records[1]["sender"] == "Bakery"


def test_incremental_import_deduplicates_existing_messages():
    engine = _make_engine()
    SessionLocal.configure(bind=engine)

    business = Business(name="Sweet Crumbs", slug="sweet-crumbs")
    with SessionLocal() as session:
        session.add(business)
        session.commit()
        business_id = business.id

    service = IngestionService(engine)

    first_export = io.BytesIO()
    with zipfile.ZipFile(first_export, "w") as archive:
        archive.writestr("chat.txt", "2024-01-02, 09:15 - Nethmi: Hi there\n")

    second_export = io.BytesIO()
    with zipfile.ZipFile(second_export, "w") as archive:
        archive.writestr(
            "chat.txt",
            "2024-01-02, 09:15 - Nethmi: Hi there\n2024-01-02, 09:16 - Nethmi: I need a cake\n",
        )

    first_result = service.import_package(business_id, first_export.getvalue(), import_name="chat-1")
    second_result = service.import_package(business_id, second_export.getvalue(), import_name="chat-2")

    with SessionLocal() as session:
        messages = session.query(Message).all()
        assert len(messages) == 2
        assert first_result.import_batch_id is not None
        assert second_result.import_batch_id is not None
        assert first_result.is_successful is True
        assert second_result.is_successful is True
