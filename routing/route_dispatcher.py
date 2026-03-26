"""
Route Dispatcher Module
=======================
Determines optimal routing path for grievances using multi-criteria decision logic.

Process:
1. Extract routing features from grievance
2. Calculate routing scores for each department
3. Determine optimal department and priority
4. Generate routing decision with explanation
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from models.grievance_models import RoutingDecision, UrgencyLevel, AnalyticalModel
from external_services.gov_services_map import (
    get_service_mapping,
    detect_service_type,
    SERVICE_KEYWORDS,
)
from core.policies import get_sla_policy, get_escalation_policy


@dataclass
class RoutingScore:
    """Score for each potential routing destination."""
    department: str
    keyword_match_score: float  # 0-1: How well keywords match
    urgency_alignment_score: float  # 0-1: How well urgency aligns
    emotion_severity_score: float  # 0-1: Emotion-based severity
    final_score: float  # 0-10: Weighted combined score
    reasoning: str  # Why this department


class RouteDispatcher:
    """
    Determines optimal department routing for grievances.
    
    Uses multi-criteria analysis:
    - Keyword matching (what department handles these keywords)
    - Urgency level (emergency departments first)
    - Emotion indicators (anger/stress = higher urgency)
    - Current department load (optional)
    """
    
    def __init__(self):
        """Initialize route dispatcher."""
        self.service_keywords = SERVICE_KEYWORDS
        
    def dispatch_route(
        self,
        analytical_model: AnalyticalModel,
    ) -> RoutingDecision:
        """
        Determine optimal routing for grievance.
        
        Args:
            analytical_model: Complete analysis with intent, emotion, etc.
            
        Returns:
            RoutingDecision with department, priority, SLA, etc.
        """
        # Calculate scores for all departments
        scores = self._calculate_routing_scores(analytical_model)
        
        # Get top-ranked department
        best_route = max(scores, key=lambda x: x.final_score)
        
        # Get service mapping (default to maharashtra)
        service_mapping = get_service_mapping(
            best_route.department,
            "maharashtra"
        )
        
        # Determine priority level
        priority = self._determine_priority(
            urgency=analytical_model.intent.urgency_level,
            emotion_severity=best_route.emotion_severity_score,
            department=best_route.department,
        )
        
        # Get SLA policy
        sla_policy = get_sla_policy(
            best_route.department,
            analytical_model.intent.urgency_level.name
        )
        
        # Build routing reason
        routing_reason = self._build_routing_reason(
            best_route,
            priority,
            analytical_model
        )
        
        # Create decision
        routing_decision = RoutingDecision(
            primary_department=best_route.department,
            mapped_service=service_mapping,
            has_gov_service_match=service_mapping is not None,
            priority_level=priority,
            reason=routing_reason,
        )
        
        return routing_decision
    
    def _calculate_routing_scores(self, analytical_model: AnalyticalModel, transcript: str = "") -> List[RoutingScore]:
        """Calculate routing score for each department."""
        scores = []
        
        # Get detected service type from intent
        detected_service = analytical_model.intent.primary_intent.split('_')[0] if '_' in analytical_model.intent.primary_intent else "general"
        
        # Score all departments
        for dept, keywords in self.service_keywords.items():
            # Keyword matching score - use intent if no transcript
            if transcript:
                keyword_score = self._calculate_keyword_match(
                    transcript,
                    keywords
                )
            else:
                # Estimate from intent
                keyword_score = 1.0 if detected_service == dept else 0.3
            
            # Urgency alignment score
            urgency_score = self._calculate_urgency_alignment(
                analytical_model.intent.urgency_level,
                dept
            )
            
            # Emotion severity score
            emotion_score = self._calculate_emotion_severity(
                analytical_model.emotion
            )
            
            # Combined score (weighted)
            final_score = (
                keyword_score * 0.4 +
                urgency_score * 0.35 +
                emotion_score * 0.25
            ) * 10  # Scale to 0-10
            
            # Boost score if this is detected service
            if detected_service == dept:
                final_score *= 1.5
            
            # Create score entry
            score = RoutingScore(
                department=dept,
                keyword_match_score=keyword_score,
                urgency_alignment_score=urgency_score,
                emotion_severity_score=emotion_score,
                final_score=min(final_score, 10),  # Cap at 10
                reasoning=f"Keywords: {keyword_score:.2f}, Urgency: {urgency_score:.2f}, Emotion: {emotion_score:.2f}",
            )
            scores.append(score)
        
        return scores
    
    def _calculate_keyword_match(self, transcript: str, keywords: List[str]) -> float:
        """Calculate keyword matching score (0-1)."""
        if not keywords:
            return 0.0
        
        transcript_lower = transcript.lower()
        matches = sum(1 for kw in keywords if kw.lower() in transcript_lower)
        
        return min(matches / len(keywords), 1.0)
    
    def _calculate_urgency_alignment(self, urgency: UrgencyLevel, department: str) -> float:
        """Calculate how well urgency aligns with department."""
        # Emergency departments for critical urgency
        emergency_depts = {"fire", "police", "medical"}
        
        if urgency == UrgencyLevel.CRITICAL:
            return 1.0 if department in emergency_depts else 0.5
        elif urgency == UrgencyLevel.HIGH:
            return 0.8 if department in {"electricity", "water", "gas"} else 0.6
        elif urgency == UrgencyLevel.MEDIUM:
            return 0.7
        else:  # LOW
            return 0.6
    
    def _calculate_emotion_severity(self, emotion_analysis) -> float:
        """Calculate severity based on emotion indicators."""
        # Higher anger/stress = higher severity
        anger_contribution = min(emotion_analysis.anger_score * 0.5, 1.0)
        stress_contribution = min(emotion_analysis.stress_level * 0.3, 1.0)
        
        return min(anger_contribution + stress_contribution, 1.0)
    
    def _determine_priority(
        self,
        urgency: UrgencyLevel,
        emotion_severity: float,
        department: str,
    ) -> int:
        """
        Determine priority level 1-5.
        
        1 = Highest (critical emergencies)
        5 = Lowest (routine complaints)
        """
        base_priority = {
            UrgencyLevel.CRITICAL: 1,
            UrgencyLevel.HIGH: 2,
            UrgencyLevel.MEDIUM: 3,
            UrgencyLevel.LOW: 4,
        }.get(urgency, 4)
        
        # Adjust based on emotion severity
        if emotion_severity > 0.7:
            base_priority = max(1, base_priority - 1)  # Bump up priority
        elif emotion_severity < 0.2:
            base_priority = min(5, base_priority + 1)  # Lower priority
        
        return base_priority
    
    def _build_routing_reason(
        self,
        best_route: RoutingScore,
        priority: int,
        analytical_model: AnalyticalModel,
    ) -> str:
        """Build human-readable routing explanation."""
        reason_parts = [
            f"Route: {best_route.department.upper()}",
            f"Intent: {analytical_model.intent.primary_intent}",
            f"Urgency: {analytical_model.intent.urgency_level.name}",
            f"Priority: P{priority}",
            f"Emotion: {analytical_model.emotion.detected_emotion.name}",
            f"Confidence: {best_route.final_score:.1f}/10",
        ]
        
        return " | ".join(reason_parts)


def determine_optimal_route(analytical_model: AnalyticalModel) -> RoutingDecision:
    """Convenience function to determine optimal route."""
    dispatcher = RouteDispatcher()
    return dispatcher.dispatch_route(analytical_model)


def apply_escalation_rules(routing_decision: RoutingDecision, analytical_model: AnalyticalModel) -> bool:
    """Check if escalation rules apply to this grievance."""
    # Check anger-based escalation
    if analytical_model.emotion.anger_score > 0.8 and analytical_model.intent.urgency_level == UrgencyLevel.CRITICAL:
        return True
    
    # Check stress-based escalation
    if analytical_model.emotion.stress_level > 0.7 and analytical_model.emotion.anger_score > 0.6:
        return True
    
    return False


def calculate_priority(
    urgency: UrgencyLevel,
    emotion_severity: float,
    keywords: List[str],
) -> int:
    """Calculate priority (1-5, where 1 is highest)."""
    dispatcher = RouteDispatcher()
    return dispatcher._determine_priority(
        urgency=urgency,
        emotion_severity=emotion_severity,
        department="general"
    )
