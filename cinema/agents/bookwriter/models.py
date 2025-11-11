"""
Shared data models for detective plot generation.
Separated to avoid circular imports between detective.py and crew.py
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import networkx as nx
import logging

logger = logging.getLogger(__name__)


def to_md_list(items: list[str]) -> str:
    """Convert list of strings to markdown list format"""
    return "\n".join([f"- {item}" for item in items])


class ActionType(Enum):
    KILLED = "killed"
    FRAMED = "framed"
    WITNESSED = "witnessed"
    DISCOVERED = "discovered"
    BETRAYED = "betrayed"
    ALLIED_WITH = "allied_with"


@dataclass
class Character:
    name: str
    role: str
    faction: Optional[str] = None
    traits: List[str] = field(default_factory=list)


@dataclass
class Relationship:
    source: str
    target: str
    action: ActionType
    time: int
    location: str
    motive: str
    witnessed_by: List[str] = field(default_factory=list)


@dataclass
class PlotConstraints:
    """User-controllable plot constraints"""
    killer: str
    victim: str
    accomplices: List[str] = field(default_factory=list)
    framed_suspect: Optional[str] = None
    witnesses: List[Tuple[str, str]] = field(default_factory=list)  # (witness, what_they_saw)
    factions: Dict[str, List[str]] = field(default_factory=dict)  # faction_name: [members]
    winners: List[str] = field(default_factory=list)  # Who benefits
    losers: List[str] = field(default_factory=list)  # Who loses
    betrayals: List[Tuple[str, str]] = field(default_factory=list)  # (betrayer, betrayed)
    alliances: List[Tuple[str, str]] = field(default_factory=list)  # (ally1, ally2)

    def to_crew(self) -> Dict:
        """Convert to CrewAI-compatible format (no tuples, use markdown lists)"""
        return {
            "killer": self.killer,
            "victim": self.victim,
            "accomplices": to_md_list(self.accomplices) if self.accomplices else "None",
            "framed_suspect": self.framed_suspect or "None",
            "witnesses": to_md_list([f"{w[0]}: {w[1]}" for w in self.witnesses]) if self.witnesses else "None",
            "winners": to_md_list(self.winners) if self.winners else "None",
            "losers": to_md_list(self.losers) if self.losers else "None",
            "betrayals": to_md_list([f"{b[0]} betrayed {b[1]}" for b in self.betrayals]) if self.betrayals else "None",
            "alliances": to_md_list([f"{a[0]} allied with {a[1]}" for a in self.alliances]) if self.alliances else "None",
        }


class RelationshipGraph:
    """
    Graph representation of all character relationships and actions.
    This is the SOURCE OF TRUTH for plot logic.
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.action_sequences = []
        logger.info("Initialized RelationshipGraph")

    def add_character(self, char: Character):
        """Add character node"""
        self.graph.add_node(
            char.name, role=char.role, faction=char.faction, traits=char.traits
        )
        logger.info(f"Added character: {char.name} ({char.role})")

    def add_relationship(self, rel: Relationship):
        """Add relationship edge"""
        self.graph.add_edge(
            rel.source,
            rel.target,
            action=rel.action,
            time=rel.time,
            location=rel.location,
            motive=rel.motive,
            witnessed_by=rel.witnessed_by,
        )
        self.action_sequences.append(rel)
        logger.info(
            f"Added relationship: {rel.source} -{rel.action.value}-> {rel.target} @ t={rel.time}"
        )

    def get_action_timeline(self) -> List[Relationship]:
        """Get chronologically sorted actions"""
        return sorted(self.action_sequences, key=lambda x: x.time)

    def get_character_actions(self, char_name: str) -> List[Relationship]:
        """Get all actions performed BY a character"""
        return [r for r in self.action_sequences if r.source == char_name]

    def get_actions_on_character(self, char_name: str) -> List[Relationship]:
        """Get all actions performed ON a character"""
        return [r for r in self.action_sequences if r.target == char_name]

    def get_witnesses(self, action: Relationship) -> List[str]:
        """Get witnesses to a specific action"""
        return action.witnessed_by

    def validate_consistency(self) -> List[str]:
        """Validate graph consistency using logical rules"""
        from collections import defaultdict
        
        issues = []

        # Rule: Dead characters can't perform actions after death
        deaths = {
            r.target: r.time
            for r in self.action_sequences
            if r.action == ActionType.KILLED
        }
        for rel in self.action_sequences:
            if rel.source in deaths and rel.time > deaths[rel.source]:
                issues.append(
                    f"VIOLATION: {rel.source} acts at t={rel.time} but died at t={deaths[rel.source]}"
                )

        # Rule: Characters can't be in two places at once
        location_timeline = defaultdict(list)
        for rel in self.action_sequences:
            location_timeline[(rel.source, rel.time)].append(rel.location)

        for (char, time), locations in location_timeline.items():
            if len(set(locations)) > 1:
                issues.append(
                    f"VIOLATION: {char} in multiple locations at t={time}: {locations}"
                )

        # Rule: Witnesses must be at the same location
        for rel in self.action_sequences:
            for witness in rel.witnessed_by:
                witness_locs = location_timeline.get((witness, rel.time), [])
                if witness_locs and rel.location not in witness_locs:
                    issues.append(
                        f"VIOLATION: {witness} witnesses {rel.action.value} but not at {rel.location}"
                    )

        return issues

    def export_to_dict(self) -> Dict:
        """Export graph to dictionary format"""
        return {
            "characters": [
                {
                    "name": node,
                    "role": self.graph.nodes[node].get("role"),
                    "faction": self.graph.nodes[node].get("faction"),
                    "traits": self.graph.nodes[node].get("traits", []),
                }
                for node in self.graph.nodes()
            ],
            "relationships": [
                {
                    "source": rel.source,
                    "target": rel.target,
                    "action": rel.action.value,
                    "time": rel.time,
                    "location": rel.location,
                    "motive": rel.motive,
                    "witnessed_by": rel.witnessed_by,
                }
                for rel in self.action_sequences
            ],
        }
