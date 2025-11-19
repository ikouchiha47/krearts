"""
Book Workflow Implementation.

Stages:
1. init: Generate storyline (up to critique)
2. generate_content: Generate novel from storyline
3. generate_chapters: Generate comic chapters from novel
4. generate_pages: Generate page images from chapters
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any

from cinema.workflow.interface import WorkflowInterface, WorkflowType, WorkflowStage, WorkflowState
from cinema.context import DirectorsContext

logger = logging.getLogger(__name__)


class BookWorkflow(WorkflowInterface):
    """Book generation workflow"""
    
    def __init__(self, workflow_id: str, ctx: DirectorsContext):
        super().__init__(workflow_id, WorkflowType.BOOK)
        self.ctx = ctx
        
        # Support both book_{id} and detective_{id} formats
        from pathlib import Path
        if not Path(self.output_dir).exists():
            detective_dir = f"output/detective_{workflow_id}"
            if Path(detective_dir).exists():
                self.output_dir = detective_dir
        
        # Load existing state if available
        state_file = Path(self.output_dir) / "workflow_state.json"
        if state_file.exists():
            import json
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            self.state = WorkflowState(**state_data)
    
    async def init(self, **kwargs) -> Dict[str, Any]:
        """
        Generate storyline up to critique.
        
        Returns storyline and critique result.
        """
        logger.info(f"📖 Initializing book workflow: {self.workflow_id}")
        
        # Use defaults if not provided
        characters = kwargs.get('characters') or "Detective Morgan, James Butler (killer), Victor Ashford (victim), Dr. Helen Price, Margaret Ashford"
        killer = kwargs.get('killer') or "James Butler"
        victim = kwargs.get('victim') or "Victor Ashford"
        relationships = kwargs.get('relationships') or ""
        accomplices = kwargs.get('accomplices') or ""
        witnesses = kwargs.get('witnesses') or ""
        betrayals = kwargs.get('betrayals') or ""
        
        logger.info(f"   Characters: {characters[:50]}...")
        logger.info(f"   Killer: {killer}")
        logger.info(f"   Victim: {victim}")
        
        # Save input config to output directory
        import json
        from pathlib import Path
        config_file = Path(self.output_dir) / "input_config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(kwargs, f, indent=2)
        logger.info(f"   Saved config to: {config_file}")
        
        # Store config in state
        self.state.config = kwargs
        
        # Import required classes
        from cinema.agents.bookwriter.crew import (
            DetectivePlotBuilder,
            PlotCritique,
            ScreenplayWriter,
            BookWriter,
            ComicStripStoryBoarding,
            DetectivePlotBuilderSchema,
        )
        from cinema.agents.bookwriter.flow import StoryBuilder, StoryBuilderInput
        
        # Get skipper settings from config
        skipper = kwargs.get('skipper', {})
        use_mock_plot = skipper.get('p', False)
        use_mock_critique = skipper.get('c', False)
        use_mock_screenplay = skipper.get('w', True)
        use_mock_storyboard = skipper.get('s', True)
        
        logger.info(f"   Skipper config: plot={use_mock_plot}, critique={use_mock_critique}, screenplay={use_mock_screenplay}, storyboard={use_mock_storyboard}")
        
        # Create crews with skipper settings
        plotbuilder = DetectivePlotBuilder(ctx=self.ctx, use_mock=use_mock_plot)
        critique = PlotCritique(ctx=self.ctx, use_mock=use_mock_critique)
        screenplay = ScreenplayWriter(ctx=self.ctx, use_mock=use_mock_screenplay)
        booker = BookWriter(ctx=self.ctx, use_mock=use_mock_screenplay)
        storyboard = ComicStripStoryBoarding(ctx=self.ctx, use_mock=use_mock_storyboard)
        
        # Build flow with halt at bookerama
        flow = StoryBuilder.build(
            ctx=self.ctx,
            plotbuilder=plotbuilder,
            critique=critique,
            storyboard=storyboard,
            screenplay=screenplay,
            booker=booker,
            flow_id=self.workflow_id,
            output_base_dir=self.output_dir,
        )
        
        # Set generation target and halt point
        flow.generation_target = "bookerama"
        flow.state.waits_at = {"bookerama": True}
        
        # Prepare input
        plot_schema = DetectivePlotBuilderSchema(
            characters=characters,
            relationships=relationships,
            killer=killer,
            victim=victim,
            accomplices=accomplices,
            witnesses=witnesses,
            betrayals=betrayals,
            examples="",
        )
        
        from cinema.agents.bookwriter.flow import StripperInputSchema, ScreenplayWriterSchema
        
        flow.state.input = StoryBuilderInput(
            plotbuilder=plot_schema,
            stripper=StripperInputSchema(
                art_style="Print Comic Noir Style",
                examples=ComicStripStoryBoarding.load_examples(),
            ),
            screenplay=ScreenplayWriterSchema(
                storyline="",
                art_style="",
                examples="",
            ),
        )
        
        # Pass config to flow state for eval skipper
        flow.state.config = kwargs
        
        # Run flow until halt
        logger.info("Running StoryBuilder flow (plan + critique)...")
        await flow.kickoff_async()
        
        # Check if flow halted as expected
        if flow.state.halted_at:
            logger.info(f"✅ Flow halted at: {flow.state.halted_at}")
        
        # Extract results
        output = flow.state.output
        if not output or not output.storyline:
            raise ValueError("Flow did not generate storyline")
        
        result = {
            "storyline": output.storyline,
            "critique": output.critique or "PASS",
            "characters": characters,
            "killer": killer,
            "victim": victim,
            "halted_at": flow.state.halted_at,
        }
        
        self.state.storyline_done = True
        self.state.current_stage = WorkflowStage.CONTENT
        self.save_state()
        
        logger.info(f"✅ Storyline generated for: {self.workflow_id}")
        return result
    
    async def generate_content(self, continue_from: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate novel from storyline.
        
        Uses StoryBuilder to generate book, pauses before storyboard.
        """
        logger.info(f"📚 Generating book content: {self.workflow_id}")
        
        from cinema.agents.bookwriter.crew import (
            DetectivePlotBuilder,
            PlotCritique,
            ScreenplayWriter,
            BookWriter,
            ComicStripStoryBoarding,
        )
        from cinema.agents.bookwriter.flow import StoryBuilder
        
        # Get skipper settings from state config
        skipper = self.state.config.get('skipper', {})
        use_mock_plot = skipper.get('p', True)  # Skip plot in content generation (already done in init)
        use_mock_critique = skipper.get('c', True)  # Skip critique in content generation
        use_mock_screenplay = skipper.get('w', False)  # Actually generate screenplay/book
        use_mock_storyboard = skipper.get('s', True)  # Skip storyboard (done separately)
        
        # Create crews with skipper settings
        plotbuilder = DetectivePlotBuilder(ctx=self.ctx, use_mock=use_mock_plot)
        critique = PlotCritique(ctx=self.ctx, use_mock=use_mock_critique)
        screenplay = ScreenplayWriter(ctx=self.ctx, use_mock=use_mock_screenplay)
        booker = BookWriter(ctx=self.ctx, use_mock=use_mock_screenplay)
        storyboard = ComicStripStoryBoarding(ctx=self.ctx, use_mock=use_mock_storyboard)
        
        if continue_from:
            logger.info(f"   Resuming from flow state: {continue_from}")
            # Resume from saved flow state
            flow = StoryBuilder.resume_from_halt(
                flow_id=continue_from,
                ctx=self.ctx,
                plotbuilder=plotbuilder,
                critique=critique,
                storyboard=storyboard,
                screenplay=screenplay,
                booker=booker,
                output_base_dir=self.output_dir,
            )
        else:
            # Build new flow with halt at storyboard
            flow = StoryBuilder.build(
                ctx=self.ctx,
                plotbuilder=plotbuilder,
                critique=critique,
                storyboard=storyboard,
                screenplay=screenplay,
                booker=booker,
                flow_id=self.workflow_id,
                output_base_dir=self.output_dir,
            )
            
            # Set generation target and halt point
            flow.generation_target = "bookerama"
            # ALWAYS halt at storyboard - chapter generation is handled separately
            flow.state.waits_at = {"storyboard": True}
        
        # Ensure storyboard halt is set even when resuming
        flow.state.waits_at["storyboard"] = True
        
        # Run flow until halt at storyboard
        logger.info("Running StoryBuilder flow (bookerama generation)...")
        await flow.kickoff_async()
        
        # Extract results
        output = flow.state.output
        if not output or not output.screenplay:
            raise ValueError("Flow did not generate screenplay/novel")
        
        # Save novel to file
        from pathlib import Path
        output_file = Path(self.output_dir) / "novel.md"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(output.screenplay)
        
        result = {
            "content": output.screenplay,
            "type": "book",
            "output_file": str(output_file)
        }
        
        self.state.content_done = True
        self.state.current_stage = WorkflowStage.CHAPTERS
        self.save_state()
        
        logger.info(f"✅ Book generated: {result['output_file']}")
        return result
    
    async def generate_characters(self) -> Dict[str, Any]:
        """
        Generate character reference images from storyline.
        
        Extracts character descriptions from the flow state and generates
        reference images (front, side, full_body, back views) for each character.
        These references are used for consistent character appearance in page generation.
        
        Returns:
            Dict with:
                - characters: Dict[str, Dict[str, str]] - character_id -> {view: path}
                - output_dir: str - directory where images were saved
        """
        from pathlib import Path
        import json
        from cinema.workflow.character_manager import CharacterReferenceManager
        from cinema.providers.gemini import GeminiMediaGen
        
        logger.info(f"📄 Generating characters: {self.workflow_id}")
        
        # Load flow state to get character descriptions
        flow_state_file = Path(f"output/flow_states/storybuilder_{self.workflow_id}.json")
        if not flow_state_file.exists():
            raise FileNotFoundError(f"Flow state not found: {flow_state_file}")
        
        with open(flow_state_file, 'r') as f:
            flow_data = json.load(f)
        
        storyline = flow_data.get('output', {}).get('storyline', '')
        if not storyline:
            raise ValueError("Storyline not found in flow state")
        
        # Parse characters from storyline (they're in markdown format)
        characters = self._extract_characters_from_storyline(storyline)
        
        if not characters:
            logger.warning("No characters found in storyline")
            return {"characters": {}, "output_dir": f"{self.output_dir}/characters"}
        
        logger.info(f"   Found {len(characters)} characters to generate")
        
        # Initialize character manager
        gemini = GeminiMediaGen()
        char_manager = CharacterReferenceManager(gemini)
        
        # Generate references for each character
        output_dir = f"{self.output_dir}/characters"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        all_characters = {}
        for char_id, char_desc in characters.items():
            logger.info(f"   Generating references for: {char_id}")
            
            try:
                # Get art_style from config
                art_style = self._get_art_style()
                
                refs = await char_manager.generate_character_references(
                    character_id=char_id,
                    character_description=char_desc,
                    output_dir=output_dir,
                    include_back_view=True,
                    art_style=art_style
                )
                all_characters[char_id] = refs
                logger.info(f"   ✅ Generated {len(refs)} views for {char_id}")
            except Exception as e:
                logger.error(f"   ❌ Failed to generate {char_id}: {e}")
                continue
        
        # Save character manifest
        manifest_file = Path(output_dir) / "character_manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(all_characters, f, indent=2)
        
        logger.info(f"✅ Characters generated: {len(all_characters)}")
        logger.info(f"   Manifest: {manifest_file}")
        
        return {
            "characters": all_characters,
            "output_dir": output_dir
        }
    
    def _get_layout_description(self, panel_arrangement: str) -> str:
        """Get detailed description of panel layout style."""

        # TODO: Get these descriptions from the LLM Output
        #       Because the knowledgebase has better text in it
        layout_descriptions = {
            "horizontal-2-panel": "Two panels side-by-side horizontally with equal or dynamic widths",
            "horizontal-3-panel": "Three panels in a horizontal row with varying widths for emphasis",
            "vertical-2-panel": "Two panels stacked vertically, equal or dynamic heights",
            "vertical-3-panel": "Three panels stacked vertically for descent/ascent sequences",
            "fractured-overlapping": "Overlapping panels with broken borders for chaos/simultaneous events",
            "zoom-progression": "Progressive zoom sequence (wide -> medium -> close-up) for building suspense",
            "cross-over-bleed": "Dominant element bleeds across multiple panels for dramatic impact",
            "shattered-exploded": "Broken, irregular panel borders for psychological distress or action",
            "dynamic-grid": "Irregular grid layout with varying panel sizes for general purpose flexibility",
        }
        return layout_descriptions.get(panel_arrangement, "Standard comic book panel layout with gutters")
    
    def _get_art_style(self) -> str:
        """
        Get art_style from generated content (storyline/novel), NOT from user config.
        
        Priority:
        1. Flow state storyline (what the LLM actually generated)
        2. Novel.md (final generated content)
        3. Chapter JSON (from comic generation)
        4. Default fallback
        
        We explicitly DO NOT use the user's input config, as the LLM may have
        refined or changed the art style during generation.
        """
        from pathlib import Path
        import json
        import re
        
        # Priority 1: Try flow state storyline (most authoritative)
        flow_state_file = Path(f"output/flow_states/storybuilder_{self.workflow_id}.json")
        if flow_state_file.exists():
            try:
                with open(flow_state_file, 'r') as f:
                    flow_data = json.load(f)
                storyline = flow_data.get('output', {}).get('storyline', '')
                if storyline:
                    # Look for "- **Art Style:** ..." pattern in storyline
                    match = re.search(r'-\s*\*\*Art Style:\*\*\s*(.+?)(?:\n|$)', storyline)
                    if match:
                        art_style = match.group(1).strip()
                        logger.info(f"   ✅ Art style from storyline: {art_style}")
                        return art_style
            except Exception as e:
                logger.debug(f"   Could not read flow state: {e}")
        
        # Priority 2: Try novel.md (generated content)
        novel_file = Path(self.output_dir) / "novel.md"
        if novel_file.exists():
            content = novel_file.read_text()
            # Look for "- **Art Style:** ..." pattern
            match = re.search(r'-\s*\*\*Art Style:\*\*\s*(.+?)(?:\n|$)', content)
            if match:
                art_style = match.group(1).strip()
                logger.info(f"   ✅ Art style from novel.md: {art_style}")
                return art_style
        
        # Priority 3: Try chapter JSON (from comic generation)
        chapter_files = sorted(Path(self.output_dir).glob("chapter_*.json"))
        if chapter_files:
            try:
                with open(chapter_files[0], 'r') as f:
                    chapter_data = json.load(f)
                art_style = chapter_data.get('art_style')
                if art_style:
                    logger.info(f"   ✅ Art style from chapter JSON: {art_style}")
                    return art_style
            except Exception as e:
                logger.debug(f"   Could not read chapter JSON: {e}")
        
        # Fallback: Use default (DO NOT use user config)
        logger.warning("   ⚠️  No art style found in generated content, using default")
        return 'Print Comic Noir Style'
    
    def _extract_characters_from_storyline(self, storyline: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract character descriptions from storyline markdown.
        
        Parses the ## Characters section and extracts physical traits,
        age, ethnicity, etc. for each character.
        
        Returns:
            Dict[character_name, character_description]
        """
        import re
        
        characters = {}
        
        # Find the Characters section (with optional number)
        # Use negative lookahead to avoid matching ### (three hashes)
        char_section_match = re.search(r'##\s*Characters\s*\d*\s*\n(.*?)(?=\n##(?!#)|\Z)', storyline, re.DOTALL)
        if not char_section_match:
            # Try alternative format
            char_section_match = re.search(r'##\s*\d+\.\s*Characters\s*\n(.*?)(?=\n##(?!#)|\Z)', storyline, re.DOTALL)
        if not char_section_match:
            return characters
        
        char_section = char_section_match.group(1)
        
        # Find character blocks: ### Character N
        char_pattern = r'###\s+Character\s+\d+\s*\n(.*?)(?=\n###\s+Character\s+\d+|\Z)'
        char_matches = re.finditer(char_pattern, char_section, re.DOTALL)
        
        for match in char_matches:
            block = match.group(1)
            
            if not block.strip():
                continue
            
            # Extract name
            name_match = re.search(r'\*\*Name:\*\*\s*(.+?)(?=\n|$)', block)
            if not name_match:
                continue
            name = name_match.group(1).strip()
            
            # Extract physical traits
            physical_match = re.search(r'\*\*Physical Traits:\*\*\s*(.+?)(?=\n\*\*|\Z)', block, re.DOTALL)
            physical = physical_match.group(1).strip() if physical_match else ""
            
            # Extract age
            age_match = re.search(r'\*\*Age:\*\*\s*(\d+)', block)
            age = age_match.group(1) if age_match else "unknown"
            
            # Extract ethnicity
            ethnicity_match = re.search(r'\*\*Ethnicity:\*\*\s*(.+?)(?=\n|$)', block)
            ethnicity = ethnicity_match.group(1).strip() if ethnicity_match else ""
            
            # Build description
            char_id = name.replace(" ", "_").replace(".", "").replace("Dr_", "")
            characters[char_id] = {
                "name": name,
                "physical_appearance": f"{name}, {age} years old, {ethnicity}. {physical}",
                "style": "photorealistic, detailed, high quality"
            }
        
        return characters
    
    async def generate_chapters(
        self,
        chapters: Optional[List[int]] = None,
        continue_from: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate comic chapters from novel.
        
        Args:
            chapters: Specific chapters (e.g., [1, 5]) or None for all
            continue_from: Continue from last chapter
        """
        logger.info(f"📄 Generating chapters: {self.workflow_id}")
        
        # Load novel
        from pathlib import Path
        from cinema.models.novel import Novel
        
        novel_file = Path(self.output_dir) / "novel.md"
        if not novel_file.exists():
            raise FileNotFoundError(f"Novel not found: {novel_file}")
        
        # Auto-generate character references if not already done
        char_manifest_file = Path(self.output_dir) / "characters" / "character_manifest.json"
        if not char_manifest_file.exists():
            logger.info("📸 Character references not found - generating now...")
            try:
                char_result = await self.generate_characters()
                logger.info(f"✅ Generated {len(char_result['characters'])} character sets")
            except Exception as e:
                logger.warning(f"⚠️  Character generation failed: {e}")
                logger.warning("   Continuing without character references")
        else:
            logger.info("✅ Character references already exist")
        
        novel_text = novel_file.read_text()
        novel = Novel.from_str(novel_text)
        
        logger.info(f"   Loaded novel: {novel.title} with {len(novel.chapters)} chapters")
        
        if continue_from:
            last_chapter = max(self.state.chapters_generated) if self.state.chapters_generated else 0
            logger.info(f"   Continuing from chapter {last_chapter}")
            # Generate next chapter
            chapters = [last_chapter + 1]
        elif chapters is None:
            # Generate all chapters
            logger.info(f"   Generating ALL chapters")
            chapters = list(range(1, len(novel.chapters) + 1))
        
        if not chapters:
            chapters = [1]  # Default to chapter 1
        
        # Filter to only chapters that exist and haven't been generated
        available_chapters = [c for c in chapters if 1 <= c <= len(novel.chapters)]
        new_chapters = [c for c in available_chapters if c not in self.state.chapters_generated]
        
        if not new_chapters:
            logger.info(f"   All requested chapters already generated")
            result = {
                "chapters": chapters,
                "output_dir": self.output_dir,
                "total_generated": len(self.state.chapters_generated)
            }
            return result
        
        logger.info(f"   Chapters to generate: {new_chapters}")
        
        # Use ParallelComicGenerator
        from cinema.pipeline.parallel_comic_generator import ParallelComicGenerator
        
        # Filter novel to only requested chapters
        filtered_chapters = [novel.chapters[i-1] for i in new_chapters]
        filtered_novel = Novel(
            title=novel.title,
            setup=novel.setup,
            context=novel.context,
            metadata=novel.metadata,
            chapters=filtered_chapters
        )
        
        # Get skipper config for chapter generation
        skipper = self.state.config.get('skipper', {})
        use_mock_chapters = skipper.get('s', False)
        
        generator = ParallelComicGenerator(
            ctx=self.ctx,
            screenplay=novel_text,
            max_concurrent=3,
            output_base_dir=self.output_dir,
            use_mock=use_mock_chapters  # Pass skipper config
        )
        
        art_style = kwargs.get('art_style', 'Print Comic Noir Style')
        aspect_ratio = kwargs.get('aspect_ratio', '4:5')
        
        logger.info(f"   Running ParallelComicGenerator for {len(new_chapters)} chapters...")
        logger.info(f"   Art style: {art_style}")
        logger.info(f"   Aspect ratio: {aspect_ratio}")
        logger.info(f"   use_mock={use_mock_chapters} (from skipper['s'])")
        comic_output = await generator.generate(
            novel=filtered_novel,
            art_style=art_style,
            aspect_ratio=aspect_ratio
        )
        
        # Update state
        for chapter in new_chapters:
            if chapter not in self.state.chapters_generated:
                self.state.chapters_generated.append(chapter)
        
        self.state.current_stage = WorkflowStage.PAGES
        self.save_state()
        
        result = {
            "chapters": new_chapters,
            "output_dir": self.output_dir,
            "total_generated": len(self.state.chapters_generated),
            "comic_output": comic_output
        }
        
        logger.info(f"✅ Chapters generated: {new_chapters}")
        return result
    
    async def generate_pages(
        self,
        pages: Optional[List[int]] = None,
        continue_from: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate page images from chapters.
        
        Args:
            pages: Specific pages (e.g., [1, 20])
            continue_from: Continue from last page
        """
        logger.info(f"🎨 Generating pages: {self.workflow_id}")
        
        from pathlib import Path
        import json
        import os
        from google import genai
        from PIL import Image
        from io import BytesIO
        
        # Load character references if available
        char_manifest_file = Path(self.output_dir) / "characters" / "character_manifest.json"
        character_references = {}
        if char_manifest_file.exists():
            with open(char_manifest_file, 'r') as f:
                character_references = json.load(f)
            logger.info(f"   Loaded {len(character_references)} character reference sets")
        else:
            logger.warning("   No character references found - images may be inconsistent")
        
        # Load chapter JSONs to get page info
        chapter_files = sorted(Path(self.output_dir).glob("chapter_*.json"))
        if not chapter_files:
            raise FileNotFoundError(f"No chapter JSONs found in {self.output_dir}")
        
        logger.info(f"   Found {len(chapter_files)} chapter files")
        
        # Build page list from chapters
        all_pages = []
        for chapter_file in chapter_files:
            with open(chapter_file, 'r') as f:
                chapter_data = json.load(f)
            
            for chapter in chapter_data.get('chapters', []):
                chapter_num = chapter.get('chapter_number')
                for scene in chapter.get('scenes', []):
                    scene_num = scene.get('scene_number')
                    for page in scene.get('pages', []):
                        page_num = page.get('page_number')
                        all_pages.append({
                            'chapter_file': str(chapter_file),
                            'chapter_number': chapter_num,
                            'scene_number': scene_num,
                            'page_number': page_num,
                            'page_data': page,
                            'global_index': len(all_pages) + 1
                        })
        
        logger.info(f"   Total pages available: {len(all_pages)}")
        
        if continue_from:
            last_page = max(self.state.pages_generated) if self.state.pages_generated else 0
            logger.info(f"   Continuing from page {last_page}")
            pages = [last_page + 1]
        
        if not pages:
            pages = list(range(1, len(all_pages) + 1))  # Default to all pages
        
        # Filter to only pages that exist and haven't been generated
        available_pages = [p for p in pages if 1 <= p <= len(all_pages)]
        new_pages = [p for p in available_pages if p not in self.state.pages_generated]
        
        if not new_pages:
            logger.info(f"   All requested pages already generated")
            result = {
                "pages": pages,
                "output_dir": f"{self.output_dir}/pages",
                "total_generated": len(self.state.pages_generated)
            }
            return result
        
        logger.info(f"   Pages to generate: {new_pages}")
        
        # Initialize Gemini client
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        client = genai.Client(api_key=api_key)
        logger.info("   ✅ Gemini client initialized")
        
        # Generate page images
        pages_dir = Path(self.output_dir) / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        
        for page_idx in new_pages:
            page_info = all_pages[page_idx - 1]  # Convert to 0-indexed
            
            logger.info(f"   Generating page {page_idx}/{len(all_pages)}...")
            logger.info(f"     Ch{page_info['chapter_number']} Sc{page_info['scene_number']} Page{page_info['page_number']}")
            
            filename = f"ch{page_info['chapter_number']}_sc{page_info['scene_number']}_page{page_info['page_number']}.png"
            output_file = pages_dir / filename
            
            # Check if already exists
            if output_file.exists():
                logger.info(f"     ⊙ Cached: {filename}")
                if page_idx not in self.state.pages_generated:
                    self.state.pages_generated.append(page_idx)
                continue
            
            try:
                page_data = page_info['page_data']
                panel_arrangement = page_data.get("panel_arrangement", "vertical-2-panel")
                panels = page_data.get("panels", [])
                logger.info(f"     Multi-panel generation ({panel_arrangement}) with {len(panels)} panels")
                from google.genai import types
                image_config = types.ImageConfig(aspect_ratio="4:5")
                config = types.GenerateContentConfig(
                    response_modalities=[types.Modality.IMAGE],
                    image_config=image_config,
                )
                art_style = self._get_art_style()
                contents = []
                if character_references:
                    unique_chars = []
                    for p in panels:
                        for cp in p.get("characters_present", []):
                            if cp not in unique_chars:
                                unique_chars.append(cp)
                    added_refs = 0
                    for cp in unique_chars:
                        for char_id, char_refs in character_references.items():
                            name_match = char_id.lower() in cp.lower() or cp.lower() in char_id.lower()
                            if name_match:
                                ref_path = char_refs.get('front')
                                if ref_path and Path(ref_path).exists():
                                    with open(ref_path, 'rb') as f:
                                        ref_image_data = f.read()
                                    contents.append({
                                        "inline_data": {
                                            "mime_type": "image/png",
                                            "data": ref_image_data
                                        }
                                    })
                                    contents.append(f"Use as character reference: {char_id}")
                                    added_refs += 1
                                break
                        if added_refs >= 3:
                            break
                # Build detailed layout prompt
                panel_borders = page_data.get("panel_borders", "clean-sharp")
                panel_transition = page_data.get("panel_transition_style", "hard-cuts")
                
                # Get unique characters in this page
                unique_chars = set()
                for p in panels:
                    for cp in p.get("characters_present", []):
                        unique_chars.add(cp)
                
                # Load character descriptions from chapter JSON
                char_descriptions = {}
                with open(page_info['chapter_file'], 'r') as f:
                    chapter_data = json.load(f)
                for char in chapter_data.get('characters', []):
                    char_name = char.get('name', '')
                    if char_name in unique_chars:
                        char_descriptions[char_name] = {
                            'physical': char.get('physical_traits', ''),
                            'age': char.get('age', ''),
                            'attire': char.get('typical_attire', ''),
                            'role': char.get('role', '')
                        }
                
                prompt_lines = []
                prompt_lines.append(f"COMIC PAGE GENERATION")
                prompt_lines.append(f"")
                prompt_lines.append(f"STYLE: {art_style}")
                prompt_lines.append(f"Layout: 4:5 portrait, {panel_arrangement} ({self._get_layout_description(panel_arrangement)})")
                prompt_lines.append(f"Borders: {panel_borders}, Transitions: {panel_transition}")
                prompt_lines.append(f"")
                
                # Add character descriptions
                if char_descriptions:
                    prompt_lines.append(f"CHARACTERS IN THIS PAGE:")
                    for char_name, desc in char_descriptions.items():
                        role_note = f" ({desc['role']})" if desc['role'] else ""
                        prompt_lines.append(f"- {char_name}{role_note}: {desc['physical']}, {desc['age']} years old. Wears: {desc['attire']}")
                    prompt_lines.append(f"")
                
                prompt_lines.append(f"RENDERING REQUIREMENTS:")
                prompt_lines.append(f"- High-contrast noir comic book style")
                prompt_lines.append(f"- Sharp, detailed rendering with accurate anatomy")
                prompt_lines.append(f"- Realistic object sizing and proportions")
                prompt_lines.append(f"- Fill full vertical frame, no letterboxing")
                
                # Check if we should include text in generation
                # Default to False - generate clean images first, add text in second pass
                include_text = kwargs.get('gemini_text', False)
                if include_text:
                    prompt_lines.append(f"- INCLUDE text, speech bubbles, and caption boxes as appropriate")
                    prompt_lines.append(f"- Use comic book lettering style with clear, readable text")
                else:
                    prompt_lines.append(f"- NO text, speech bubbles, or caption boxes (text added later)")
                
                prompt_lines.append(f"")
                prompt_lines.append(f"PANELS ({len(panels)}):")
                for i, panel in enumerate(panels, 1):
                    visual_desc = panel.get("visual_description", "")
                    # Strip redundant style info from visual_desc
                    visual_desc = visual_desc.replace("A single comic book panel in High-contrast noir comic book style. ", "")
                    visual_desc = visual_desc.replace("Portrait 4:5.", "").strip()
                    
                    chars = panel.get("characters_present", [])
                    shot = panel.get("shot_type", "")
                    angle = panel.get("camera_angle", "")
                    
                    prompt_lines.append(f"{i}. [{shot} shot, {angle}] {visual_desc}")
                    if chars:
                        prompt_lines.append(f"   Characters: {', '.join(chars)}")
                    
                    # Add dialogue for context
                    dialogue = panel.get("dialogue", [])
                    if dialogue:
                        for line in dialogue:
                            char = line.get("character", "")
                            text = line.get("text", "")
                            if char == "Narrator":
                                prompt_lines.append(f"   [Context] Narration: \"{text}\"")
                            else:
                                prompt_lines.append(f"   [Context] {char}: \"{text}\"")
                prompt = "\n".join(prompt_lines)
                contents.append(prompt)
                logger.info(f"     📝 Prompt:\n{prompt}")
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model="gemini-2.5-flash-image",
                    contents=contents,
                    config=config,
                )
                generated_image = None
                for part in response.candidates[0].content.parts:
                    if part.inline_data is not None:
                        generated_image = Image.open(BytesIO(part.inline_data.data))
                        break
                
                if generated_image is None:
                    logger.error(f"     ❌ Gemini did not return image for {filename}")
                    continue
                
                # Save clean image (no text)
                clean_filename = f"ch{page_info['chapter_number']}_sc{page_info['scene_number']}_page{page_info['page_number']}_clean.png"
                clean_output_file = pages_dir / clean_filename
                generated_image.save(clean_output_file)
                logger.info(f"     ✅ Saved clean image: {clean_filename}")
                
                # Stage 2: Add text with controlled placement
                logger.info(f"     📝 Adding text to image...")
                from cinema.providers.gemini import GeminiMediaGen
                gemini = GeminiMediaGen()
                
                image_with_text = await gemini.add_text_to_image(
                    generated_image,
                    panels
                )
                
                # Save final image with text
                image_with_text.save(output_file)
                logger.info(f"     ✅ Saved with text: {filename}")
                
                # TODO: Bounding box detection - commented out for now
                # We'll come back to this later for text overlay placement
                # await self._detect_and_save_bounding_boxes(
                #     generated_image,
                #     page_info,
                #     output_file
                # )
                
                if page_idx not in self.state.pages_generated:
                    self.state.pages_generated.append(page_idx)
                
            except Exception as e:
                logger.error(f"     ❌ Failed: {e}")
                continue
        
        self.save_state()
        
        result = {
            "pages": new_pages,
            "output_dir": str(pages_dir),
            "total_generated": len(self.state.pages_generated)
        }
        
        logger.info(f"✅ Pages generated: {new_pages}")
        
        # Text overlays are now handled by Gemini during generation
        # No need for post-processing text overlay
        logger.info("📝 Text included in Gemini generation (no post-processing needed)")
        
        return result
    
    async def _detect_and_save_bounding_boxes(
        self,
        image,  # PIL Image
        page_info: dict,
        image_path  # Path
    ):
        """
        Detect bounding boxes for important objects in the generated image.
        
        Splits multi-panel pages into individual panels and detects objects per panel.
        
        Args:
            image: Generated PIL Image
            page_info: Page metadata including panels with important_objects
            image_path: Path where image was saved
        """
        from cinema.providers.gemini import GeminiMediaGen
        from PIL import Image
        import json
        
        panels = page_info['page_data'].get('panels', [])
        if not panels:
            logger.debug(f"     No panels to process")
            return
        
        panel_arrangement = page_info['page_data'].get('panel_arrangement', 'vertical-2-panel')
        
        logger.info(f"     🔍 Detecting objects per panel ({panel_arrangement})")
        
        # Split image into panels based on arrangement
        panel_images = self._split_page_into_panels(image, panel_arrangement, len(panels))
        
        if len(panel_images) != len(panels):
            logger.warning(f"     ⚠️  Panel count mismatch: {len(panel_images)} images vs {len(panels)} metadata")
            return
        
        # Initialize Gemini for object detection
        gemini = GeminiMediaGen()
        
        all_detections = []
        
        # Detect objects in each panel
        for i, (panel_img, panel_data) in enumerate(zip(panel_images, panels)):
            panel_num = panel_data.get('panel_number', i + 1)
            
            # Get labels for this panel
            labels = [obj.get('label') for obj in panel_data.get('important_objects', []) if obj.get('label')]
            
            if not labels:
                logger.debug(f"     Panel {panel_num}: No objects to detect")
                continue
            
            logger.info(f"     Panel {panel_num}: Detecting {len(labels)} objects")
            
            try:
                # Detect objects in this panel
                detections = await gemini.detect_objects(panel_img, labels)
                
                if detections:
                    # Map coordinates back to full page
                    panel_offset = self._get_panel_offset(i, panel_arrangement, image.size, len(panels))
                    
                    for detection in detections:
                        # Convert panel-local coordinates to page coordinates
                        box_2d = detection.get('box_2d', [])
                        if len(box_2d) == 4:
                            detection['box_2d'] = self._map_panel_to_page_coords(
                                box_2d, panel_offset, panel_img.size, image.size
                            )
                            detection['panel_number'] = panel_num
                            all_detections.append(detection)
                    
                    logger.info(f"     Panel {panel_num}: ✅ Detected {len(detections)} objects")
                else:
                    logger.warning(f"     Panel {panel_num}: ⚠️  No objects detected")
            
            except Exception as e:
                logger.error(f"     Panel {panel_num}: ❌ Detection failed: {e}")
        
        if not all_detections:
            logger.warning(f"     ⚠️  No objects detected in any panel")
            return
        
        # Save detections to JSON file alongside image
        detection_file = image_path.with_suffix('.detections.json')
        with open(detection_file, 'w') as f:
            json.dump({
                'image': str(image_path.name),
                'panel_arrangement': panel_arrangement,
                'num_panels': len(panels),
                'detections': all_detections
            }, f, indent=2)
        
        logger.info(f"     ✅ Total detected: {len(all_detections)} objects across {len(panels)} panels")
        
        # Update the chapter JSON with actual detected bounding boxes
        await self._update_chapter_with_detections(page_info, all_detections)
    
    def _split_page_into_panels(self, image, panel_arrangement: str, num_panels: int):
        """Split a multi-panel page into individual panel images."""
        from PIL import Image
        
        width, height = image.size
        panels = []
        
        if 'vertical' in panel_arrangement:
            # Vertical split (stacked panels)
            panel_height = height // num_panels
            for i in range(num_panels):
                y1 = i * panel_height
                y2 = (i + 1) * panel_height if i < num_panels - 1 else height
                panel = image.crop((0, y1, width, y2))
                panels.append(panel)
        
        elif 'horizontal' in panel_arrangement:
            # Horizontal split (side-by-side panels)
            panel_width = width // num_panels
            for i in range(num_panels):
                x1 = i * panel_width
                x2 = (i + 1) * panel_width if i < num_panels - 1 else width
                panel = image.crop((x1, 0, x2, height))
                panels.append(panel)
        
        else:
            # Default: treat as single panel
            panels.append(image)
        
        return panels
    
    def _get_panel_offset(self, panel_index: int, panel_arrangement: str, page_size: tuple, num_panels: int) -> tuple:
        """Get the (x, y) offset of a panel within the full page."""
        width, height = page_size
        
        if 'vertical' in panel_arrangement:
            # Vertical arrangement: panels stacked top to bottom
            panel_height = height // num_panels
            return (0, panel_index * panel_height)
        
        elif 'horizontal' in panel_arrangement:
            # Horizontal arrangement: panels side by side
            panel_width = width // num_panels
            return (panel_index * panel_width, 0)
        
        else:
            return (0, 0)
    
    def _map_panel_to_page_coords(self, box_2d: list, panel_offset: tuple, panel_size: tuple, page_size: tuple) -> list:
        """Map panel-local coordinates to full page coordinates."""
        y_min, x_min, y_max, x_max = box_2d
        offset_x, offset_y = panel_offset
        panel_width, panel_height = panel_size
        page_width, page_height = page_size
        
        # Convert from normalized panel coords to pixel coords
        panel_x1 = x_min * panel_width / 1000
        panel_y1 = y_min * panel_height / 1000
        panel_x2 = x_max * panel_width / 1000
        panel_y2 = y_max * panel_height / 1000
        
        # Add panel offset
        page_x1 = panel_x1 + offset_x
        page_y1 = panel_y1 + offset_y
        page_x2 = panel_x2 + offset_x
        page_y2 = panel_y2 + offset_y
        
        # Convert back to normalized page coords
        norm_x_min = int(page_x1 * 1000 / page_width)
        norm_y_min = int(page_y1 * 1000 / page_height)
        norm_x_max = int(page_x2 * 1000 / page_width)
        norm_y_max = int(page_y2 * 1000 / page_height)
        
        return [norm_y_min, norm_x_min, norm_y_max, norm_x_max]
    
    async def _update_chapter_with_detections(self, page_info: dict, detections: List[dict]):
        """Update chapter JSON file with actual detected bounding boxes."""
        import json
        from pathlib import Path
        
        chapter_file = Path(page_info['chapter_file'])
        
        # Load chapter data
        with open(chapter_file, 'r') as f:
            chapter_data = json.load(f)
        
        # Find the matching page and update important_objects
        chapter_num = page_info['chapter_number']
        scene_num = page_info['scene_number']
        page_num = page_info['page_number']
        
        for chapter in chapter_data.get('chapters', []):
            if chapter.get('chapter_number') != chapter_num:
                continue
            
            for scene in chapter.get('scenes', []):
                if scene.get('scene_number') != scene_num:
                    continue
                
                for page in scene.get('pages', []):
                    if page.get('page_number') != page_num:
                        continue
                    
                    # Update each panel's important_objects with detected boxes
                    for panel in page.get('panels', []):
                        panel_objects = panel.get('important_objects', [])
                        
                        # Match detections to panel objects by label
                        for obj in panel_objects:
                            label = obj.get('label')
                            for detection in detections:
                                if detection.get('label') == label:
                                    # Update with actual detected box
                                    obj['box_2d'] = detection['box_2d']
                                    obj['confidence'] = detection.get('confidence', 1.0)
                                    obj['detected'] = True
                                    break
        
        # Save updated chapter data
        with open(chapter_file, 'w') as f:
            json.dump(chapter_data, f, indent=2)
        
        logger.debug(f"     Updated {chapter_file.name} with detected bounding boxes")
    
    def _add_text_overlays_to_pages(self, page_numbers: List[int]):
        """Add text overlays to generated pages."""
        from cinema.utils.text_overlay import ComicTextOverlay
        from PIL import Image
        from pathlib import Path
        import json
        
        overlay = ComicTextOverlay()
        pages_dir = Path(self.output_dir) / "pages"
        
        # Load chapter data
        chapter_files = sorted(Path(self.output_dir).glob("chapter_*.json"))
        
        # Build page info map
        page_info_map = {}
        for chapter_file in chapter_files:
            with open(chapter_file) as f:
                data = json.load(f)
            
            for chapter in data.get('chapters', []):
                ch_num = chapter.get('chapter_number')
                for scene in chapter.get('scenes', []):
                    scene_num = scene.get('scene_number')
                    for page in scene.get('pages', []):
                        page_num = page.get('page_number')
                        key = f"ch{ch_num}_sc{scene_num}_page{page_num}.png"
                        page_info_map[key] = {
                            'panels': page.get('panels', []),
                            'layout': page.get('panel_arrangement', 'vertical-2-panel')
                        }
        
        # Add text to each page
        text_added = 0
        for page_file in pages_dir.glob("*.png"):
            if "_with_text" in page_file.name:
                continue
            
            page_info = page_info_map.get(page_file.name)
            if not page_info:
                continue
            
            # Check if page has text
            has_text = any(p.get('dialogue') or p.get('narration') for p in page_info['panels'])
            if not has_text:
                continue
            
            # Load image and add text
            img = Image.open(page_file)
            img_with_text = overlay.add_text_to_page(
                img,
                page_info['panels'],
                page_info['layout'],
                (img.width, img.height)
            )
            
            # Save with _with_text suffix
            output_file = pages_dir / f"{page_file.stem}_with_text.png"
            img_with_text.save(output_file)
            text_added += 1
        
        logger.info(f"✅ Text overlays added to {text_added} pages")
    

