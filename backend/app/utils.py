"""
Utility functions for ticket generation and priority detection
"""
import random
import string
from datetime import datetime


def generate_ticket_id() -> str:
    """
    Generate a unique ticket ID in format: TCK + timestamp + random chars
    Example: TCK1234567890ABCD
    
    Returns:
        str: Unique ticket ID
    """
    timestamp = str(int(datetime.utcnow().timestamp()))[-6:]  # Last 6 digits of timestamp
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"TCK{timestamp}{random_suffix}"


def detect_priority(issue: str) -> str:
    """
    Detect priority level based on keywords in the issue description
    
    Priority rules:
    - HIGH: Contains "flood", "fire", "accident"
    - LOW: Contains "garbage", "waste"
    - MEDIUM: Default
    
    Args:
        issue (str): The issue description
        
    Returns:
        str: Priority level (LOW, MEDIUM, HIGH)
    """
    issue_lower = issue.lower()
    
    # High priority keywords
    high_priority_keywords = ["flood", "fire", "accident", "emergency", "critical"]
    for keyword in high_priority_keywords:
        if keyword in issue_lower:
            return "HIGH"
    
    # Low priority keywords
    low_priority_keywords = ["garbage", "waste", "litter", "minor"]
    for keyword in low_priority_keywords:
        if keyword in issue_lower:
            return "LOW"
    
    # Default to MEDIUM
    return "MEDIUM"


# State machine transitions
VALID_TRANSITIONS = {
    "OPEN": ["ASSIGNED"],
    "ASSIGNED": ["IN_PROGRESS"],
    "IN_PROGRESS": ["RESOLVED"],
    "RESOLVED": ["CLOSED", "REOPENED"],
    "REOPENED": ["IN_PROGRESS"],
    "CLOSED": []  # Final state, no transitions allowed
}


def is_valid_transition(current_status: str, new_status: str) -> bool:
    """
    Validate if a status transition is allowed
    
    Args:
        current_status (str): Current ticket status
        new_status (str): Desired new status
        
    Returns:
        bool: True if transition is valid, False otherwise
    """
    if current_status not in VALID_TRANSITIONS:
        return False
    return new_status in VALID_TRANSITIONS[current_status]


def simulate_sms_notification(ticket_id: str) -> None:
    """
    Simulate SMS notification when a ticket is created
    
    Args:
        ticket_id (str): The created ticket ID
    """
    print(f"📱 SMS: Your complaint is registered. Ticket ID: {ticket_id}")
