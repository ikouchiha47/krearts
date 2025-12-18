"""
Genre-Agnostic Plot Graph Validator

This module provides a flexible graph-based validation system that works across genres.
It extracts plot structure as a graph (nodes = characters/events, edges = relationships/causality)
and validates based on genre-specific rules.

Architecture:
1. PlotGraphExtractor: LLM extracts graph from storyline
2. GenreValidator: Validates graph based on genre rules
3. ValidationResult: Structured output for UI/debugging
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# GRAPH MODELS (Genre-Agnostic)
# ============================================================================


class NodeType(str, Enum):
    """Types of nodes in plot graph"""
    CHARACTER = "character"
    EVENT = "event"
    LOCATION = "location"
    OBJECT = "object"  # MacGuffin, weapon, artifact


class EdgeType(str, Enum):
    """Types of edges in plot graph"""
    # Character relationships
    ALLIED_WITH = "allied_with"
    OPPOSED_TO = "opposed_to"
    MENTORS = "mentors"
    LOVES = "loves"
    BETRAYS = "betrays"
    
    # Event causality
    CAUSES = "causes"
    PREVENTS = "prevents"
    DISCOVERS = "discovers"
    
    # Participation
    PARTICIPATES_IN = "participates_in"
    WITNESSES = "witnesses"
    
    # Possession
    POSSESSES = "possesses"
    SEEKS = "seeks"


class PlotNode(BaseModel):
    """A node in the plot graph"""
    id: str = Field(..., description="Unique identifier")
    type: NodeType = Field(..., description="Node type")
    name: str = Field(..., description="Display name")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")


class PlotEdge(BaseModel):
    """An edge in the plot graph"""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: EdgeType = Field(..., description="Edge type")
    time: Optional[int] = Field(None, description="When this relationship occurs (timeline order)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")


class PlotGraph(BaseModel):
    """Complete plot graph"""
    nodes: List[PlotNode] = Field(default_factory=list)
    edges: List[PlotEdge] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_networkx(self) -> nx.DiGraph:
        """Convert to NetworkX graph for analysis"""
        G = nx.DiGraph()
        
        # Add nodes
        for node in self.nodes:
            G.add_node(node.id, **node.model_dump())
        
        # Add edges
        for edge in self.edges:
            G.add_edge(edge.source, edge.target, **edge.model_dump())
        
        return G
    
    def get_character_nodes(self) -> List[PlotNode]:
        """Get all character nodes"""
        return [n for n in self.nodes if n.type == NodeType.CHARACTER]
    
    def get_event_nodes(self) -> List[PlotNode]:
        """Get all event nodes"""
        return [n for n in self.nodes if n.type == NodeType.EVENT]
    
    def get_edges_by_type(self, edge_type: EdgeType) -> List[PlotEdge]:
        """Get all edges of a specific type"""
        return [e for e in self.edges if e.type == edge_type]
    
    def get_character_relationships(self, character_id: str) -> List[PlotEdge]:
        """Get all relationships involving a character"""
        return [e for e in self.edges if e.source == character_id or e.target == character_id]


# ============================================================================
# VALIDATION RESULTS
# ============================================================================


class ViolationSeverity(str, Enum):
    """Severity levels for validation violations"""
    CRITICAL = "critical"  # Story is broken
    HIGH = "high"  # Major plot hole
    MEDIUM = "medium"  # Inconsistency
    LOW = "low"  # Minor issue


@dataclass
class Violation:
    """A validation violation"""
    severity: ViolationSeverity
    rule: str
    message: str
    affected_nodes: List[str] = field(default_factory=list)
    affected_edges: List[Tuple[str, str]] = field(default_factory=list)
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of plot graph validation"""
    is_valid: bool
    violations: List[Violation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    graph: Optional[PlotGraph] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "is_valid": self.is_valid,
            "violations": [
                {
                    "severity": v.severity.value,
                    "rule": v.rule,
                    "message": v.message,
                    "affected_nodes": v.affected_nodes,
                    "affected_edges": v.affected_edges,
                    "suggestion": v.suggestion,
                }
                for v in self.violations
            ],
            "warnings": self.warnings,
            "stats": self.stats,
        }
    
    def get_critical_violations(self) -> List[Violation]:
        """Get only critical violations"""
        return [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]
    
    def get_high_violations(self) -> List[Violation]:
        """Get high severity violations"""
        return [v for v in self.violations if v.severity == ViolationSeverity.HIGH]


# ============================================================================
# GENRE VALIDATORS (Abstract Base + Implementations)
# ============================================================================


class GenreValidator(ABC):
    """
    Abstract base class for genre-specific validators.
    
    Each genre implements its own validation rules.
    """
    
    @abstractmethod
    def validate(self, graph: PlotGraph) -> ValidationResult:
        """Validate plot graph according to genre rules"""
        pass
    
    @abstractmethod
    def get_required_node_types(self) -> List[NodeType]:
        """Get required node types for this genre"""
        pass
    
    @abstractmethod
    def get_required_edge_types(self) -> List[EdgeType]:
        """Get required edge types for this genre"""
        pass


class DetectiveValidator(GenreValidator):
    """Validator for detective/mystery stories"""
    
    def get_required_node_types(self) -> List[NodeType]:
        return [NodeType.CHARACTER, NodeType.EVENT]
    
    def get_required_edge_types(self) -> List[EdgeType]:
        return [EdgeType.OPPOSED_TO, EdgeType.DISCOVERS, EdgeType.WITNESSES]
    
    def validate(self, graph: PlotGraph) -> ValidationResult:
        """Validate detective story structure"""
        violations = []
        warnings = []
        
        # Get characters
        characters = graph.get_character_nodes()
        char_ids = {c.id for c in characters}
        
        # Rule 1: Must have detective
        detectives = [c for c in characters if c.properties.get("role") == "detective"]
        if not detectives:
            violations.append(Violation(
                severity=ViolationSeverity.CRITICAL,
                rule="detective_required",
                message="Story must have at least one detective character",
                suggestion="Add a character with role='detective'"
            ))
        
        # Rule 2: Must have victim
        victims = [c for c in characters if c.properties.get("role") == "victim"]
        if not victims:
            violations.append(Violation(
                severity=ViolationSeverity.CRITICAL,
                rule="victim_required",
                message="Detective story must have a victim",
                suggestion="Add a character with role='victim'"
            ))
        
        # Rule 3: Must have killer
        killers = [c for c in characters if c.properties.get("role") == "killer"]
        if not killers:
            violations.append(Violation(
                severity=ViolationSeverity.CRITICAL,
                rule="killer_required",
                message="Detective story must have a killer",
                suggestion="Add a character with role='killer'"
            ))
        
        # Rule 4: Killer must have motive (edge to victim)
        if killers and victims:
            killer_id = killers[0].id
            victim_id = victims[0].id
            
            # Check for relationship between killer and victim
            killer_victim_edges = [
                e for e in graph.edges
                if (e.source == killer_id and e.target == victim_id) or
                   (e.source == victim_id and e.target == killer_id)
            ]
            
            if not killer_victim_edges:
                violations.append(Violation(
                    severity=ViolationSeverity.HIGH,
                    rule="killer_motive_required",
                    message="Killer must have relationship with victim (motive)",
                    affected_nodes=[killer_id, victim_id],
                    suggestion="Add edge showing killer's connection to victim"
                ))
        
        # Rule 5: Must have clues (discoveries)
        discovery_edges = graph.get_edges_by_type(EdgeType.DISCOVERS)
        if len(discovery_edges) < 3:
            violations.append(Violation(
                severity=ViolationSeverity.HIGH,
                rule="insufficient_clues",
                message=f"Detective story needs at least 3 clues, found {len(discovery_edges)}",
                suggestion="Add more discovery events (clues)"
            ))
        
        # Rule 6: Detective must discover clues
        if detectives:
            detective_id = detectives[0].id
            detective_discoveries = [e for e in discovery_edges if e.source == detective_id]
            
            if len(detective_discoveries) < 2:
                violations.append(Violation(
                    severity=ViolationSeverity.MEDIUM,
                    rule="detective_must_discover",
                    message="Detective must discover at least 2 clues",
                    affected_nodes=[detective_id],
                    suggestion="Add discovery edges from detective to clues"
                ))
        
        # Rule 7: Check for witnesses
        witness_edges = graph.get_edges_by_type(EdgeType.WITNESSES)
        if not witness_edges:
            warnings.append("No witnesses found - consider adding for complexity")
        
        # Rule 8: Check for red herrings (framed suspects)
        framed = [c for c in characters if c.properties.get("role") == "framed_suspect"]
        if not framed:
            warnings.append("No red herrings (framed suspects) - story may be too simple")
        
        # Stats
        stats = {
            "total_characters": len(characters),
            "detectives": len(detectives),
            "victims": len(victims),
            "killers": len(killers),
            "witnesses": len(witness_edges),
            "clues": len(discovery_edges),
            "red_herrings": len(framed),
        }
        
        is_valid = len([v for v in violations if v.severity in [ViolationSeverity.CRITICAL, ViolationSeverity.HIGH]]) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            violations=violations,
            warnings=warnings,
            stats=stats,
            graph=graph
        )


class ShonenBattleValidator(GenreValidator):
    """Validator for shonen battle stories"""
    
    def get_required_node_types(self) -> List[NodeType]:
        return [NodeType.CHARACTER, NodeType.EVENT]
    
    def get_required_edge_types(self) -> List[EdgeType]:
        return [EdgeType.OPPOSED_TO, EdgeType.MENTORS]
    
    def validate(self, graph: PlotGraph) -> ValidationResult:
        """Validate shonen battle structure"""
        violations = []
        warnings = []
        
        characters = graph.get_character_nodes()
        
        # Rule 1: Must have protagonist
        protagonists = [c for c in characters if c.properties.get("role") == "protagonist"]
        if not protagonists:
            violations.append(Violation(
                severity=ViolationSeverity.CRITICAL,
                rule="protagonist_required",
                message="Story must have a protagonist",
                suggestion="Add a character with role='protagonist'"
            ))
        
        # Rule 2: Must have antagonist/villain
        villains = [c for c in characters if c.properties.get("role") in ["arc_villain", "final_boss"]]
        if not villains:
            violations.append(Violation(
                severity=ViolationSeverity.CRITICAL,
                rule="villain_required",
                message="Battle story must have a villain",
                suggestion="Add a character with role='arc_villain' or 'final_boss'"
            ))
        
        # Rule 3: Protagonist should have mentor
        mentors = [c for c in characters if c.properties.get("role") == "mentor"]
        if not mentors:
            warnings.append("No mentor found - protagonist may lack guidance")
        else:
            # Check if mentor actually mentors protagonist
            if protagonists:
                mentor_edges = [
                    e for e in graph.edges
                    if e.type == EdgeType.MENTORS and
                       e.source == mentors[0].id and
                       e.target == protagonists[0].id
                ]
                if not mentor_edges:
                    violations.append(Violation(
                        severity=ViolationSeverity.MEDIUM,
                        rule="mentor_relationship_missing",
                        message="Mentor exists but doesn't mentor protagonist",
                        affected_nodes=[mentors[0].id, protagonists[0].id],
                        suggestion="Add mentors edge from mentor to protagonist"
                    ))
        
        # Rule 4: Should have rival
        rivals = [c for c in characters if c.properties.get("role") == "rival"]
        if not rivals:
            warnings.append("No rival found - consider adding for character growth")
        
        # Rule 5: Should have team members
        team = [c for c in characters if c.properties.get("role") == "team"]
        if len(team) < 2:
            warnings.append("Few team members - shonen stories typically have 2-4 allies")
        
        # Rule 6: Protagonist must oppose villain
        if protagonists and villains:
            opposition_edges = [
                e for e in graph.edges
                if e.type == EdgeType.OPPOSED_TO and
                   ((e.source == protagonists[0].id and e.target == villains[0].id) or
                    (e.source == villains[0].id and e.target == protagonists[0].id))
            ]
            if not opposition_edges:
                violations.append(Violation(
                    severity=ViolationSeverity.HIGH,
                    rule="protagonist_villain_conflict",
                    message="Protagonist must be in conflict with villain",
                    affected_nodes=[protagonists[0].id, villains[0].id],
                    suggestion="Add opposed_to edge between protagonist and villain"
                ))
        
        # Rule 7: Check power system
        power_system = graph.metadata.get("power_system")
        if not power_system:
            warnings.append("No power system defined - shonen battles need clear power rules")
        
        # Stats
        stats = {
            "total_characters": len(characters),
            "protagonists": len(protagonists),
            "villains": len(villains),
            "mentors": len(mentors),
            "rivals": len(rivals),
            "team_members": len(team),
            "has_power_system": bool(power_system),
        }
        
        is_valid = len([v for v in violations if v.severity in [ViolationSeverity.CRITICAL, ViolationSeverity.HIGH]]) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            violations=violations,
            warnings=warnings,
            stats=stats,
            graph=graph
        )


class CyberpunkValidator(GenreValidator):
    """Validator for cyberpunk stories"""
    
    def get_required_node_types(self) -> List[NodeType]:
        return [NodeType.CHARACTER, NodeType.EVENT, NodeType.OBJECT]
    
    def get_required_edge_types(self) -> List[EdgeType]:
        return [EdgeType.OPPOSED_TO, EdgeType.SEEKS]
    
    def validate(self, graph: PlotGraph) -> ValidationResult:
        """Validate cyberpunk structure"""
        violations = []
        warnings = []
        
        characters = graph.get_character_nodes()
        
        # Rule 1: Must have protagonist (hacker/rebel)
        protagonists = [c for c in characters if c.properties.get("role") in ["hacker", "street_kid", "protagonist"]]
        if not protagonists:
            violations.append(Violation(
                severity=ViolationSeverity.CRITICAL,
                rule="protagonist_required",
                message="Cyberpunk story must have a protagonist (hacker/rebel)",
                suggestion="Add a character with role='hacker' or 'street_kid'"
            ))
        
        # Rule 2: Must have system/corporation antagonist
        antagonists = [c for c in characters if c.properties.get("role") in ["corpo", "ai", "system"]]
        if not antagonists:
            violations.append(Violation(
                severity=ViolationSeverity.CRITICAL,
                rule="system_antagonist_required",
                message="Cyberpunk story must have system/corporate antagonist",
                suggestion="Add a character with role='corpo' or 'system'"
            ))
        
        # Rule 3: Should have MacGuffin (data, tech, artifact)
        objects = [n for n in graph.nodes if n.type == NodeType.OBJECT]
        if not objects:
            warnings.append("No MacGuffin (data/tech/artifact) - cyberpunk often has object of desire")
        
        # Rule 4: Check for class divide theme
        class_divide = graph.metadata.get("themes", {}).get("class_divide")
        if not class_divide:
            warnings.append("No class divide theme - core to cyberpunk genre")
        
        # Rule 5: Technology level
        tech_level = graph.metadata.get("world_context", {}).get("technology_level")
        if not tech_level or "cyber" not in tech_level.lower():
            warnings.append("Technology level not clearly cyberpunk (cybernetics, AI, VR)")
        
        # Stats
        stats = {
            "total_characters": len(characters),
            "protagonists": len(protagonists),
            "antagonists": len(antagonists),
            "macguffins": len(objects),
            "has_class_divide_theme": bool(class_divide),
            "has_cyberpunk_tech": bool(tech_level and "cyber" in tech_level.lower()),
        }
        
        is_valid = len([v for v in violations if v.severity in [ViolationSeverity.CRITICAL, ViolationSeverity.HIGH]]) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            violations=violations,
            warnings=warnings,
            stats=stats,
            graph=graph
        )


# ============================================================================
# VALIDATOR FACTORY
# ============================================================================


class ValidatorFactory:
    """Factory for creating genre-specific validators"""
    
    _validators: Dict[str, type[GenreValidator]] = {
        "detective": DetectiveValidator,
        "mystery": DetectiveValidator,
        "shonen": ShonenBattleValidator,
        "battle": ShonenBattleValidator,
        "cyberpunk": CyberpunkValidator,
        "sci-fi": CyberpunkValidator,
    }
    
    @classmethod
    def register_validator(cls, genre: str, validator_class: type[GenreValidator]):
        """Register a new genre validator"""
        cls._validators[genre.lower()] = validator_class
    
    @classmethod
    def get_validator(cls, genre: str) -> GenreValidator:
        """Get validator for genre"""
        genre_lower = genre.lower()
        if genre_lower not in cls._validators:
            raise ValueError(f"No validator registered for genre: {genre}")
        return cls._validators[genre_lower]()
    
    @classmethod
    def list_supported_genres(cls) -> List[str]:
        """List all supported genres"""
        return list(cls._validators.keys())


# ============================================================================
# PLOT GRAPH EXTRACTOR (LLM-Based)
# ============================================================================


class PlotGraphExtractor:
    """
    Extracts plot graph from storyline using LLM.
    
    This is the LLM component that reads the storyline and outputs structured graph data.
    """
    
    def __init__(self):
        """Initialize extractor"""
        pass
    
    async def extract_from_storyline(
        self,
        storyline_text: str,
        genre: str,
        characters: Optional[List[Dict[str, Any]]] = None
    ) -> PlotGraph:
        """
        Extract plot graph from storyline text.
        
        This will be implemented as a CrewAI task that:
        1. Reads the storyline
        2. Identifies characters, events, relationships
        3. Outputs structured PlotGraph
        
        For now, returns empty graph (to be implemented with LLM).
        """
        # TODO: Implement LLM extraction
        # This will be a CrewAI agent with:
        # - Input: storyline_text, genre
        # - Output: PlotGraph (Pydantic model)
        # - Tools: DirectoryReadTool, FileReadTool for genre knowledge
        
        logger.warning("PlotGraphExtractor.extract_from_storyline not yet implemented")
        logger.info(f"Would extract graph from {len(storyline_text)} chars of storyline")
        logger.info(f"Genre: {genre}")
        
        # Return empty graph for now
        return PlotGraph(
            nodes=[],
            edges=[],
            metadata={"genre": genre}
        )


# ============================================================================
# MAIN VALIDATION SYSTEM
# ============================================================================


def convert_plotgraph_output_to_validation_graph(plot_output) -> PlotGraph:
    """
    Convert PlotGraphOutput (from LLM) to PlotGraph (for validation).
    
    Args:
        plot_output: PlotGraphOutput from PlotGraphBuilder crew
    
    Returns:
        PlotGraph ready for validation
    """
    nodes = []
    edges = []
    
    # Convert characters to nodes
    for char in plot_output.characters:
        node = PlotNode(
            id=char.get("name", ""),
            type=NodeType.CHARACTER,
            name=char.get("name", ""),
            properties={
                "role": char.get("role", ""),
                "backstory": char.get("backstory", ""),
                "motivation": char.get("motivation", ""),
                "personality": char.get("personality", ""),
                "skills": char.get("skills", ""),
                "arc": char.get("arc", ""),
            }
        )
        nodes.append(node)
    
    # Convert events to nodes
    for event in plot_output.events:
        node = PlotNode(
            id=event.get("name", ""),
            type=NodeType.EVENT,
            name=event.get("name", ""),
            properties={
                "type": event.get("type", ""),
                "participants": event.get("participants", []),
                "time": event.get("time", 0),
                "location": event.get("location", ""),
                "outcome": event.get("outcome", ""),
            }
        )
        nodes.append(node)
    
    # Convert relationships to edges
    for rel in plot_output.relationships:
        # Map string type to EdgeType enum
        rel_type_str = rel.get("type", "").upper()
        try:
            edge_type = EdgeType[rel_type_str]
        except KeyError:
            # Default to ALLIED_WITH if unknown
            logger.warning(f"Unknown relationship type: {rel_type_str}, defaulting to ALLIED_WITH")
            edge_type = EdgeType.ALLIED_WITH
        
        edge = PlotEdge(
            source=rel.get("source", ""),
            target=rel.get("target", ""),
            type=edge_type,
            time=rel.get("time"),
            properties={
                "strength": rel.get("strength", ""),
                "reason": rel.get("reason", ""),
            }
        )
        edges.append(edge)
    
    # Create graph
    graph = PlotGraph(
        nodes=nodes,
        edges=edges,
        metadata={
            "genres": plot_output.genres,
            "primary_genre": plot_output.primary_genre,
            "title": plot_output.title,
            "theme": plot_output.theme,
            "world_context": plot_output.world_context,
            "genre_metadata": plot_output.genre_metadata,
            "art_style": "",  # Art style is not part of plot structure
            "narrative_structure": plot_output.narrative_structure or "three-act",
        }
    )
    
    return graph


class PlotValidationSystem:
    """
    Main system for plot graph validation.
    
    Usage:
        system = PlotValidationSystem()
        result = await system.validate_storyline(storyline_text, genre="detective")
        
        if not result.is_valid:
            for violation in result.get_critical_violations():
                print(f"CRITICAL: {violation.message}")
    """
    
    def __init__(self):
        self.extractor = PlotGraphExtractor()
    
    def validate_plotgraph_output(self, plot_output) -> ValidationResult:
        """
        Validate a PlotGraphOutput directly (from PlotGraphBuilder crew).
        
        Args:
            plot_output: PlotGraphOutput from LLM
        
        Returns:
            ValidationResult
        """
        # Convert to validation graph
        graph = convert_plotgraph_output_to_validation_graph(plot_output)
        
        # Validate using genre-specific validator (use primary genre)
        return self.validate_graph(graph, plot_output.primary_genre)
    
    async def validate_storyline(
        self,
        storyline_text: str,
        genre: str,
        characters: Optional[List[Dict[str, Any]]] = None
    ) -> ValidationResult:
        """
        Validate storyline by extracting graph and checking genre rules.
        
        Args:
            storyline_text: The storyline markdown text
            genre: Genre name (detective, shonen, cyberpunk, etc.)
            characters: Optional character data
        
        Returns:
            ValidationResult with violations, warnings, and stats
        """
        logger.info(f"Validating {genre} storyline...")
        
        # Step 1: Extract graph from storyline
        graph = await self.extractor.extract_from_storyline(
            storyline_text, genre, characters
        )
        
        # Step 2: Get genre validator
        validator = ValidatorFactory.get_validator(genre)
        
        # Step 3: Validate
        result = validator.validate(graph)
        
        logger.info(f"Validation complete: {'PASS' if result.is_valid else 'FAIL'}")
        logger.info(f"  Violations: {len(result.violations)}")
        logger.info(f"  Warnings: {len(result.warnings)}")
        
        return result
    
    def validate_graph(self, graph: PlotGraph, genre: str) -> ValidationResult:
        """
        Validate an already-extracted graph.
        
        Args:
            graph: PlotGraph to validate
            genre: Genre name
        
        Returns:
            ValidationResult
        """
        validator = ValidatorFactory.get_validator(genre)
        return validator.validate(graph)
