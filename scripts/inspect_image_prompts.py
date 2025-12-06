#!/usr/bin/env python3
"""
Inspect image generation prompts for chapter pages.

Shows exactly what prompts are sent to Gemini for image generation.
Useful for debugging prompt issues.

Usage:
    python scripts/inspect_image_prompts.py <workflow_id> --chapter 3 --page 5
    python scripts/inspect_image_prompts.py <workflow_id> --chapter 3 --all
"""
import json
import sys
from pathlib import Path
from typing import Optional

import click

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_page_info(chapter_data: dict, page_num: int) -> Optional[dict]:
    """Extract page info from chapter JSON."""
    for chapter in chapter_data.get('chapters', []):
        for scene in chapter.get('scenes', []):
            for page in scene.get('pages', []):
                if page.get('page_number') == page_num:
                    return {
                        'chapter_number': chapter.get('chapter_number'),
                        'scene_number': scene.get('scene_number'),
                        'page_number': page_num,
                        'page_data': page
                    }
    return None


def build_image_prompt(page_info: dict, art_style: str = "Print Comic Noir Style") -> str:
    """
    Build the exact prompt that would be sent to Gemini.
    This mirrors the logic in book_workflow.py generate_pages()
    """
    page_data = page_info['page_data']
    panel_arrangement = page_data.get("panel_arrangement", "vertical-2-panel")
    panels = page_data.get("panels", [])
    panel_borders = page_data.get("panel_borders", "clean-sharp")
    panel_transition = page_data.get("panel_transition_style", "hard-cuts")
    
    # Get unique characters
    unique_chars = set()
    for p in panels:
        for cp in p.get("characters_present", []):
            unique_chars.add(cp)
    
    # Build prompt lines
    prompt_lines = []
    prompt_lines.append(f"COMIC PAGE GENERATION")
    prompt_lines.append(f"")
    prompt_lines.append(f"STYLE: {art_style}")
    prompt_lines.append(f"Layout: 4:5 portrait, {panel_arrangement}")
    prompt_lines.append(f"Borders: {panel_borders}, Transitions: {panel_transition}")
    prompt_lines.append(f"")
    
    # Character descriptions (would be loaded from chapter JSON in real workflow)
    if unique_chars:
        prompt_lines.append(f"CHARACTERS IN THIS PAGE:")
        for char_name in unique_chars:
            prompt_lines.append(f"- {char_name}: [Character description would be here]")
        prompt_lines.append(f"")
    
    prompt_lines.append(f"RENDERING REQUIREMENTS:")
    prompt_lines.append(f"- High-contrast noir comic book style")
    prompt_lines.append(f"- Sharp, detailed rendering with accurate anatomy")
    prompt_lines.append(f"- Realistic object sizing and proportions")
    prompt_lines.append(f"- Fill full vertical frame, no letterboxing")
    prompt_lines.append(f"- NO text, speech bubbles, or caption boxes (text added later)")
    prompt_lines.append(f"")
    prompt_lines.append(f"PANELS ({len(panels)}):")
    
    for i, panel in enumerate(panels, 1):
        visual_desc = panel.get("visual_description", "")
        # Strip redundant style info
        visual_desc = visual_desc.replace("A single comic book panel in High-contrast noir comic book style. ", "")
        visual_desc = visual_desc.replace("A single comic book panel in Print Comic Noir Style. ", "")
        visual_desc = visual_desc.replace("Portrait 4:5.", "").strip()
        
        chars = panel.get("characters_present", [])
        shot = panel.get("shot_type", "")
        angle = panel.get("camera_angle", "")
        
        prompt_lines.append(f"{i}. [{shot} shot, {angle}] {visual_desc}")
        if chars:
            prompt_lines.append(f"   Characters: {', '.join(chars)}")
        
        # Show dialogue as context (even though it won't be in the image)
        dialogue = panel.get("dialogue", [])
        if dialogue:
            for line in dialogue:
                char = line.get("character", "")
                text = line.get("text", "")
                if char == "Narrator":
                    prompt_lines.append(f"   [Context] Narration: \"{text}\"")
                else:
                    prompt_lines.append(f"   [Context] {char}: \"{text}\"")
    
    return "\n".join(prompt_lines)


def build_text_addition_prompt(page_info: dict) -> str:
    """
    Build the prompt for adding text to the clean image.
    This mirrors the logic in add_text_to_image()
    """
    page_data = page_info['page_data']
    panels = page_data.get('panels', [])
    
    text_elements = []
    
    for i, panel in enumerate(panels, 1):
        dialogue = panel.get("dialogue", [])
        
        if not dialogue:
            continue
        
        for line in dialogue:
            char = line.get("character", "")
            text = line.get("text", "")
            
            if char == "Narrator":
                text_elements.append(
                    f"Panel {i} - NARRATION CAPTION (you may rephrase creatively):\n  \"{text}\""
                )
            else:
                bubble_type = "THOUGHT BUBBLE" if "think" in text.lower() else "SPEECH BUBBLE"
                text_elements.append(
                    f"Panel {i} - {bubble_type} for {char}:\n  EXACT TEXT (copy character-by-character): \"{text}\"\n  DO NOT CHANGE ANY WORDS"
                )
    
    if not text_elements:
        return "NO TEXT ELEMENTS TO ADD"
    
    text_elements_str = "\n".join(text_elements)
    
    prompt = f"""Add text elements to this comic book panel image.

CRITICAL INSTRUCTIONS - READ CAREFULLY:

1. For NARRATION captions: You may rephrase creatively to fit noir style
2. For SPEECH bubbles: You MUST use the EXACT text provided below
3. For THOUGHT bubbles: You MUST use the EXACT text provided below

RULES FOR SPEECH AND THOUGHT BUBBLES:
- Copy the text CHARACTER BY CHARACTER - do not change ANY words
- Do not rephrase, paraphrase, or "improve" the dialogue
- Do not fix grammar or spelling - use it EXACTLY as written
- Do not add or remove punctuation
- The text is already finalized - your job is ONLY to render it visually

TEXT ELEMENTS TO ADD:
{text_elements_str}

STYLE REQUIREMENTS:
- Use classic comic book lettering (bold, uppercase for emphasis)
- Narration captions: Rectangular boxes with beige/yellow background, black border
- Speech bubbles: White rounded bubbles with black border and tail pointing to speaker
- Thought bubbles: Cloud-like bubbles with scalloped edges
- Ensure text is readable and properly sized
- Place text to avoid covering important visual elements

VERIFICATION:
Before finalizing, verify that every speech/thought bubble contains the EXACT text from above.
If you changed even one word, you have failed the task.

IMPORTANT: Keep the existing artwork unchanged - only add text elements."""
    
    return prompt


@click.command()
@click.argument('workflow_id')
@click.option('--chapter', '-c', type=int, required=True, help='Chapter number')
@click.option('--page', '-p', type=int, help='Single page number')
@click.option('--all', 'all_pages', is_flag=True, help='Show all pages in chapter')
@click.option('--show-text-prompt', is_flag=True, help='Also show text addition prompt')
@click.option('--save', is_flag=True, help='Save prompts to files')
def main(workflow_id: str, chapter: int, page: Optional[int], all_pages: bool, show_text_prompt: bool, save: bool):
    """
    Inspect image generation prompts for chapter pages.
    
    Examples:
        # Show prompt for single page
        python scripts/inspect_image_prompts.py 43e21caa -c 3 -p 5
        
        # Show all pages in chapter
        python scripts/inspect_image_prompts.py 43e21caa -c 3 --all
        
        # Show both image and text prompts
        python scripts/inspect_image_prompts.py 43e21caa -c 3 -p 5 --show-text-prompt
        
        # Save prompts to files
        python scripts/inspect_image_prompts.py 43e21caa -c 3 -p 5 --save
    """
    # Load chapter JSON
    chapter_file = Path(f"output/book_{workflow_id}/chapter_{chapter:02d}.json")
    
    if not chapter_file.exists():
        click.echo(f"❌ Chapter file not found: {chapter_file}", err=True)
        sys.exit(1)
    
    with open(chapter_file, 'r') as f:
        chapter_data = json.load(f)
    
    # Get art style from chapter
    art_style = chapter_data.get('art_style', 'Print Comic Noir Style')
    
    # Determine which pages to show
    if all_pages:
        pages = []
        for ch in chapter_data.get('chapters', []):
            for scene in ch.get('scenes', []):
                for pg in scene.get('pages', []):
                    pages.append(pg.get('page_number'))
    elif page:
        pages = [page]
    else:
        click.echo("Error: Must specify --page or --all", err=True)
        sys.exit(1)
    
    # Process each page
    for page_num in pages:
        page_info = get_page_info(chapter_data, page_num)
        
        if not page_info:
            click.echo(f"❌ Page {page_num} not found in chapter {chapter}", err=True)
            continue
        
        click.echo("=" * 80)
        click.echo(f"Chapter {chapter}, Scene {page_info['scene_number']}, Page {page_num}")
        click.echo("=" * 80)
        click.echo()
        
        # Build and show image generation prompt
        click.echo("📸 IMAGE GENERATION PROMPT (Stage 1: Clean Image)")
        click.echo("-" * 80)
        image_prompt = build_image_prompt(page_info, art_style)
        click.echo(image_prompt)
        click.echo()
        
        # Show text addition prompt if requested
        if show_text_prompt:
            click.echo("📝 TEXT ADDITION PROMPT (Stage 2: Add Text)")
            click.echo("-" * 80)
            text_prompt = build_text_addition_prompt(page_info)
            click.echo(text_prompt)
            click.echo()
        
        # Save to files if requested
        if save:
            output_dir = Path(f"output/book_{workflow_id}/prompt_inspection")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            image_prompt_file = output_dir / f"ch{chapter}_page{page_num}_image_prompt.txt"
            with open(image_prompt_file, 'w') as f:
                f.write(image_prompt)
            click.echo(f"💾 Saved image prompt: {image_prompt_file}")
            
            if show_text_prompt:
                text_prompt_file = output_dir / f"ch{chapter}_page{page_num}_text_prompt.txt"
                with open(text_prompt_file, 'w') as f:
                    f.write(text_prompt)
                click.echo(f"💾 Saved text prompt: {text_prompt_file}")
            
            click.echo()
        
        # Show panel summary
        panels = page_info['page_data'].get('panels', [])
        click.echo(f"📊 SUMMARY:")
        click.echo(f"  Panels: {len(panels)}")
        click.echo(f"  Layout: {page_info['page_data'].get('panel_arrangement')}")
        click.echo(f"  Art Style: {art_style}")
        
        # Count dialogue
        total_dialogue = sum(len(p.get('dialogue', [])) for p in panels)
        click.echo(f"  Dialogue lines: {total_dialogue}")
        
        click.echo()


if __name__ == '__main__':
    main()
