# narrative_graph_core.py
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class Belief:
    statement: str
    confidence: float
    formed_at: int

@dataclass
class Value:
    type: str
    importance: float
    description: str

@dataclass
class Worldview:
    core_beliefs: Dict[str, Belief] = field(default_factory=dict)
    values_hierarchy: Dict[str, float] = field(default_factory=dict)
    biases: List[str] = field(default_factory=list)

    def interpret(self, event: 'Event') -> str:
        """Generate character’s interpretation based on worldview."""
        # Simple heuristic: highest-weight value drives interpretation
        top_value = max(self.values_hierarchy, key=self.values_hierarchy.get)
        return f"{top_value}: {event.context}"

@dataclass
class Relationship:
    trust: float = 1.0
    respect: float = 1.0
    shared_history: List['Event'] = field(default_factory=list)
    tensions: Dict[str, float] = field(default_factory=dict)

@dataclass
class Event:
    participants: List[str]
    context: str
    outcomes: Dict[str, Any] = field(default_factory=dict)
    interpretations: Dict[str, str] = field(default_factory=dict)

@dataclass
class CharacterArc:
    char_id: str
    worldview: Worldview
    relationships: Dict[str, Relationship] = field(default_factory=dict)

@dataclass
class StoryGraph:
    characters: Dict[str, CharacterArc] = field(default_factory=dict)
    events: List[Event] = field(default_factory=list)

    def add_character(self, char_id: str, worldview: Worldview) -> CharacterArc:
        arc = CharacterArc(char_id=char_id, worldview=worldview)
        self.characters[char_id] = arc
        return arc

    def add_event(self, event: Event) -> None:
        # Generate interpretations for each participant
        for pid in event.participants:
            if pid in self.characters:
                event.interpretations[pid] = self.characters[pid].worldview.interpret(event)
        self.events.append(event)
        # Update relationships based on divergent interpretations
        self._update_relationships(event)

    def _update_relationships(self, event: Event) -> None:
        # Decay trust/respect when interpretations diverge
        for a, b in zip(event.participants, event.participants[1:]):
            if a in self.characters and b in self.characters:
                rel = self.characters[a].relationships.setdefault(b, Relationship())
                rel.shared_history.append(event)
                # Simple heuristic: divergent interpretations increase tension
                ia, ib = event.interpretations.get(a, ''), event.interpretations.get(b, '')
                if ia != ib:
                    rel.trust *= 0.95
                    rel.respect *= 0.97