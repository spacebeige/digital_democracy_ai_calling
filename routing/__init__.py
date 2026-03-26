"""
Routing Module
==============
Handles intelligent routing of grievances to appropriate departments and escalation levels.

This module orchestrates:
1. Department selection based on keywords and intent
2. Escalation decision logic
3. SLA assignment
4. Priority calculation
"""

from .route_dispatcher import (
    RouteDispatcher,
    determine_optimal_route,
    apply_escalation_rules,
    calculate_priority,
)
from .escalation_engine import (
    EscalationEngine,
    check_escalation_triggers,
    apply_escalation_policy,
)

__all__ = [
    "RouteDispatcher",
    "EscalationEngine",
    "determine_optimal_route",
    "apply_escalation_rules",
    "calculate_priority",
    "check_escalation_triggers",
    "apply_escalation_policy",
]
