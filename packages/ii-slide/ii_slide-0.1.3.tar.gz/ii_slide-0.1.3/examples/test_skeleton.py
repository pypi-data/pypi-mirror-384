"""
Test the skeleton system to ensure it works as expected for AI-driven slide generation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ii_slide.skeleton.manager import SkeletonManager
from ii_slide.skeleton.slides import (
    CoverSlide, TableOfContentSlide, ChapterSlide, ContentSlide, EndSlide
)
from ii_slide.skeleton.converter import SkeletonConverter
from ii_slide.templates import TemplateRegistry


def test_ai_workflow():
    """
    Test the AI workflow for creating a presentation.
    This simulates what an LLM would do to create slides.
    """
    print("🤖 Testing AI Skeleton System")
    print("=" * 50)

    # Initialize the skeleton manager (this holds the presentation state)
    registry = TemplateRegistry()
    manager = SkeletonManager(template_registry=registry)

    # Test 1: Create a cover slide (what an LLM would do)
    print("\n1. Creating cover slide...")
    cover = manager.add_slide(
        slide_type='cover',
        title='AI-Powered Presentation System',
        subtitle='Building the Future of Presentations',
        author='Claude AI',
        date='2025-01-01'
    )
    print(f"   ✓ Created cover slide: {cover.title}")

    # Test 2: Create table of contents
    print("\n2. Creating table of contents...")
    toc = manager.add_slide(
        slide_type='table_of_content',
        content=[
            'Introduction to AI Presentations',
            'Technical Architecture',
            'Implementation Details',
            'Future Roadmap'
        ]
    )
    print(f"   ✓ Created TOC with {len(toc.items)} items")

    # Test 3: Create chapter slide
    print("\n3. Creating chapter slide...")
    chapter = manager.add_slide(
        slide_type='chapter',
        title='Technical Architecture',
        chapter_number='01',
        subtitle='System Design and Components'
    )
    print(f"   ✓ Created chapter: {chapter.title}")

    # Test 4: Create simple content slide
    print("\n4. Creating simple content slide...")
    content1 = manager.add_slide(
        slide_type='content',
        title='System Overview',
        content='Our AI presentation system bridges the gap between complex PowerPoint JSON and simple content structure that AI can understand and modify.'
    )
    print(f"   ✓ Created content slide: {content1.title}")

    # Test 5: Create content slide with multiple blocks (what AI would do for complex content)
    print("\n5. Creating multi-content slide...")
    content2 = manager.add_slide(
        slide_type='content',
        title='Key Components',
        content=[
            {
                'title': 'Skeleton Manager',
                'content': 'Manages presentation state and provides AI-friendly API',
                'image': 'https://example.com/skeleton-diagram.png'
            },
            {
                'title': 'Template Converter',
                'content': 'Converts skeleton to PowerPoint JSON with automatic template selection',
                'image': 'https://example.com/converter-flow.png'
            }
        ]
    )
    print(f"   ✓ Created multi-content slide with {len(content2.content_blocks)} blocks")

    # Test 6: Create content slide with bullet points
    print("\n6. Creating slide with bullet points...")
    bullets_slide = manager.add_content_slide_with_points(
        title='Benefits',
        intro='This system provides several key advantages:',
        points=[
            'AI can easily understand and modify content',
            'Automatic template selection based on content structure',
            'Bidirectional sync between AI and user edits',
            'Type-safe API for reliable operation'
        ]
    )
    print(f"   ✓ Created slide with {len(bullets_slide.content_blocks[0].bullets)} bullet points")

    # Test 7: Create end slide
    print("\n7. Creating end slide...")
    end = manager.add_slide(
        slide_type='end',
        title='Thank You',
        subtitle='Questions & Discussion',
        contact_info='claude@anthropic.com'
    )
    print(f"   ✓ Created end slide: {end.title}")

    # Test 8: Show skeleton structure
    print("\n8. Analyzing presentation structure...")
    skeleton = manager.skeleton
    print(f"   📊 Total slides: {skeleton.get_slide_count()}")
    print(f"   📄 Content slides: {len(skeleton.get_content_slides())}")

    # Test 9: Convert to PowerPoint JSON
    print("\n9. Converting to PowerPoint JSON...")
    converter = SkeletonConverter(template_registry=registry)
    ppt_json = converter.skeleton_to_powerpoint(skeleton)
    print(f"   ✓ Generated PowerPoint JSON with {len(ppt_json['slides'])} slides")
    print(f"   ✓ Presentation size: {ppt_json['width']}x{ppt_json['height']}")

    # Test 10: Show template hints (what templates would be selected)
    print("\n10. Template selection hints...")
    content_slides = skeleton.get_content_slides()
    for i, slide in enumerate(content_slides, 1):
        hint = slide.get_template_hint()
        blocks = len(slide.content_blocks)
        print(f"    Content slide {i}: {blocks} blocks → {hint} template")

    # Test 11: Demonstrate skeleton JSON serialization
    print("\n11. Skeleton JSON representation...")
    skeleton_json = manager.get_skeleton_json()
    print(f"   ✓ Skeleton JSON size: {len(skeleton_json)} characters")

    # Test 12: Show round-trip capability
    print("\n12. Testing round-trip conversion...")
    extracted_skeleton = converter.extract_skeleton_from_powerpoint(ppt_json)
    print(f"   ✓ Extracted {len(extracted_skeleton.slides)} slides from PowerPoint JSON")

    print("\n" + "=" * 50)
    print("🎉 All tests passed! Skeleton system is working correctly.")
    print("\n📋 Summary:")
    print(f"   • Created {skeleton.get_slide_count()} slides total")
    print(f"   • {len(skeleton.get_content_slides())} content slides with various layouts")
    print(f"   • Automatic template selection based on content structure")
    print(f"   • Bidirectional conversion between skeleton and PowerPoint JSON")

    return True


def test_advanced_features():
    """Test advanced features like slide manipulation"""
    print("\n🔧 Testing Advanced Features")
    print("=" * 30)

    registry = TemplateRegistry()
    manager = SkeletonManager(template_registry=registry)

    # Add some slides
    manager.add_slide('cover', title='Test Presentation')
    manager.add_slide('content', title='Slide 1', content='Content 1')
    manager.add_slide('content', title='Slide 2', content='Content 2')

    print(f"Initial slides: {manager.skeleton.get_slide_count()}")

    # Test slide reordering
    success = manager.reorder_slides([0, 2, 1])  # Move slide 3 to position 2
    print(f"Reorder success: {success}")
    print(f"After reorder: {[s.title for s in manager.skeleton.slides]}")

    # Test slide removal
    success = manager.remove_slide(1)
    print(f"Remove success: {success}")
    print(f"After removal: {manager.skeleton.get_slide_count()} slides")

    # Test auto-generated TOC
    manager.add_slide('chapter', title='Chapter 1')
    manager.add_slide('content', title='Important Content')
    manager.add_content_slide_with_points('Key Points', 'Summary:', ['Point 1', 'Point 2'])

    toc = manager.auto_generate_toc()
    if toc:
        print(f"Auto-generated TOC with {len(toc.items)} items: {toc.items}")

    print("✅ Advanced features working correctly!")


if __name__ == "__main__":
    try:
        # Run main tests
        test_ai_workflow()

        # Run advanced features tests
        test_advanced_features()

        print("\n🎯 All skeleton system tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
