from __future__ import annotations

import json
import logging
import re
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

from .identity import derive_whatsapp_identity_keys
from .parser import parse_whatsapp_chat_text
from .validator import temporary_zip_workspace, validate_zip_package

logger = logging.getLogger(__name__)


# Import lazily to avoid circular dependency; used in import_package only.
def _get_relevance_service(engine):
    from app.relevance.service import RelevanceService  # noqa: PLC0415
    return RelevanceService(engine=engine)


CHAT_TEXT_SUFFIXES = {".txt", ".csv", ".json"}


def _discover_chat_files(workspace_root: Path) -> list[Path]:
    return sorted(
        path
        for path in workspace_root.rglob("*")
        if path.is_file() and path.suffix.lower() in CHAT_TEXT_SUFFIXES
    )


def _conversation_ref_for_chat_file(file_path: Path, workspace_root: Path) -> str:
    stem = file_path.stem.strip()
    if stem.lower() in {"_chat", "chat"} and file_path.parent != workspace_root:
        return file_path.parent.name
    return stem or "chat"


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
    "opus": "audio",
    "ogg": "audio",
    "pdf": "document",
    "doc": "document",
    "docx": "document",
    "txt": "document",
    "csv": "document",
}

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
VIDEO_EXTENSIONS = {"mp4", "mov"}
AUDIO_EXTENSIONS = {"mp3", "m4a", "opus", "ogg"}


def _serialize_json_list(values: list[str]) -> str | None:
    if not values:
        return None
    return json.dumps(values)


def _deserialize_json_list(payload: str | None) -> list[str]:
    if not payload:
        return []
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError:
        return [payload]
    if isinstance(decoded, list):
        return [str(item) for item in decoded]
    return [str(decoded)]


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

    def _make_legacy_fingerprint(
        self,
        conversation_id: int,
        timestamp,
        source_timestamp: str,
        sender: str,
        content: str,
        message_type: str,
    ) -> str:
        if timestamp is not None:
            timestamp_key = timestamp.isoformat()
        else:
            timestamp_key = f"raw:{source_timestamp}"
        raw = (
            f"{conversation_id}|{timestamp_key}|{(sender or '').strip().lower()}|"
            f"{(content or '').strip()}|{message_type}"
        )
        return sha256(raw.encode("utf-8")).hexdigest()

    def _make_fingerprint_v2(
        self,
        conversation_id: int,
        timestamp,
        source_timestamp: str,
        sender: str,
        content: str,
        message_type: str,
        intra_minute_sequence: int,
    ) -> str:
        if timestamp is not None:
            timestamp_key = timestamp.isoformat()
        else:
            timestamp_key = f"raw:{source_timestamp}"
        raw = (
            f"{conversation_id}|{timestamp_key}|{(sender or '').strip().lower()}|"
            f"{(content or '').strip()}|{message_type}|{intra_minute_sequence}"
        )
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

    def _media_mime_type(self, ext: str) -> str | None:
        if ext in IMAGE_EXTENSIONS:
            return f"image/{'jpeg' if ext == 'jpg' else ext}"
        if ext in VIDEO_EXTENSIONS:
            return f"video/{ext}"
        if ext in AUDIO_EXTENSIONS:
            return f"audio/{ext}"
        return f"application/{ext}"

    def _ensure_identity(self, session, business_id: int, conversation_ref: str, sender: str):
        whatsapp_number, normalized_number = derive_whatsapp_identity_keys(conversation_ref, sender)
        identity = session.execute(
            select(WhatsAppIdentity).where(
                WhatsAppIdentity.business_id == business_id,
                WhatsAppIdentity.normalized_number == normalized_number,
            )
        ).scalar_one_or_none()

        if identity is not None:
            return identity

        identity = WhatsAppIdentity(
            business_id=business_id,
            whatsapp_number=whatsapp_number,
            normalized_number=normalized_number,
            is_verified=False,
        )
        session.add(identity)
        session.flush()
        return identity

    def _ensure_participant(
        self,
        session,
        conversation_id: int,
        business_id: int,
        identity: WhatsAppIdentity,
        display_name: str,
    ):
        participant = session.execute(
            select(Participant).where(
                Participant.conversation_id == conversation_id,
                Participant.whatsapp_identity_id == identity.id,
            )
        ).scalar_one_or_none()
        if participant is not None:
            return participant

        participant = Participant(
            conversation_id=conversation_id,
            business_id=business_id,
            whatsapp_identity_id=identity.id,
            display_name=display_name,
            participant_type=None,
        )
        session.add(participant)
        session.flush()
        return participant

    def _ensure_conversation(
        self,
        session,
        business_id: int,
        conversation_ref: str,
        import_batch_id: int,
    ):
        existing = session.execute(
            select(Conversation).where(
                Conversation.business_id == business_id,
                Conversation.conversation_ref == conversation_ref,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing

        conversation = Conversation(
            business_id=business_id,
            conversation_ref=conversation_ref,
            import_batch_id=import_batch_id,
        )
        session.add(conversation)
        session.flush()
        return conversation

    def _finalize_import_batch(
        self,
        session,
        import_batch: ImportBatch,
        status: str,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        import_batch.status = status
        import_batch.errors_json = _serialize_json_list(errors)
        import_batch.warnings_json = _serialize_json_list(warnings)
        session.flush()

    @staticmethod
    def load_import_batch_diagnostics(import_batch: ImportBatch) -> tuple[list[str], list[str]]:
        return (
            _deserialize_json_list(import_batch.errors_json),
            _deserialize_json_list(import_batch.warnings_json),
        )

    def import_package(self, business_id: int, file_bytes: bytes, import_name: str = "whatsapp-export") -> ImportBatchResult:
        validation = validate_zip_package(file_bytes)
        final_errors: list[str] = []
        final_warnings: list[str] = []
        imported_count = 0
        batch_result: ImportBatchResult

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
                self._finalize_import_batch(
                    session,
                    import_batch,
                    status="failed",
                    errors=validation.errors,
                    warnings=validation.warnings,
                )
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
                    chat_files = _discover_chat_files(temp_dir)

                    if not chat_files:
                        final_errors.append(
                            "No supported chat export files were found in the extracted archive."
                        )

                    for file_path in chat_files:
                        try:
                            decoded = file_path.read_text(encoding="utf-8", errors="replace")
                            records = parse_whatsapp_chat_text(decoded)
                            if not records:
                                final_warnings.append(f"No parseable records found in {file_path.name}")
                                continue

                            conversation_ref = _conversation_ref_for_chat_file(file_path, temp_dir)
                            conversation = self._ensure_conversation(
                                session,
                                business_id,
                                conversation_ref,
                                import_batch.id,
                            )

                            for index, row in enumerate(records):
                                sender = str(row.get("sender") or "Unknown").strip()
                                timestamp = row.get("timestamp")
                                source_timestamp = str(row.get("source_timestamp") or "").strip()
                                timestamp_parsed = bool(row.get("timestamp_parsed"))
                                content = str(row.get("content") or "").strip()
                                message_type = str(row.get("message_type") or "text")
                                intra_minute_sequence = int(row.get("intra_minute_sequence") or 0)

                                if not timestamp_parsed:
                                    final_warnings.append(
                                        f"Unparseable timestamp preserved for message in {file_path.name}:{index}: "
                                        f"{source_timestamp or 'unknown'}"
                                    )

                                fingerprint_v2 = self._make_fingerprint_v2(
                                    conversation.id,
                                    timestamp,
                                    source_timestamp,
                                    sender,
                                    content,
                                    message_type,
                                    intra_minute_sequence,
                                )

                                if intra_minute_sequence == 0:
                                    legacy_fingerprint = self._make_legacy_fingerprint(
                                        conversation.id,
                                        timestamp,
                                        source_timestamp,
                                        sender,
                                        content,
                                        message_type,
                                    )
                                    existing_message = session.execute(
                                        select(Message).where(
                                            Message.conversation_id == conversation.id,
                                            Message.message_fingerprint.in_([fingerprint_v2, legacy_fingerprint])
                                        )
                                    ).scalar_one_or_none()
                                else:
                                    existing_message = session.execute(
                                        select(Message).where(
                                            Message.conversation_id == conversation.id,
                                            Message.message_fingerprint == fingerprint_v2
                                        )
                                    ).scalar_one_or_none()

                                if existing_message is not None:
                                    continue

                                identity = self._ensure_identity(session, business_id, conversation_ref, sender)
                                participant = self._ensure_participant(
                                    session,
                                    conversation.id,
                                    business_id,
                                    identity,
                                    sender,
                                )

                                message = Message(
                                    conversation_id=conversation.id,
                                    import_batch_id=import_batch.id,
                                    participant_id=participant.id,
                                    source_message_id=f"{file_path.name}:{index}",
                                    message_fingerprint=fingerprint_v2,
                                    content=content,
                                    message_type=message_type,
                                    sent_at=timestamp,
                                    source_timestamp=source_timestamp or None,
                                )
                                session.add(message)
                                session.flush()

                                media_refs = self._extract_media_references(content)
                                if media_refs:
                                    final_warnings.append(
                                        f"Advanced media interpretation was not performed for {file_path.name}:{index}."
                                    )
                                for media_id in media_refs:
                                    ext = media_id.rsplit(".", 1)[-1].lower()
                                    session.add(
                                        Media(
                                            message_id=message.id,
                                            media_type=MEDIA_SUFFIXES.get(ext, "document"),
                                            file_name=media_id,
                                            source_path=media_id,
                                            mime_type=self._media_mime_type(ext),
                                        )
                                    )
                                imported_count += 1
                                session.flush()

                            session.commit()
                        except Exception as exc:
                            session.rollback()
                            final_errors.append(f"Failed to process {file_path.name}: {exc}")

                if imported_count and final_errors:
                    status = "partial"
                elif imported_count:
                    status = "completed"
                else:
                    status = "failed"
                    if not final_errors and not final_warnings:
                        final_errors.append(
                            "Import completed without persisting any messages from the uploaded archive."
                        )

                self._finalize_import_batch(
                    session,
                    import_batch,
                    status=status,
                    errors=final_errors,
                    warnings=final_warnings,
                )
                batch_result = ImportBatchResult(
                    import_batch_id=import_batch.id,
                    is_successful=imported_count > 0 and status != "failed",
                    status=status,
                    errors=final_errors,
                    warnings=final_warnings,
                )
            except Exception as exc:
                final_errors.append(f"Import failed: {exc}")
                self._finalize_import_batch(
                    session,
                    import_batch,
                    status="failed",
                    errors=final_errors,
                    warnings=final_warnings,
                )
                batch_result = ImportBatchResult(
                    import_batch_id=import_batch.id,
                    is_successful=False,
                    status="failed",
                    errors=final_errors,
                    warnings=final_warnings,
                )

        return batch_result
