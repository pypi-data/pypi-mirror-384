"""
Example of how an AI agent would use the ii-slide backend
This demonstrates the intended workflow for AI-driven presentation creation
"""
import requests
import json
from typing import List, Dict, Any


class IISlideAIAgent:
    """
    AI Agent wrapper for ii-slide backend
    Provides high-level methods for AI presentation creation
    """

    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.session = requests.Session()
        self.presentation_id = None

    def create_presentation(self, topic: str, template: str = "modern") -> str:
        """
        Create a new presentation on a given topic

        Args:
            topic: The presentation topic
            template: Template to use

        Returns:
            Presentation ID
        """
        # Initialize the presentation
        response = self.session.post(
            f"{self.backend_url}/api/ai/init_slide",
            json={"template_id": template}
        )
        response.raise_for_status()

        result = response.json()
        self.presentation_id = result["presentation_id"]

        print(f"🎯 Created presentation: {self.presentation_id}")
        return self.presentation_id

    def add_cover(self, title: str, subtitle: str = None, author: str = "AI Assistant") -> str:
        """Add cover slide"""
        response = self.session.post(
            f"{self.backend_url}/slides/cover",
            json={
                "title": title,
                "subtitle": subtitle,
                "author": author,
                "date": "2024"
            }
        )
        response.raise_for_status()
        return str(response.json()["slide_index"])

    def add_chapter(self, title: str, number: str, subtitle: str = None) -> str:
        """Add chapter divider slide"""
        response = self.session.post(
            f"{self.backend_url}/slides/chapter",
            json={
                "title": title,
                "chapter_number": number,
                "subtitle": subtitle
            }
        )
        response.raise_for_status()
        return str(response.json()["slide_index"])

    def add_content(self, title: str, points: List[Dict[str, str]], images: List[str] = None) -> str:
        """
        Add content slide with bullet points and optional images

        Args:
            title: Slide title
            points: List of content points, each with 'title' and 'content'
            images: Optional list of image URLs
        """
        content_blocks = []

        for i, point in enumerate(points):
            block = {
                "item_title": point.get("title", ""),
                "item": point.get("content", "")
            }

            # Add image if provided
            if images and i < len(images):
                block["image_src"] = images[i]
                block["image_caption"] = f"Image for {point.get('title', 'content')}"

            content_blocks.append(block)

        response = self.session.post(
            f"{self.backend_url}/slides/content",
            json={
                "title": title,
                "content_blocks": content_blocks
            }
        )
        response.raise_for_status()
        return str(response.json()["slide_index"])

    def add_closing(self, title: str = "Thank You", subtitle: str = None) -> str:
        """Add closing slide"""
        response = self.session.post(
            f"{self.backend_url}/slides/end",
            json={
                "title": title,
                "subtitle": subtitle
            }
        )
        response.raise_for_status()
        return str(response.json()["slide_index"])

    def get_final_presentation(self) -> Dict[str, Any]:
        """Get the final presentation JSON for export"""
        response = self.session.get(f"{self.backend_url}/api/presentation")
        response.raise_for_status()
        return response.json()

    def generate_tech_presentation(self, technology: str) -> str:
        """
        Generate a complete technical presentation about a technology

        Args:
            technology: The technology to present about

        Returns:
            Presentation ID
        """
        print(f"🤖 Generating presentation about: {technology}")

        # Create presentation
        self.create_presentation(f"{technology} Overview")

        # Add cover
        cover_id = self.add_cover(
            title=f"Introduction to {technology}",
            subtitle="A Comprehensive Overview"
        )
        print(f"✅ Added cover slide: {cover_id}")

        # Add introduction chapter
        intro_id = self.add_chapter(
            title="Introduction",
            number="01",
            subtitle="What is " + technology + "?"
        )
        print(f"✅ Added intro chapter: {intro_id}")

        # Add overview content
        overview_id = self.add_content(
            title=f"What is {technology}?",
            points=[
                {
                    "title": "Definition",
                    "content": f"{technology} is a powerful technology used for modern applications"
                },
                {
                    "title": "Key Benefits",
                    "content": "Improved performance, scalability, and developer experience"
                },
                {
                    "title": "Use Cases",
                    "content": "Web applications, mobile apps, enterprise systems"
                }
            ]
        )
        print(f"✅ Added overview slide: {overview_id}")

        # Add features chapter
        features_id = self.add_chapter(
            title="Key Features",
            number="02",
            subtitle="Core Capabilities"
        )
        print(f"✅ Added features chapter: {features_id}")

        # Add features content
        features_content_id = self.add_content(
            title="Core Features",
            points=[
                {
                    "title": "Performance",
                    "content": "Optimized for speed and efficiency"
                },
                {
                    "title": "Scalability",
                    "content": "Handles growing workloads seamlessly"
                },
                {
                    "title": "Developer Experience",
                    "content": "Easy to learn and use with great tooling"
                }
            ],
            images=["https://via.placeholder.com/400x300"] * 3
        )
        print(f"✅ Added features content: {features_content_id}")

        # Add implementation chapter
        impl_id = self.add_chapter(
            title="Implementation",
            number="03",
            subtitle="Getting Started"
        )
        print(f"✅ Added implementation chapter: {impl_id}")

        # Add getting started content
        start_id = self.add_content(
            title="Getting Started",
            points=[
                {
                    "title": "Installation",
                    "content": "Simple setup process with package managers"
                },
                {
                    "title": "Configuration",
                    "content": "Flexible configuration options for different environments"
                },
                {
                    "title": "First Steps",
                    "content": "Create your first application in minutes"
                }
            ]
        )
        print(f"✅ Added getting started slide: {start_id}")

        # Add conclusion
        conclusion_id = self.add_closing(
            title="Questions?",
            subtitle=f"Ready to start with {technology}?"
        )
        print(f"✅ Added conclusion slide: {conclusion_id}")

        print(f"🎉 Generated complete presentation about {technology}")
        return self.presentation_id


def main():
    """Main example function"""
    print("🚀 AI Agent Presentation Generation Example")

    # Create AI agent
    agent = IISlideAIAgent()

    try:
        # Generate a presentation about React
        presentation_id = agent.generate_tech_presentation("React")

        # Get final presentation
        final_presentation = agent.get_final_presentation()
        slide_count = len(final_presentation["presentation"]["slides"])

        print(f"\n📊 Final Results:")
        print(f"   - Presentation ID: {presentation_id}")
        print(f"   - Total Slides: {slide_count}")
        print(f"   - Backend URL: {agent.backend_url}")

        # Save presentation
        with open("ai_generated_presentation.json", "w") as f:
            json.dump(final_presentation, f, indent=2)
        print(f"   - Saved to: ai_generated_presentation.json")

        print("\n✨ AI-generated presentation ready!")
        print("💡 You can now open this in the PPTist frontend")

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        print("💡 Start the server with: python -m ii_slide.backend.main")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()