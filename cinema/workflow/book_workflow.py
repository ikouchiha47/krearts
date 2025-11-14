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
        
        logger.info(f"   Running ParallelComicGenerator for {len(new_chapters)} chapters...")
        logger.info(f"   use_mock={use_mock_chapters} (from skipper['s'])")
        comic_output = await generator.generate(
            novel=filtered_novel,
            art_style=art_style
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
            pages = list(range(1, min(11, len(all_pages) + 1)))  # Default to first 10 pages
        
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
                # Generate page
                page_data = page_info['page_data']
                panel_arrangement = page_data.get("panel_arrangement", "vertical-2-panel")
                panels = page_data.get("panels", [])
                
                logger.info(f"     Generating {len(panels)} panels ({panel_arrangement})")
                
                # Generate panel images
                panel_images = []
                for i, panel in enumerate(panels, 1):
                    visual_desc = panel.get("visual_description", "")
                    if not visual_desc:
                        logger.warning(f"       Panel {i} has no visual description, skipping")
                        continue
                    
                    logger.info(f"       Panel {i}/{len(panels)}...")
                    
                    # Generate panel image
                    response = await asyncio.to_thread(
                        client.models.generate_content,
                        model="gemini-2.5-flash-image",
                        contents=visual_desc,
                        config={"response_modalities": ["IMAGE"]},
                    )
                    
                    # Extract image
                    for part in response.candidates[0].content.parts:
                        if part.inline_data is not None:
                            img = Image.open(BytesIO(part.inline_data.data))
                            panel_images.append(img)
                            break
                
                # Composite panels into page
                logger.info(f"     Compositing {len(panel_images)} panels...")
                page_image = self._composite_page(panel_images, panel_arrangement)
                
                # Save
                page_image.save(output_file)
                logger.info(f"     ✅ Saved: {filename}")
                
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
        return result
    
    def _composite_page(self, panel_images: List, panel_arrangement: str, page_size=(1200, 1600)):
        """Composite multiple panel images into a single comic page."""
        from PIL import Image
        
        # Layout configurations
        LAYOUT_CONFIGS = {
            "horizontal-2-panel": {"rows": 1, "cols": 2},
            "horizontal-3-panel": {"rows": 1, "cols": 3},
            "vertical-2-panel": {"rows": 2, "cols": 1},
            "vertical-3-panel": {"rows": 3, "cols": 1},
            "zoom-progression": {"rows": 3, "cols": 1},
            "dynamic-grid": {"rows": 2, "cols": 2},
        }
        
        page_width, page_height = page_size
        config = LAYOUT_CONFIGS.get(panel_arrangement, LAYOUT_CONFIGS["vertical-2-panel"])
        
        # Create blank page
        page = Image.new('RGB', (page_width, page_height), color='white')
        
        rows = config["rows"]
        cols = config["cols"]
        gutter = 20
        
        # Calculate panel dimensions
        panel_height = (page_height - (rows + 1) * gutter) // rows
        panel_width = (page_width - (cols + 1) * gutter) // cols
        
        # Place panels
        panel_idx = 0
        for row in range(rows):
            for col in range(cols):
                if panel_idx >= len(panel_images):
                    break
                
                x = gutter + col * (panel_width + gutter)
                y = gutter + row * (panel_height + gutter)
                
                panel = panel_images[panel_idx].resize((panel_width, panel_height), Image.Resampling.LANCZOS)
                page.paste(panel, (x, y))
                
                panel_idx += 1
        
        return page
