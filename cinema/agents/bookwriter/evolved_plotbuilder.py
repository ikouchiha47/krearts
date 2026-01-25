"""
Self-Evolving Story Graph Workflow Integration

This module provides a workflow node that replaces PlotStructureBuilder
with a self-evolving story graph system. It integrates with the existing
BookWorkflow and detective_maker pipeline.

Usage:
    # Replace PlotStructureBuilder with EvolvedPlotStructureBuilder
    builder = EvolvedPlotStructureBuilder(use_llm_validation=True)
    result = await builder.run(inputs)
    
    # Output is compatible with existing pipeline
    # result["plot_structure"] can be passed to NarrativeBuilderWithStoryBuilder
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from narrative_graph import (
    StoryGraph,
    CharacterArc,
    Worldview,
    Value,
    ValueType,
    Belief,
    Event,
    EventType,
    RelationshipType,
    ConsequenceEngine,
)

logger = logging.getLogger(__name__)


# ============================================================================
# LLM INTEGRATION FOR VALIDATION
# ============================================================================


class LLMStoryValidator:
    """
    Uses LLM to validate story logic and generate reasoning.
    This is where you'd integrate with your DirectorsContext/OpenAI.
    """
    
    def __init__(self, ctx=None):
        self.ctx = ctx  # DirectorsContext from your pipeline
    
    async def validate_consequence(
        self,
        event: Event,
        consequence: Any,  # Consequence object
        char1_arc: CharacterArc,
        char2_arc: Optional[CharacterArc],
        relationship: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Ask LLM: Is this consequence believable given character arcs?
        
        This replaces the heuristic validation in ConsequenceEngine
        with actual LLM reasoning.
        """
        
        # Build prompt
        prompt = self._build_validation_prompt(
            event, consequence, char1_arc, char2_arc, relationship
        )
        
        # Call LLM (integrate with your existing LLM setup)
        if self.ctx:
            # Use your existing LLM infrastructure
            response = await self._call_llm(prompt)
        else:
            # Fallback to heuristic validation
            engine = ConsequenceEngine()
            is_valid, reasoning, confidence = engine.evaluate_consequence_validity(
                event, consequence, char1_arc, char2_arc, relationship
            )
            return {
                "valid": is_valid,
                "reasoning": reasoning,
                "confidence": confidence,
                "suggested_improvements": []
            }
        
        return self._parse_llm_response(response)
    
    def _build_validation_prompt(
        self,
        event: Event,
        consequence: Any,
        char1_arc: CharacterArc,
        char2_arc: Optional[CharacterArc],
        relationship: Optional[Any]
    ) -> str:
        """Build LLM prompt for consequence validation"""
        
        prompt_parts = [
            "# Story Consequence Validation",
            "",
            "## Character A Arc",
            f"- ID: {char1_arc.character_id}",
            f"- Growth trajectory: {char1_arc.growth_trajectory}",
            f"- Worldview shifts: {len(char1_arc.worldview_shifts)}",
            f"- Experiences: {len(char1_arc.experiences)}",
        ]
        
        # Add top values
        top_values = sorted(
            char1_arc.worldview.values_hierarchy,
            key=lambda v: v.importance,
            reverse=True
        )[:3]
        
        if top_values:
            prompt_parts.append("- Core values:")
            for v in top_values:
                prompt_parts.append(f"  - {v.type.value}: {v.description} (importance: {v.importance})")
        
        # Add Character B if present
        if char2_arc:
            prompt_parts.extend([
                "",
                "## Character B Arc",
                f"- ID: {char2_arc.character_id}",
                f"- Growth trajectory: {char2_arc.growth_trajectory}",
                f"- Worldview shifts: {len(char2_arc.worldview_shifts)}",
                f"- Experiences: {len(char2_arc.experiences)}",
            ])
            
            top_values_b = sorted(
                char2_arc.worldview.values_hierarchy,
                key=lambda v: v.importance,
                reverse=True
            )[:3]
            
            if top_values_b:
                prompt_parts.append("- Core values:")
                for v in top_values_b:
                    prompt_parts.append(f"  - {v.type.value}: {v.description} (importance: {v.importance})")
        
        # Add relationship context
        if relationship:
            prompt_parts.extend([
                "",
                "## Relationship",
                f"- Type: {relationship.relationship_type.value}",
                f"- Trust level: {relationship.trust_level} (-1 to 1)",
                f"- Shared experiences: {len(relationship.shared_experiences)}",
                f"- Conflicts: {len(relationship.conflicts)}",
            ])
        
        # Add event
        prompt_parts.extend([
            "",
            "## Triggering Event",
            f"- Type: {event.type.value}",
            f"- Description: {event.description}",
            f"- Stakes: {event.stakes}",
            f"- Participants: {', '.join(event.participants)}",
        ])
        
        # Add proposed consequence
        prompt_parts.extend([
            "",
            "## Proposed Consequence",
            f"- Description: {consequence.description}",
            f"- Severity: {consequence.severity}",
            f"- Affected: {', '.join(consequence.affected_characters)}",
            f"- Reversible: {consequence.reversible}",
        ])
        
        # Add validation questions
        prompt_parts.extend([
            "",
            "## Validation Questions",
            "",
            "Is this consequence:",
            "1. **Logically consistent** with the event and character arcs?",
            "2. **Emotionally believable** given the characters' worldviews?",
            "3. **Narratively earned** - have the characters developed enough?",
            "",
            "Provide:",
            "- Overall assessment (VALID/INVALID/NEEDS_REVISION)",
            "- Detailed reasoning for each question",
            "- Confidence score (0.0 to 1.0)",
            "- Suggested improvements if needed",
        ])
        
        return "\n".join(prompt_parts)
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM with prompt - integrate with your existing setup"""
        # TODO: Integrate with your DirectorsContext
        # For now, return placeholder
        return "VALID\nReasoning: All checks pass.\nConfidence: 0.85"
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        lines = response.strip().split("\n")
        
        valid = "VALID" in lines[0].upper()
        reasoning = "\n".join(lines[1:])
        
        # Extract confidence if present
        confidence = 0.8  # default
        for line in lines:
            if "confidence" in line.lower():
                try:
                    confidence = float(line.split(":")[-1].strip())
                except:
                    pass
        
        return {
            "valid": valid,
            "reasoning": reasoning,
            "confidence": confidence,
            "suggested_improvements": []
        }
    
    async def generate_event_interpretations(
        self,
        event: Event,
        char1_arc: CharacterArc,
        char2_arc: CharacterArc
    ) -> Dict[str, str]:
        """
        Generate how each character interprets the same event.
        This is key for "friends turning enemies" - they see events differently.
        """
        
        prompt = f"""
# Event Interpretation

Two characters witness the same event but may interpret it differently based on their worldviews.

## Character 1: {char1_arc.character_id}
Core values: {', '.join(v.type.value for v in char1_arc.worldview.values_hierarchy[:3])}
Recent experiences: {len(char1_arc.experiences)}

## Character 2: {char2_arc.character_id}
Core values: {', '.join(v.type.value for v in char2_arc.worldview.values_hierarchy[:3])}
Recent experiences: {len(char2_arc.experiences)}

## Event
{event.description}

How does each character interpret this event? What do they think it means?
What emotions does it trigger based on their values?
"""
        
        if self.ctx:
            response = await self._call_llm(prompt)
        else:
            # Fallback
            response = f"""
Character 1 sees it as: {event.description} (through lens of {char1_arc.worldview.values_hierarchy[0].type.value if char1_arc.worldview.values_hierarchy else 'survival'})
Character 2 sees it as: {event.description} (through lens of {char2_arc.worldview.values_hierarchy[0].type.value if char2_arc.worldview.values_hierarchy else 'survival'})
"""
        
        # Parse interpretations
        return {
            char1_arc.character_id: response.split("\n")[0],
            char2_arc.character_id: response.split("\n")[1] if len(response.split("\n")) > 1 else ""
        }


# ============================================================================
# EVOLVED PLOT STRUCTURE BUILDER
# ============================================================================


class EvolvedPlotStructureBuilder:
    """
    Replaces PlotStructureBuilder from detective_maker.py
    
    Instead of using fixed constraints (killer, victim, etc.),
    this builds a self-evolving story graph where relationships
    and plot developments emerge naturally.
    
    Output format is compatible with existing pipeline.
    """
    
    def __init__(
        self,
        use_llm_validation: bool = True,
        ctx = None,
        min_events: int = 10,
        min_consequences: int = 5
    ):
        self.use_llm_validation = use_llm_validation
        self.ctx = ctx
        self.min_events = min_events
        self.min_consequences = min_consequences
        
        self.graph = StoryGraph()
        self.validator = LLMStoryValidator(ctx) if use_llm_validation else None
    
    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point - replaces PlotStructureBuilder.run()
        
        Inputs:
            - seed: Story seed/premise
            - characters: List of character descriptions
            - genre: Story genre (optional)
            - target_structure: Desired story structure (optional)
        
        Outputs (compatible with existing pipeline):
            - plot_structure: Same format as PlotStructureBuilder
            - graph: StoryGraph object for validation
        """
        logger.info("=== Evolved Plot Structure Generation ===")
        
        # Extract inputs
        seed = inputs.get("seed", "")
        characters = inputs.get("characters", [])
        genre = inputs.get("genre", "drama")
        
        logger.info(f"  Seed: {seed[:100]}...")
        logger.info(f"  Characters: {len(characters)}")
        logger.info(f"  Genre: {genre}")
        
        # Step 1: Initialize characters
        await self._initialize_characters(characters, genre)
        
        # Step 2: Set up initial relationships
        await self._initialize_relationships()
        
        # Step 3: Generate story events (self-evolving)
        events = await self._generate_story_events(seed, genre)
        
        # Step 4: Validate plot coherence
        is_valid, violations = self.graph.validate_plot_coherence()
        
        if not is_valid:
            logger.warning("Plot has coherence issues:")
            for v in violations:
                logger.warning(f"  - {v}")
            # Could retry here or fix violations
        
        # Step 5: Export in compatible format
        plot_structure = self._export_compatible_format()
        
        logger.info(f"✓ Generated {len(events)} events with {len(self.graph.consequences)} consequences")
        
        return {
            **inputs,
            "plot_structure": plot_structure,
            "graph": self.graph,
        }
    
    async def _initialize_characters(
        self,
        character_descriptions: List[Any],
        genre: str
    ):
        """Initialize characters with worldviews"""
        
        for i, char_desc in enumerate(character_descriptions):
            # Parse character description (could be string or dict)
            if isinstance(char_desc, dict):
                char_id = char_desc.get("id", f"char_{i}")
                name = char_desc.get("name", f"Character {i}")
                values = char_desc.get("values", [])
            else:
                char_id = f"char_{i}"
                name = str(char_desc).split(",")[0].strip()
                values = []
            
            # Create initial worldview
            worldview = await self._generate_initial_worldview(name, genre, values)
            
            # Add to graph
            arc = self.graph.add_character(
                char_id=char_id,
                initial_worldview=worldview,
                growth_trajectory=f"Growth arc for {name}"
            )
            
            logger.info(f"  ✓ Initialized {char_id}: {len(worldview.values_hierarchy)} values")
    
    async def _generate_initial_worldview(
        self,
        character_name: str,
        genre: str,
        provided_values: List[str]
    ) -> Worldview:
        """Generate initial worldview for a character"""
        
        # Use LLM to generate realistic worldview based on genre
        # For now, use heuristics
        
        genre_value_map = {
            "detective": [ValueType.TRUTH, ValueType.JUSTICE, ValueType.DUTY],
            "thriller": [ValueType.SURVIVAL, ValueType.POWER, ValueType.FREEDOM],
            "drama": [ValueType.LOYALTY, ValueType.COMPASSION, ValueType.TRUTH],
            "tragedy": [ValueType.REDEMPTION, ValueType.LOYALTY, ValueType.JUSTICE],
        }
        
        value_types = genre_value_map.get(genre, [ValueType.TRUTH, ValueType.LOYALTY])
        
        # Create values with varying importance
        values = []
        for i, vtype in enumerate(value_types):
            importance = 1.0 - (i * 0.2)  # Descending importance
            values.append(Value(
                type=vtype,
                importance=importance,
                description=f"{character_name} values {vtype.value} highly"
            ))
        
        # Create initial beliefs
        beliefs = {
            "belief_1": Belief(
                statement=f"{character_name} believes in their core values",
                confidence=0.8,
                formed_at=0
            )
        }
        
        return Worldview(
            core_beliefs=beliefs,
            values_hierarchy=values,
            biases=[f"confirmation_bias_toward_{value_types[0].value}"]
        )
    
    async def _initialize_relationships(self):
        """Set up initial relationships between characters"""
        
        char_ids = list(self.graph.character_arcs.keys())
        
        # Create relationships between all character pairs
        for i, char1 in enumerate(char_ids):
            for char2 in char_ids[i+1:]:
                # Start with neutral or slightly positive relationships
                initial_trust = 0.3  # Slight positive default
                
                self.graph.add_relationship(
                    char1_id=char1,
                    char2_id=char2,
                    initial_trust=initial_trust,
                    relationship_type=RelationshipType.NEUTRAL
                )
        
        logger.info(f"  ✓ Initialized {len(self.graph.relationships)//2} relationships")
    
    async def _generate_story_events(
        self,
        seed: str,
        genre: str
    ) -> List[Event]:
        """
        Generate story events that evolve based on character arcs.
        
        This is where the magic happens - each event triggers consequences
        that naturally lead to the next event.
        """
        
        events = []
        beat = 0
        
        # Use LLM to generate event sequence from seed
        # For demo, use predefined event types
        
        event_templates = self._get_event_templates_for_genre(genre)
        
        for i, template in enumerate(event_templates[:self.min_events]):
            beat += 1
            
            # Create event
            event = Event(
                id=f"event_{beat}",
                beat_number=beat,
                type=template["type"],
                description=template["description"],
                participants=template.get("participants", list(self.graph.character_arcs.keys())[:2]),
                stakes=template.get("stakes", 0.5),
                requires_interpretation=template.get("requires_interpretation", False)
            )
            
            # Add event and generate consequences
            consequences = self.graph.add_event(event)
            
            logger.info(f"  Beat {beat}: {event.type.value} -> {len(consequences)} consequences")
            
            # Log important consequences
            for cons in consequences:
                if cons.severity > 0.7:
                    logger.info(f"    ⚠️  Major: {cons.description}")
            
            events.append(event)
        
        return events
    
    def _get_event_templates_for_genre(self, genre: str) -> List[Dict[str, Any]]:
        """Get event templates appropriate for genre"""
        
        # These would ideally come from LLM generation
        # For now, use templates
        
        detective_templates = [
            {
                "type": EventType.DISCOVERY,
                "description": "A body is found",
                "stakes": 0.9,
                "requires_interpretation": False
            },
            {
                "type": EventType.REVELATION,
                "description": "A witness comes forward with conflicting testimony",
                "stakes": 0.6,
                "requires_interpretation": True
            },
            {
                "type": EventType.CONFRONTATION,
                "description": "Partners disagree on investigation approach",
                "stakes": 0.5,
                "requires_interpretation": True
            },
            {
                "type": EventType.BETRAYAL,
                "description": "One partner conceals evidence",
                "stakes": 0.8,
                "requires_interpretation": False
            },
            {
                "type": EventType.DECISION,
                "description": "Must choose between justice and loyalty",
                "stakes": 0.9,
                "requires_interpretation": False
            },
        ]
        
        drama_templates = [
            {
                "type": EventType.CONFLICT,
                "description": "Friends disagree on moral dilemma",
                "stakes": 0.6,
                "requires_interpretation": True
            },
            {
                "type": EventType.REVELATION,
                "description": "Hidden truth comes to light",
                "stakes": 0.7,
                "requires_interpretation": False
            },
            {
                "type": EventType.BETRAYAL,
                "description": "One friend breaks trust",
                "stakes": 0.8,
                "requires_interpretation": False
            },
            {
                "type": EventType.CONFRONTATION,
                "description": "Face-to-face argument about values",
                "stakes": 0.7,
                "requires_interpretation": True
            },
            {
                "type": EventType.SACRIFICE,
                "description": "One must sacrifice for the other",
                "stakes": 0.9,
                "requires_interpretation": False
            },
        ]
        
        genre_map = {
            "detective": detective_templates,
            "drama": drama_templates,
            "thriller": drama_templates,  # Reuse for now
        }
        
        templates = genre_map.get(genre, drama_templates)
        
        # Extend with generic events
        templates.extend([
            {
                "type": EventType.DECISION,
                "description": "Critical choice must be made",
                "stakes": 0.8,
                "requires_interpretation": False
            },
            {
                "type": EventType.LOSS,
                "description": "Something important is lost",
                "stakes": 0.6,
                "requires_interpretation": False
            },
        ])
        
        return templates
    
    def _export_compatible_format(self) -> Dict[str, Any]:
        """
        Export in format compatible with existing pipeline.
        
        This matches the format from PlotStructureBuilder:
        - graph: character and relationship data
        - truth_table: who knows what
        - timeline: chronological events
        - constraints: plot constraints
        """
        
        base_export = self.graph.export_plot_structure()
        
        # Build truth table (who knows what)
        truth_table = self._build_truth_table()
        
        # Build constraints (extract from graph)
        constraints = self._extract_constraints()
        
        return {
            "graph": {
                "characters": [
                    {
                        "id": c["id"],
                        "worldview": c["arc"]["worldview"],
                        "experiences": c["arc"]["experiences"],
                    }
                    for c in base_export["characters"]
                ],
                "relationships": base_export["relationships"],
                "action_sequences": base_export["events"],
            },
            "truth_table": truth_table,
            "timeline": base_export["timeline"],
            "constraints": constraints,
            "causal_chains": base_export["causal_chains"],
            "world_states": base_export["world_states"],
        }
    
    def _build_truth_table(self) -> Dict[str, Any]:
        """Build truth table (who knows what at each beat)"""
        
        truth_table = {}
        
        for beat_state in self.graph.world_states:
            beat = beat_state.beat_number
            truth_table[f"beat_{beat}"] = {
                "facts": beat_state.objective_facts,
                "beliefs": {
                    char_id: [b.statement for b in beliefs.values()]
                    for char_id, beliefs in beat_state.character_beliefs.items()
                }
            }
        
        return truth_table
    
    def _extract_constraints(self) -> Dict[str, Any]:
        """Extract constraints from graph for compatibility"""
        
        # For evolved graphs, constraints are emergent
        # Extract key relationships
        
        constraints = {
            "genre": "evolved",
            "character_count": len(self.graph.character_arcs),
            "event_count": len(self.graph.events),
            "consequence_count": len(self.graph.consequences),
        }
        
        # Find key relationships
        for (char1, char2), rel in self.graph.relationships.items():
            if char1 > char2:  # Only once per pair
                continue
            
            if rel.trust_level < -0.6:
                constraints[f"antagonists"] = constraints.get("antagonists", []) + [(char1, char2)]
            elif rel.trust_level > 0.6:
                constraints[f"allies"] = constraints.get("allies", []) + [(char1, char2)]
        
        return constraints


# ============================================================================
# INTEGRATION WITH EXISTING PIPELINE
# ============================================================================


async def demo_evolved_plot():
    """
    Demo showing how to use EvolvedPlotStructureBuilder
    to replace PlotStructureBuilder in detective_maker.py
    """
    
    print("=== Demo: Self-Evolving Story Graph ===\n")
    
    # Create builder
    builder = EvolvedPlotStructureBuilder(
        use_llm_validation=False,  # Set True when LLM integrated
        min_events=8,
        min_consequences=5
    )
    
    # Prepare inputs (same format as PlotStructureBuilder)
    inputs = {
        "seed": "Two detectives must solve a murder, but they have different ideas about justice",
        "characters": [
            {"id": "detective_a", "name": "Detective Alex", "values": ["justice", "truth"]},
            {"id": "detective_b", "name": "Detective Blake", "values": ["loyalty", "compassion"]},
            {"id": "suspect", "name": "Suspect", "values": ["survival", "freedom"]},
        ],
        "genre": "detective"
    }
    
    # Run builder
    result = await builder.run(inputs)
    
    # Display results
    print("\n=== Results ===")
    print(f"Characters: {len(result['plot_structure']['graph']['characters'])}")
    print(f"Relationships: {len(result['plot_structure']['relationships'])}")
    print(f"Events: {len(result['plot_structure']['timeline'])}")
    print(f"Consequences: {len(result['plot_structure']['causal_chains'])}")
    
    print("\n=== Timeline ===")
    for entry in result['plot_structure']['timeline'][:5]:
        print(f"Beat {entry['beat']}: {entry['type']} - {entry['description']}")
        if entry['consequences']:
            print(f"  -> {len(entry['consequences'])} consequences")
    
    print("\n=== Key Relationships ===")
    for rel in result['plot_structure']['relationships']:
        char1, char2 = rel['char1'], rel['char2']
        trust = rel['state']['trust_level']
        rel_type = rel['state']['relationship_type']
        print(f"{char1} <-> {char2}: {rel_type} (trust: {trust:.2f})")
    
    print("\n=== Validation ===")
    graph = result['graph']
    is_valid, violations = graph.validate_plot_coherence()
    print(f"Plot coherence: {'VALID' if is_valid else 'INVALID'}")
    if violations:
        for v in violations:
            print(f"  - {v}")
    
    print("\n✓ Demo complete!")
    print("\nThis output format is compatible with your existing pipeline.")
    print("You can now pass result['plot_structure'] to NarrativeBuilderWithStoryBuilder")


if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_evolved_plot())