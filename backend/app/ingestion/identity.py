from __future__ import annotations

import re

_PHONE_PATTERN = re.compile(r"\+?\d{10,15}")


def _normalize_phone(raw_phone: str) -> str:
    digits = re.sub(r"\D", "", raw_phone)
    if raw_phone.strip().startswith("+"):
        return f"+{digits}"
    return digits


def derive_whatsapp_identity_keys(conversation_ref: str, sender: str) -> tuple[str, str]:
    """Derive durable WhatsApp identity keys from export sender information.

    When a reliable phone number is present in the sender field, use it as a
    business-scoped identity key. Otherwise, scope the identity to the conversation
    so that identical display names in different conversations remain separate.
    """
    display_name = sender.strip() or "unknown"
    compact_sender = display_name.replace(" ", "").replace("-", "")

    phone_match = _PHONE_PATTERN.search(compact_sender)
    if phone_match:
        normalized_phone = _normalize_phone(phone_match.group())
        return normalized_phone, normalized_phone

    scoped_key = f"conv:{conversation_ref}:{display_name.lower()}"
    return display_name, scoped_key
