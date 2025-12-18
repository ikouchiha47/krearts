#!/usr/bin/env python3
"""
Test the comic configuration API endpoints.
"""

import asyncio
import json
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

def test_comic_config_api():
    """Test comic configuration API endpoints"""
    print("🧪 Testing Comic Configuration API")
    print("=" * 50)
    
    # Use a test workflow ID
    workflow_id = "test_comic_config"
    
    # Test 1: Get default comic config
    print("📖 Getting default comic config...")
    try:
        response = requests.get(f"{BASE_URL}/workflows/book/{workflow_id}/comic-config")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Default config: {json.dumps(config, indent=2)}")
        else:
            print(f"❌ Failed to get config: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error getting config: {e}")
    
    # Test 2: Set custom comic config
    print("\n📝 Setting custom comic config...")
    custom_config = {
        "pages_per_chapter": 8,
        "chapter_style": "classic_dense",
        "panels_per_page": 6,
        "panel_layout": "grid_3x3",
        "panel_transitions": "smooth",
        "use_smart_compression": True,
        "context_window": 2,
        "summary_window": 3
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/workflows/book/{workflow_id}/comic-config",
            json=custom_config,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            saved_config = response.json()
            print(f"✅ Saved config: {json.dumps(saved_config, indent=2)}")
        else:
            print(f"❌ Failed to save config: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error saving config: {e}")
    
    # Test 3: Test chapter generation with comic config
    print("\n📚 Testing chapter generation with comic config...")
    chapter_request = {
        "chapters": "1",
        "art_style": "spiderverse",
        "aspect_ratio": "4:5",
        "comic_config": custom_config
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/workflows/book/{workflow_id}/chapters",
            json=chapter_request,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            job = response.json()
            print(f"✅ Chapter generation job created: {job['id']}")
            print(f"   Status: {job['status']}")
            print(f"   Metadata: {json.dumps(job['metadata'], indent=2)}")
        else:
            print(f"❌ Failed to create chapter job: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error creating chapter job: {e}")
    
    print("\n✅ Comic Configuration API Test Complete!")


def test_config_validation():
    """Test configuration validation"""
    print("\n🔍 Testing Configuration Validation")
    print("=" * 40)
    
    workflow_id = "test_validation"
    
    # Test invalid config
    invalid_configs = [
        {"pages_per_chapter": 0},  # Too low
        {"pages_per_chapter": 30},  # Too high
        {"panels_per_page": 1},  # Too low
        {"panels_per_page": 15},  # Too high
        {"context_window": 0},  # Too low
        {"summary_window": 10},  # Too high
    ]
    
    for i, invalid_config in enumerate(invalid_configs, 1):
        print(f"Test {i}: {invalid_config}")
        try:
            response = requests.post(
                f"{BASE_URL}/workflows/book/{workflow_id}/comic-config",
                json=invalid_config,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 422:
                print(f"✅ Validation error (expected): {response.status_code}")
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🚀 Starting Comic Configuration API Tests")
    print("Make sure the server is running on localhost:8000")
    print()
    
    try:
        test_comic_config_api()
        test_config_validation()
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()