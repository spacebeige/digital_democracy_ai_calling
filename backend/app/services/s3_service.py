"""
AWS S3 Service for QR Code Storage and Management
"""

from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from app.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_S3_BUCKET_NAME,
    AWS_S3_REGION,
    AWS_S3_UPLOAD_DIR,
    USE_S3_FOR_QR,
)


def get_s3_client():
    """Create and return a boto3 S3 client."""
    if not USE_S3_FOR_QR:
        raise RuntimeError("S3 is not configured. Set USE_S3_FOR_QR=true and AWS credentials in .env")
    
    return boto3.client(
        "s3",
        region_name=AWS_S3_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def upload_qr_to_s3(image_bytes: bytes, ticket_id: str) -> str:
    """
    Upload QR code image to AWS S3 and return the public URL.
    
    Args:
        image_bytes: QR code image as bytes
        ticket_id: Ticket identifier for filename
    
    Returns:
        Public S3 URL of the uploaded image
    
    Raises:
        RuntimeError: If S3 is not configured or upload fails
    """
    if not USE_S3_FOR_QR:
        raise RuntimeError("S3 storage is not enabled. Configure AWS credentials in .env")
    
    try:
        s3_client = get_s3_client()
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{AWS_S3_UPLOAD_DIR}/qr_{ticket_id}_{timestamp}.png"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=AWS_S3_BUCKET_NAME,
            Key=filename,
            Body=image_bytes,
            ContentType="image/png",
            ACL="public-read",  # Make it publicly readable
        )
        
        # Generate public URL
        s3_url = f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_S3_REGION}.amazonaws.com/{filename}"
        
        return s3_url
    
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_msg = e.response["Error"]["Message"]
        raise RuntimeError(f"S3 upload failed: {error_code} - {error_msg}")
    except Exception as e:
        raise RuntimeError(f"S3 upload error: {str(e)}")


def delete_qr_from_s3(s3_url: str) -> bool:
    """
    Delete a QR code image from S3.
    
    Args:
        s3_url: S3 URL of the image to delete
    
    Returns:
        True if successful, False otherwise
    """
    if not USE_S3_FOR_QR:
        return False
    
    try:
        # Extract key from URL: https://bucket.s3.region.amazonaws.com/key
        if f"{AWS_S3_BUCKET_NAME}.s3" not in s3_url:
            return False
        
        key = s3_url.split(f"{AWS_S3_BUCKET_NAME}.s3.{AWS_S3_REGION}.amazonaws.com/")[-1]
        
        s3_client = get_s3_client()
        s3_client.delete_object(Bucket=AWS_S3_BUCKET_NAME, Key=key)
        
        return True
    
    except Exception as e:
        print(f"S3 deletion error: {str(e)}")
        return False


def test_s3_connection() -> bool:
    """Test if S3 connection is working."""
    if not USE_S3_FOR_QR:
        return False
    
    try:
        s3_client = get_s3_client()
        s3_client.head_bucket(Bucket=AWS_S3_BUCKET_NAME)
        return True
    except Exception:
        return False
