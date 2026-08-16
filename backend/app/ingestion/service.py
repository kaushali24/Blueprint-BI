from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path

from sqlalchemy import select

from app.database.connection import session_scope
from app.database.models import (
    Conversation,
    ImportBatch,
    Media,
    Message,
    Participant,
    WhatsAppIdentity,
)

from .parser import parse_whatsapp_chat_text
from .validator import temporary_zip_workspace, validate_zip_package


MEDIA_SUFFIXES = {
    "jpg": "image",
    "jpeg": "image",
    "png": "image",
    "gif": "image",
    "webp": "image",
    "mp4": "video",
    "mov": "video",
    "mp3": "audio",
    "m4a": "audio",
    "pdf": "document",
    "doc": "document",
    "docx": "document",
    "txt": "document",
    "csv": "document",
}


@dataclass
class ImportBatchResult:
    import_batch_id: int | None = None
    is_successful: bool = False
    status: str = "failed"
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class IngestionService:
    def __init__(self, engine=None):
        self.engine = engine

    def _make_fingerprint(self, conversation_id: int, timestamp, sender: str, content: str, message_type: str) -> str:
        raw = f"{conversation_id}|{timestamp.isoformat()}|{(sender or '').strip().lower()}|{(content or '').strip()}|{message_type}"
        return sha256(raw.encode("utf-8")).hexdigest()

    def _extract_media_references(self, content: str) -> list[str]:
        pattern = re.compile(r"(?:[A-Za-z0-9_.-]+\.(?:[A-Za-z0-9]+))")
        matches = pattern.findall(content)
        refs: list[str] = []
        for match in matches:
            ext = match.rsplit(".", 1)[-1].lower()
            if ext in MEDIA_SUFFIXES:
                refs.append(match)
        return refs

    def _ensure_identity(self, session, business_id: int, sender: str):
        normalized = sender.strip()
        if not normalized:
            normalized = "unknown"
        identity = session.execute(
            select(WhatsAppIdentity).where(
                WhatsAppIdentity.business_id == business_id,
                WhatsAppIdentity.normalized_number == normalized,
            )
        ).scalar_one_or_none()

        if identity is not None:
            return identity

        identity = WhatsAppIdentity(
            business_id=business_id,
            whatsapp_number=normalized,
            normalized_number=normalized,
            is_verified=False,
        )
        session.add(identity)
        session.flush()
        return identity

    def _ensure_conversation(self, session, business_id: int, conversation_ref: str):
        existing = session.execute(
            select(Conversation).where(
                Conversation.business_id == business_id,
                Conversation.conversation_ref == conversation_ref,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing

        conversation = Conversation(business_id=business_id, conversation_ref=conversation_ref)
        session.add(conversation)
        session.flush()
        return conversation

    def import_package(self, business_id: int, file_bytes: bytes, import_name: str = "whatsapp-export") -> ImportBatchResult:
        validation = validate_zip_package(file_bytes)
        final_errors: list[str] = []
        final_warnings: list[str] = []
        imported_count = 0

        with session_scope(bind=self.engine) as session:
            import_batch = ImportBatch(
                business_id=business_id,
                import_name=import_name,
                source_file_name=import_name,
                status="pending",
            )
            session.add(import_batch)
            session.flush()

            if not validation.is_valid:
                import_batch.status = "failed"
                session.flush()
                return ImportBatchResult(
                    import_batch_id=import_batch.id,
                    is_successful=False,
                    status="failed",
                    errors=validation.errors,
                    warnings=validation.warnings,
                )

            import_batch.status = "processing"
            session.flush()
            final_warnings.extend(validation.warnings)

            try:
                with temporary_zip_workspace(file_bytes) as (temp_dir, workspace_warnings):
                    final_warnings.extend(workspace_warnings)
                    supported_files = sorted(p for p in temp_dir.iterdir() if p.is_file())

                    for file_path in supported_files:
                        try:
                            if file_path.suffix.lower() not in {".txt", ".csv", ".json"}:
                                final_warnings.append(f"Skipped non-supported file: {file_path.name}")
                                continue

                            decoded = file_path.read_text(encoding="utf-8", errors="replace")
                            records = parse_whatsapp_chat_text(decoded)
                            if not records:
                                final_warnings.append(f"No parseable records found in {file_path.name}")
                                continue

                            conversation_ref = file_path.stem or "chat"
                            conversation = self._ensure_conversation(session, business_id, conversation_ref)

                            for index, row in enumerate(records):
                                sender = str(row.get("sender") or "Unknown").strip()
                                timestamp = row.get("timestamp")
                                content = str(row.get("content") or "").strip()
                                fingerprint = self._make_fingerprint(
                                    conversation.id,
                                    timestamp,
                                    sender,
                                    content,
                                    "text",
                                )

                                existing_message = session.execute(
                                    select(Message).where(
                                        Message.conversation_id == conversation.id,
                                        Message.message_fingerprint == fingerprint,
                                    )
                                ).scalar_one_or_none()
                                if existing_message is not None:
                                    continue

                                identity = self._ensure_identity(session, business_id, sender)
                                participant = Participant(
                                    conversation_id=conversation.id,
                                    business_id=business_id,
                                    whatsapp_identity_id=identity.id,
                                    display_name=sender,
                                    participant_type="customer",
                                )
                                session.add(participant)
                                session.flush()

                                message = Message(
                                    conversation_id=conversation.id,
                                    participant_id=participant.id,
                                    source_message_id=f"{file_path.name}:{index}",
                                    message_fingerprint=fingerprint,
                                    content=content,
                                    message_type="text",
                                    sent_at=timestamp,
                                )
                                session.add(message)
                                session.flush()

                                for media_id in self._extract_media_references(content):
                                    ext = media_id.rsplit(".", 1)[-1].lower()
                                    session.add(
                                        Media(
                                            message_id=message.id,
                                            media_type=MEDIA_SUFFIXES.get(ext, "document"),
                                            file_name=media_id,
                                            source_path=media_id,
                                            mime_type=f"application/{ext}" if ext not in {"jpg", "jpeg", "png", "gif", "webp", "mp4", "mov", "mp3", "m4a"} else None,
                                        )
                                    )
                                imported_count += 1
                                session.flush()

                            session.commit()
                        except Exception as exc:
                            session.rollback()
                            final_errors.append(f"Failed to process {file_path.name}: {exc}")

                import_batch.status = "completed" if imported_count else "failed"
                if imported_count and final_errors:
                    import_batch.status = "partial"
                if not imported_count and final_errors:
                    import_batch.status = "failed"

                session.flush()
                return ImportBatchResult(
                    import_batch_id=import_batch.id,
                    is_successful=imported_count > 0 and not final_errors,
                    status=import_batch.status,
                    errors=final_errors,
                    warnings=final_warnings,
                )
            except Exception as exc:
                import_batch.status = "failed"
                session.flush()
                return ImportBatchResult(
                    import_batch_id=import_batch.id,
                    is_successful=False,
                    status="failed",
                    errors=[f"Import failed: {exc}"] + final_errors,
                    warnings=final_warnings,
                )
