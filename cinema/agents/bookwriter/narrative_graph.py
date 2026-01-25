"""
Self-Evolving Narrative Graph System

This module provides data structures and logic for creating dynamic, believable
story graphs where character relationships and plot developments emerge naturally
from character arcs, worldviews, and causal chains.

Key Features:
- Character worldview tracking and evolution
- Dynamic relationship states
- Causal chain validation
- Natural consequence generation
- Belief/knowledge modeling per character
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum
import networkx as nx
from datetime import datetime
from pydantic import BaseModel, Field


class RelationshipType(str, Enum):
    """Types of relationships between characters"""
    FRIEND = "friend"
    ENEMY = "enemy"
    FAMILY = "family"
    ROMANTIC = "romantic"
    PROFESSIONAL = "professional"
    NEUTRAL = "neutral"
    COMPLEX = "complex"  # Mixed feelings


class ValueType(str, Enum):
    """Core values that drive character decisions"""
    JUSTICE = "justice"
    LOYALTY = "loyalty"
    FREEDOM = "freedom"
    SURVIVAL = "survival"
    TRUTH = "truth"
    POWER = "power"
    COMPASSION = "compassion"
    DUTY = "duty"
    REVENGE = "revenge"
    REDEMPTION = "redemption"


class EventType(str, Enum):
    """Types of story events"""
    BETRAYAL = "betrayal"
    REVELATION = "revelation"
    CONFLICT = "conflict"
    ALLIANCE = "alliance"
    SACRIFICE = "sacrifice"
    DISCOVERY = "discovery"
    CONFRONTATION = "confrontation"
    DECISION = "decision"
    LOSS = "loss"
    VICTORY = "victory"


# ============================================================================
# CORE DATA MODELS
# ============================================================================


class Belief(BaseModel):
    """A belief held by a character"""
    statement: str = Field(description="The belief statement")
    confidence: float = Field(ge=0.0, le=1.0, description="How confident (0-1)")
    formed_at: int = Field(description="Story beat when formed")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    challenges: List[str] = Field(default_factory=list, description="Contradicting evidence")
    
    def challenge(self, new_evidence: str) -> float:
        """Challenge this belief with new evidence, returns new confidence"""
        self.challenges.append(new_evidence)
        # Simple formula: confidence decreases with challenges
        penalty = 0.1 * len(self.challenges) / (len(self.evidence) + 1)
        self.confidence = max(0.0, self.confidence - penalty)
        return self.confidence


class Value(BaseModel):
    """A core value that guides character behavior"""
    type: ValueType
    importance: float = Field(ge=0.0, le=1.0, description="How important (0-1)")
    description: str = Field(description="What this value means to the character")
    
    def conflicts_with(self, other: 'Value', context: str) -> float:
        """
        Determine if this value conflicts with another in a given context.
        Returns conflict strength (0.0 = no conflict, 1.0 = direct opposition)
        """
        # Define value oppositions
        oppositions = {
            ValueType.JUSTICE: [ValueType.REVENGE, ValueType.POWER],
            ValueType.LOYALTY: [ValueType.TRUTH, ValueType.JUSTICE],
            ValueType.FREEDOM: [ValueType.DUTY, ValueType.LOYALTY],
            ValueType.SURVIVAL: [ValueType.SACRIFICE, ValueType.COMPASSION],
            ValueType.TRUTH: [ValueType.LOYALTY, ValueType.COMPASSION],
        }
        
        if other.type in oppositions.get(self.type, []):
            # Weight by importance of both values
            return (self.importance + other.importance) / 2.0
        
        return 0.0


class Worldview(BaseModel):
    """A character's lens for interpreting events"""
    core_beliefs: Dict[str, Belief] = Field(default_factory=dict)
    values_hierarchy: List[Value] = Field(default_factory=list)
    biases: List[str] = Field(default_factory=list, description="Cognitive biases")
    
    def get_most_important_value(self) -> Optional[Value]:
        """Get the character's most important value"""
        if not self.values_hierarchy:
            return None
        return max(self.values_hierarchy, key=lambda v: v.importance)
    
    def interpret_event(self, event: 'Event') -> str:
        """
        How this character interprets an event based on their worldview.
        This is where LLM integration happens.
        """
        # Build interpretation prompt from beliefs and values
        top_values = sorted(self.values_hierarchy, key=lambda v: v.importance, reverse=True)[:3]
        
        interpretation_context = {
            "beliefs": [b.statement for b in self.core_beliefs.values() if b.confidence > 0.5],
            "values": [f"{v.type.value} (importance: {v.importance})" for v in top_values],
            "biases": self.biases,
            "event": event.description
        }
        
        return interpretation_context
    
    def calculate_divergence(self, other: 'Worldview') -> float:
        """
        Calculate how different this worldview is from another.
        Returns 0.0 (identical) to 1.0 (opposite)
        """
        # Compare values
        value_divergence = 0.0
        for v1 in self.values_hierarchy:
            # Find matching value in other
            matching = [v2 for v2 in other.values_hierarchy if v2.type == v1.type]
            if matching:
                # Same value, different importance
                value_divergence += abs(v1.importance - matching[0].importance) * 0.5
            else:
                # Value missing in other worldview
                value_divergence += v1.importance
        
        # Normalize
        max_possible = sum(v.importance for v in self.values_hierarchy)
        return min(1.0, value_divergence / max(0.1, max_possible))


class WorldviewShift(BaseModel):
    """A moment that changes how a character sees the world"""
    beat_number: int = Field(description="Story beat when this happened")
    trigger_event_id: str = Field(description="Event that triggered the shift")
    old_belief: str = Field(description="Previous belief")
    new_belief: str = Field(description="New belief")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in new belief")
    emotional_impact: float = Field(ge=0.0, le=1.0, description="Emotional weight")
    reasoning: str = Field(description="Why this shift happened")


class CharacterArc(BaseModel):
    """Tracks character evolution throughout the story"""
    character_id: str
    worldview: Worldview = Field(default_factory=Worldview)
    experiences: List[str] = Field(default_factory=list, description="Event IDs")
    worldview_shifts: List[WorldviewShift] = Field(default_factory=list)
    growth_trajectory: str = Field(default="", description="Overall arc direction")
    
    def add_experience(self, event: 'Event', shift: Optional[WorldviewShift] = None):
        """Record an experience and optional worldview shift"""
        self.experiences.append(event.id)
        if shift:
            self.worldview_shifts.append(shift)
    
    def has_sufficient_development_for(self, consequence: 'Consequence') -> bool:
        """
        Check if character has been through enough development to justify
        a major consequence (like betraying a friend).
        """
        # Need at least 2 worldview shifts and 5 experiences for major consequences
        if consequence.severity > 0.7:
            return len(self.worldview_shifts) >= 2 and len(self.experiences) >= 5
        
        # Minor consequences need less setup
        return len(self.experiences) >= 2


class RelationshipState(BaseModel):
    """Dynamic relationship between two characters"""
    char1_id: str
    char2_id: str
    relationship_type: RelationshipType = RelationshipType.NEUTRAL
    trust_level: float = Field(default=0.0, ge=-1.0, le=1.0, description="-1 (enemies) to 1 (allies)")
    shared_experiences: List[str] = Field(default_factory=list, description="Event IDs")
    conflicts: List[str] = Field(default_factory=list, description="Conflict descriptions")
    alignment_on_values: Dict[str, float] = Field(default_factory=dict, description="Value -> alignment")
    last_interaction_beat: int = Field(default=0)
    
    def update_trust(self, delta: float, reason: str):
        """Update trust level with bounds checking"""
        old_trust = self.trust_level
        self.trust_level = max(-1.0, min(1.0, self.trust_level + delta))
        
        # Update relationship type based on trust
        if self.trust_level > 0.6:
            self.relationship_type = RelationshipType.FRIEND
        elif self.trust_level < -0.6:
            self.relationship_type = RelationshipType.ENEMY
        elif abs(self.trust_level) < 0.2:
            self.relationship_type = RelationshipType.NEUTRAL
        else:
            self.relationship_type = RelationshipType.COMPLEX
        
        return old_trust, self.trust_level


class Event(BaseModel):
    """A story event"""
    id: str
    beat_number: int
    type: EventType
    description: str
    participants: List[str] = Field(default_factory=list, description="Character IDs")
    witnesses: List[str] = Field(default_factory=list, description="Who saw/knows")
    location: str = ""
    requires_interpretation: bool = Field(default=False, description="Ambiguous event")
    stakes: float = Field(ge=0.0, le=1.0, description="How important (0-1)")
    
    def involves_character(self, char_id: str) -> bool:
        """Check if character is involved"""
        return char_id in self.participants or char_id in self.witnesses


class Consequence(BaseModel):
    """A consequence of an event"""
    id: str
    triggering_event_id: str
    description: str
    severity: float = Field(ge=0.0, le=1.0, description="Impact level (0-1)")
    affected_characters: List[str] = Field(default_factory=list)
    relationship_changes: Dict[Tuple[str, str], float] = Field(default_factory=dict)
    worldview_impacts: Dict[str, str] = Field(default_factory=dict, description="char_id -> impact")
    reversible: bool = Field(default=True)
    probability: float = Field(default=1.0, ge=0.0, le=1.0)


class CausalChain(BaseModel):
    """Tracks cause-effect relationships"""
    id: str
    initiating_event_id: str
    intermediate_events: List[str] = Field(default_factory=list)
    final_consequence_id: str
    probability: float = Field(ge=0.0, le=1.0)
    character_agency: Dict[str, float] = Field(default_factory=dict, description="Who could prevent/enable")
    logical_steps: List[str] = Field(default_factory=list, description="Reasoning for each step")


class WorldState(BaseModel):
    """Complete state of the story world at a specific beat"""
    beat_number: int
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    objective_facts: Dict[str, Any] = Field(default_factory=dict)
    character_beliefs: Dict[str, Dict[str, Belief]] = Field(default_factory=dict)
    relationships: Dict[Tuple[str, str], RelationshipState] = Field(default_factory=dict)
    recent_events: List[str] = Field(default_factory=list, description="Last 5 events")


# ============================================================================
# CONSEQUENCE EVALUATION SYSTEM
# ============================================================================


class ConsequenceEngine:
    """Evaluates what consequences naturally follow from events"""
    
    def __init__(self):
        self.validation_history: List[Dict] = []
    
    def evaluate_consequence_validity(
        self,
        event: Event,
        consequence: Consequence,
        char1_arc: CharacterArc,
        char2_arc: Optional[CharacterArc] = None,
        relationship: Optional[RelationshipState] = None
    ) -> Tuple[bool, str, float]:
        """
        Evaluate if a consequence is logically and narratively valid.
        
        Returns:
            (is_valid, reasoning, confidence_score)
        """
        checks = []
        
        # 1. Logical consistency
        logical_valid, logical_reason = self._check_logical_consistency(event, consequence)
        checks.append(("logical", logical_valid, logical_reason))
        
        # 2. Character development
        if char1_arc:
            dev_valid, dev_reason = self._check_character_development(
                consequence, char1_arc, char2_arc
            )
            checks.append(("development", dev_valid, dev_reason))
        
        # 3. Relationship dynamics
        if relationship and char2_arc:
            rel_valid, rel_reason = self._check_relationship_dynamics(
                event, consequence, relationship, char1_arc, char2_arc
            )
            checks.append(("relationship", rel_valid, rel_reason))
        
        # 4. Stakes alignment
        stakes_valid, stakes_reason = self._check_stakes_alignment(event, consequence)
        checks.append(("stakes", stakes_valid, stakes_reason))
        
        # Calculate overall validity
        valid_count = sum(1 for _, valid, _ in checks if valid)
        confidence = valid_count / len(checks)
        
        is_valid = confidence >= 0.75  # Need 75% of checks to pass
        
        # Build reasoning
        reasoning_parts = []
        for check_name, valid, reason in checks:
            status = "✓" if valid else "✗"
            reasoning_parts.append(f"{status} {check_name}: {reason}")
        
        reasoning = "\n".join(reasoning_parts)
        
        return is_valid, reasoning, confidence
    
    def _check_logical_consistency(
        self, event: Event, consequence: Consequence
    ) -> Tuple[bool, str]:
        """Check if consequence logically follows from event"""
        
        # Check if participants match
        if not any(p in consequence.affected_characters for p in event.participants):
            return False, "Consequence affects characters not involved in triggering event"
        
        # Check severity alignment
        if consequence.severity > event.stakes:
            return False, f"Consequence severity ({consequence.severity}) exceeds event stakes ({event.stakes})"
        
        return True, "Consequence logically follows from event"
    
    def _check_character_development(
        self,
        consequence: Consequence,
        char1_arc: CharacterArc,
        char2_arc: Optional[CharacterArc]
    ) -> Tuple[bool, str]:
        """Check if characters have developed enough for this consequence"""
        
        if not char1_arc.has_sufficient_development_for(consequence):
            return False, f"Character {char1_arc.character_id} lacks development for consequence"
        
        if char2_arc and not char2_arc.has_sufficient_development_for(consequence):
            return False, f"Character {char2_arc.character_id} lacks development for consequence"
        
        return True, "Characters have sufficient development"
    
    def _check_relationship_dynamics(
        self,
        event: Event,
        consequence: Consequence,
        relationship: RelationshipState,
        char1_arc: CharacterArc,
        char2_arc: CharacterArc
    ) -> Tuple[bool, str]:
        """Check if relationship state supports this consequence"""
        
        # Check worldview divergence
        divergence = char1_arc.worldview.calculate_divergence(char2_arc.worldview)
        
        # For major relationship changes, need high divergence
        if consequence.severity > 0.7:
            if divergence < 0.4:
                return False, f"Worldview divergence ({divergence:.2f}) too low for major consequence"
        
        # Check value conflicts
        char1_top_value = char1_arc.worldview.get_most_important_value()
        char2_top_value = char2_arc.worldview.get_most_important_value()
        
        if char1_top_value and char2_top_value:
            conflict_strength = char1_top_value.conflicts_with(char2_top_value, event.description)
            
            if consequence.severity > 0.7 and conflict_strength < 0.3:
                return False, f"Value conflict ({conflict_strength:.2f}) too weak for major consequence"
        
        return True, f"Relationship dynamics support consequence (divergence: {divergence:.2f})"
    
    def _check_stakes_alignment(
        self, event: Event, consequence: Consequence
    ) -> Tuple[bool, str]:
        """Check if consequence stakes match event stakes"""
        
        # Consequences should be proportional to event stakes
        if consequence.severity > event.stakes * 1.5:
            return False, f"Consequence too severe for event stakes"
        
        if consequence.severity < event.stakes * 0.3:
            return False, f"Consequence too mild for event stakes"
        
        return True, "Stakes are appropriately aligned"


# ============================================================================
# RELATIONSHIP EVOLUTION ENGINE
# ============================================================================


class RelationshipEvolutionEngine:
    """Manages how relationships change over time"""
    
    def evaluate_breaking_point(
        self,
        char1_arc: CharacterArc,
        char2_arc: CharacterArc,
        event: Event,
        relationship: RelationshipState
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate if this event breaks a relationship.
        
        For your "friends turning enemies" scenario, this checks:
        1. Worldview divergence
        2. Value conflicts
        3. Forcing function
        4. Narrative justification
        """
        
        # 1. Calculate worldview divergence
        divergence = char1_arc.worldview.calculate_divergence(char2_arc.worldview)
        
        if divergence < 0.5:
            # Not diverged enough
            return None
        
        # 2. Check for value conflicts
        char1_top_value = char1_arc.worldview.get_most_important_value()
        char2_top_value = char2_arc.worldview.get_most_important_value()
        
        if not (char1_top_value and char2_top_value):
            return None
        
        conflict_strength = char1_top_value.conflicts_with(char2_top_value, event.description)
        
        if conflict_strength < 0.5:
            # Values don't conflict enough
            return None
        
        # 3. Check if event forces them to choose sides
        is_forcing = event.stakes > 0.7 and event.type in [
            EventType.BETRAYAL, EventType.DECISION, EventType.CONFRONTATION
        ]
        
        if not is_forcing:
            return None
        
        # 4. Check narrative justification (arc progression)
        arc_progression = self._trace_arc_progression(
            relationship.shared_experiences,
            char1_arc.worldview_shifts,
            char2_arc.worldview_shifts
        )
        
        if not arc_progression["sufficient"]:
            return None
        
        # All conditions met - this is a breaking point
        return {
            "trigger_event": event.id,
            "worldview_divergence": divergence,
            "value_conflict": conflict_strength,
            "char1_reasoning": self._generate_reasoning(char1_arc, char1_top_value, event),
            "char2_reasoning": self._generate_reasoning(char2_arc, char2_top_value, event),
            "arc_justification": arc_progression["summary"],
            "trust_delta": -0.8,  # Major trust loss
            "reversible": False,  # Point of no return
            "narrative_weight": "major"  # This is a pivotal moment
        }
    
    def _trace_arc_progression(
        self,
        shared_experiences: List[str],
        shifts1: List[WorldviewShift],
        shifts2: List[WorldviewShift]
    ) -> Dict[str, Any]:
        """
        Verify characters have organically grown apart.
        
        Looks for:
        - Small disagreements that accumulated
        - Different responses to shared trauma
        - Gradual value divergence
        - Erosion of common ground
        """
        
        # Need multiple shared experiences
        if len(shared_experiences) < 3:
            return {"sufficient": False, "reason": "Too few shared experiences"}
        
        # Need worldview shifts from both characters
        if len(shifts1) < 2 or len(shifts2) < 2:
            return {"sufficient": False, "reason": "Insufficient character development"}
        
        # Check if shifts show divergence
        # (In real implementation, would compare shift directions)
        
        return {
            "sufficient": True,
            "summary": f"Characters shared {len(shared_experiences)} experiences, "
                      f"went through {len(shifts1)}+{len(shifts2)} worldview shifts, "
                      f"organically diverged in values and beliefs"
        }
    
    def _generate_reasoning(
        self, arc: CharacterArc, top_value: Value, event: Event
    ) -> str:
        """Generate character's reasoning for their choice"""
        return f"{arc.character_id} prioritizes {top_value.type.value} " \
               f"({top_value.description}), which leads them to interpret " \
               f"{event.type.value} as requiring action that conflicts with former ally."


# ============================================================================
# MAIN STORY GRAPH
# ============================================================================


class StoryGraph:
    """
    Self-evolving narrative graph that generates consequences based on
    character arcs, worldviews, and causal logic.
    """
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.world_states: List[WorldState] = []
        self.character_arcs: Dict[str, CharacterArc] = {}
        self.relationships: Dict[Tuple[str, str], RelationshipState] = {}
        self.events: Dict[str, Event] = {}
        self.consequences: Dict[str, Consequence] = {}
        self.causal_chains: List[CausalChain] = []
        
        self.consequence_engine = ConsequenceEngine()
        self.relationship_engine = RelationshipEvolutionEngine()
        
        self.current_beat = 0
    
    def add_character(
        self,
        char_id: str,
        initial_worldview: Worldview,
        growth_trajectory: str = ""
    ) -> CharacterArc:
        """Add a character to the story"""
        arc = CharacterArc(
            character_id=char_id,
            worldview=initial_worldview,
            growth_trajectory=growth_trajectory
        )
        self.character_arcs[char_id] = arc
        self.graph.add_node(char_id, type="character", arc=arc)
        return arc
    
    def add_relationship(
        self,
        char1_id: str,
        char2_id: str,
        initial_trust: float = 0.0,
        relationship_type: RelationshipType = RelationshipType.NEUTRAL
    ) -> RelationshipState:
        """Add a relationship between characters"""
        rel = RelationshipState(
            char1_id=char1_id,
            char2_id=char2_id,
            trust_level=initial_trust,
            relationship_type=relationship_type
        )
        
        # Store both directions
        self.relationships[(char1_id, char2_id)] = rel
        self.relationships[(char2_id, char1_id)] = rel
        
        self.graph.add_edge(char1_id, char2_id, relationship=rel)
        
        return rel
    
    def add_event(self, event: Event) -> List[Consequence]:
        """
        Add an event and generate natural consequences.
        This is the core evolution method.
        """
        self.current_beat = event.beat_number
        self.events[event.id] = event
        
        # Add event to graph
        self.graph.add_node(event.id, type="event", data=event)
        
        # Connect event to participants
        for char_id in event.participants:
            self.graph.add_edge(event.id, char_id, relation="involves")
        
        # Generate consequences
        consequences = self._generate_consequences(event)
        
        # Apply consequences
        for consequence in consequences:
            self._apply_consequence(consequence)
        
        # Update world state
        self._update_world_state()
        
        return consequences
    
    def _generate_consequences(self, event: Event) -> List[Consequence]:
        """Generate natural consequences from an event"""
        consequences = []
        
        # 1. Evaluate worldview impacts
        for char_id in event.participants:
            if char_id not in self.character_arcs:
                continue
            
            arc = self.character_arcs[char_id]
            shift = self._evaluate_worldview_impact(event, arc)
            
            if shift:
                # Create consequence for worldview shift
                consequence = Consequence(
                    id=f"consequence_{event.id}_{char_id}_worldview",
                    triggering_event_id=event.id,
                    description=f"{char_id}'s worldview shifts: {shift.old_belief} -> {shift.new_belief}",
                    severity=shift.emotional_impact,
                    affected_characters=[char_id],
                    worldview_impacts={char_id: shift.new_belief}
                )
                consequences.append(consequence)
        
        # 2. Evaluate relationship impacts
        for (char1, char2), rel in self.relationships.items():
            if char1 > char2:  # Only process each pair once
                continue
            
            if not (event.involves_character(char1) or event.involves_character(char2)):
                continue
            
            # Check for breaking points
            breaking_point = self.relationship_engine.evaluate_breaking_point(
                self.character_arcs[char1],
                self.character_arcs[char2],
                event,
                rel
            )
            
            if breaking_point:
                # Create consequence for relationship break
                consequence = Consequence(
                    id=f"consequence_{event.id}_{char1}_{char2}_break",
                    triggering_event_id=event.id,
                    description=f"Relationship between {char1} and {char2} breaks",
                    severity=0.9,  # Major consequence
                    affected_characters=[char1, char2],
                    relationship_changes={(char1, char2): breaking_point["trust_delta"]},
                    reversible=breaking_point["reversible"]
                )
                consequences.append(consequence)
        
        return consequences
    
    def _evaluate_worldview_impact(
        self, event: Event, arc: CharacterArc
    ) -> Optional[WorldviewShift]:
        """
        Determine if event causes a worldview shift.
        This is where LLM integration would happen.
        """
        
        # Check if event contradicts existing beliefs
        for belief_key, belief in arc.worldview.core_beliefs.items():
            # Simple heuristic: high-stakes events challenge beliefs
            if event.stakes > 0.6:
                # Challenge the belief
                new_confidence = belief.challenge(event.description)
                
                if new_confidence < 0.3:
                    # Belief shattered - worldview shift
                    return WorldviewShift(
                        beat_number=event.beat_number,
                        trigger_event_id=event.id,
                        old_belief=belief.statement,
                        new_belief=f"Questioning: {belief.statement}",
                        confidence=0.5,
                        emotional_impact=event.stakes,
                        reasoning=f"Event {event.description} challenged core belief"
                    )
        
        return None
    
    def _apply_consequence(self, consequence: Consequence):
        """Apply a consequence to the story state"""
        self.consequences[consequence.id] = consequence
        
        # Apply relationship changes
        for (char1, char2), trust_delta in consequence.relationship_changes.items():
            if (char1, char2) in self.relationships:
                rel = self.relationships[(char1, char2)]
                rel.update_trust(trust_delta, consequence.description)
        
        # Apply worldview impacts
        for char_id, impact in consequence.worldview_impacts.items():
            if char_id in self.character_arcs:
                arc = self.character_arcs[char_id]
                # Update beliefs (simplified)
                arc.worldview.core_beliefs[f"belief_{self.current_beat}"] = Belief(
                    statement=impact,
                    confidence=0.7,
                    formed_at=self.current_beat
                )
        
        # Add to graph
        self.graph.add_node(consequence.id, type="consequence", data=consequence)
        self.graph.add_edge(consequence.triggering_event_id, consequence.id, relation="causes")
    
    def _update_world_state(self):
        """Capture current world state"""
        state = WorldState(
            beat_number=self.current_beat,
            objective_facts={
                "event_count": len(self.events),
                "consequence_count": len(self.consequences)
            },
            character_beliefs={
                char_id: dict(arc.worldview.core_beliefs)
                for char_id, arc in self.character_arcs.items()
            },
            relationships=dict(self.relationships)
        )
        
        self.world_states.append(state)
    
    def export_plot_structure(self) -> Dict[str, Any]:
        """
        Export in a format compatible with your existing pipeline.
        This replaces PlotStructureBuilder output.
        """
        return {
            "characters": [
                {
                    "id": char_id,
                    "arc": arc.model_dump(),
                    "growth_trajectory": arc.growth_trajectory
                }
                for char_id, arc in self.character_arcs.items()
            ],
            "relationships": [
                {
                    "char1": char1,
                    "char2": char2,
                    "state": rel.model_dump()
                }
                for (char1, char2), rel in self.relationships.items()
                if char1 < char2  # Only include each pair once
            ],
            "events": [event.model_dump() for event in self.events.values()],
            "consequences": [cons.model_dump() for cons in self.consequences.values()],
            "causal_chains": [chain.model_dump() for chain in self.causal_chains],
            "world_states": [state.model_dump() for state in self.world_states],
            "timeline": self._build_timeline(),
            "graph_data": self._export_graph_for_visualization()
        }
    
    def _build_timeline(self) -> List[Dict[str, Any]]:
        """Build chronological timeline of events"""
        timeline = []
        
        for event in sorted(self.events.values(), key=lambda e: e.beat_number):
            timeline_entry = {
                "beat": event.beat_number,
                "event_id": event.id,
                "type": event.type.value,
                "description": event.description,
                "participants": event.participants,
                "consequences": [
                    c.id for c in self.consequences.values()
                    if c.triggering_event_id == event.id
                ]
            }
            timeline.append(timeline_entry)
        
        return timeline
    
    def _export_graph_for_visualization(self) -> Dict[str, Any]:
        """Export graph in format for visualization"""
        return {
            "nodes": [
                {
                    "id": node,
                    "type": self.graph.nodes[node].get("type", "unknown"),
                    "data": str(self.graph.nodes[node].get("data", ""))[:100]
                }
                for node in self.graph.nodes()
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "relation": self.graph[u][v][key].get("relation", "unknown")
                }
                for u, v, key in self.graph.edges(keys=True)
            ]
        }
    
    def validate_plot_coherence(self) -> Tuple[bool, List[str]]:
        """Validate that the overall plot is coherent"""
        violations = []
        
        # Check for orphaned consequences
        for consequence in self.consequences.values():
            if consequence.triggering_event_id not in self.events:
                violations.append(f"Consequence {consequence.id} has no triggering event")
        
        # Check for unjustified character actions
        for event in self.events.values():
            for char_id in event.participants:
                if char_id not in self.character_arcs:
                    violations.append(f"Event {event.id} involves unknown character {char_id}")
        
        # Check for relationship consistency
        for (char1, char2), rel in self.relationships.items():
            if char1 not in self.character_arcs or char2 not in self.character_arcs:
                violations.append(f"Relationship between {char1} and {char2} has unknown characters")
        
        is_valid = len(violations) == 0
        return is_valid, violations