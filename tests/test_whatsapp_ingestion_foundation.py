import io
import zipfile
from datetime import datetime

from sqlalchemy import create_engine, event

from app.database import Base
from app.database.connection import SessionLocal
from app.database.models import Business, Conversation, Message
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


def test_parse_whatsapp_chat_text_supports_real_android_export_format():
    lines = """06/07/2026, 09:12 - Messages and calls are end-to-end encrypted. Only people in this chat can read, listen to, or share them. Learn more
06/07/2026, 09:12 - Dilhani: hi nadeeka akka
06/07/2026, 12:33 - Dilhani: IMG-20260706-WA0001.jpg (file attached)
14/07/2026, 09:40 - Dilhani: PTT-20260714-WA0001.opus (file attached)
06/07/2026, 11:47 - Nadeeka: hi dear 😊 සුබ දවසක්"""

    records = parse_whatsapp_chat_text(lines)

    assert len(records) == 4
    assert records[0]["sender"] == "Dilhani"
    assert records[0]["content"] == "hi nadeeka akka"
    assert records[0]["timestamp"] == datetime(2026, 7, 6, 9, 12, tzinfo=records[0]["timestamp"].tzinfo)
    assert "IMG-20260706-WA0001.jpg" in records[1]["content"]
    assert "PTT-20260714-WA0001.opus" in records[2]["content"]
    assert records[3]["sender"] == "Nadeeka"


def test_parse_whatsapp_chat_text_supports_bracket_export_format():
    lines = "[06/07/2026, 09:12] Dilhani: hi nadeeka akka\n[06/07/2026, 11:47] Nadeeka: hi dear"

    records = parse_whatsapp_chat_text(lines)

    assert len(records) == 2
    assert records[0]["sender"] == "Dilhani"
    assert records[1]["sender"] == "Nadeeka"


def test_parse_whatsapp_chat_text_appends_continuation_lines():
    lines = """06/07/2026, 09:12 - Dilhani: line one
continued on next line
06/07/2026, 09:13 - Nadeeka: ok"""

    records = parse_whatsapp_chat_text(lines)

    assert len(records) == 2
    assert records[0]["content"] == "line one\ncontinued on next line"
    assert records[1]["sender"] == "Nadeeka"


def test_import_package_processes_nested_whatsapp_export_structure():
    engine = _make_engine()
    SessionLocal.configure(bind=engine)

    business = Business(name="Nested Bakery", slug="nested-bakery")
    with SessionLocal() as session:
        session.add(business)
        session.commit()
        business_id = business.id

    service = IngestionService(engine)
    chat_text = (
        "06/07/2026, 09:12 - Messages and calls are end-to-end encrypted. Learn more\n"
        "06/07/2026, 09:12 - Dilhani: hi nadeeka akka\n"
        "06/07/2026, 12:33 - Dilhani: IMG-20260706-WA0001.jpg (file attached)\n"
    )

    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("WhatsApp Chat with Dilhani/_chat.txt", chat_text)
        archive.writestr("WhatsApp Chat with Dilhani/IMG-20260706-WA0001.jpg", b"fake-image")

    result = service.import_package(
        business_id,
        payload.getvalue(),
        import_name="WhatsApp Chat with Dilhani.zip",
    )

    with SessionLocal() as session:
        messages = session.query(Message).all()
        conversations = session.query(Conversation).all()

        assert result.is_successful is True
        assert result.status == "completed"
        assert len(conversations) == 1
        assert conversations[0].conversation_ref == "WhatsApp Chat with Dilhani"
        assert len(messages) == 2


def test_incremental_import_deduplicates_real_format_messages():
    engine = _make_engine()
    SessionLocal.configure(bind=engine)

    business = Business(name="Nadeeka Cakes", slug="nadeeka-cakes")
    with SessionLocal() as session:
        session.add(business)
        session.commit()
        business_id = business.id

    service = IngestionService(engine)
    chat_line = "06/07/2026, 09:12 - Dilhani: hi nadeeka akka\n"

    first_export = io.BytesIO()
    with zipfile.ZipFile(first_export, "w") as archive:
        archive.writestr("WhatsApp Chat with Dilhani.txt", chat_line)

    second_export = io.BytesIO()
    with zipfile.ZipFile(second_export, "w") as archive:
        archive.writestr(
            "WhatsApp Chat with Dilhani.txt",
            chat_line + "06/07/2026, 09:13 - Dilhani: mata cake ekak one\n",
        )

    first_result = service.import_package(business_id, first_export.getvalue(), import_name="dilhani-1")
    second_result = service.import_package(business_id, second_export.getvalue(), import_name="dilhani-2")

    with SessionLocal() as session:
        messages = session.query(Message).all()
        assert len(messages) == 2
        assert first_result.is_successful is True
        assert second_result.is_successful is True


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
