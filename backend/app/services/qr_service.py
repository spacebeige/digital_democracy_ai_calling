from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from urllib.parse import quote

import boto3
from botocore.exceptions import BotoCoreError, ClientError
import qrcode

from app.config import (
    AWS_ACCESS_KEY_ID,
    AWS_S3_BUCKET_NAME,
    AWS_S3_PUBLIC_BASE_URL,
    AWS_S3_QR_PREFIX,
    AWS_S3_REGION,
    AWS_SECRET_ACCESS_KEY,
    QR_IMAGE_DIR,
    USE_S3_FOR_QR,
)


def _sanitize_ticket_id(ticket_id: str) -> str:
    safe = (ticket_id or "").strip().replace(" ", "_")
    return "".join(ch for ch in safe if ch.isalnum() or ch in {"-", "_"}) or "ticket"


def _build_s3_public_url(object_key: str) -> str:
    base = (AWS_S3_PUBLIC_BASE_URL or "").strip().rstrip("/")
    encoded_key = quote(object_key)
    if base:
        return f"{base}/{encoded_key}"

    bucket = (AWS_S3_BUCKET_NAME or "").strip()
    region = (AWS_S3_REGION or "").strip() or "us-east-1"
    if region == "us-east-1":
        return f"https://{bucket}.s3.amazonaws.com/{encoded_key}"
    return f"https://{bucket}.s3.{region}.amazonaws.com/{encoded_key}"


def _upload_qr_to_s3(file_path: Path) -> str:
    bucket = (AWS_S3_BUCKET_NAME or "").strip()
    if not bucket:
        raise RuntimeError("AWS_S3_BUCKET_NAME is required when USE_S3_FOR_QR is true")

    if not (AWS_ACCESS_KEY_ID or "").strip() or not (AWS_SECRET_ACCESS_KEY or "").strip():
        raise RuntimeError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are required when USE_S3_FOR_QR is true")

    prefix = (AWS_S3_QR_PREFIX or "qr").strip().strip("/")
    object_key = f"{prefix}/{file_path.name}" if prefix else file_path.name

    client = boto3.client(
        "s3",
        region_name=(AWS_S3_REGION or "us-east-1").strip() or "us-east-1",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    try:
        client.upload_file(
            str(file_path),
            bucket,
            object_key,
            ExtraArgs={"ContentType": "image/png", "ACL": "public-read"},
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Failed to upload QR image to S3: {exc}")

    return _build_s3_public_url(object_key)


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


def generate_ticket_qr_media(
    ticket_id: str,
    session_id: str | None = None,
    qr_link: str | None = None,
    ticket_metadata: dict | None = None,
) -> tuple[Path, str | None]:
    image_path = generate_ticket_qr(
        ticket_id=ticket_id,
        session_id=session_id,
        qr_link=qr_link,
        ticket_metadata=ticket_metadata,
    )

    if USE_S3_FOR_QR:
        return image_path, _upload_qr_to_s3(image_path)

    return image_path, None
