from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

import qrcode

from app.config import QR_IMAGE_DIR


def _sanitize_ticket_id(ticket_id: str) -> str:
    safe = (ticket_id or "").strip().replace(" ", "_")
    return "".join(ch for ch in safe if ch.isalnum() or ch in {"-", "_"}) or "ticket"


def generate_ticket_qr(
    ticket_id: str,
    session_id: str | None = None,
    qr_link: str | None = None,
    ticket_metadata: dict | None = None,
) -> Path:
    QR_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "ticket_id": (ticket_id or "").strip(),
        "session_id": (session_id or "").strip() or None,
    }
    if ticket_metadata:
        payload["metadata"] = ticket_metadata

    qr_data = (qr_link or "").strip() or json.dumps(payload, ensure_ascii=False)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_ticket = _sanitize_ticket_id(ticket_id)
    file_path = QR_IMAGE_DIR / f"ticket_{safe_ticket}_{timestamp}.png"
    image.save(file_path)
    return file_path
