"""
Test the new LangGraph-based image generation agent
"""

import pytest
import asyncio
import logging
from src.image_generation.image_generation_agent import ImageGenerationAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestImageGenerationAgent:
    """Test suite for the ImageGenerationAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create an ImageGenerationAgent instance"""
        return ImageGenerationAgent()
    
    @pytest.mark.asyncio
    async def test_real_world_image_generation(self, agent):
        """Test generating a real-world image"""
        question = "A baker has 12 cupcakes. She sells 5 cupcakes to customers. How many cupcakes does she have left?"
        
        result = await agent.generate_image_for_question(
            question=question,
            grade=3,
            subject="mathematics"
        )
        
        logger.info(f"Generated image URL: {result}")
        assert result is not None, "Image generation should return a URL"
        assert isinstance(result, str), "Result should be a string URL"
    
    @pytest.mark.asyncio
    async def test_geometric_shape_generation(self, agent):
        """Test generating geometric shapes"""
        question = "What is the area of a circle with radius 5 cm?"
        
        result = await agent.generate_image_for_question(
            question=question,
            grade=8,
            subject="geometry"
        )
        
        logger.info(f"Generated geometric image URL: {result}")
        assert result is not None, "Geometric image generation should return a URL"
        assert isinstance(result, str), "Result should be a string URL"
    
    @pytest.mark.asyncio
    async def test_bar_chart_generation(self, agent):
        """Test generating a chart/graph"""
        question = """A bar chart shows the number of books read by four students in one month:

        Anna: 8 books
        Ben: 5 books
        Clara: 12 books
        David: 7 books

        Using the bar chart:
        Who read the most books?
        How many more books did Clara read than Ben?
        What is the total number of books read by all four students combined?"""
        
        result = await agent.generate_image_for_question(
            question=question,
            grade=6,
            subject="mathematics"
        )
        
        logger.info(f"Generated chart URL: {result}")
        assert result is not None, "Chart generation should return a URL"
        assert isinstance(result, str), "Result should be a string URL"
    
    @pytest.mark.asyncio
    async def test_clock_time_generation(self, agent):
        """Test generating a clock showing specific time"""
        question = "What time is it when the short hand points to 4 and the long hand points to two points past 7?"
        
        result = await agent.generate_image_for_question(
            question=question,
            grade=2,
            subject="mathematics"
        )
        
        logger.info(f"Generated clock image URL: {result}")
        assert result is not None, "Clock image generation should return a URL"
        assert isinstance(result, str), "Result should be a string URL"
    
    @pytest.mark.asyncio
    async def test_number_line_generation(self, agent):
        """Test generating a number line"""
        question = """Start at 2 on a number line. Move 3 steps to the right.
        What number do you land on?
        Now, from that new number, move 5 steps to the left.

        Where do you end up?"""
        
        result = await agent.generate_image_for_question(
            question=question,
            grade=1,
            subject="mathematics"
        )
        
        logger.info(f"Generated number line URL: {result}")
        assert result is not None, "Number line generation should return a URL"
        assert isinstance(result, str), "Result should be a string URL"
    
    @pytest.mark.asyncio
    async def test_equation_visualization(self, agent):
        """Test generating mathematical equation image"""
        question = "Solve the quadratic equation x² + 2x - 3 = 0"
        
        result = await agent.generate_image_for_question(
            question=question,
            grade=10,
            subject="algebra"
        )
        
        logger.info(f"Generated equation image URL: {result}")
        assert result is not None, "Equation image generation should return a URL"
        assert isinstance(result, str), "Result should be a string URL"
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes properly"""
        assert agent is not None, "Agent should initialize"
        assert hasattr(agent, 'graph'), "Agent should have a graph attribute"
        assert hasattr(agent, 'llm'), "Agent should have an LLM attribute"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, agent):
        """Test error handling with invalid input"""
        # Test with empty question
        result = await agent.generate_image_for_question(
            question="",
            grade=5,
            subject="mathematics"
        )
        
        # Should handle gracefully (either return None or a default image)
        logger.info(f"Result for empty question: {result}")
        # Don't assert specific behavior, just ensure it doesn't crash

    @pytest.mark.asyncio
    async def run_single_test():
        agent = ImageGenerationAgent()
        
        print("Testing image generation agent...")
        question = "A farmer has 8 apples and gives away 3. How many apples are left?"
        
        result = await agent.generate_image_for_question(
            question=question,
            grade=2,
            subject="mathematics"
        )
        
        print(f"✅ Generated image: {result}")
        return result


if __name__ == "__main__":
    """Run a single test directly for quick verification"""
    test_agent = TestImageGenerationAgent()
    # Run the test
    result = asyncio.run(test_agent.test_real_world_image_generation())
    if result:
        print("🎉 Image generation agent test passed!")
    else:
        print("❌ Image generation agent test failed!")