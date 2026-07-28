import json
from datetime import UTC, datetime
from pathlib import Path

from app.modules.conversation.domain import ConversationState
from app.modules.conversation.logger import (
    ConversationTurnEvent,
    JsonlConversationLogger,
    mask_extracted_slots,
    mask_pii_text,
)


def test_mask_pii_text_hides_phone_customer_id_email_and_known_address() -> None:
    masked = mask_pii_text("ID 0123456789, WA +62 812-3456-7890, email user@example.com")

    assert "0123456789" not in masked
    assert "6281234567890" not in masked.replace(" ", "").replace("-", "")
    assert "user@example.com" not in masked
    assert "****" in masked
    assert "[email dimasking]" in masked
    assert (
        mask_pii_text(
            "Jalan Melati No. 10, Jakarta",
            state=ConversationState.BORONGAN_ASK_ADDRESS,
        )
        == "[alamat dimasking]"
    )


def test_mask_extracted_slots_keeps_safe_values_and_masks_sensitive_values() -> None:
    masked = mask_extracted_slots(
        {
            "phone_number": "+6281234567890",
            "customer_id": "0123456789",
            "survey_address": "Jalan Melati No. 10",
            "building_type": "rumah",
            "budget": 20_000_000,
        }
    )

    assert masked == {
        "phone_number": "+62812****7890",
        "customer_id": "012****789",
        "survey_address": "[alamat dimasking]",
        "building_type": "rumah",
        "budget": 20_000_000,
    }


def test_jsonl_logger_appends_one_valid_json_object_per_line(tmp_path: Path) -> None:
    logger = JsonlConversationLogger(tmp_path)
    event = ConversationTurnEvent(
        event_id="01K1A2B3C4D5E6F7G8H9J0001",
        timestamp=datetime(2026, 7, 29, 16, 0, tzinfo=UTC).isoformat(),
        conversation_id="01K1A2B3C4D5E6F7G8H9J0002",
        turn=1,
        sender="user",
        raw_text="nomor saya 081234567890",
        normalized_text="unsafe value should be replaced",
        predicted_intent=None,
        confidence=None,
        state_before="WELCOME",
        state_after="INFO_MODE",
        extracted_slots={"phone_number": "+6281234567890"},
        response_text="Silakan pilih topik.",
        model_version=None,
    )

    logger.append(event)
    logger.append(event)

    log_path = tmp_path / "conversations-2026-07-29.jsonl"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert all(json.loads(line)["event_id"] == event.event_id for line in lines)
    assert "081234567890" not in log_path.read_text(encoding="utf-8")
    assert json.loads(lines[0])["extracted_slots"] == {"phone_number": "+62812****7890"}
