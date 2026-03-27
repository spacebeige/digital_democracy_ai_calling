from __future__ import annotations

import re

from twilio.base.exceptions import TwilioException
from twilio.rest import Client

from app.config import (
    SMS_DEFAULT_COUNTRY_CODE,
    SMS_DRY_RUN,
    SMS_MMS_FALLBACK_TO_TEXT,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER,
)


NON_DIGIT_PATTERN = re.compile(r"[^0-9]")


def _twilio_message_url(message_sid: str | None) -> str | None:
    sid = (message_sid or "").strip()
    if not sid or not TWILIO_ACCOUNT_SID:
        return None
    return f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages/{sid}.json"


def _normalize_sms_number(phone: str) -> str:
    digits = NON_DIGIT_PATTERN.sub("", phone or "")
    if not digits:
        raise ValueError("Phone number must include digits")

    if phone.strip().startswith("+"):
        return f"+{digits}"

    if len(digits) == 10 and SMS_DEFAULT_COUNTRY_CODE.startswith("+"):
        return f"{SMS_DEFAULT_COUNTRY_CODE}{digits}"

    return f"+{digits}"


def build_ticket_sms_text(
    custom_text: str,
    ticket_id: str,
    session_id: str | None = None,
    qr_link: str | None = None,
) -> str:
    custom = (custom_text or "").strip()
    ticket = (ticket_id or "").strip()
    if not custom:
        raise ValueError("custom_text cannot be empty")
    if not ticket:
        raise ValueError("ticket_id cannot be empty")

    lines = [custom, f"Ticket ID: {ticket}"]
    if session_id and session_id.strip():
        lines.append(f"Session: {session_id.strip()}")
    if qr_link and qr_link.strip():
        lines.append("Click the link below to generate session QR")
        lines.append(f"Track Link: {qr_link.strip()}")
    return "\n".join(lines)


def _append_ticket_metadata(lines: list[str], metadata: dict | None) -> None:
    if not metadata:
        return

    ordered_keys = [
        ("id", "ID"),
        ("issue", "Issue"),
        ("location", "Location"),
        ("priority", "Priority"),
        ("status", "Status"),
        ("created_at", "Created At"),
        ("updated_at", "Updated At"),
    ]
    for key, label in ordered_keys:
        value = metadata.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            lines.append(f"{label}: {text}")


def _create_twilio_message(
    client: Client,
    to: str,
    body: str,
    media_url: str | None = None,
):
    payload = {
        "to": to,
        "from_": TWILIO_FROM_NUMBER,
        "body": body,
    }
    if media_url:
        payload["media_url"] = [media_url]
    return client.messages.create(**payload)


def send_ticket_sms(
    to: str,
    custom_text: str,
    ticket_id: str,
    media_url: str | None = None,
    session_id: str | None = None,
    qr_link: str | None = None,
    ticket_metadata: dict | None = None,
    dry_run: bool = False,
) -> dict:
    normalized_to = _normalize_sms_number(to)
    normalized_qr_link = (qr_link or "").strip() or None
    body_lines = build_ticket_sms_text(
        custom_text,
        ticket_id,
        session_id,
        qr_link=normalized_qr_link,
    ).split("\n")
    _append_ticket_metadata(body_lines, ticket_metadata)
    body = "\n".join(body_lines)

    normalized_media_url = (media_url or "").strip() or None

    effective_dry_run = dry_run or SMS_DRY_RUN
    if effective_dry_run:
        return {
            "success": True,
            "to": normalized_to,
            "ticket_id": ticket_id,
            "body": body,
            "qr_link": normalized_qr_link,
            "media_url": None,
            "status": "dry_run",
            "detail": "dry_run does not create a Twilio message link",
        }

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_FROM_NUMBER:
        raise RuntimeError("Twilio credentials are missing. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER")

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        message = _create_twilio_message(
            client=client,
            to=normalized_to,
            body=body,
            media_url=normalized_media_url,
        )
    except TwilioException as exc:
        if normalized_media_url and SMS_MMS_FALLBACK_TO_TEXT:
            try:
                fallback_message = _create_twilio_message(
                    client=client,
                    to=normalized_to,
                    body=body,
                    media_url=None,
                )
                twilio_url = _twilio_message_url(fallback_message.sid)
                return {
                    "success": True,
                    "to": normalized_to,
                    "ticket_id": ticket_id,
                    "body": body,
                    "qr_link": normalized_qr_link,
                    "media_url": twilio_url,
                    "status": fallback_message.status or "queued",
                    "sid": fallback_message.sid,
                    "detail": f"MMS failed and fallback to text SMS was used: {exc}",
                }
            except TwilioException as fallback_exc:
                return {
                    "success": False,
                    "to": normalized_to,
                    "ticket_id": ticket_id,
                    "body": body,
                    "qr_link": normalized_qr_link,
                    "media_url": None,
                    "status": "failed",
                    "detail": f"MMS failed: {exc}; text fallback failed: {fallback_exc}",
                }

        return {
            "success": False,
            "to": normalized_to,
            "ticket_id": ticket_id,
            "body": body,
            "qr_link": normalized_qr_link,
            "media_url": None,
            "status": "failed",
            "detail": str(exc),
        }

    twilio_url = _twilio_message_url(message.sid)

    return {
        "success": True,
        "to": normalized_to,
        "ticket_id": ticket_id,
        "body": body,
        "qr_link": normalized_qr_link,
        "media_url": twilio_url,
        "status": message.status or "queued",
        "sid": message.sid,
    }
