"""
Escalation Engine Module
========================
Handles automatic escalation logic based on grievance characteristics.

Escalation Triggers:
1. Anger score > 0.8 + CRITICAL urgency → Immediate supervisor escalation
2. No response > 30 minutes + HIGH urgency → Escalation
3. Anger > 0.6 + Stress > 0.7 → Operator intervention
4. Multiple calls for same issue → Management review
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from models.grievance_models import AnalyticalModel, UrgencyLevel
from core.policies import ESCALATION_POLICIES, get_escalation_policy


@dataclass
class EscalationTrigger:
    """An escalation rule that was triggered."""
    trigger_name: str
    trigger_condition: str
    from_level: str
    to_level: str
    timeframe_minutes: int
    action_required: str
    triggered: bool
    reason: str


class EscalationEngine:
    """
    Determines if and how grievance should be escalated.
    
    Escalation Levels:
    1. Tier 1: Frontline operator
    2. Tier 2: Supervisor/team lead
    3. Tier 3: Department manager
    4. Tier 4: Senior management/government liaison
    """
    
    def __init__(self):
        """Initialize escalation engine."""
        self.escalation_policies = ESCALATION_POLICIES
    
    def check_escalation(
        self,
        analytical_model: AnalyticalModel,
        time_since_filing_minutes: int = 0,
        num_previous_calls: int = 0,
    ) -> List[EscalationTrigger]:
        """
        Check all escalation conditions.
        
        Args:
            analytical_model: Complete grievance analysis
            time_since_filing_minutes: How long grievance has been open
            num_previous_calls: Number of previous calls for same issue
            
        Returns:
            List of triggered escalation rules
        """
        triggered = []
        
        # Check each escalation policy
        triggered.append(self._check_anger_escalation(analytical_model))
        triggered.append(self._check_timeout_escalation(analytical_model, time_since_filing_minutes))
        triggered.append(self._check_stress_escalation(analytical_model))
        triggered.append(self._check_repeated_calls_escalation(analytical_model, num_previous_calls))
        
        # Filter to only triggered escalations
        triggered = [t for t in triggered if t and t.triggered]
        
        return triggered
    
    def _check_anger_escalation(self, analytical_model: AnalyticalModel) -> Optional[EscalationTrigger]:
        """Check if anger-based escalation applies."""
        if (analytical_model.emotion.anger_score > 0.8 and 
            analytical_model.intent.urgency_level == UrgencyLevel.CRITICAL):
            
            return EscalationTrigger(
                trigger_name="ANGER_CRITICAL_ESCALATION",
                trigger_condition="anger_score > 0.8 AND urgency == CRITICAL",
                from_level="tier_1_operator",
                to_level="tier_2_supervisor",
                timeframe_minutes=5,
                action_required="Immediate call to user, escalate to senior management",
                triggered=True,
                reason=f"High anger (score: {analytical_model.emotion.anger_score:.2f}) in CRITICAL situation",
            )
        
        return None
    
    def _check_timeout_escalation(
        self,
        analytical_model: AnalyticalModel,
        time_since_filing: int,
    ) -> Optional[EscalationTrigger]:
        """Check if timeout-based escalation applies."""
        if (time_since_filing > 30 and 
            analytical_model.intent.urgency_level == UrgencyLevel.HIGH):
            
            return EscalationTrigger(
                trigger_name="TIMEOUT_ESCALATION",
                trigger_condition="no_response > 30 minutes AND urgency == HIGH",
                from_level="tier_1_operator",
                to_level="tier_2_supervisor",
                timeframe_minutes=30,
                action_required="Call user, check with assigned department, update ticket",
                triggered=True,
                reason=f"No response for {time_since_filing} minutes on HIGH urgency",
            )
        
        return None
    
    def _check_stress_escalation(self, analytical_model: AnalyticalModel) -> Optional[EscalationTrigger]:
        """Check if stress-based escalation applies."""
        if (analytical_model.emotion.anger_score > 0.6 and 
            analytical_model.emotion.stress_level > 0.7):
            
            return EscalationTrigger(
                trigger_name="STRESS_ESCALATION",
                trigger_condition="anger_score > 0.6 AND stress_level > 0.7",
                from_level="tier_1_operator",
                to_level="tier_2_supervisor",
                timeframe_minutes=10,
                action_required="Call user with empathy script, validate complaint, reassure",
                triggered=True,
                reason=f"High stress (anger: {analytical_model.emotion.anger_score:.2f}, stress: {analytical_model.emotion.stress_level:.2f})",
            )
        
        return None
    
    def _check_repeated_calls_escalation(
        self,
        analytical_model: AnalyticalModel,
        num_previous_calls: int,
    ) -> Optional[EscalationTrigger]:
        """Check if repeated calls escalation applies."""
        if num_previous_calls > 2:
            return EscalationTrigger(
                trigger_name="REPEATED_CALLS_ESCALATION",
                trigger_condition="multiple_calls_same_issue > 2",
                from_level="tier_1_operator",
                to_level="management",
                timeframe_minutes=60,
                action_required="Full case review, direct contact with department, status update",
                triggered=True,
                reason=f"This is call #{num_previous_calls} for same issue",
            )
        
        return None
    
    def should_escalate_to_management(
        self,
        escalation_triggers: List[EscalationTrigger],
    ) -> bool:
        """Determine if escalation reaches management level."""
        # Any trigger targeting "management" or above
        return any(t.to_level in ["management", "senior_management"] for t in escalation_triggers)
    
    def get_escalation_instructions(
        self,
        escalation_triggers: List[EscalationTrigger],
    ) -> str:
        """Generate escalation instructions."""
        if not escalation_triggers:
            return "No escalation needed. Standard tier 1 handling."
        
        instructions = []
        for trigger in escalation_triggers:
            instructions.append(f"⚠️  {trigger.trigger_name}")
            instructions.append(f"   Escalate to: {trigger.to_level.upper()}")
            instructions.append(f"   Within: {trigger.timeframe_minutes} minutes")
            instructions.append(f"   Action: {trigger.action_required}")
        
        return "\n".join(instructions)


def check_escalation_triggers(analytical_model: AnalyticalModel) -> List[EscalationTrigger]:
    """Convenience function to check all escalation triggers."""
    engine = EscalationEngine()
    return engine.check_escalation(analytical_model)


def apply_escalation_policy(
    escalation_triggers: List[EscalationTrigger],
) -> Dict[str, any]:
    """Apply escalation policy and return actions."""
    engine = EscalationEngine()
    
    return {
        "should_escalate": len(escalation_triggers) > 0,
        "escalation_level": "management" if engine.should_escalate_to_management(escalation_triggers) else "supervisor",
        "instructions": engine.get_escalation_instructions(escalation_triggers),
        "triggers": [t.__dict__ for t in escalation_triggers],
    }
