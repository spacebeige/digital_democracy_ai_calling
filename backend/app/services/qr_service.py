from pathlib import Path
import json
import io
import qrcode
from datetime import datetime

from app.config import QR_IMAGE_DIR, USE_S3_FOR_QR


def generate_ticket_qr(
    ticket_id: str,
    session_id: str | None,
    qr_link: str | None = None,
    ticket_metadata: dict | None = None,
) -> str:
    """
    Generate a QR code image for a ticket and upload to S3 if configured.
    
    Args:
        ticket_id: Unique ticket identifier
        session_id: Session identifier (optional)
        qr_link: URL to encode in the QR code (optional)
        ticket_metadata: Additional metadata to embed (optional)
    
    Returns:
        URL of the generated QR image (S3 URL if S3 enabled, local path otherwise)
    """
    # Prepare QR data
    qr_data = {
        "ticket_id": ticket_id,
    }
    
    if session_id:
        qr_data["session_id"] = session_id
    
    if ticket_metadata:
        qr_data["metadata"] = ticket_metadata
    
    if qr_link:
        qr_data["link"] = qr_link
    
    # Use the QR link if provided, otherwise use JSON data
    qr_content = qr_link if qr_link else json.dumps(qr_data)
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # If S3 is enabled, upload to S3
    if USE_S3_FOR_QR:
        try:
            from app.services.s3_service import upload_qr_to_s3
            
            # Convert image to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            
            # Upload to S3 and return URL
            s3_url = upload_qr_to_s3(img_bytes.getvalue(), ticket_id)
            return s3_url
        
        except Exception as e:
            print(f"S3 upload failed ({str(e)}), falling back to local storage")
            # Fall back to local storage if S3 fails
    
    # Save locally as fallback or if S3 not configured
    QR_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ticket_{ticket_id}_{timestamp}.png"
    image_path = QR_IMAGE_DIR / filename
    
    img.save(image_path)
    
    # Return local path (should be served via static files)
    return str(image_path)
