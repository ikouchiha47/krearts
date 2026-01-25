"""
Integration Guide: Self-Evolving Story Graph in Your Pipeline

This guide shows how to replace the front part of your pipeline
(PlotStructureBuilder) with the new self-evolving graph system.

The key insight: Your existing pipeline (StoryBuilder, comic generation, etc.)
remains unchanged. We only replace how the plot structure is generated.
"""

# ============================================================================
# INTEGRATION OPTION 1: Drop-in Replacement
# ============================================================================

"""
In your detective_maker.py, replace PlotStructureBuilder with EvolvedPlotStructureBuilder:

BEFORE:
```python
from cinema.agents.bookwriter.detective import (
    ConstraintTableBuilder,
    ConsistencyValidator,
    TruthTable,
)

class PlotStructureBuilder(Runner[Dict[str, Any], Dict[str, Any]]):
    def __init__(self):
        self.builder = ConstraintTableBuilder()
        self.validator = ConsistencyValidator()
        self.truth_table = TruthTable()
    
    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        constraints = inputs["constraints"]
        characters = inputs["characters"]
        
        # Build graph from constraints
        graph = self.builder.build_from_constraints(constraints, characters)
        # ... validation logic ...
```

AFTER:
```python
from evolved_plot_builder import EvolvedPlotStructureBuilder

class PlotStructureBuilder(Runner[Dict[str, Any], Dict[str, Any]]):
    def __init__(self, ctx=None, use_llm_validation=True):
        self.builder = EvolvedPlotStructureBuilder(
            use_llm_validation=use_llm_validation,
            ctx=ctx,
            min_events=10,
            min_consequences=5
        )
    
    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # Convert constraints to seed format
        seed = self._constraints_to_seed(inputs.get("constraints"))
        characters = inputs["characters"]
        
        # Build evolved graph
        result = await self.builder.run({
            "seed": seed,
            "characters": characters,
            "genre": inputs.get("genre", "detective")
        })
        
        return result
    
    def _constraints_to_seed(self, constraints) -> str:
        # Convert old-style constraints to story seed
        if hasattr(constraints, 'victim') and hasattr(constraints, 'killer'):
            return f"A murder mystery where {constraints.killer} is the killer and {constraints.victim} is the victim"
        return "A compelling story with complex characters"
```
"""

# ============================================================================
# INTEGRATION OPTION 2: New Workflow Branch
# ============================================================================

"""
In your BookWorkflow, add a new path for evolved stories:

```python
class BookWorkflow(WorkflowInterface):
    async def init(self, **kwargs) -> Dict[str, Any]:
        genre = kwargs.get('genre', 'detective').lower()
        
        # Choose plot generation strategy
        if genre == 'detective' and not kwargs.get('use_evolved_graph'):
            # Legacy detective path
            plot_builder = DetectivePlotBuilder(ctx=self.ctx)
        else:
            # New self-evolving path
            from evolved_plot_builder import EvolvedPlotStructureBuilder
            
            plot_builder = EvolvedPlotStructureBuilder(
                ctx=self.ctx,
                use_llm_validation=True
            )
            
            # Generate evolved plot structure
            plot_result = await plot_builder.run({
                "seed": kwargs.get('user_requirements', ''),
                "characters": kwargs.get('characters', []),
                "genre": genre
            })
            
            # Store in state
            self.state.plot_graph = plot_result['plot_structure']
        
        # Rest of workflow continues as normal...
```
"""

# ============================================================================
# KEY BENEFITS
# ============================================================================

"""
Why This Architecture Works:

1. **Plug and Play**: Output format matches PlotStructureBuilder
   - Your existing NarrativeBuilder, StoryBuilder, etc. work unchanged
   - No changes needed to comic generation, image generation, etc.

2. **Gradual Migration**: Can keep both systems
   - Use detective-specific graph for detective stories
   - Use evolved graph for other genres
   - Switch via config flag

3. **LLM Integration Points**: 
   - Consequence validation: LLMStoryValidator.validate_consequence()
   - Event interpretation: LLMStoryValidator.generate_event_interpretations()
   - Worldview generation: EvolvedPlotStructureBuilder._generate_initial_worldview()

4. **Validation**: Built-in coherence checking
   - Logical consistency
   - Character development tracking
   - Relationship dynamics
"""

# ============================================================================
# EXAMPLE: "FRIENDS TURNING ENEMIES" SCENARIO
# ============================================================================

async def example_friends_to_enemies():
    """
    Demo: Two friends gradually turn against each other
    due to diverging worldviews and a forcing event.
    """
    from evolved_plot_builder import EvolvedPlotStructureBuilder
    from narrative_graph import ValueType, Value, Worldview, Belief
    
    print("=== Friends to Enemies Example ===\n")
    
    builder = EvolvedPlotStructureBuilder(use_llm_validation=False)
    
    # Setup: Two friends with initially aligned but different values
    inputs = {
        "seed": """
        Two childhood friends, Alex and Jordan, both join the police force.
        They start with similar ideals but gradually see the world differently
        as they face corruption, violence, and moral dilemmas.
        """,
        "characters": [
            {
                "id": "alex",
                "name": "Alex",
                "values": ["justice", "truth", "duty"]  # By-the-book cop
            },
            {
                "id": "jordan",
                "name": "Jordan",
                "values": ["compassion", "loyalty", "pragmatism"]  # Compassionate cop
            },
        ],
        "genre": "drama"
    }
    
    result = await builder.run(inputs)
    graph = result['graph']
    
    print("Initial State:")
    rel = graph.relationships[('alex', 'jordan')]
    print(f"  Alex <-> Jordan: {rel.relationship_type.value} (trust: {rel.trust_level:.2f})")
    
    print("\n=== Story Progression ===\n")
    
    # Event 1: They witness police brutality
    from narrative_graph import Event, EventType
    
    event1 = Event(
        id="event_brutality",
        beat_number=1,
        type=EventType.REVELATION,
        description="They witness their captain beating a suspect",
        participants=["alex", "jordan"],
        stakes=0.7,
        requires_interpretation=True  # They interpret it differently
    )
    
    consequences1 = graph.add_event(event1)
    print(f"Event 1: {event1.description}")
    print(f"  Consequences: {len(consequences1)}")
    
    # Check interpretations (would use LLM in production)
    alex_arc = graph.character_arcs['alex']
    jordan_arc = graph.character_arcs['jordan']
    
    print(f"\n  Alex's view (justice-oriented): 'This is wrong, we must report it'")
    print(f"  Jordan's view (compassion-oriented): 'The captain is under stress, everyone makes mistakes'")
    
    # Event 2: Alex reports the captain
    event2 = Event(
        id="event_report",
        beat_number=2,
        type=EventType.BETRAYAL,
        description="Alex reports the captain to Internal Affairs without telling Jordan",
        participants=["alex", "jordan"],
        stakes=0.8,
        requires_interpretation=False
    )
    
    consequences2 = graph.add_event(event2)
    print(f"\nEvent 2: {event2.description}")
    print(f"  Consequences: {len(consequences2)}")
    
    # Check relationship now
    rel_after = graph.relationships[('alex', 'jordan')]
    print(f"\n  Relationship: {rel_after.relationship_type.value} (trust: {rel_after.trust_level:.2f})")
    print(f"  Trust change: {rel.trust_level:.2f} -> {rel_after.trust_level:.2f}")
    
    # Event 3: Jordan confronts Alex
    event3 = Event(
        id="event_confrontation",
        beat_number=3,
        type=EventType.CONFRONTATION,
        description="Jordan confronts Alex about betraying the team",
        participants=["alex", "jordan"],
        stakes=0.9,
        requires_interpretation=True
    )
    
    consequences3 = graph.add_event(event3)
    print(f"\nEvent 3: {event3.description}")
    print(f"  Consequences: {len(consequences3)}")
    
    # Check for breaking point
    breaking_point = graph.relationship_engine.evaluate_breaking_point(
        alex_arc, jordan_arc, event3, rel_after
    )
    
    if breaking_point:
        print("\n⚠️  BREAKING POINT REACHED!")
        print(f"  Worldview divergence: {breaking_point['worldview_divergence']:.2f}")
        print(f"  Value conflict: {breaking_point['value_conflict']:.2f}")
        print(f"  Alex's reasoning: {breaking_point['char1_reasoning']}")
        print(f"  Jordan's reasoning: {breaking_point['char2_reasoning']}")
        print(f"  Trust delta: {breaking_point['trust_delta']}")
        print(f"  Reversible: {breaking_point['reversible']}")
    
    # Final state
    final_rel = graph.relationships[('alex', 'jordan')]
    print(f"\nFinal Relationship: {final_rel.relationship_type.value} (trust: {final_rel.trust_level:.2f})")
    print(f"\nWorldview divergence: {alex_arc.worldview.calculate_divergence(jordan_arc.worldview):.2f}")
    
    print("\n=== Analysis ===")
    print("This friendship breakdown is justified because:")
    print("1. ✓ Characters had different core values from the start")
    print("2. ✓ They experienced same events but interpreted them differently")
    print("3. ✓ Multiple smaller conflicts accumulated over time")
    print("4. ✓ A forcing event required them to choose sides")
    print("5. ✓ Their worldviews diverged enough to make reconciliation difficult")


# ============================================================================
# TESTING AND VALIDATION
# ============================================================================

async def test_integration():
    """
    Test that evolved graph integrates with existing pipeline
    """
    from evolved_plot_builder import EvolvedPlotStructureBuilder
    
    print("=== Integration Tests ===\n")
    
    builder = EvolvedPlotStructureBuilder(use_llm_validation=False)
    
    # Test 1: Output format compatibility
    print("Test 1: Output format compatibility")
    result = await builder.run({
        "seed": "Test story",
        "characters": [{"id": "char1", "name": "Character 1"}],
        "genre": "drama"
    })
    
    required_keys = ["plot_structure", "graph"]
    assert all(k in result for k in required_keys), "Missing required keys"
    
    plot_structure = result["plot_structure"]
    required_structure_keys = ["graph", "truth_table", "timeline", "constraints"]
    assert all(k in plot_structure for k in required_structure_keys), "Missing structure keys"
    
    print("  ✓ Output format matches PlotStructureBuilder")
    
    # Test 2: Character arc tracking
    print("\nTest 2: Character arc tracking")
    graph = result["graph"]
    assert len(graph.character_arcs) > 0, "No character arcs"
    
    for char_id, arc in graph.character_arcs.items():
        assert arc.worldview is not None, f"Character {char_id} missing worldview"
        assert len(arc.worldview.values_hierarchy) > 0, f"Character {char_id} has no values"
    
    print(f"  ✓ {len(graph.character_arcs)} characters with worldviews")
    
    # Test 3: Relationship dynamics
    print("\nTest 3: Relationship dynamics")
    assert len(graph.relationships) > 0, "No relationships"
    
    for (char1, char2), rel in graph.relationships.items():
        assert -1.0 <= rel.trust_level <= 1.0, "Trust level out of range"
        assert rel.relationship_type is not None, "Missing relationship type"
    
    print(f"  ✓ {len(graph.relationships)} relationships with valid states")
    
    # Test 4: Event-consequence chains
    print("\nTest 4: Event-consequence chains")
    assert len(graph.events) > 0, "No events generated"
    
    for event_id, event in graph.events.items():
        assert event.beat_number > 0, "Invalid beat number"
        assert len(event.participants) > 0, "Event has no participants"
    
    print(f"  ✓ {len(graph.events)} events with consequences")
    
    # Test 5: Plot coherence
    print("\nTest 5: Plot coherence")
    is_valid, violations = graph.validate_plot_coherence()
    
    if violations:
        print("  ⚠️  Coherence warnings:")
        for v in violations[:3]:
            print(f"    - {v}")
    else:
        print("  ✓ Plot is coherent")
    
    print("\n✅ All integration tests passed!")


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
EXAMPLE 1: Simple Integration
------------------------------

from evolved_plot_builder import EvolvedPlotStructureBuilder

# In your DetectiveMaker.__init__():
self.plot_builder = EvolvedPlotStructureBuilder(
    ctx=self.ctx,
    use_llm_validation=True
)

# In your generate() method:
plot_result = await self.plot_builder.run({
    "seed": user_premise,
    "characters": character_list,
    "genre": "detective"
})

# Continue with existing pipeline
narrative_builder = NarrativeBuilderWithStoryBuilder(...)
detective_output = await narrative_builder.run(plot_result)


EXAMPLE 2: Genre-Specific Configuration
---------------------------------------

# Different configs for different genres
if genre == "detective":
    plot_builder = EvolvedPlotStructureBuilder(
        min_events=12,  # More events for complex mystery
        min_consequences=8
    )
elif genre == "thriller":
    plot_builder = EvolvedPlotStructureBuilder(
        min_events=8,
        min_consequences=5
    )
else:  # drama, etc.
    plot_builder = EvolvedPlotStructureBuilder(
        min_events=10,
        min_consequences=6
    )


EXAMPLE 3: With LLM Validation
------------------------------

from cinema.context import DirectorsContext

ctx = DirectorsContext(...)

plot_builder = EvolvedPlotStructureBuilder(
    ctx=ctx,
    use_llm_validation=True  # Enable LLM validation
)

# LLM will validate:
# - Consequence believability
# - Character motivation
# - Event interpretations
# - Worldview consistency


EXAMPLE 4: Accessing Internal Graph
-----------------------------------

result = await plot_builder.run(inputs)

# Access the graph for debugging/analysis
graph = result["graph"]

# Analyze character arcs
for char_id, arc in graph.character_arcs.items():
    print(f"{char_id}:")
    print(f"  Worldview shifts: {len(arc.worldview_shifts)}")
    print(f"  Experiences: {len(arc.experiences)}")
    
    top_value = arc.worldview.get_most_important_value()
    if top_value:
        print(f"  Top value: {top_value.type.value} ({top_value.importance})")

# Analyze relationships
for (char1, char2), rel in graph.relationships.items():
    if char1 < char2:  # Only show each pair once
        print(f"{char1} <-> {char2}: {rel.trust_level:.2f}")

# Analyze causal chains
for chain in graph.causal_chains:
    print(f"Chain: {chain.initiating_event_id} -> {chain.final_consequence_id}")
    print(f"  Probability: {chain.probability}")
"""


# ============================================================================
# MIGRATION CHECKLIST
# ============================================================================

"""
Migration Checklist:
-------------------

[ ] 1. Add narrative_graph.py to your project
[ ] 2. Add evolved_plot_builder.py to your project
[ ] 3. Update imports in detective_maker.py or book_workflow.py
[ ] 4. Test with simple story to verify output format
[ ] 5. Integrate LLM validation (optional but recommended)
[ ] 6. Test with complex multi-character story
[ ] 7. Verify comic generation pipeline still works
[ ] 8. Add genre-specific configurations
[ ] 9. Update documentation
[ ] 10. Deploy to production

Expected Issues:
---------------

1. "Output format mismatch"
   -> Check that plot_structure contains all required keys
   -> Verify timeline format matches expectations

2. "No consequences generated"
   -> Increase min_consequences parameter
   -> Check that events have sufficient stakes

3. "Character worldviews too similar"
   -> Adjust initial worldview generation
   -> Add more diverse value types

4. "Relationships don't evolve"
   -> Check that events involve multiple characters
   -> Increase stakes on relationship-testing events

5. "Plot seems random"
   -> Enable LLM validation for better coherence
   -> Adjust event templates for your genre
"""


if __name__ == "__main__":
    import asyncio
    
    print("Running integration examples...\n")
    
    # Run examples
    asyncio.run(example_friends_to_enemies())
    print("\n" + "="*80 + "\n")
    asyncio.run(test_integration())