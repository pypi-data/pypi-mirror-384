"""
Test script for the ii-slide backend
Demonstrates AI agent usage of the skeleton interface
"""
import requests
import json
import asyncio
import websockets
from typing import Dict, Any


class IISlideClient:
    """Client for testing ii-slide backend"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def init_slide(self, template_id: str = "modern") -> Dict[str, Any]:
        """Initialize a new presentation"""
        response = self.session.post(
            f"{self.base_url}/api/ai/init_slide",
            json={"template_id": template_id}
        )
        response.raise_for_status()
        return response.json()

    def add_cover_slide(self, title: str, subtitle: str = None, author: str = None, date: str = None) -> Dict[str, Any]:
        """Add cover slide"""
        response = self.session.post(
            f"{self.base_url}/slides/cover",
            json={
                "title": title,
                "subtitle": subtitle,
                "author": author,
                "date": date
            }
        )
        response.raise_for_status()
        return response.json()

    def add_content_slide(self, title: str, content_blocks: list = None) -> Dict[str, Any]:
        """Add content slide"""
        if content_blocks is None:
            content_blocks = []

        response = self.session.post(
            f"{self.base_url}/slides/content",
            json={
                "title": title,
                "content_blocks": content_blocks
            }
        )
        response.raise_for_status()
        return response.json()

    def add_chapter_slide(self, title: str, chapter_number: str, subtitle: str = None) -> Dict[str, Any]:
        """Add chapter slide"""
        response = self.session.post(
            f"{self.base_url}/slides/chapter",
            json={
                "title": title,
                "chapter_number": chapter_number,
                "subtitle": subtitle
            }
        )
        response.raise_for_status()
        return response.json()

    def add_end_slide(self, title: str = "Thank You", subtitle: str = None) -> Dict[str, Any]:
        """Add end slide"""
        response = self.session.post(
            f"{self.base_url}/slides/end",
            json={
                "title": title,
                "subtitle": subtitle
            }
        )
        response.raise_for_status()
        return response.json()

    def get_skeleton(self) -> Dict[str, Any]:
        """Get current skeleton"""
        response = self.session.get(f"{self.base_url}/api/ai/skeleton")
        response.raise_for_status()
        return response.json()

    def get_presentation(self) -> Dict[str, Any]:
        """Get current presentation skeleton"""
        response = self.session.get(f"{self.base_url}/presentation")
        response.raise_for_status()
        return response.json()

    def get_presentation_pptist(self) -> Dict[str, Any]:
        """Get current PPTist JSON"""
        response = self.session.get(f"{self.base_url}/api/presentation")
        response.raise_for_status()
        return response.json()

    def get_status(self) -> Dict[str, Any]:
        """Get sync status"""
        response = self.session.get(f"{self.base_url}/api/sync/status")
        response.raise_for_status()
        return response.json()


async def test_websocket():
    """Test WebSocket connection"""
    try:
        async with websockets.connect("ws://localhost:8000/ws") as websocket:
            print("✅ WebSocket connected")

            # Listen for a few messages
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    print(f"📨 Received: {message[:100]}...")
                except asyncio.TimeoutError:
                    print(f"⏰ No message received in iteration {i+1}")
                    break

            print("🔌 WebSocket test completed")

    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")


def main():
    """Main test function"""
    print("🧪 Testing ii-slide backend...")

    client = IISlideClient()

    try:
        # Test 1: Initialize presentation
        print("\n1️⃣ Initializing presentation...")
        init_result = client.init_slide("modern")
        print(f"✅ Initialized: {init_result['presentation_id']}")

        # Test 2: Add cover slide
        print("\n2️⃣ Adding cover slide...")
        cover_result = client.add_cover_slide(
            title="AI-Generated Presentation",
            subtitle="Powered by ii-slide",
            author="AI Assistant",
            date="2024-01-01"
        )
        print(f"✅ Added cover slide: {cover_result['slide_index']}")

        # Test 3: Add chapter slide
        print("\n3️⃣ Adding chapter slide...")
        chapter_result = client.add_chapter_slide(
            title="Introduction",
            chapter_number="01",
            subtitle="Getting Started"
        )
        print(f"✅ Added chapter slide: {chapter_result['slide_index']}")

        # Test 4: Add content slides
        print("\n4️⃣ Adding content slides...")

        # Content slide 1
        content1_result = client.add_content_slide(
            title="Key Features",
            content_blocks=[
                {
                    "item_title": "AI Integration",
                    "item": "Seamless AI agent interaction with presentation content"
                },
                {
                    "item_title": "Real-time Sync",
                    "item": "Bidirectional synchronization between AI and UI"
                },
                {
                    "item_title": "Template System",
                    "item": "Automatic layout selection based on content structure"
                }
            ]
        )
        print(f"✅ Added content slide 1: {content1_result['slide_index']}")

        # Content slide 2 with images
        content2_result = client.add_content_slide(
            title="Architecture Overview",
            content_blocks=[
                {
                    "item_title": "Backend Components",
                    "item": "State manager, skeleton system, and PPTist adapter",
                    "image_src": "https://via.placeholder.com/400x300",
                    "image_caption": "Architecture diagram"
                }
            ]
        )
        print(f"✅ Added content slide 2: {content2_result['slide_index']}")

        # Test 5: Add end slide
        print("\n5️⃣ Adding end slide...")
        end_result = client.add_end_slide(
            title="Questions?",
            subtitle="Thank you for your attention"
        )
        print(f"✅ Added end slide: {end_result['slide_index']}")

        # Test 6: Get current state
        print("\n6️⃣ Checking presentation state...")
        status = client.get_status()
        print(f"✅ Status: {status['slide_count']} slides, version {status['version']}")

        # Test 7: Get skeleton representation
        print("\n7️⃣ Getting skeleton representation...")
        skeleton = client.get_skeleton()
        skeleton_data = json.loads(skeleton['skeleton'])
        print(f"✅ Skeleton has {len(skeleton_data['slides'])} slides")

        # Test 8: Get PPTist representation
        print("\n8️⃣ Getting PPTist representation...")
        pptist_presentation = client.get_presentation_pptist()
        pptist_slides = pptist_presentation['presentation']['slides']
        print(f"✅ PPTist JSON has {len(pptist_slides)} slides")

        # Test 9: WebSocket (if server is running)
        print("\n9️⃣ Testing WebSocket connection...")
        asyncio.run(test_websocket())

        print("\n🎉 All tests completed successfully!")
        print(f"\n📊 Final presentation stats:")
        print(f"   - Presentation ID: {init_result['presentation_id']}")
        print(f"   - Total slides: {status['slide_count']}")
        print(f"   - Current version: {status['version']}")
        print(f"   - Skeleton slides: {status['skeleton_slide_count']}")

        # Save final presentation for inspection
        final_presentation = client.get_presentation_pptist()
        with open("test_presentation_output.json", "w") as f:
            json.dump(final_presentation, f, indent=2)
        print(f"   - Saved to: test_presentation_output.json")

        # Save final skeleton for inspection
        final_skeleton = client.get_skeleton()
        with open("test_skeleton_output.json", "w") as f:
            json.dump(final_skeleton, f, indent=2)
        print(f"   - Skeleton saved to: test_skeleton_output.json")

    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Is the server running?")
        print("💡 Start the server with: python -m ii_slide.backend.main")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()