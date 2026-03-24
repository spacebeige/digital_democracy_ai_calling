from __future__ import annotations

from pathlib import Path

import qrcode

from app.config import QR_IMAGE_DIR


def _safe_fragment(value: str) -> str:
    return "".join(char for char in value if char.isalnum() or char in {"-", "_"})[:64]


def generate_ticket_qr(
    ticket_id: str,
    session_id: str | None = None,
    qr_link: str | None = None,
    ticket_metadata: dict | None = None,
) -> Path:
    QR_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    ticket_part = _safe_fragment(ticket_id) or "ticket"
    session_part = _safe_fragment(session_id or "session")
    filename = f"{ticket_part}-{session_part}.png"
    image_path = QR_IMAGE_DIR / filename

    if qr_link and qr_link.strip():
        payload = qr_link.strip()
    else:
        payload = {
            "ticket_id": ticket_id,
            "session_id": session_id,
        }
        if ticket_metadata:
            payload.update({k: v for k, v in ticket_metadata.items() if v is not None})

    qr = qrcode.QRCode(version=2, box_size=8, border=2)
    qr.add_data(str(payload))
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    image.save(image_path)

    return image_path
