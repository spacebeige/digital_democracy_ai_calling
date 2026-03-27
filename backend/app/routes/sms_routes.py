from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import QR_IMAGE_DIR, TWILIO_PUBLIC_BASE_URL
from app.schemas import SendTicketSMSRequest, SendTicketSMSResponse
from app.services.qr_service import generate_ticket_qr_media
from app.services.sms_service import send_ticket_sms


router = APIRouter(tags=["sms"])


def _build_public_media_url(image_path: Path) -> str:
    base_url = (TWILIO_PUBLIC_BASE_URL or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("TWILIO_PUBLIC_BASE_URL is required for MMS media_url")

    relative_name = image_path.name
    return f"{base_url}/public/qr/{relative_name}"


@router.post("/send-ticket", response_model=SendTicketSMSResponse)
def send_ticket(payload: SendTicketSMSRequest) -> SendTicketSMSResponse:
    try:
        ticket_metadata = {
            "id": payload.id,
            "issue": payload.issue,
            "location": payload.location,
            "priority": payload.priority,
            "status": payload.status,
            "created_at": payload.created_at,
            "updated_at": payload.updated_at,
        }

        media_url = None
        if payload.include_qr_image:
            if not payload.qr_link or not payload.qr_link.strip():
                raise ValueError("qr_link is required when include_qr_image is true")
            image_path, s3_media_url = generate_ticket_qr_media(
                payload.ticket_id,
                payload.session_id,
                qr_link=payload.qr_link,
                ticket_metadata=ticket_metadata,
            )
            if QR_IMAGE_DIR not in image_path.parents and image_path.parent != QR_IMAGE_DIR:
                raise RuntimeError("Generated QR path is invalid")
            media_url = s3_media_url or _build_public_media_url(image_path)

        result = send_ticket_sms(
            to=payload.to,
            custom_text=payload.custom_text,
            ticket_id=payload.ticket_id,
            session_id=payload.session_id,
            qr_link=payload.qr_link,
            ticket_metadata=ticket_metadata,
            media_url=media_url,
            dry_run=payload.dry_run,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"SMS dispatch failed: {exc}")
