"""
Test PowerPoint JSON to Skeleton conversion.
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import only the converter module which doesn't have dataclass issues
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "ii_slide" / "skeleton"))
from ppt_to_skeleton import (
    PowerPointToSkeletonConverter,
    convert_powerpoint_to_skeleton,
    SkeletonPresentation
)


def test_conversion():
    """Test converting PowerPoint JSON to Skeleton format"""

    # Sample PowerPoint JSON with various elements
    ppt_json = {
        "type": "traditional",
        "width": 960,
        "height": 540,
        "slides": [
            {
                "id": "slide_001",
                "type": "cover",
                "elements": [
                    {
                        "type": "text",
                        "id": "title_main",
                        "content": '<p style="text-align: center;"><span style="font-size: 48px;font-weight: bold;">Welcome to AI Presentations</span></p>',
                        "textType": "title",
                        "width": 700,
                        "height": 80,
                        "left": 130,
                        "top": 200
                    },
                    {
                        "type": "text",
                        "id": "subtitle_main",
                        "content": '<p style="text-align: center;"><span style="font-size: 24px;">Building the Future</span></p>',
                        "textType": "subtitle",
                        "width": 700,
                        "height": 40,
                        "left": 130,
                        "top": 280
                    },
                    {
                        "type": "text",
                        "id": "author_text",
                        "content": '<p><span>Claude AI</span></p>',
                        "textType": "author",
                        "width": 200,
                        "height": 30,
                        "left": 130,
                        "top": 450
                    },
                    {
                        "type": "image",
                        "id": "logo_img",
                        "src": "https://example.com/logo.png",
                        "width": 100,
                        "height": 100,
                        "left": 430,
                        "top": 50,
                        "from_user": False  # AI generated - should be excluded
                    }
                ]
            },
            {
                "id": "slide_002",
                "type": "content",
                "elements": [
                    {
                        "type": "text",
                        "id": "content_title",
                        "content": '<p><span style="font-size: 32px;font-weight: bold;">Key Features</span></p>',
                        "textType": "title",
                        "width": 700,
                        "height": 50,
                        "left": 130,
                        "top": 40
                    },
                    {
                        "type": "text",
                        "id": "item_title_1",
                        "content": '<p><span style="font-weight: bold;">Semantic Understanding</span></p>',
                        "textType": "itemTitle",
                        "width": 300,
                        "height": 30,
                        "left": 130,
                        "top": 120
                    },
                    {
                        "type": "text",
                        "id": "item_1",
                        "content": '<p><span>AI understands the content structure, not just formatting</span></p>',
                        "textType": "item",
                        "width": 300,
                        "height": 60,
                        "left": 130,
                        "top": 160
                    },
                    {
                        "type": "image",
                        "id": "user_image_1",
                        "src": "https://example.com/diagram.png",
                        "width": 300,
                        "height": 200,
                        "left": 500,
                        "top": 150,
                        "from_user": True  # User uploaded - should be included
                    },
                    {
                        "type": "shape",
                        "id": "deco_shape",
                        "path": "M 0 0 L 100 0",
                        "width": 100,
                        "height": 2,
                        "left": 130,
                        "top": 250
                        # No textType, not an image with from_user - should be excluded
                    },
                    {
                        "type": "text",
                        "id": "no_type_text",
                        "content": "This text has no textType",
                        "width": 300,
                        "height": 30,
                        "left": 130,
                        "top": 300
                        # No textType - should be excluded
                    }
                ]
            },
            {
                "id": "slide_003",
                "type": "end",
                "elements": [
                    {
                        "type": "text",
                        "id": "thank_you",
                        "content": '<p style="text-align: center;"><span style="font-size: 60px;font-weight: bold;">Thank You</span></p>',
                        "textType": "title",
                        "width": 700,
                        "height": 100,
                        "left": 130,
                        "top": 200
                    },
                    {
                        "type": "text",
                        "id": "contact",
                        "content": '<p><span>Contact: ai@example.com</span></p>',
                        "textType": "contact",
                        "width": 300,
                        "height": 30,
                        "left": 330,
                        "top": 450
                    }
                ]
            }
        ]
    }

    print("🔄 Converting PowerPoint JSON to Skeleton")
    print("=" * 50)

    # Create converter
    converter = PowerPointToSkeletonConverter()

    # Convert to skeleton
    skeleton = converter.convert(ppt_json)

    print(f"\n✅ Conversion completed")
    print(f"   • Input slides: {len(ppt_json['slides'])}")
    print(f"   • Output slides: {len(skeleton.slides)}")

    # Show details for each slide
    print("\n📊 Skeleton Structure:")
    for i, slide in enumerate(skeleton.slides, 1):
        print(f"\n   Slide {i} (type: {slide.type}, id: {slide.id}):")
        print(f"      • Texts: {len(slide.texts)}")
        for text in slide.texts:
            content_preview = text['content'][:50] + "..." if len(text['content']) > 50 else text['content']
            print(f"        - {text['textType']}: {content_preview}")
        print(f"      • Images: {len(slide.images)}")
        for img in slide.images:
            print(f"        - {img['id']}: {img['src']} (from_user={img['from_user']})")

    # Test JSON output
    skeleton_json = skeleton.to_json()
    print(f"\n📄 Skeleton JSON (first 500 chars):")
    print(skeleton_json[:500] + "..." if len(skeleton_json) > 500 else skeleton_json)

    # Test ID mapping
    id_mapping = converter.get_id_mapping()
    print(f"\n🔗 ID Mappings: {len(id_mapping)} elements mapped")

    return skeleton


def test_id_matching():
    """Test ID matching with target skeleton"""

    print("\n\n🔄 Testing ID Matching")
    print("=" * 50)

    # Original PowerPoint JSON (no IDs)
    ppt_json = {
        "type": "traditional",
        "slides": [
            {
                "type": "cover",
                "elements": [
                    {
                        "type": "text",
                        "content": "Title Text",
                        "textType": "title"
                    }
                ]
            }
        ]
    }

    # Target skeleton with specific IDs
    target_skeleton = {
        "slides": [
            {
                "id": "existing_slide_123",
                "type": "cover",
                "texts": [
                    {
                        "id": "existing_text_456",
                        "type": "text",
                        "textType": "title",
                        "content": "Old Title"
                    }
                ]
            }
        ]
    }

    # Convert with ID matching
    result = convert_powerpoint_to_skeleton(ppt_json, target_skeleton)

    print(f"Original slide had no ID → matched to: {result['slides'][0]['id']}")
    print(f"Original text had no ID → matched to: {result['slides'][0]['texts'][0]['id']}")

    assert result['slides'][0]['id'] == "existing_slide_123", "Slide ID should match target"
    assert result['slides'][0]['texts'][0]['id'] == "existing_text_456", "Text ID should match target"

    print("\n✅ ID matching successful!")


def test_filtering():
    """Test that only relevant elements are extracted"""

    print("\n\n🔬 Testing Element Filtering")
    print("=" * 50)

    ppt_json = {
        "type": "traditional",
        "slides": [
            {
                "type": "content",
                "elements": [
                    # Should be included - has textType
                    {
                        "type": "text",
                        "content": "Included text",
                        "textType": "title"
                    },
                    # Should be excluded - no textType
                    {
                        "type": "text",
                        "content": "Excluded text - no textType"
                    },
                    # Should be included - from_user=true
                    {
                        "type": "image",
                        "src": "user_image.png",
                        "from_user": True
                    },
                    # Should be excluded - from_user=false
                    {
                        "type": "image",
                        "src": "ai_image.png",
                        "from_user": False
                    },
                    # Should be excluded - not text or image
                    {
                        "type": "shape",
                        "path": "M 0 0 L 100 100"
                    }
                ]
            }
        ]
    }

    skeleton = convert_powerpoint_to_skeleton(ppt_json)

    print(f"Input elements: 5")
    print(f"Output texts: {len(skeleton['slides'][0]['texts'])} (expected: 1)")
    print(f"Output images: {len(skeleton['slides'][0]['images'])} (expected: 1)")

    assert len(skeleton['slides'][0]['texts']) == 1, "Should only include text with textType"
    assert len(skeleton['slides'][0]['images']) == 1, "Should only include image with from_user=true"

    print("\n✅ Filtering working correctly!")


if __name__ == "__main__":
    try:
        # Test main conversion
        skeleton = test_conversion()

        # Test ID matching
        test_id_matching()

        # Test filtering
        test_filtering()

        print("\n\n🎯 All PowerPoint to Skeleton tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()