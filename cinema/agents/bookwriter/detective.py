"""
Graph-Based Detective Plot Generator
Completely controllable through constraint tables and relationship graphs.
LLM only fills in narrative descriptions for pre-determined logical structure.
"""

import json
import logging
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import asdict
from collections import defaultdict
import numpy as np

from cinema.agents.bookwriter.models import (
    ActionType,
    Character,
    Relationship,
    PlotConstraints,
    RelationshipGraph,
)

# Import crews only for type hints - avoid circular import at module level
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cinema.agents.bookwriter.crew import DetectivePlotBuilder, ComicStripStoryBoarding

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Classes moved to models.py to avoid circular imports
# Character, Relationship, PlotConstraints, RelationshipGraph, ActionType


class ConstraintTableBuilder:
    """
    Build plot from constraint tables.
    User specifies: who did what to whom, when, where.
    """
    
    def __init__(self):
        self.graph = RelationshipGraph()
        logger.info("Initialized ConstraintTableBuilder")
    
    def build_from_constraints(self, constraints: PlotConstraints, all_characters: List[Character]) -> RelationshipGraph:
        """
        Build complete relationship graph from constraints.
        This is PURELY LOGICAL - no creative content yet.
        """
        logger.info("="*80)
        logger.info("BUILDING PLOT FROM CONSTRAINTS")
        logger.info("="*80)
        
        # Add all characters
        for char in all_characters:
            self.graph.add_character(char)
        
        # Time counter
        t = 0
        
        # 1. Build alliances (before crime)
        logger.info("\n1. Building alliances...")
        for ally1, ally2 in constraints.alliances:
            self.graph.add_relationship(Relationship(
                source=ally1,
                target=ally2,
                action=ActionType.ALLIED_WITH,
                time=t,
                location="pre_crime",
                motive="mutual benefit"
            ))
            t += 1
        
        # 2. The murder (main event)
        logger.info("\n2. Adding murder...")
        crime_location = "crime_scene"
        murder_time = t
        
        self.graph.add_relationship(Relationship(
            source=constraints.killer,
            target=constraints.victim,
            action=ActionType.KILLED,
            time=murder_time,
            location=crime_location,
            motive="to be described by LLM",
            witnessed_by=[]  # Will add witnesses
        ))
        t += 1
        
        # 3. Add accomplices
        logger.info("\n3. Adding accomplices...")
        for accomplice in constraints.accomplices:
            self.graph.add_relationship(Relationship(
                source=accomplice,
                target=constraints.killer,
                action=ActionType.ALLIED_WITH,
                time=murder_time - 1,  # Before murder
                location=crime_location,
                motive="accomplice motive",
            ))
        
        # 4. Add witnesses
        logger.info("\n4. Adding witnesses...")
        for witness, what_witnessed in constraints.witnesses:
            # Find the action they witnessed
            murder_rel = next(r for r in self.graph.action_sequences 
                            if r.action == ActionType.KILLED)
            murder_rel.witnessed_by.append(witness)
            
            self.graph.add_relationship(Relationship(
                source=witness,
                target=what_witnessed,
                action=ActionType.WITNESSED,
                time=murder_time,
                location=crime_location,
                motive="was at scene"
            ))
        
        # 5. Frame someone (if specified)
        logger.info("\n5. Adding framing...")
        if constraints.framed_suspect:
            self.graph.add_relationship(Relationship(
                source=constraints.killer,
                target=constraints.framed_suspect,
                action=ActionType.FRAMED,
                time=murder_time + 1,
                location=crime_location,
                motive="deflect suspicion"
            ))
            t += 1
        
        # 6. Add betrayals (including witness eliminations)
        logger.info("\n6. Adding betrayals...")
        for betrayer, betrayed in constraints.betrayals:
            # Check if betrayed is a witness - if so, this is a witness elimination (second murder)
            is_witness = any(w[0] == betrayed for w in constraints.witnesses)
            
            if is_witness:
                # This is a witness elimination - a second murder
                logger.info(f"   Witness elimination: {betrayer} kills {betrayed}")
                self.graph.add_relationship(Relationship(
                    source=betrayer,
                    target=betrayed,
                    action=ActionType.KILLED,  # This is a murder, not just betrayal
                    time=t,
                    location="secondary_crime_scene",
                    motive="eliminate witness"
                ))
            else:
                # Regular betrayal (non-lethal)
                logger.info(f"   Betrayal: {betrayer} betrays {betrayed}")
                self.graph.add_relationship(Relationship(
                    source=betrayer,
                    target=betrayed,
                    action=ActionType.BETRAYED,
                    time=t,
                    location="various",
                    motive="self-interest"
                ))
            t += 1
        
        # 7. Discovery
        logger.info("\n7. Adding discovery...")
        # Detective or first non-involved character discovers body
        discoverers = [c.name for c in all_characters 
                      if c.name != constraints.killer 
                      and c.name != constraints.victim
                      and c.name not in constraints.accomplices]
        
        if discoverers:
            self.graph.add_relationship(Relationship(
                source=discoverers[0],
                target=constraints.victim,
                action=ActionType.DISCOVERED,
                time=murder_time + 2,
                location=crime_location,
                motive="investigation"
            ))
        
        logger.info("\n✓ Graph built from constraints")
        return self.graph


class ConsistencyValidator:
    """Validate plot logic using constraint satisfaction"""
    
    def __init__(self):
        logger.info("Initialized ConsistencyValidator")
    
    def validate(self, graph: RelationshipGraph) -> Tuple[bool, List[str]]:
        """
        Validate using logical constraint rules.
        Returns: (is_valid, list_of_violations)
        """
        logger.info("\n" + "="*80)
        logger.info("VALIDATING PLOT CONSISTENCY")
        logger.info("="*80)
        
        violations = graph.validate_consistency()
        
        # Additional validation rules
        
        # Rule: Every killer must have opportunity (be at crime scene)
        for rel in graph.action_sequences:
            if rel.action == ActionType.KILLED:
                killer = rel.source
                crime_time = rel.time
                crime_location = rel.location
                
                # Check if killer was at location at that time
                killer_locations = [r.location for r in graph.action_sequences 
                                   if r.source == killer and r.time == crime_time]
                
                if killer_locations and crime_location not in killer_locations:
                    violations.append(f"VIOLATION: Killer {killer} not at crime scene")
        
        # Rule: Witnesses must be at the scene
        for rel in graph.action_sequences:
            for witness in rel.witnessed_by:
                witness_at_scene = any(
                    r.source == witness and r.time == rel.time and r.location == rel.location
                    for r in graph.action_sequences
                )
                if not witness_at_scene:
                    violations.append(f"VIOLATION: Witness {witness} not at scene of {rel.action.value}")
        
        is_valid = len(violations) == 0
        
        if is_valid:
            logger.info("✓ Plot is logically consistent")
        else:
            logger.warning(f"✗ Found {len(violations)} violations:")
            for v in violations:
                logger.warning(f"  {v}")
        
        return is_valid, violations


class TruthTable:
    """
    Truth table for clue-suspect relationships.
    Determines which clues point to which suspects.
    """
    
    def __init__(self):
        self.table = {}
        logger.info("Initialized TruthTable")
    
    def build_from_graph(self, graph: RelationshipGraph, constraints: PlotConstraints) -> np.ndarray:
        """
        Build truth table: rows = clues, columns = suspects
        1 = clue points to suspect, 0 = doesn't point
        """
        logger.info("\n" + "="*80)
        logger.info("BUILDING TRUTH TABLE")
        logger.info("="*80)
        
        # Extract clues from relationships
        clues = []
        for rel in graph.action_sequences:
            clue_name = f"{rel.action.value}_{rel.source}_{rel.target}"
            clues.append({
                'name': clue_name,
                'points_to': rel.source,  # Action performer
                'is_true_clue': rel.source == constraints.killer,
                'location': rel.location,
                'time': rel.time
            })
        
        # All potential suspects
        suspects = [c for c in graph.graph.nodes() 
                   if c != constraints.victim]
        
        # Build truth table matrix
        n_clues = len(clues)
        n_suspects = len(suspects)
        table = np.zeros((n_clues, n_suspects), dtype=int)
        
        logger.info(f"Truth table dimensions: {n_clues} clues × {n_suspects} suspects")
        
        for i, clue in enumerate(clues):
            for j, suspect in enumerate(suspects):
                # Clue points to suspect if it involves them
                points_to = 1 if clue['points_to'] == suspect else 0
                table[i, j] = points_to
                
                if points_to:
                    logger.info(f"  Clue '{clue['name']}' → {suspect}")
        
        self.table = {
            'matrix': table,
            'clues': clues,
            'suspects': suspects
        }
        
        return table
    
    def get_red_herrings(self, real_culprit: str) -> List[Dict]:
        """Identify which clues are red herrings"""
        red_herrings = []
        
        for clue in self.table['clues']:
            if not clue['is_true_clue']:
                red_herrings.append(clue)
        
        logger.info(f"Identified {len(red_herrings)} red herrings")
        return red_herrings
    
    def export(self) -> Dict:
        """Export truth table"""
        return {
            'matrix': self.table['matrix'].tolist(),
            'clues': self.table['clues'],
            'suspects': self.table['suspects']
        }


class NarrativeGenerator:
    """
    LLM only fills in NARRATIVE DESCRIPTIONS for pre-determined logical structure.
    Everything structural is already decided by the graph.
    """

    def __init__(
        self,
        plotbuilder: "DetectivePlotBuilder",
        storyboard: "ComicStripStoryBoarding",
    ):

        logger.info("Initialized NarrativeGenerator")
        self.plotbuilder = plotbuilder
        self.storyboard = storyboard

    async def generate_descriptions(
        self,
        graph: RelationshipGraph,
        constraints: PlotConstraints,
        artstyle: Optional[str] = "noir",
    ):
        """
        Ask LLM to generate ONLY descriptions for the logical structure.
        Structure is locked, LLM just adds flavor text.
        
        Returns:
            DetectiveStoryOutput with complete narrative and panel prompts
        """
        from cinema.models.detective_output import DetectiveStoryOutput
        
        logger.info("\n" + "="*80)
        logger.info("GENERATING NARRATIVE DESCRIPTIONS")
        logger.info("="*80)
        
        # Step 1: Build input for detective plotbuilder
        # Export graph to dict format
        graph_dict = graph.export_to_dict()
        
        # Build inputs for plotbuilder crew
        plotbuilder_inputs = {
            "characters": json.dumps(graph_dict["characters"], indent=2),
            "relationships": json.dumps(graph_dict["relationships"], indent=2, default=str),
            "killer": constraints.killer,
            "victim": constraints.victim,
            "accomplices": constraints.accomplices,
            "witnesses": [w[0] for w in constraints.witnesses],
            "betrayals": [b[0] for b in constraints.betrayals],
        }
        
        logger.info("Running DetectivePlotBuilder crew...")
        plotbuilder_result = await self.plotbuilder.crew().kickoff_async(
            inputs=plotbuilder_inputs
        )

        # Collect narrative structure as raw text
        from cinema.agents.bookwriter.crew import DetectivePlotBuilder as DPB

        narrative_text = DPB.collect(plotbuilder_result)  # type: ignore[attr-defined]
        logger.info("✓ Detective plot narrative generated")
        
        # Step 2: Build inputs for comic strip storyboarding
        storyboard_inputs = {
            "narrative_structure": narrative_text,
            "art_style": artstyle,
        }
        
        logger.info("Running ComicStripStoryBoarding crew...")
        storyboard_result = await self.storyboard.crew().kickoff_async(
            inputs=storyboard_inputs
        )

        # Collect as DetectiveStoryOutput pydantic model
        from cinema.agents.bookwriter.crew import ComicStripStoryBoarding as CSB

        detective_output = CSB.collect(  # type: ignore[attr-defined]
            storyboard_result, output_model=DetectiveStoryOutput
        )
        
        logger.info("✓ Generated narrative descriptions with panel prompts")
        return detective_output



class DetectivePlotSystem:
    """
    Main system: Pure constraint-based plot generation.
    Graph + Tables define ALL logic, LLM only adds descriptions.
    """

    def __init__(
        self,
        plotbuilder: Optional["DetectivePlotBuilder"] = None,
        storyboard: Optional["ComicStripStoryBoarding"] = None,
    ):
        self.builder = ConstraintTableBuilder()
        self.validator = ConsistencyValidator()
        self.truth_table = TruthTable()
        
        # Only create narrator if crews are provided
        if plotbuilder and storyboard:
            self.narrator = NarrativeGenerator(plotbuilder, storyboard)
        else:
            self.narrator = None
            
        logger.info("Initialized DetectivePlotSystem")
    
    async def generate_from_constraints(
        self,
        constraints: PlotConstraints,
        characters: List[Character],
        artstyle: str = "noir"
    ):
        """
        Generate complete plot from pure constraints.
        Returns: (graph, truth_table, detective_story_output or None)
        
        If narrator is not initialized (no crews provided), returns None for detective_output.
        """
        from cinema.models.detective_output import DetectiveStoryOutput
        
        logger.info("\n" + "#"*80)
        logger.info("# GENERATING PLOT FROM CONSTRAINTS")
        logger.info("#"*80)
        
        # Step 1: Build graph from constraints
        graph = self.builder.build_from_constraints(constraints, characters)
        
        # Step 2: Validate consistency
        is_valid, violations = self.validator.validate(graph)
        
        if not is_valid:
            logger.error("Plot has logical violations!")
            for v in violations:
                logger.error(f"  {v}")
            raise ValueError("Plot is logically inconsistent")
        
        # Step 3: Build truth table
        truth_matrix = self.truth_table.build_from_graph(graph, constraints)
        
        # Step 4: Generate narrative (LLM only does this part) - optional
        detective_output = None
        if self.narrator:
            detective_output = await self.narrator.generate_descriptions(
                graph, constraints, artstyle
            )
        
        logger.info("\n" + "#"*80)
        logger.info("# PLOT GENERATION COMPLETE")
        logger.info("#"*80)
        
        return graph, self.truth_table.export(), detective_output
    
    def export_full_plot(
        self,
        graph: RelationshipGraph,
        truth_table: Dict,
        detective_output,
        filename: str = "plot_structure.json"
    ):
        """Export complete plot with all layers"""
        
        export = {
            "logical_structure": {
                "graph": graph.export_to_dict(),
                "truth_table": truth_table,
                "timeline": [
                    {
                        "source": rel.source,
                        "target": rel.target,
                        "action": rel.action.value,
                        "time": rel.time,
                        "location": rel.location,
                        "motive": rel.motive,
                        "witnessed_by": rel.witnessed_by,
                    }
                    for rel in graph.get_action_timeline()
                ]
            },
        }
        
        # Add detective output if available
        if detective_output:
            from cinema.models.detective_output import DetectiveStoryOutput
            if isinstance(detective_output, DetectiveStoryOutput):
                export["detective_story"] = detective_output.model_dump()
        
        with open(filename, 'w') as f:
            json.dump(export, f, indent=2, default=str)
        
        logger.info(f"\n✓ Exported complete plot to {filename}")
        return export
