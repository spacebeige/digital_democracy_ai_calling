#!/usr/bin/env python3
"""
SMS NOTIFIER MODULE
===================
Sends SMS notifications via Twilio for complaints and status updates.

Features:
- Send complaint acknowledgment SMS
- Send status update SMS
- QR code generation with tracking link
- Dry-run mode for testing
- Multi-language SMS support
"""

import os
import logging
from typing import Optional, Dict
from datetime import datetime
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# ============================================================================
# SMS TEMPLATES (Multi-language)
# ============================================================================

SMS_TEMPLATES = {
    "complaint_received_en": "Your grievance #{complaint_id} has been received. Department: {department}. Urgency: {urgency}. Status: http://bit.ly/{tracking_id}",
    
    "complaint_received_hi": "आपकी शिकायत #{complaint_id} प्राप्त हुई। विभाग: {department}। आपातकाल: {urgency}। स्थिति: http://bit.ly/{tracking_id}",
    
    "status_update_en": "Update on complaint #{complaint_id}: {status}. Track here: http://bit.ly/{tracking_id}",
    
    "status_update_hi": "शिकायत #{complaint_id} पर अपडेट: {status}। यहाँ ट्रैक करें: http://bit.ly/{tracking_id}",
    
    "escalated_en": "Your grievance #{complaint_id} has been escalated to {department}. Reference: {tracking_id}",
    
    "escalated_hi": "आपकी शिकायत #{complaint_id} को {department} में स्थानांतरित कर दिया गया है। संदर्भ: {tracking_id}",
}

DEPARTMENT_NAMES = {
    "fire": {"en": "Fire Department", "hi": "अग्निशमन विभाग"},
    "police": {"en": "Police Department", "hi": "पुलिस विभाग"},
    "health": {"en": "Health Department", "hi": "स्वास्थ्य विभाग"},
    "water": {"en": "Water Department", "hi": "जल विभाग"},
    "electricity": {"en": "Electricity Department", "hi": "विद्युत विभाग"},
    "general": {"en": "General Query", "hi": "सामान्य प्रश्न"},
}

URGENCY_NAMES = {
    "critical": {"en": "CRITICAL", "hi": "गंभीर"},
    "high": {"en": "HIGH", "hi": "उच्च"},
    "medium": {"en": "MEDIUM", "hi": "माध्यम"},
    "low": {"en": "LOW", "hi": "कम"},
}


class TwilioSMSNotifier:
    """Send SMS notifications via Twilio."""
    
    def __init__(self):
        """Initialize Twilio SMS notifier."""
        try:
            from twilio.rest import Client
            self.twilio_client = Client
            self.twilio_available = True
        except ImportError:
            logger.warning("twilio not installed. Install with: pip install twilio")
            self.twilio_available = False
        
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER")
        self.dry_run = os.getenv("SMS_DRY_RUN", "false").lower() == "true"
        self.base_url = os.getenv("TWILIO_PUBLIC_BASE_URL", "")
        self.country_code = os.getenv("SMS_DEFAULT_COUNTRY_CODE", "+91")
        
        if self.twilio_available and self.account_sid and self.auth_token:
            self.client = self.twilio_client(self.account_sid, self.auth_token)
            logger.info(f"✓ Twilio SMS notifier initialized (Dry-run: {self.dry_run})")
        else:
            self.client = None
            logger.warning("Twilio SMS notifier not fully configured")
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone number with country code."""
        # Remove any non-digit characters
        phone = ''.join(c for c in phone if c.isdigit())
        
        # If already has country code, return as-is
        if phone.startswith(self.country_code.lstrip('+')):
            return f"+{phone}"
        
        # Add country code if not present
        if not phone.startswith('91'):  # India's code without +
            phone = self.country_code.lstrip('+') + phone
        
        return f"+{phone}"
    
    def send_complaint_acknowledgment(
        self,
        phone_number: str,
        complaint_id: str,
        department: str,
        urgency: str,
        language: str = "en",
        transcript: str = ""
    ) -> Dict:
        """Send complaint acknowledgment SMS."""
        
        if not self.client and not self.dry_run:
            logger.warning("Twilio client not available")
            return {"success": False, "error": "Twilio not configured"}
        
        try:
            # Generate tracking ID
            tracking_id = complaint_id[:8].lower()
            
            # Get message template
            template_key = f"complaint_received_{language}"
            template = SMS_TEMPLATES.get(
                template_key,
                SMS_TEMPLATES.get("complaint_received_en")  # Fallback
            )
            
            # Get department and urgency names
            dept_name = DEPARTMENT_NAMES.get(department, {}).get(language, department)
            urgency_name = URGENCY_NAMES.get(urgency.lower(), {}).get(language, urgency)
            
            # Format message
            message_text = template.format(
                complaint_id=complaint_id[:8],
                department=dept_name,
                urgency=urgency_name,
                tracking_id=tracking_id
            )
            
            # Ensure message is not too long
            if len(message_text) > 160:
                message_text = message_text[:157] + "..."
            
            phone = self._format_phone_number(phone_number)
            
            # Log or send
            if self.dry_run:
                logger.info(f"[DRY-RUN] SMS to {phone}: {message_text}")
                return {
                    "success": True,
                    "dry_run": True,
                    "phone": phone,
                    "message": message_text,
                    "complaint_id": complaint_id
                }
            else:
                # Actually send via Twilio
                message = self.client.messages.create(
                    body=message_text,
                    from_=self.from_number,
                    to=phone
                )
                logger.info(f"✓ SMS sent to {phone} (SID: {message.sid})")
                return {
                    "success": True,
                    "phone": phone,
                    "message_sid": message.sid,
                    "complaint_id": complaint_id,
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"✗ Failed to send SMS: {e}")
            return {"success": False, "error": str(e)}
    
    def send_status_update(
        self,
        phone_number: str,
        complaint_id: str,
        status: str,
        language: str = "en"
    ) -> Dict:
        """Send status update SMS."""
        
        if not self.client and not self.dry_run:
            return {"success": False, "error": "Twilio not configured"}
        
        try:
            tracking_id = complaint_id[:8].lower()
            
            template_key = f"status_update_{language}"
            template = SMS_TEMPLATES.get(
                template_key,
                SMS_TEMPLATES.get("status_update_en")
            )
            
            message_text = template.format(
                complaint_id=complaint_id[:8],
                status=status[:30],
                tracking_id=tracking_id
            )
            
            if len(message_text) > 160:
                message_text = message_text[:157] + "..."
            
            phone = self._format_phone_number(phone_number)
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Status SMS to {phone}: {message_text}")
                return {
                    "success": True,
                    "dry_run": True,
                    "phone": phone,
                    "message": message_text
                }
            else:
                message = self.client.messages.create(
                    body=message_text,
                    from_=self.from_number,
                    to=phone
                )
                logger.info(f"✓ Status SMS sent to {phone}")
                return {
                    "success": True,
                    "phone": phone,
                    "message_sid": message.sid,
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"✗ Failed to send status SMS: {e}")
            return {"success": False, "error": str(e)}
    
    def send_escalation_notification(
        self,
        phone_number: str,
        complaint_id: str,
        new_department: str,
        language: str = "en"
    ) -> Dict:
        """Send SMS when complaint is escalated."""
        
        if not self.client and not self.dry_run:
            return {"success": False, "error": "Twilio not configured"}
        
        try:
            tracking_id = complaint_id[:8].lower()
            
            template_key = f"escalated_{language}"
            template = SMS_TEMPLATES.get(
                template_key,
                SMS_TEMPLATES.get("escalated_en")
            )
            
            dept_name = DEPARTMENT_NAMES.get(new_department, {}).get(language, new_department)
            
            message_text = template.format(
                complaint_id=complaint_id[:8],
                department=dept_name,
                tracking_id=tracking_id
            )
            
            if len(message_text) > 160:
                message_text = message_text[:157] + "..."
            
            phone = self._format_phone_number(phone_number)
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Escalation SMS to {phone}: {message_text}")
                return {"success": True, "dry_run": True, "phone": phone}
            else:
                message = self.client.messages.create(
                    body=message_text,
                    from_=self.from_number,
                    to=phone
                )
                logger.info(f"✓ Escalation SMS sent to {phone}")
                return {"success": True, "phone": phone, "message_sid": message.sid}
        
        except Exception as e:
            logger.error(f"✗ Failed to send escalation SMS: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_tracking_url(
        self,
        complaint_id: str,
        session_id: str
    ) -> str:
        """Generate tracking URL for complaint status."""
        
        if not self.base_url:
            return f"/complaints/{complaint_id}/status"
        
        params = {
            "id": complaint_id,
            "session": session_id,
            "ts": datetime.now().timestamp()
        }
        
        return f"{self.base_url}/complaints/track?{urlencode(params)}"


def create_sms_notifier() -> Optional[TwilioSMSNotifier]:
    """Factory function to create SMS notifier instance."""
    try:
        notifier = TwilioSMSNotifier()
        return notifier if notifier.client or notifier.dry_run else None
    except Exception as e:
        logger.error(f"Failed to create SMS notifier: {e}")
        return None


# ============================================================================
# INTEGRATION WITH COMPLAINT PIPELINE
# ============================================================================

def notify_complaint_received(
    complaint_data: Dict,
    phone_number: str,
    language: str = "en"
) -> Dict:
    """Notify user that complaint has been received."""
    
    notifier = create_sms_notifier()
    if not notifier:
        logger.warning("SMS notifier not available")
        return {"success": False, "error": "SMS notifier not configured"}
    
    result = notifier.send_complaint_acknowledgment(
        phone_number=phone_number,
        complaint_id=complaint_data.get("session_id", "UNKNOWN"),
        department=complaint_data.get("department_assigned", "general"),
        urgency=complaint_data.get("urgency_level", "low"),
        language=language,
        transcript=complaint_data.get("transcript", "")
    )
    
    return result


if __name__ == "__main__":
    # Test SMS notifier
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("\n🧪 Testing SMS Notifier Module\n")
    print("=" * 60)
    
    # Create notifier
    notifier = TwilioSMSNotifier()
    
    # Test 1: Complaint acknowledgment (English)
    print("\n📝 Test 1: Complaint Acknowledgment (English)")
    print("-" * 60)
    result = notifier.send_complaint_acknowledgment(
        phone_number="9876543210",
        complaint_id="COMP-001",
        department="fire",
        urgency="critical",
        language="en"
    )
    print(f"Result: {result}\n")
    
    # Test 2: Complaint acknowledgment (Hindi)
    print("📝 Test 2: Complaint Acknowledgment (Hindi)")
    print("-" * 60)
    result = notifier.send_complaint_acknowledgment(
        phone_number="9876543210",
        complaint_id="COMP-002",
        department="police",
        urgency="high",
        language="hi"
    )
    print(f"Result: {result}\n")
    
    # Test 3: Status update
    print("📝 Test 3: Status Update")
    print("-" * 60)
    result = notifier.send_status_update(
        phone_number="9876543210",
        complaint_id="COMP-001",
        status="Being processed by Fire Dept",
        language="en"
    )
    print(f"Result: {result}\n")
    
    # Test 4: Escalation notification
    print("📝 Test 4: Escalation Notification")
    print("-" * 60)
    result = notifier.send_escalation_notification(
        phone_number="9876543210",
        complaint_id="COMP-001",
        new_department="police",
        language="hi"
    )
    print(f"Result: {result}\n")
    
    print("=" * 60)
    print("✅ SMS Notifier tests complete\n")
