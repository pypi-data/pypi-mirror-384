"""
Test script for custom PowerPoint JSON
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ii_slide.models import Presentation

def test_custom_json(json_file_path):
    """Test parsing custom PowerPoint JSON file"""

    # Load JSON from file
    print(f"Loading JSON from: {json_file_path}")
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ Successfully loaded JSON")
    except Exception as e:
        print(f"✗ Error loading JSON: {e}")
        return

    # Parse the JSON into Python objects
    print("\nParsing PowerPoint JSON...")
    try:
        presentation = Presentation.from_json(data)
        print(f"✓ Successfully parsed presentation with {len(presentation.slides)} slides")
        print(f"  Presentation type: {presentation.type}")
        print(f"  Dimensions: {presentation.width}x{presentation.height}")

        # Show slide details
        for i, slide in enumerate(presentation.slides):
            print(f"  Slide {i+1}: {slide.type.value} ({len(slide.elements)} elements)")

    except Exception as e:
        print(f"✗ Error parsing presentation: {e}")
        import traceback
        traceback.print_exc()
        return

    # Convert to skeleton
    print("\nConverting to AI-friendly skeleton...")
    try:
        skeleton = presentation.to_skeleton()
        print("✓ Skeleton conversion successful")

        # Save skeleton for inspection
        skeleton_file = Path(json_file_path).with_suffix('.skeleton.json')
        with open(skeleton_file, 'w', encoding='utf-8') as f:
            json.dump(skeleton, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved skeleton to: {skeleton_file}")

        # Show skeleton summary
        for i, slide_skel in enumerate(skeleton["slides"]):
            texts = len(slide_skel.get("texts", []))
            images = len(slide_skel.get("images", []))
            shapes = len(slide_skel.get("shapes", []))
            print(f"  Slide {i+1} skeleton: {texts} texts, {images} images, {shapes} shapes")

    except Exception as e:
        print(f"✗ Error converting to skeleton: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test round-trip conversion
    print("\nTesting round-trip conversion...")
    try:
        # Create a copy and modify skeleton
        test_skeleton = json.loads(json.dumps(skeleton))

        # Find first text element and modify it
        modified = False
        for slide_skel in test_skeleton["slides"]:
            for text in slide_skel.get("texts", []):
                if text.get("content"):
                    original_content = text["content"]
                    text["content"] = f"[MODIFIED] {original_content}"
                    print(f"  Modified text: '{original_content}' → '{text['content']}'")
                    modified = True
                    break
            if modified:
                break

        if modified:
            # Apply changes back to presentation
            presentation.update_from_skeleton(test_skeleton)

            # Save updated presentation
            updated_file = Path(json_file_path).with_suffix('.updated.json')
            with open(updated_file, 'w', encoding='utf-8') as f:
                json.dump(presentation.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"✓ Saved updated presentation to: {updated_file}")
        else:
            print("  No text elements found to modify")

    except Exception as e:
        print(f"✗ Error in round-trip test: {e}")
        import traceback
        traceback.print_exc()

    print("\n✓ Test completed successfully!")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python test_custom.py <path_to_your_json_file>")
        print("\nExample:")
        print("  python test_custom.py my_presentation.json")
        print("  python test_custom.py /path/to/slides.json")
        sys.exit(1)

    json_file = sys.argv[1]
    if not Path(json_file).exists():
        print(f"Error: File '{json_file}' not found")
        sys.exit(1)

    test_custom_json(json_file)