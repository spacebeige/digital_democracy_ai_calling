"""
Policy Management & Display Module
===================================
Provides policies for:
- Grievance handling procedures
- Escalation rules
- Response SLAs
- Department guidelines
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Optional


class PolicyType(Enum):
    """Types of policies available."""
    GRIEVANCE_HANDLING = "grievance_handling"
    ESCALATION = "escalation"
    SLA = "service_level_agreement"
    DEPARTMENT_GUIDELINES = "department_guidelines"
    RESPONSE_TEMPLATES = "response_templates"


@dataclass
class EscalationPolicy:
    """Escalation rules based on grievance characteristics."""
    trigger: str  # What triggers escalation
    from_level: str  # Current level
    to_level: str  # Escalate to
    timeframe_minutes: int  # When to escalate
    responsible_team: str  # Which team handles escalation
    action_required: str  # What should be done
    
    def to_dict(self):
        return asdict(self)


@dataclass
class SLAPolicy:
    """Service Level Agreement for different departments."""
    department: str
    urgency_level: str  # CRITICAL, HIGH, MEDIUM, LOW
    first_response_minutes: int
    resolution_minutes: int
    escalation_point_minutes: int
    team_size: int
    
    def to_dict(self):
        return asdict(self)


@dataclass
class ResponseTemplate:
    """Pre-approved response templates for different scenarios."""
    scenario: str  # e.g., "fire_emergency", "power_outage"
    language: str  # en, hi, mr, ta, te, etc.
    response_text: str
    required_info: List[str]  # Info to collect from user
    next_action: str  # What happens after response
    
    def to_dict(self):
        return asdict(self)


@dataclass
class DepartmentGuideline:
    """Guidelines for handling specific department complaints."""
    department: str
    complaint_types: List[str]
    required_documents: List[str]
    processing_steps: List[str]
    contact_escalation_point: str
    common_issues: List[str]
    
    def to_dict(self):
        return asdict(self)


# ─────────────────────────────────────────────────────────────────
# ESCALATION POLICIES
# ─────────────────────────────────────────────────────────────────

ESCALATION_POLICIES = [
    EscalationPolicy(
        trigger="anger_score > 0.8 and urgency == CRITICAL",
        from_level="tier_1_operator",
        to_level="tier_2_supervisor",
        timeframe_minutes=5,
        responsible_team="Grievance Supervisor",
        action_required="Immediate call to user, escalate to senior management",
    ),
    EscalationPolicy(
        trigger="no_response_since_30_minutes and urgency == HIGH",
        from_level="tier_1_operator",
        to_level="tier_2_supervisor",
        timeframe_minutes=30,
        responsible_team="Supervisor",
        action_required="Call user, check with assigned department, update ticket",
    ),
    EscalationPolicy(
        trigger="anger_score > 0.6 and stress > 0.7",
        from_level="tier_1_operator",
        to_level="tier_2_supervisor",
        timeframe_minutes=10,
        responsible_team="Intervention Team",
        action_required="Call user with empathy script, validate complaint",
    ),
    EscalationPolicy(
        trigger="multiple_calls_same_issue > 2",
        from_level="tier_1_operator",
        to_level="management",
        timeframe_minutes=60,
        responsible_team="Case Manager",
        action_required="Full case review, direct contact with department",
    ),
]

# ─────────────────────────────────────────────────────────────────
# SLA POLICIES
# ─────────────────────────────────────────────────────────────────

SLA_POLICIES = [
    SLAPolicy(
        department="fire",
        urgency_level="CRITICAL",
        first_response_minutes=1,
        resolution_minutes=5,
        escalation_point_minutes=2,
        team_size=5,
    ),
    SLAPolicy(
        department="police",
        urgency_level="CRITICAL",
        first_response_minutes=1,
        resolution_minutes=15,
        escalation_point_minutes=5,
        team_size=4,
    ),
    SLAPolicy(
        department="electricity",
        urgency_level="HIGH",
        first_response_minutes=30,
        resolution_minutes=120,
        escalation_point_minutes=90,
        team_size=3,
    ),
    SLAPolicy(
        department="water",
        urgency_level="HIGH",
        first_response_minutes=60,
        resolution_minutes=240,
        escalation_point_minutes=180,
        team_size=2,
    ),
    SLAPolicy(
        department="municipal",
        urgency_level="MEDIUM",
        first_response_minutes=240,
        resolution_minutes=1440,
        escalation_point_minutes=720,
        team_size=2,
    ),
    SLAPolicy(
        department="gas",
        urgency_level="HIGH",
        first_response_minutes=15,
        resolution_minutes=60,
        escalation_point_minutes=30,
        team_size=4,
    ),
]

# ─────────────────────────────────────────────────────────────────
# RESPONSE TEMPLATES
# ─────────────────────────────────────────────────────────────────

RESPONSE_TEMPLATES = [
    ResponseTemplate(
        scenario="fire_emergency",
        language="en",
        response_text="🚨 EMERGENCY: Fire services are being alerted immediately. Please evacuate to a safe location and await emergency personnel. Do not use elevators.",
        required_info=["exact_location", "number_of_people", "any_injuries"],
        next_action="Connect to fire_department_101",
    ),
    ResponseTemplate(
        scenario="fire_emergency",
        language="hi",
        response_text="🚨 आपातकाल: अग्निशमन सेवाएं तुरंत सतर्क की जा रही हैं। कृपया सुरक्षित स्थान पर जाएं और बाहर निकलें। लिफ्ट का उपयोग न करें।",
        required_info=["exact_location", "people_count", "injuries"],
        next_action="Connect to fire_department_101",
    ),
    ResponseTemplate(
        scenario="power_outage",
        language="en",
        response_text="Your electricity complaint has been registered. Our technicians will inspect your area within 2 hours. You can check status using this ticket number.",
        required_info=["area_name", "is_neighborhood_affected", "backup_available"],
        next_action="Assign to MSEDCL lineman, set timer for follow-up",
    ),
    ResponseTemplate(
        scenario="water_shortage",
        language="en",
        response_text="Your water supply complaint is being forwarded to the Water Board. Normal supply should resume within 24 hours. Tanker assistance available if needed.",
        required_info=["area_name", "days_no_water", "household_size"],
        next_action="Notify water supply department",
    ),
    ResponseTemplate(
        scenario="theft_report",
        language="en",
        response_text="Your complaint has been registered with the local police station. An FIR will be filed within 24 hours. Keep this ticket number for reference.",
        required_info=["item_stolen", "approximate_value", "location_of_theft"],
        next_action="Forward to police, generate FIR",
    ),
]

# ─────────────────────────────────────────────────────────────────
# DEPARTMENT GUIDELINES
# ─────────────────────────────────────────────────────────────────

DEPARTMENT_GUIDELINES = [
    DepartmentGuideline(
        department="electricity",
        complaint_types=["no_power", "high_bill", "meter_issue", "frequent_outage"],
        required_documents=["meter_photo", "bill_copy", "id_proof"],
        processing_steps=[
            "1. Verify meter number and connection",
            "2. Check outage status in system",
            "3. Dispatch lineman if needed",
            "4. Provide ETA to customer",
            "5. Follow up after 24 hours",
        ],
        contact_escalation_point="MSEDCL Circle Office - 1912",
        common_issues=[
            "Temporary outage due to maintenance",
            "Overload in area",
            "Meter malfunction",
            "Bill calculation error",
        ],
    ),
    DepartmentGuideline(
        department="water",
        complaint_types=["no_water", "low_pressure", "leak", "water_quality"],
        required_documents=["connection_photo", "area_map", "id_proof"],
        processing_steps=[
            "1. Verify connection details",
            "2. Check supply status in area",
            "3. Identify issue type",
            "4. Dispatch repair team",
            "5. Verify resolution",
        ],
        contact_escalation_point="Water Board - 1916",
        common_issues=[
            "Scheduled maintenance shutdown",
            "Leak in main pipeline",
            "Pressure regulation issue",
            "Meter blockage",
        ],
    ),
    DepartmentGuideline(
        department="fire",
        complaint_types=["active_fire", "gas_leak", "chemical_spill", "fire_safety"],
        required_documents=["incident_photo", "witness_contact"],
        processing_steps=[
            "1. Confirm emergency status",
            "2. Alert fire brigade immediately",
            "3. Provide location coordinates",
            "4. Keep user on line",
            "5. Provide safety instructions",
        ],
        contact_escalation_point="Fire Department - 101",
        common_issues=[
            "Active fire situation",
            "Potential gas hazard",
            "Chemical emergency",
        ],
    ),
    DepartmentGuideline(
        department="police",
        complaint_types=["theft", "assault", "harassment", "safety_concern"],
        required_documents=["fir_details", "witness_list", "evidence_description"],
        processing_steps=[
            "1. Take full complaint details",
            "2. Verify location and time",
            "3. Identify victim and accused",
            "4. Forward to nearest police station",
            "5. Provide FIR number",
        ],
        contact_escalation_point="Police Station - 100 or 112",
        common_issues=[
            "Theft in progress",
            "Assault near location",
            "Harassment at residence",
        ],
    ),
]

# ─────────────────────────────────────────────────────────────────
# GRIEVANCE HANDLING PROCEDURES
# ─────────────────────────────────────────────────────────────────

GRIEVANCE_HANDLING_PROCEDURE = {
    "intake_phase": {
        "duration_minutes": 15,
        "steps": [
            "1. Greet user in their language",
            "2. Record basic information (name, contact, location)",
            "3. Listen to complaint without interruption",
            "4. Extract key details and keywords",
            "5. Assign urgency level",
        ],
        "quality_checks": [
            "Is user language preference noted?",
            "Is location verified?",
            "Are phone/email captured?",
        ],
    },
    "analysis_phase": {
        "duration_minutes": 5,
        "steps": [
            "1. Classify complaint type (NLP analysis)",
            "2. Detect emotion state",
            "3. Determine departmental routing",
            "4. Calculate SLA",
            "5. Set escalation triggers",
        ],
        "quality_checks": [
            "Is classification accurate?",
            "Are escalation conditions met?",
        ],
    },
    "routing_phase": {
        "duration_minutes": 10,
        "steps": [
            "1. Identify correct department",
            "2. Prepare complaint summary",
            "3. Generate ticket number",
            "4. Notify receiving department",
            "5. Set follow-up reminder",
        ],
        "quality_checks": [
            "Is ticket number generated?",
            "Has department acknowledged?",
        ],
    },
    "response_phase": {
        "duration_minutes": "variable by SLA",
        "steps": [
            "1. Generate appropriate response",
            "2. Provide ticket tracking info",
            "3. Set expectation timeline",
            "4. Offer assistance options",
            "5. Close ticket or mark for follow-up",
        ],
        "quality_checks": [
            "Did user understand resolution?",
            "Is follow-up scheduled?",
        ],
    },
}


def get_escalation_policy(scenario: str) -> Optional[EscalationPolicy]:
    """Get escalation policy matching scenario."""
    for policy in ESCALATION_POLICIES:
        if policy.trigger.lower() in scenario.lower():
            return policy
    return None


def get_sla_policy(department: str, urgency: str) -> Optional[SLAPolicy]:
    """Get SLA policy for department and urgency level."""
    for policy in SLA_POLICIES:
        if policy.department == department and policy.urgency_level == urgency:
            return policy
    return None


def get_response_template(scenario: str, language: str = "en") -> Optional[ResponseTemplate]:
    """Get response template for scenario and language."""
    for template in RESPONSE_TEMPLATES:
        if template.scenario == scenario and template.language == language:
            return template
    return None


def get_department_guideline(department: str) -> Optional[DepartmentGuideline]:
    """Get guidelines for specific department."""
    for guideline in DEPARTMENT_GUIDELINES:
        if guideline.department == department:
            return guideline
    return None
