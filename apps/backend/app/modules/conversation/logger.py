"""Append-only JSONL conversation evidence with deterministic PII masking."""

import json
import re
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Protocol

from app.modules.conversation.domain import ConversationState

_PHONE_PATTERN = re.compile(r"(?<![0-9])(?:\+?62|0)[0-9\s().-]{6,}[0-9](?![0-9])")
_CUSTOMER_ID_PATTERN = re.compile(r"(?<![0-9])[0-9]{10}(?![0-9])")
_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+\b"
)
_ADDRESS_STATES = {
    ConversationState.BORONGAN_ASK_ADDRESS,
    ConversationState.HARIAN_ASK_ADDRESS,
}
_ADDRESS_FIELDS = {"survey_address", "work_address"}


@dataclass(frozen=True, slots=True)
class ConversationTurnEvent:
    """One user turn and the bot decision produced from it."""

    event_id: str
    timestamp: str
    conversation_id: str
    turn: int
    sender: str
    raw_text: str
    normalized_text: str
    predicted_intent: str | None
    confidence: float | None
    state_before: str
    state_after: str
    extracted_slots: dict[str, object]
    response_text: str
    model_version: str | None


class ConversationTurnLogger(Protocol):
    """Boundary used by the service to emit one safe event per user turn."""

    def append(self, event: ConversationTurnEvent) -> None:
        """Append one complete event."""


class NullConversationTurnLogger:
    """No-op implementation for isolated unit tests."""

    def append(self, event: ConversationTurnEvent) -> None:
        del event


def _masked_phone(match: re.Match[str]) -> str:
    raw = match.group(0)
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("62"):
        canonical = f"+{digits}"
        prefix_length = 6
    else:
        canonical = digits
        prefix_length = 4
    if len(canonical) <= prefix_length + 4:
        return f"{canonical[:3]}****{canonical[-2:]}"
    return f"{canonical[:prefix_length]}****{canonical[-4:]}"


def mask_pii_text(text: str, *, state: ConversationState | None = None) -> str:
    """Mask phone, customer ID, email, and state-known address input."""

    if state in _ADDRESS_STATES and text.strip():
        return "[alamat dimasking]"
    masked = _EMAIL_PATTERN.sub("[email dimasking]", text)
    masked = _PHONE_PATTERN.sub(_masked_phone, masked)
    return _CUSTOMER_ID_PATTERN.sub(
        lambda match: f"{match.group(0)[:3]}****{match.group(0)[-3:]}",
        masked,
    )


def mask_extracted_slots(slots: dict[str, object]) -> dict[str, object]:
    """Return a detached snapshot safe for runtime evidence logs."""

    masked: dict[str, object] = {}
    for field, value in slots.items():
        if field == "phone_number":
            masked[field] = mask_pii_text(str(value))
        elif field == "customer_id":
            raw = str(value)
            masked[field] = f"{raw[:3]}****{raw[-3:]}"
        elif field in _ADDRESS_FIELDS:
            masked[field] = "[alamat dimasking]"
        else:
            masked[field] = value
    return masked


def normalize_log_text(text: str) -> str:
    """Apply stable lowercase and whitespace normalization after masking."""

    return " ".join(text.casefold().split())


class JsonlConversationLogger:
    """Thread-safe JSONL writer partitioned by local calendar date."""

    def __init__(self, log_directory: Path) -> None:
        self._log_directory = log_directory
        self._lock = RLock()

    def append(self, event: ConversationTurnEvent) -> None:
        timestamp = datetime.fromisoformat(event.timestamp)
        log_path = self._log_directory / f"conversations-{timestamp.date().isoformat()}.jsonl"
        state_before = ConversationState(event.state_before)
        masked_raw_text = mask_pii_text(event.raw_text, state=state_before)
        safe_event = replace(
            event,
            raw_text=masked_raw_text,
            normalized_text=normalize_log_text(masked_raw_text),
            extracted_slots=mask_extracted_slots(event.extracted_slots),
            response_text=mask_pii_text(event.response_text),
        )
        line = json.dumps(asdict(safe_event), ensure_ascii=False, separators=(",", ":"))
        with self._lock:
            self._log_directory.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"{line}\n")
