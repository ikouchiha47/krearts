#!/usr/bin/env python3
"""
Analyze generated comic page images using:
- libvips: Image processing and quality metrics
- OCR: Detect any text in images
- Ollama moondream:v2: Visual analysis and description
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

try:
    from PIL import Image
    import pytesseract
except ImportError:
    print("⚠️  pytesseract not installed. Install with: pip install pytesseract Pillow")
    pytesseract = None


def analyze_with_vips(image_path: Path) -> Dict[str, Any]:
    """Analyze image quality using vips CLI."""
    
    try:
        # Check if vips is available
        result = subprocess.run(
            ["vips", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return {"error": "vips CLI not available"}
        
        # Use PIL to get basic info (simpler than vips for this)
        from PIL import Image as PILImage
        img = PILImage.open(image_path)
        
        stats = {
            "width": img.width,
            "height": img.height,
            "mode": img.mode,
            "format": img.format,
        }
        
        # Calculate average brightness using vips avg
        result = subprocess.run(
            ["vips", "avg", str(image_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            try:
                stats['brightness'] = round(float(result.stdout.strip()), 2)
            except:
                pass
        
        # Get file size
        stats['file_size_kb'] = round(image_path.stat().st_size / 1024, 1)
        
        return stats
        
    except FileNotFoundError:
        return {"error": "vips CLI not found. Install with: brew install vips"}
    except Exception as e:
        return {"error": str(e)}


def detect_text_ocr(image_path: Path) -> Dict[str, Any]:
    """Detect text in image using OCR."""
    if not pytesseract:
        return {"error": "pytesseract not available"}
    
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        
        # Get detailed data
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        # Count text blocks
        text_blocks = [t for t in data['text'] if t.strip()]
        
        return {
            "text_detected": bool(text.strip()),
            "text_blocks": len(text_blocks),
            "text_preview": text.strip()[:200] if text.strip() else None,
            "confidence": round(sum(data['conf']) / len(data['conf']), 2) if data['conf'] else 0
        }
    except Exception as e:
        return {"error": str(e)}


async def analyze_with_moondream(image_path: Path, prompt: str = None) -> Dict[str, Any]:
    """Analyze image using Ollama moondream:v2."""
    
    if prompt is None:
        prompt = """Analyze this comic book panel image and describe:
1. Art style and visual quality
2. Characters present and their appearance
3. Setting and environment
4. Color palette and lighting
5. Composition and framing
6. Any issues or artifacts

Be specific and detailed."""
    
    try:
        # Check if ollama is available
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "moondream" not in result.stdout:
            return {"error": "moondream model not found. Run: ollama pull moondream:v2"}
        
        # Run moondream analysis using ollama API
        # First, encode image to base64
        import base64
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Use ollama API
        import requests
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'moondream:v2',
                'prompt': prompt,
                'images': [image_data],
                'stream': False
            },
            timeout=120
        )
        
        if response.status_code != 200:
            return {"error": f"Ollama API failed: {response.text}"}
        
        result_text = response.json().get('response', '')
        
        return {
            "analysis": result_text.strip(),
            "model": "moondream:v2"
        }
        
        if result.returncode != 0:
            return {"error": f"Ollama failed: {result.stderr}"}
        
        return {
            "analysis": result.stdout.strip(),
            "model": "moondream:v2"
        }
        
    except FileNotFoundError:
        return {"error": "Ollama not installed. Install from: https://ollama.ai"}
    except subprocess.TimeoutExpired:
        return {"error": "Ollama analysis timed out"}
    except Exception as e:
        return {"error": str(e)}


async def analyze_page(image_path: Path, page_info: Dict[str, Any]) -> Dict[str, Any]:
    """Comprehensive analysis of a comic page."""
    
    print(f"\n{'='*80}")
    print(f"Analyzing: {image_path.name}")
    print(f"{'='*80}")
    
    analysis = {
        "file": str(image_path),
        "page_number": page_info.get("page_number"),
        "scene_number": page_info.get("scene_number"),
    }
    
    # 1. Vips analysis
    print("📊 Running libvips analysis...")
    vips_stats = analyze_with_vips(image_path)
    analysis["vips"] = vips_stats
    
    if "error" not in vips_stats:
        print(f"   Size: {vips_stats['width']}x{vips_stats['height']}")
        print(f"   Sharpness: {vips_stats.get('sharpness', 'N/A')}")
        print(f"   Brightness: {vips_stats.get('brightness', 'N/A')}")
    
    # 2. OCR analysis
    print("🔍 Running OCR text detection...")
    ocr_results = detect_text_ocr(image_path)
    analysis["ocr"] = ocr_results
    
    if "error" not in ocr_results:
        print(f"   Text detected: {ocr_results['text_detected']}")
        print(f"   Text blocks: {ocr_results['text_blocks']}")
        if ocr_results.get('text_preview'):
            print(f"   Preview: {ocr_results['text_preview'][:100]}...")
    
    # 3. Moondream visual analysis
    print("🤖 Running Ollama moondream analysis...")
    
    # Build context-aware prompt
    panel_desc = page_info.get("page_description", "")
    expected_chars = []
    for panel in page_info.get("panels", []):
        expected_chars.extend(panel.get("characters_present", []))
    expected_chars = list(set(expected_chars))
    
    prompt = f"""Describe this comic book page in detail. What do you see? Include:
- Overall composition and layout
- Characters and their appearance
- Setting and environment details  
- Art style and visual quality
- Colors and lighting
- Any text or dialogue visible
- Overall quality assessment

Expected scene: {panel_desc}
Expected characters: {', '.join(expected_chars) if expected_chars else 'None'}"""
    
    moondream_results = await analyze_with_moondream(image_path, prompt)
    analysis["moondream"] = moondream_results
    
    if "error" not in moondream_results:
        print(f"\n   Analysis:\n{moondream_results['analysis']}\n")
    else:
        print(f"   ⚠️  {moondream_results['error']}")
    
    return analysis


async def analyze_all_pages(workflow_id: str):
    """Analyze all pages for a workflow."""
    
    output_dir = Path(f"output/book_{workflow_id}")
    pages_dir = output_dir / "pages"
    chapter_file = output_dir / "chapter_01.json"
    
    if not chapter_file.exists():
        print(f"❌ Chapter file not found: {chapter_file}")
        return
    
    # Load chapter data
    with open(chapter_file) as f:
        data = json.load(f)
    
    chapters = data.get('chapters', [])
    if not chapters:
        print("❌ No chapters found")
        return
    
    ch = chapters[0]
    
    print("=" * 80)
    print(f"IMAGE ANALYSIS: Chapter 1 - {ch.get('chapter_title', 'N/A')}")
    print("=" * 80)
    
    # Build page info map
    page_info_map = {}
    for scene in ch.get('scenes', []):
        scene_num = scene.get('scene_number')
        for page in scene.get('pages', []):
            page_num = page.get('page_number')
            key = f"ch1_sc{scene_num}_page{page_num}.png"
            page_info_map[key] = page
    
    # Analyze each page
    all_analyses = []
    image_files = sorted(pages_dir.glob("*.png"))
    
    for image_file in image_files:
        page_info = page_info_map.get(image_file.name, {})
        analysis = await analyze_page(image_file, page_info)
        all_analyses.append(analysis)
    
    # Save results
    results_file = output_dir / "image_analysis.json"
    with open(results_file, 'w') as f:
        json.dump(all_analyses, f, indent=2)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Results saved to: {results_file}")
    
    # Summary
    print("\n📊 SUMMARY:")
    print(f"   Total pages analyzed: {len(all_analyses)}")
    
    avg_brightness = sum(a['vips'].get('brightness', 0) for a in all_analyses if 'vips' in a and 'brightness' in a['vips'])
    if avg_brightness:
        avg_brightness = avg_brightness / len(all_analyses)
        print(f"   Average brightness: {avg_brightness:.2f}")
    
    if pytesseract:
        pages_with_text = sum(1 for a in all_analyses if a.get('ocr', {}).get('text_detected'))
        print(f"   Pages with text detected: {pages_with_text}/{len(all_analyses)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_images.py <workflow_id>")
        print("Example: python analyze_images.py 6021a791")
        print("\nRequirements:")
        print("  - pip install pytesseract pillow")
        print("  - brew install vips tesseract (macOS)")
        print("  - ollama pull moondream:v2")
        print("\nOptional: Skip moondream with --skip-moondream flag")
        sys.exit(1)
    
    workflow_id = sys.argv[1]
    asyncio.run(analyze_all_pages(workflow_id))
