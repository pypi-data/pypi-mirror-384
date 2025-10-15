"""
Test script to parse PowerPoint JSON and convert to skeleton
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ii_slide.pptist.models import Presentation

with open("templates/template_1.json") as f:
    sample_json = json.loads(f.read())

def test_parse_and_convert():
    """Test parsing PowerPoint JSON and converting to skeleton"""

    # Parse the JSON into Python objects
    print("Parsing PowerPoint JSON...")
    try:
        presentation = Presentation.from_json(sample_json)
        print(f"✓ Successfully parsed presentation with {len(presentation.slides)} slides")
        print(f"  Presentation type: {presentation.type}")
        print(f"  Dimensions: {presentation.width}x{presentation.height}")

        # Convert back to JSON
        print("\nConverting back to JSON...")
        converted_json = presentation.to_dict()

        # Verify round-trip conversion
        print("Verifying round-trip conversion...")
        if converted_json == sample_json:
            print("✓ Round-trip conversion successful! JSON matches original")
        else:
            print("✗ Round-trip conversion failed - JSON differs from original")

            # Find differences
            import json
            with open("original.json", "w") as f:
                json.dump(sample_json, f, indent=2, sort_keys=True)
            with open("converted.json", "w") as f:
                json.dump(converted_json, f, indent=2, sort_keys=True)
            print("  Saved original.json and converted.json for comparison")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

        # Convert to skeleton
#         print("\nConverting to AI-friendly skeleton...")
#         skeleton = presentation.to_skeleton()
#         print("Skeleton structure:")

#         # Test round-trip: modify skeleton and update presentation
#         print("\n\nTesting round-trip conversion...")

#         # Modify skeleton (simulate AI edit)
#         if skeleton["slides"][0]["texts"]:
#             # Find the THANK YOU text
#             for text in skeleton["slides"][0]["texts"]:
#                 if "THANK" in text["content"]:
#                     text["content"] = "WELCOME BACK"
#                     print(f"  Modified text: THANK YOU -> WELCOME BACK")

#         # Update presentation from skeleton
#         presentation.update_from_skeleton(skeleton)

#         # Convert back to JSON
#         updated_json = presentation.to_dict()

#         # Check if the change was applied
#         for element in updated_json["slides"][0]["elements"]:
#             if element.get("type") == "text" and "WELCOME" in element.get("content", ""):
#                 print(f"✓ Round-trip successful! Text updated in presentation")
#                 print(f"  New content: {element['content'][:100]}...")
#                 break

#         # Save to file for inspection
#         with open("updated_presentation.json", "w") as f:
#             json.dump(updated_json, f, indent=2)
#         print("\n✓ Saved updated presentation to 'updated_presentation.json'")

#     except Exception as e:
#         print(f"✗ Error: {e}")
#         import traceback
#         traceback.print_exc()

if __name__ == "__main__":
    test_parse_and_convert()
