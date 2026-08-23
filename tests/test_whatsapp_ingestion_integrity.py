import io
import zipfile
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from app.database import Base
from app.database.connection import SessionLocal
from app.database.models import (
    Business,
    Conversation,
    ImportBatch,
    Media,
    Message,
    Participant,
    WhatsAppIdentity,
)
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


def _create_business(engine, name: str, slug: str) -> int:
    SessionLocal.configure(bind=engine)
    with SessionLocal() as session:
        business = Business(name=name, slug=slug)
        session.add(business)
        session.commit()
        return business.id


def _zip_with_files(files: dict[str, str]) -> bytes:
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    return payload.getvalue()


def test_import_provenance_is_persisted_on_conversation_and_messages():
    engine = _make_engine()
    business_id = _create_business(engine, "Provenance Bakery", "provenance-bakery")
    service = IngestionService(engine)

    payload = _zip_with_files({"chat.txt": "2024-01-02, 09:15 - Nethmi: Hello\n"})
    result = service.import_package(business_id, payload, import_name="batch-1")

    with SessionLocal() as session:
        import_batch = session.get(ImportBatch, result.import_batch_id)
        conversation = session.execute(select(Conversation)).scalar_one()
        message = session.execute(select(Message)).scalar_one()

        assert import_batch is not None
        assert conversation.import_batch_id == import_batch.id
        assert message.import_batch_id == import_batch.id


def test_reimport_preserves_original_message_provenance():
    engine = _make_engine()
    business_id = _create_business(engine, "Provenance Repeat", "provenance-repeat")
    service = IngestionService(engine)

    chat = "2024-01-02, 09:15 - Nethmi: Hello\n"
    first_payload = _zip_with_files({"chat.txt": chat})
    second_payload = _zip_with_files({"chat.txt": chat + "2024-01-02, 09:16 - Nethmi: Follow up\n"})

    first_result = service.import_package(business_id, first_payload, import_name="first-batch")
    with SessionLocal() as session:
        original_message = session.execute(
            select(Message).where(Message.content == "Hello")
        ).scalar_one()
        original_batch_id = original_message.import_batch_id
        original_conversation_batch_id = session.get(
            Conversation, original_message.conversation_id
        ).import_batch_id

    second_result = service.import_package(business_id, second_payload, import_name="second-batch")

    with SessionLocal() as session:
        hello_message = session.execute(
            select(Message).where(Message.content == "Hello")
        ).scalar_one()
        follow_up = session.execute(
            select(Message).where(Message.content == "Follow up")
        ).scalar_one()
        conversation = session.get(Conversation, hello_message.conversation_id)

        assert first_result.import_batch_id != second_result.import_batch_id
        assert hello_message.import_batch_id == original_batch_id
        assert follow_up.import_batch_id == second_result.import_batch_id
        assert conversation.import_batch_id == original_conversation_batch_id


def test_participant_is_reused_for_multiple_messages_from_same_sender():
    engine = _make_engine()
    business_id = _create_business(engine, "Participant Bakery", "participant-bakery")
    service = IngestionService(engine)

    payload = _zip_with_files(
        {
            "chat.txt": (
                "2024-01-02, 09:15 - Alice: Hello\n"
                "2024-01-02, 09:16 - Alice: Second message\n"
            )
        }
    )
    service.import_package(business_id, payload, import_name="participant-batch")

    with SessionLocal() as session:
        participants = session.execute(select(Participant)).scalars().all()
        messages = session.execute(select(Message)).scalars().all()

        assert len(participants) == 1
        assert len(messages) == 2
        assert {message.participant_id for message in messages} == {participants[0].id}


def test_same_display_name_in_different_conversations_creates_distinct_identities():
    engine = _make_engine()
    business_id = _create_business(engine, "Identity Bakery", "identity-bakery")
    service = IngestionService(engine)

    payload = _zip_with_files(
        {
            "chat-a.txt": "2024-01-02, 09:15 - Alice: Hello from A\n",
            "chat-b.txt": "2024-01-02, 09:15 - Alice: Hello from B\n",
        }
    )
    service.import_package(business_id, payload, import_name="identity-batch")

    with SessionLocal() as session:
        identities = session.execute(select(WhatsAppIdentity)).scalars().all()
        participants = session.execute(select(Participant)).scalars().all()

        assert len(identities) == 2
        assert len(participants) == 2
        assert identities[0].normalized_number != identities[1].normalized_number


def test_phone_number_identity_is_reused_across_conversations():
    engine = _make_engine()
    business_id = _create_business(engine, "Phone Bakery", "phone-bakery")
    service = IngestionService(engine)

    payload = _zip_with_files(
        {
            "chat-a.txt": "2024-01-02, 09:15 - +94771234567: Hello\n",
            "chat-b.txt": "2024-01-02, 09:16 - +94771234567: Another chat\n",
        }
    )
    service.import_package(business_id, payload, import_name="phone-batch")

    with SessionLocal() as session:
        identities = session.execute(select(WhatsAppIdentity)).scalars().all()
        participants = session.execute(select(Participant)).scalars().all()

        assert len(identities) == 1
        assert len(participants) == 2


def test_media_records_are_persisted():
    engine = _make_engine()
    business_id = _create_business(engine, "Media Bakery", "media-bakery")
    service = IngestionService(engine)

    payload = _zip_with_files(
        {
            "chat.txt": "06/07/2026, 12:33 - Dilhani: IMG-20260706-WA0001.jpg (file attached)\n",
        }
    )
    service.import_package(business_id, payload, import_name="media-batch")

    with SessionLocal() as session:
        media_rows = session.execute(select(Media)).scalars().all()
        message = session.execute(select(Message)).scalar_one()

        assert len(media_rows) == 1
        assert media_rows[0].message_id == message.id
        assert media_rows[0].file_name == "IMG-20260706-WA0001.jpg"
        assert media_rows[0].media_type == "image"


def test_validate_zip_package_rejects_path_traversal():
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("../escape/chat.txt", "2024-01-02, 09:15 - Nethmi: Hi\n")

    validation = validate_zip_package(payload.getvalue())

    assert validation.is_valid is False
    assert any("unsafe" in error.lower() for error in validation.errors)


def test_business_isolation_keeps_imported_records_separate():
    engine = _make_engine()
    SessionLocal.configure(bind=engine)

    with SessionLocal() as session:
        session.add_all(
            [
                Business(name="Biz A", slug="biz-a-ingestion"),
                Business(name="Biz B", slug="biz-b-ingestion"),
            ]
        )
        session.commit()
        business_a_id = session.execute(select(Business).where(Business.slug == "biz-a-ingestion")).scalar_one().id
        business_b_id = session.execute(select(Business).where(Business.slug == "biz-b-ingestion")).scalar_one().id

    service = IngestionService(engine)
    chat = "2024-01-02, 09:15 - Nethmi: Hello\n"
    service.import_package(business_a_id, _zip_with_files({"chat.txt": chat}), import_name="a")
    service.import_package(business_b_id, _zip_with_files({"chat.txt": chat}), import_name="b")

    with SessionLocal() as session:
        a_messages = session.execute(
            select(Message).join(Conversation).where(Conversation.business_id == business_a_id)
        ).scalars().all()
        b_messages = session.execute(
            select(Message).join(Conversation).where(Conversation.business_id == business_b_id)
        ).scalars().all()

        assert len(a_messages) == 1
        assert len(b_messages) == 1
        assert a_messages[0].id != b_messages[0].id


def test_unchanged_export_imported_twice_does_not_create_duplicate_messages():
    engine = _make_engine()
    business_id = _create_business(engine, "Repeat Bakery", "repeat-bakery")
    service = IngestionService(engine)

    payload = _zip_with_files({"chat.txt": "2024-01-02, 09:15 - Nethmi: Hello\n"})
    first = service.import_package(business_id, payload, import_name="repeat-1")
    second = service.import_package(business_id, payload, import_name="repeat-2")

    with SessionLocal() as session:
        messages = session.execute(select(Message)).scalars().all()
        batches = session.execute(select(ImportBatch)).scalars().all()

        assert len(messages) == 1
        assert len(batches) == 2
        assert first.import_batch_id != second.import_batch_id


def test_multiple_conversations_in_one_zip_are_imported_separately():
    engine = _make_engine()
    business_id = _create_business(engine, "Multi Chat Bakery", "multi-chat-bakery")
    service = IngestionService(engine)

    payload = _zip_with_files(
        {
            "chat-a.txt": "2024-01-02, 09:15 - Alice: A message\n",
            "chat-b.txt": "2024-01-02, 09:16 - Bob: B message\n",
        }
    )
    result = service.import_package(business_id, payload, import_name="multi-chat")

    with SessionLocal() as session:
        conversations = session.execute(select(Conversation)).scalars().all()
        messages = session.execute(select(Message)).scalars().all()

        assert result.status == "completed"
        assert len(conversations) == 2
        assert len(messages) == 2


def test_partial_import_preserves_successful_chat_and_records_errors():
    engine = _make_engine()
    business_id = _create_business(engine, "Partial Bakery", "partial-bakery")
    service = IngestionService(engine)

    payload = _zip_with_files(
        {
            "good.txt": "2024-01-02, 09:15 - Nethmi: Good chat\n",
            "bad.txt": "this file cannot be parsed as whatsapp content\n",
        }
    )
    result = service.import_package(business_id, payload, import_name="partial-batch")

    with SessionLocal() as session:
        import_batch = session.get(ImportBatch, result.import_batch_id)
        errors, warnings = IngestionService.load_import_batch_diagnostics(import_batch)
        messages = session.execute(select(Message)).scalars().all()

        assert result.status == "completed"
        assert len(messages) == 1
        assert messages[0].content == "Good chat"
        assert any("No parseable records" in warning for warning in warnings)


def test_transaction_rollback_does_not_discard_previously_committed_chat():
    engine = _make_engine()
    business_id = _create_business(engine, "Rollback Bakery", "rollback-bakery")
    service = IngestionService(engine)

    payload = _zip_with_files(
        {
            "first.txt": "2024-01-02, 09:15 - Nethmi: First chat\n",
            "second.txt": "2024-01-02, 09:16 - Nethmi: Second chat\n",
        }
    )

    original_commit = Session.commit
    commit_calls = {"count": 0}

    def flaky_commit(session_self):
        commit_calls["count"] += 1
        if commit_calls["count"] == 2:
            raise RuntimeError("simulated persistence failure")
        return original_commit(session_self)

    with patch.object(Session, "commit", flaky_commit):
        result = service.import_package(business_id, payload, import_name="rollback-batch")

    with SessionLocal() as session:
        import_batch = session.get(ImportBatch, result.import_batch_id)
        errors, _warnings = IngestionService.load_import_batch_diagnostics(import_batch)
        messages = session.execute(select(Message)).scalars().all()

        assert result.status == "partial"
        assert len(messages) == 1
        assert messages[0].content == "First chat"
        assert any("Failed to process second.txt" in error for error in errors)


def test_import_batch_errors_and_warnings_are_durable():
    engine = _make_engine()
    business_id = _create_business(engine, "Diagnostics Bakery", "diagnostics-bakery")
    service = IngestionService(engine)

    payload = _zip_with_files({"bad.txt": "unparseable content\n"})
    result = service.import_package(business_id, payload, import_name="diagnostics-batch")

    with SessionLocal() as session:
        import_batch = session.get(ImportBatch, result.import_batch_id)
        errors, warnings = IngestionService.load_import_batch_diagnostics(import_batch)

        assert result.status == "failed"
        assert import_batch.status == "failed"
        assert import_batch.errors_json is not None or import_batch.warnings_json is not None
        assert any("No parseable records" in warning for warning in warnings)


def test_unparseable_timestamp_is_preserved_without_using_current_time():
    records = parse_whatsapp_chat_text("99/99/9999, 99:99 - Alice: bad timestamp\n")

    assert len(records) == 1
    assert records[0]["timestamp"] is None
    assert records[0]["timestamp_parsed"] is False
    assert "99/99/9999" in records[0]["source_timestamp"]

    engine = _make_engine()
    business_id = _create_business(engine, "Timestamp Bakery", "timestamp-bakery")
    service = IngestionService(engine)

    payload = _zip_with_files({"chat.txt": "99/99/9999, 99:99 - Alice: bad timestamp\n"})
    result = service.import_package(business_id, payload, import_name="timestamp-batch")

    with SessionLocal() as session:
        message = session.execute(select(Message)).scalar_one()
        errors, warnings = IngestionService.load_import_batch_diagnostics(
            session.get(ImportBatch, result.import_batch_id)
        )

        assert message.sent_at is None
        assert message.source_timestamp is not None
        assert "99/99/9999" in message.source_timestamp
        assert any("Unparseable timestamp" in warning for warning in warnings)
        assert message.content == "bad timestamp"


def test_raw_message_content_is_not_modified_during_ingestion():
    engine = _make_engine()
    business_id = _create_business(engine, "Raw Bakery", "raw-bakery")
    service = IngestionService(engine)

    original = "06/07/2026, 11:47 - Nadeeka: hi dear 😊 සුබ දවසක්\n"
    service.import_package(business_id, _zip_with_files({"chat.txt": original}), import_name="raw-batch")

    with SessionLocal() as session:
        message = session.execute(select(Message)).scalar_one()
        assert message.content == "hi dear 😊 සුබ දවසක්"


def test_raw_ingestion_leaves_participant_type_null_and_preserves_associations():
    engine = _make_engine()
    business_id = _create_business(engine, "Neutral Bakery", "neutral-bakery")
    service = IngestionService(engine)

    chat_text = (
        "06/07/2026, 09:12 - Dilhani: hi nadeeka akka\n"
        "06/07/2026, 11:47 - Nadeeka: hi dear 😊 සුබ දවසක්\n"
    )
    result = service.import_package(
        business_id,
        _zip_with_files({"chat.txt": chat_text}),
        import_name="neutral-batch",
    )
    assert result.is_successful is True

    with SessionLocal() as session:
        participants = session.execute(
            select(Participant).order_by(Participant.id)
        ).scalars().all()
        identities = session.execute(
            select(WhatsAppIdentity).order_by(WhatsAppIdentity.id)
        ).scalars().all()
        messages = session.execute(
            select(Message).order_by(Message.id)
        ).scalars().all()
        conversations = session.execute(select(Conversation)).scalars().all()

        assert len(participants) == 2
        assert len(identities) == 2
        assert len(messages) == 2
        assert len(conversations) == 1

        # 1. Raw ingestion does not classify participants as customers or owners
        for p in participants:
            assert p.participant_type is None
            assert p.business_id == business_id
            assert p.conversation_id == conversations[0].id

        # 2. Participant identities and linkages are preserved
        assert participants[0].display_name == "Dilhani"
        assert participants[0].whatsapp_identity_id == identities[0].id
        assert identities[0].whatsapp_number == "Dilhani"
        assert identities[0].normalized_number == "conv:chat:dilhani"

        assert participants[1].display_name == "Nadeeka"
        assert participants[1].whatsapp_identity_id == identities[1].id
        assert identities[1].whatsapp_number == "Nadeeka"
        assert identities[1].normalized_number == "conv:chat:nadeeka"

        # 3. Message participant linkages and provenance remain intact
        assert messages[0].participant_id == participants[0].id
        assert messages[0].import_batch_id == result.import_batch_id
        assert messages[1].participant_id == participants[1].id
        assert messages[1].import_batch_id == result.import_batch_id


def test_identical_messages_in_same_minute_are_preserved():
    engine = _make_engine()
    business_id = _create_business(engine, "Dedupe Bakery", "dedupe-bakery")
    service = IngestionService(engine)

    # Identical messages in same minute
    chat = (
        "2024-01-02, 10:32 - Customer: ok\n"
        "2024-01-02, 10:32 - Customer: ok\n"
    )
    first_payload = _zip_with_files({"chat.txt": chat})
    service.import_package(business_id, first_payload, import_name="batch-1")

    with SessionLocal() as session:
        messages = session.execute(select(Message)).scalars().all()
        assert len(messages) == 2, "Both identical messages should be inserted"

    # Re-import same export
    service.import_package(business_id, first_payload, import_name="batch-2")

    with SessionLocal() as session:
        messages = session.execute(select(Message)).scalars().all()
        assert len(messages) == 2, "No duplicate rows should be inserted on re-import"


def test_legacy_message_recovery_preserves_compatibility():
    engine = _make_engine()
    business_id = _create_business(engine, "Legacy Bakery", "legacy-bakery")
    service = IngestionService(engine)

    # Simulate legacy DB state: one legacy message (seq=0 was imported, seq=1 was lost)
    with SessionLocal() as session:
        conv = Conversation(business_id=business_id, conversation_ref="chat")
        session.add(conv)
        session.flush()
        
        identity = WhatsAppIdentity(business_id=business_id, whatsapp_number="Customer", normalized_number="conv:chat:customer")
        session.add(identity)
        session.flush()

        participant = Participant(business_id=business_id, conversation_id=conv.id, whatsapp_identity_id=identity.id, display_name="Customer")
        session.add(participant)
        session.flush()

        from datetime import datetime, timezone
        
        batch = ImportBatch(business_id=business_id, import_name="legacy", source_file_name="legacy", status="completed")
        session.add(batch)
        session.flush()

        # Manually create legacy fingerprint
        legacy_fp = service._make_legacy_fingerprint(
            conv.id, datetime(2024, 1, 2, 10, 32, tzinfo=timezone.utc), "2024-01-02, 10:32", "Customer", "ok", "text"
        )
        msg = Message(
            conversation_id=conv.id,
            participant_id=participant.id,
            import_batch_id=batch.id,
            sent_at=datetime(2024, 1, 2, 10, 32, tzinfo=timezone.utc),
            source_timestamp="2024-01-02, 10:32",
            content="ok",
            message_type="text",
            message_fingerprint=legacy_fp
        )
        session.add(msg)
        session.commit()

    # Now import an export containing TWO "ok" messages.
    chat = (
        "2024-01-02, 10:32 - Customer: ok\n"
        "2024-01-02, 10:32 - Customer: ok\n"
    )
    payload = _zip_with_files({"chat.txt": chat})
    service.import_package(business_id, payload, import_name="batch-2")

    with SessionLocal() as session:
        messages = session.execute(select(Message).order_by(Message.id)).scalars().all()
        assert len(messages) == 2, "Second message should be recovered, first should be skipped"

