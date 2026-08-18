from __future__ import annotations

import re
from datetime import datetime, timezone

# Android / default export: 06/07/2026, 09:12 - Sender: message
_ANDROID_PATTERN = re.compile(
    r"^(?P<date>\d{1,2}/\d{1,2}/\d{2,4}),\s*"
    r"(?P<time>\d{1,2}:\d{2})(?::\d{2})?"
    r"(?:\s*(?P<ampm>[AaPp][Mm]))?"
    r"\s*-\s*"
    r"(?P<sender>[^:]+):\s*"
    r"(?P<content>.*)$"
)

# ISO-style export: 2024-01-02, 09:15 - Sender: message
_ISO_PATTERN = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2}),\s*"
    r"(?P<time>\d{1,2}:\d{2})(?::\d{2})?"
    r"(?:\s*(?P<ampm>[AaPp][Mm]))?"
    r"\s*-\s*"
    r"(?P<sender>[^:]+):\s*"
    r"(?P<content>.*)$"
)

# iOS / bracket export: [06/07/2026, 09:12] Sender: message
_BRACKET_PATTERN = re.compile(
    r"^\[(?P<date>\d{1,2}/\d{1,2}/\d{2,4}),\s*"
    r"(?P<time>\d{1,2}:\d{2})(?::\d{2})?"
    r"(?:\s*(?P<ampm>[AaPp][Mm]))?"
    r"\]\s*"
    r"(?P<sender>[^:]+):\s*"
    r"(?P<content>.*)$"
)

# System / metadata lines: 06/07/2026, 09:12 - Messages and calls are end-to-end encrypted...
_SYSTEM_LINE_PATTERN = re.compile(
    r"^(?P<date>\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}),\s*"
    r"(?P<time>\d{1,2}:\d{2})(?::\d{2})?"
    r"(?:\s*(?P<ampm>[AaPp][Mm]))?"
    r"\s*-\s*"
    r"(?P<content>.+)$"
)

_SYSTEM_CONTENT_PREFIXES = (
    "messages and calls are end-to-end encrypted",
    "messages to this chat and calls are end-to-end encrypted",
    "messages to this group are end-to-end encrypted",
    "you created this group",
    "you changed the subject",
    "you changed this group's icon",
    "you changed the group description",
    "security code changed",
    "<media omitted>",
)

_DATE_FORMATS = (
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d/%m/%y",
    "%m/%d/%y",
    "%Y-%m-%d",
)


def _format_source_timestamp(date_raw: str, time_raw: str, ampm: str | None) -> str:
    source = f"{date_raw.strip()}, {time_raw.strip()}"
    if ampm and ampm.strip():
        return f"{source} {ampm.strip()}"
    return source


def _parse_timestamp(date_raw: str, time_raw: str, ampm: str | None) -> tuple[datetime | None, str, bool]:
    source_timestamp = _format_source_timestamp(date_raw, time_raw, ampm)
    ampm_normalized = (ampm or "").strip().lower()

    if "/" in date_raw:
        date_candidates = _DATE_FORMATS[:4]
    else:
        date_candidates = ("%Y-%m-%d",)

    time_candidates: list[str] = ["%H:%M", "%H:%M:%S"]
    if ampm_normalized:
        time_candidates = ["%I:%M %p", "%I:%M:%S %p", *time_candidates]

    for date_fmt in date_candidates:
        for time_fmt in time_candidates:
            combined = f"{date_raw.strip()}, {time_raw.strip()}"
            if ampm_normalized and "%p" not in time_fmt:
                combined = f"{combined} {ampm_normalized}"
            fmt = f"{date_fmt}, {time_fmt}"
            try:
                parsed = datetime.strptime(combined, fmt).replace(tzinfo=timezone.utc)
                return parsed, source_timestamp, True
            except ValueError:
                continue

    return None, source_timestamp, False


def _is_system_content(content: str) -> bool:
    normalized = content.strip().lower()
    return any(normalized.startswith(prefix) for prefix in _SYSTEM_CONTENT_PREFIXES)


def _try_parse_message_line(line: str) -> dict | None:
    for pattern in (_ANDROID_PATTERN, _ISO_PATTERN, _BRACKET_PATTERN):
        match = pattern.match(line)
        if not match:
            continue

        sender = match.group("sender").strip()
        content = match.group("content").strip()
        timestamp, source_timestamp, timestamp_parsed = _parse_timestamp(
            match.group("date"),
            match.group("time"),
            match.group("ampm"),
        )

        return {
            "timestamp": timestamp,
            "source_timestamp": source_timestamp,
            "timestamp_parsed": timestamp_parsed,
            "sender": sender,
            "content": content,
            "message_type": "text",
        }

    system_match = _SYSTEM_LINE_PATTERN.match(line)
    if system_match and _is_system_content(system_match.group("content")):
        return None

    return None


def parse_whatsapp_chat_text(raw_text: str) -> list[dict]:
    """Parse WhatsApp chat export text into structured message records.

    Supported formats include:
        06/07/2026, 09:12 - Dilhani: hi nadeeka akka
        2024-01-02, 09:15 - Nethmi: Hi there
        [06/07/2026, 09:12] Dilhani: hi nadeeka akka

    Continuation lines without a timestamp are appended to the previous message.
    Known WhatsApp system/metadata lines are skipped.
    """
    records: list[dict] = []

    for line in (raw_text or "").splitlines():
        line = line.strip("\ufeff").rstrip()
        if not line or re.fullmatch(r"-{3,}", line):
            continue

        parsed = _try_parse_message_line(line)
        if parsed is not None:
            records.append(parsed)
            continue

        if records:
            records[-1]["content"] = f"{records[-1]['content']}\n{line}".strip()

    return records
