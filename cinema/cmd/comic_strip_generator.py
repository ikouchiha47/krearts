"""
Comic Strip Generator Pipeline

Flow:
1. detective.py → Generate narrative structure
2. stripper agent → Convert to comic storyboard with enhanced prompts
3. Character generator → Create character reference images
4. Panel generator → Generate comic panels
"""

import json
import logging
from pathlib import Path
from typing import Optional, List
from google import genai
from google.genai import types

from cinema.agents.bookwriter.detective import (
    DetectivePlotSystem,
    PlotConstraints,
    Character as DetectiveCharacter
)
from cinema.agents.bookwriter.crew import BookWriterCrew
from cinema.models.comic_strip import (
    ComicStripStoryboard,
    CharacterSheet,
    ComicPage,
    ComicPanel
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComicStripPipeline:
    """Main pipeline for comic strip generation"""
    
    def __init__(
        self,
        output_dir: str = "output/comic_strips",
        art_style: str = "Noir Comic Book Style"
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.art_style = art_style
        self.gemini_client = genai.Client()
        
        # Initialize detective system
        self.detective_system = DetectivePlotSystem()
        
        logger.info(f"Initialized ComicStripPipeline with art style: {art_style}")
    
    def generate_narrative(
        self,
        constraints: PlotConstraints,
        characters: List[DetectiveCharacter]
    ) -> dict:
        """
        Step 1: Generate narrative structure using detective.py
        """
        logger.info("="*80)
        logger.info("STEP 1: Generating Narrative Structure")
        logger.info("="*80)
        
        graph, truth_table, narrative = self.detective_system.generate_from_constraints(
            constraints, characters
        )
        
        # Export to dict for crew input
        narrative_structure = {
            "characters": [
                {
                    "name": node,
                    **graph.graph.nodes[node]
                }
                for node in graph.graph.nodes()
            ],
            "relationships": [
                {
                    "source": rel.source,
                    "target": rel.target,
                    "action": rel.action.value,
                    "time": rel.time,
                    "location": rel.location,
                    "motive": rel.motive,
                    "witnessed_by": rel.witnessed_by
                }
                for rel in graph.action_sequences
            ],
            "narrative_descriptions": narrative,
            "constraints": {
                "killer": constraints.killer,
                "victim": constraints.victim,
                "accomplices": constraints.accomplices,
                "witnesses": constraints.witnesses
            }
        }
        
        logger.info(f"✓ Generated narrative with {len(characters)} characters")
        return narrative_structure
    
    def generate_storyboard(
        self,
        narrative_structure: dict
    ) -> ComicStripStoryboard:
        """
        Step 2: Convert narrative to comic storyboard using stripper agent
        """
        logger.info("="*80)
        logger.info("STEP 2: Generating Comic Storyboard")
        logger.info("="*80)
        
        # Initialize crew with stripper agent
        crew = BookWriterCrew()
        
        # Run stripper task
        inputs = {
            "narrative_structure": json.dumps(narrative_structure, indent=2),
            "art_style": self.art_style
        }
        
        logger.info("Running stripper agent to enhance prompts...")
        result = crew.kickoff(inputs=inputs)
        
        # Parse result to ComicStripStoryboard
        if hasattr(result, 'pydantic'):
            storyboard = result.pydantic
        else:
            # Parse from JSON
            storyboard = ComicStripStoryboard.model_validate_json(result.raw)
        
        logger.info(f"✓ Generated storyboard with {len(storyboard.pages)} pages")
        
        # Save storyboard
        storyboard_path = self.output_dir / "storyboard.json"
        with open(storyboard_path, 'w') as f:
            f.write(storyboard.model_dump_json(indent=2))
        logger.info(f"✓ Saved storyboard to {storyboard_path}")
        
        return storyboard
    
    def generate_character_references(
        self,
        characters: List[CharacterSheet]
    ) -> dict:
        """
        Step 3: Generate character reference images
        """
        logger.info("="*80)
        logger.info("STEP 3: Generating Character References")
        logger.info("="*80)
        
        character_refs = {}
        
        for char in characters:
            logger.info(f"Generating reference for {char.name}...")
            
            # Build character reference prompt
            prompt = self._build_character_reference_prompt(char)
            
            # Generate image
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt],
                config={"response_modalities": ["IMAGE"]}
            )
            
            # Save image
            for part in response.parts:
                if part.inline_data is not None:
                    image = part.as_image()
                    image_path = self.output_dir / f"char_{char.name.replace(' ', '_')}.png"
                    image.save(image_path)
                    
                    character_refs[char.name] = str(image_path)
                    char.reference_image_path = str(image_path)
                    
                    logger.info(f"✓ Saved {char.name} reference to {image_path}")
        
        return character_refs
    
    def generate_comic_panels(
        self,
        storyboard: ComicStripStoryboard,
        character_refs: dict
    ) -> List[str]:
        """
        Step 4: Generate comic panel images
        """
        logger.info("="*80)
        logger.info("STEP 4: Generating Comic Panels")
        logger.info("="*80)
        
        generated_panels = []
        
        for page in storyboard.pages:
            logger.info(f"\nGenerating Page {page.page_number}: {page.scene_title}")
            
            for panel in page.panels:
                logger.info(f"  Panel {panel.panel_number}: {panel.action_description[:50]}...")
                
                # Use enhanced prompt from stripper agent
                prompt = panel.enhanced_prompt or self._build_panel_prompt(panel, page.art_style)
                
                # Generate panel image
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[prompt],
                    config={"response_modalities": ["IMAGE"]}
                )
                
                # Save panel
                for part in response.parts:
                    if part.inline_data is not None:
                        image = part.as_image()
                        panel_filename = f"page_{page.page_number:02d}_panel_{panel.panel_number}.png"
                        panel_path = self.output_dir / panel_filename
                        image.save(panel_path)
                        
                        generated_panels.append(str(panel_path))
                        logger.info(f"  ✓ Saved to {panel_path}")
        
        logger.info(f"\n✓ Generated {len(generated_panels)} total panels")
        return generated_panels
    
    def _build_character_reference_prompt(self, char: CharacterSheet) -> str:
        """Build prompt for character reference image"""
        return (
            f"Character reference sheet in {self.art_style}. "
            f"Full body portrait of {char.name}. "
            f"Physical appearance: {char.physical_description}. "
            f"Clothing: {char.clothing}. "
            f"Personality traits visible in expression: {', '.join(char.personality_traits)}. "
            f"Clean, neutral background. Multiple angles (front, side, back). "
            f"Consistent character design for comic book use. Portrait orientation."
        )
    
    def _build_panel_prompt(self, panel: ComicPanel, art_style: str) -> str:
        """Build prompt for comic panel (fallback if stripper didn't enhance)"""
        prompt = f"A single comic book panel in {art_style}. "
        prompt += f"{panel.shot_type.replace('_', ' ').title()} shot. "
        prompt += f"{panel.action_description}. "
        prompt += f"Location: {panel.location}. "
        prompt += f"Emotional tone: {panel.emotional_tone}. "
        
        if panel.character_focus:
            prompt += f"Characters: {', '.join(panel.character_focus)}. "
        
        if panel.dialogue:
            prompt += f"Caption box: '{panel.dialogue}'. "
        
        if panel.sound_effects:
            prompt += f"Sound effect: '{panel.sound_effects}'. "
        
        prompt += "Landscape orientation."
        
        return prompt
    
    def run_full_pipeline(
        self,
        constraints: PlotConstraints,
        characters: List[DetectiveCharacter],
        title: str = "Untitled Comic"
    ) -> ComicStripStoryboard:
        """
        Run complete pipeline: narrative → storyboard → characters → panels
        """
        logger.info("\n" + "#"*80)
        logger.info(f"# COMIC STRIP PIPELINE: {title}")
        logger.info("#"*80)
        
        # Step 1: Generate narrative
        narrative = self.generate_narrative(constraints, characters)
        
        # Step 2: Generate storyboard
        storyboard = self.generate_storyboard(narrative)
        storyboard.title = title
        
        # Step 3: Generate character references
        character_refs = self.generate_character_references(storyboard.characters)
        
        # Step 4: Generate comic panels
        panel_paths = self.generate_comic_panels(storyboard, character_refs)
        
        logger.info("\n" + "#"*80)
        logger.info("# PIPELINE COMPLETE")
        logger.info("#"*80)
        logger.info(f"Title: {storyboard.title}")
        logger.info(f"Pages: {len(storyboard.pages)}")
        logger.info(f"Panels: {len(panel_paths)}")
        logger.info(f"Characters: {len(storyboard.characters)}")
        logger.info(f"Output: {self.output_dir}")
        
        return storyboard


def main():
    """Example usage"""
    
    # Define detective story
    characters = [
        DetectiveCharacter("Detective Morgan", "detective"),
        DetectiveCharacter("Victor Ashford", "victim"),
        DetectiveCharacter("James Butler", "butler"),
        DetectiveCharacter("Dr. Helen Price", "doctor"),
    ]
    
    constraints = PlotConstraints(
        killer="James Butler",
        victim="Victor Ashford",
        accomplices=[],
        framed_suspect=None,
        witnesses=[("Dr. Helen Price", "suspicious activity")],
        alliances=[],
        winners=["James Butler"],
        losers=["Victor Ashford"],
        betrayals=[]
    )
    
    # Run pipeline
    pipeline = ComicStripPipeline(
        output_dir="output/comic_strips/midnight_murder",
        art_style="Noir Comic Book Style"
    )
    
    storyboard = pipeline.run_full_pipeline(
        constraints=constraints,
        characters=characters,
        title="The Midnight Murder"
    )
    
    print(f"\n✓ Comic strip generated: {storyboard.title}")
    print(f"  Pages: {len(storyboard.pages)}")
    print(f"  Total panels: {storyboard.total_panels}")


if __name__ == "__main__":
    main()
