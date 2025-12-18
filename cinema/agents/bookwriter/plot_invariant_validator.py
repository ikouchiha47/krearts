"""
Plot Invariant Specification (PIS) Validator

A genre-agnostic, score-based validator that checks narrative structure
rather than genre-specific labels.

Based on 7 minimal plot invariants that define what makes a story exist.
"""

from typing import Dict, List, Any, Tuple, Callable
from dataclasses import dataclass


@dataclass
class PlotScore:
    """Plot validation score with breakdown"""
    score: float  # 0.0 - 1.0
    breakdown: Dict[str, Dict[str, float]]
    interpretation: str
    
    @property
    def is_valid(self) -> bool:
        """Consider plots with score >= 0.6 as structurally valid"""
        return self.score >= 0.6
    
    @property
    def strength(self) -> str:
        """Human-readable strength assessment"""
        if self.score < 0.4:
            return "Not a story"
        elif self.score < 0.6:
            return "Weak/incomplete"
        elif self.score < 0.75:
            return "Structurally valid"
        elif self.score < 0.9:
            return "Strong foundation"
        else:
            return "Robust plot skeleton"


class PlotInvariantValidator:
    """
    Validates plot structure using 7 minimal invariants.
    
    PIS-01: Agency - At least one entity causes events intentionally
    PIS-02: Intent - An agent wants or seeks something
    PIS-03: Opposition - Something resists that intent
    PIS-04: Causality - Events are not independent
    PIS-05: Change - State before ≠ state after
    PIS-06: Escalation - Pressure or stakes increase
    PIS-07: Irreversibility - Some change cannot be undone
    """
    
    # Feature weights (reflect structural importance)
    PIS_FEATURES = {
        "agency": 1.0,
        "intent": 1.0,
        "opposition": 1.2,      # Core conflict
        "causality": 1.5,       # Most important for coherence
        "change": 1.2,          # Essential for narrative
        "escalation": 1.0,
        "irreversibility": 1.1,
    }
    
    # Opposition relationship types
    OPPOSITION_REL_TYPES = {
        "opposes", "betrays", "blocks", "threatens", "hunts", 
        "opposed_to", "enemies_with", "rivals_with"
    }
    
    # Irreversible event types
    IRREVERSIBLE_EVENT_TYPES = {
        "death", "murder", "revelation", "final_battle", "confession", 
        "aftermath", "discovery", "betrayal", "transformation"
    }
    
    # Irreversible outcome keywords
    IRREVERSIBLE_KEYWORDS = {
        "dead", "killed", "revealed", "destroyed", "exposed", 
        "lost forever", "cannot return", "permanently", "final"
    }
    
    def validate_plot(self, graph: Any) -> PlotScore:
        """
        Validate plot structure and return score with breakdown.
        
        Args:
            graph: PlotGraphOutput object
            
        Returns:
            PlotScore with overall score and feature breakdown
        """
        total = 0.0
        max_score = 0.0
        breakdown = {}
        
        for name, weight in self.PIS_FEATURES.items():
            scorer = getattr(self, f"_score_{name}")
            raw_score = scorer(graph)
            weighted = raw_score * weight
            
            breakdown[name] = {
                "raw": round(raw_score, 3),
                "weight": weight,
                "weighted": round(weighted, 3)
            }
            
            total += weighted
            max_score += weight
        
        final_score = total / max_score
        
        return PlotScore(
            score=round(final_score, 3),
            breakdown=breakdown,
            interpretation=self._interpret_score(final_score, breakdown)
        )
    
    def _get_protagonists(self, graph: Any) -> List[Dict[str, Any]]:
        """Find protagonist characters (flexible role matching)"""
        protagonists = []
        for char in graph.characters:
            role = char.get("role", "").lower()
            if role in ["protagonist", "detective", "hero", "main_character"]:
                protagonists.append(char)
        return protagonists
    
    def _get_event_pairs(self, events: List[Dict[str, Any]]) -> List[Tuple[Dict, Dict]]:
        """Get consecutive event pairs sorted by time"""
        sorted_events = sorted(events, key=lambda e: e.get("time", 0))
        return list(zip(sorted_events, sorted_events[1:]))
    
    def _score_agency(self, graph: Any) -> float:
        """PIS-01: At least one protagonist participates in events"""
        protagonists = self._get_protagonists(graph)
        if not protagonists:
            return 0.0
        
        protagonist_names = {c["name"] for c in protagonists}
        
        participates = any(
            protagonist_names.intersection(e.get("participants", []))
            for e in graph.events
        )
        
        return 1.0 if participates else 0.5
    
    def _score_intent(self, graph: Any) -> float:
        """PIS-02: Someone wants something"""
        for char in graph.characters:
            if char.get("motivation"):
                return 1.0
        return 0.0
    
    def _score_opposition(self, graph: Any) -> float:
        """PIS-03: Resistance to intent exists"""
        for rel in graph.relationships:
            if rel.get("type") in self.OPPOSITION_REL_TYPES:
                return 1.0
        return 0.0
    
    def _score_causality(self, graph: Any) -> float:
        """PIS-04: Events influence later events"""
        if len(graph.events) < 2:
            return 0.0
        
        causal_links = 0
        
        for e1, e2 in self._get_event_pairs(graph.events):
            if e1.get("outcome"):
                # Crude but effective: outcome exists and later event exists
                causal_links += 1
        
        if causal_links == 0:
            return 0.0
        elif causal_links == 1:
            return 0.5
        else:
            return 1.0
    
    def _score_change(self, graph: Any) -> float:
        """PIS-05: Something changes state"""
        # Check for outcomes in events
        if any(e.get("outcome") for e in graph.events):
            return 1.0
        
        # Check for character arcs
        if any(c.get("arc") for c in graph.characters):
            return 1.0
        
        return 0.0
    
    def _score_escalation(self, graph: Any) -> float:
        """PIS-06: Pressure or stakes increase"""
        if len(graph.events) < 3:
            return 0.0
        
        # Crude heuristic: later events have outcomes (indicating consequences)
        later_events = sorted(graph.events, key=lambda e: e.get("time", 0))[1:]
        escalating = sum(1 for e in later_events if e.get("outcome"))
        
        if escalating >= 2:
            return 1.0
        elif escalating == 1:
            return 0.5
        else:
            return 0.0
    
    def _score_irreversibility(self, graph: Any) -> float:
        """PIS-07: Some change cannot be undone"""
        # Check event types
        for event in graph.events:
            if event.get("type") in self.IRREVERSIBLE_EVENT_TYPES:
                return 1.0
            
            # Check outcome text for irreversible keywords
            outcome = event.get("outcome", "").lower()
            if any(keyword in outcome for keyword in self.IRREVERSIBLE_KEYWORDS):
                return 1.0
        
        return 0.0
    
    def _interpret_score(self, score: float, breakdown: Dict[str, Dict[str, float]]) -> str:
        """Generate human-readable interpretation"""
        issues = []
        strengths = []
        
        for feature, data in breakdown.items():
            raw = data["raw"]
            if raw == 0.0:
                issues.append(f"Missing {feature}")
            elif raw == 0.5:
                issues.append(f"Weak {feature}")
            elif raw == 1.0:
                strengths.append(feature)
        
        interpretation = f"Score: {score:.3f} ({PlotScore(score, {}, '').strength})"
        
        if issues:
            interpretation += f"\nIssues: {', '.join(issues)}"
        
        if strengths:
            interpretation += f"\nStrengths: {', '.join(strengths)}"
        
        return interpretation


# Convenience function
def validate_plot_structure(graph: Any) -> PlotScore:
    """Validate plot structure using PIS invariants"""
    validator = PlotInvariantValidator()
    return validator.validate_plot(graph)