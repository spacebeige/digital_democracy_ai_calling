from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import QR_IMAGE_DIR, TWILIO_PUBLIC_BASE_URL, USE_S3_FOR_QR
from app.schemas import SendTicketSMSRequest, SendTicketSMSResponse
from app.services.qr_service import generate_ticket_qr
from app.services.sms_service import send_ticket_sms


router = APIRouter(tags=["sms"])


def _build_public_media_url(image_path_or_url: str) -> str:
    """
    Build public media URL for Twilio.
    If S3 is enabled, image_path_or_url is already a full S3 URL.
    Otherwise, it's a local path that needs to be converted.
    """
    # If it's already a URL (from S3), return it as-is
    if image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://"):
        return image_path_or_url
    
    # Otherwise it's a local path, convert to public URL
    if not TWILIO_PUBLIC_BASE_URL:
        raise RuntimeError("TWILIO_PUBLIC_BASE_URL is required for local media_url or use S3 instead")
    
    base_url = TWILIO_PUBLIC_BASE_URL.strip().rstrip("/")
    relative_name = Path(image_path_or_url).name
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
            
            # Generate QR (returns S3 URL if S3 enabled, local path otherwise)
            image_url_or_path = generate_ticket_qr(
                payload.ticket_id,
                payload.session_id,
                qr_link=payload.qr_link,
                ticket_metadata=ticket_metadata,
            )
            
            # Convert to public URL if needed
            media_url = _build_public_media_url(image_url_or_path)
            
            # If using local storage, validate path
            if not (image_url_or_path.startswith("http://") or image_url_or_path.startswith("https://")):
                image_path = Path(image_url_or_path)
                if QR_IMAGE_DIR not in image_path.parents and image_path.parent != QR_IMAGE_DIR:
                    raise RuntimeError("Generated QR path is invalid")

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
