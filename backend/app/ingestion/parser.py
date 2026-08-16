from __future__ import annotations

import re
from datetime import datetime, timezone

_MESSAGE_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2},\s*\d{2}:\d{2})\s*-\s*(?P<sender>[^:]+):\s*(?P<content>.*)$"
)


def parse_whatsapp_chat_text(raw_text: str) -> list[dict]:
    """Parse a basic WhatsApp chat export format.

    Supported format example:
        2024-01-02, 09:15 - Nethmi: Hi there
    """
    records: list[dict] = []

    for line in (raw_text or "").splitlines():
        line = line.strip()
        if not line:
            continue

        match = _MESSAGE_PATTERN.match(line)
        if not match:
            continue

        timestamp_raw = match.group("timestamp")
        sender = match.group("sender").strip()
        content = match.group("content").strip()

        try:
            timestamp = datetime.strptime(timestamp_raw, "%Y-%m-%d, %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            timestamp = datetime.now(timezone.utc)

        records.append(
            {
                "timestamp": timestamp,
                "sender": sender,
                "content": content,
            }
        )

    return records
