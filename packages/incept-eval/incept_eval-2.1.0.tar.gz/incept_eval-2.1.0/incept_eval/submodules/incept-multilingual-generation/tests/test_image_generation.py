#!/usr/bin/env python3
"""
Direct test for image generation module - no mocks, runs actual API calls
Run with: python -m pytest tests/test_image_generation.py -v -s
"""

import pytest
import os
import sys
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from image_gen_module import ImageGenModule

# Configure logging to see progress
logging.basicConfig(level=logging.INFO)

@dataclass
class TestQuestion:
    question_text: str

class TestImageGeneration:
    """Test image generation with real API calls"""
    
    def setup_method(self):
        """Setup test environment"""
        self.image_gen = ImageGenModule()
        
        # Verify API keys are available
        assert os.getenv('OPENAI_API_KEY'), "OPENAI_API_KEY required"
        assert os.getenv('GEMINI_API_KEY'), "GEMINI_API_KEY required"
    
    def test_single_question_image_generation(self):
        """Test image generation for a single simple question"""
        test_question = TestQuestion("In a right triangle, one leg measures (x + 1) cm, the other leg measures 4 cm, and the hypotenuse measures (x + 3) cm. Use the Pythagorean Theorem to find the value of x.")
        questions = [test_question]
        
        # Generate images
        results = self.image_gen.generate_images_parallel(questions)
        
        # Verify results
        assert len(results) == 1
        assert results[0] is not None
        
        # Check that at least one method succeeded
        successful_methods = [method for method, result in results[0].items() if result is not None]
        assert len(successful_methods) > 0, f"No image generation methods succeeded"
        
        print(f"✅ Generated images with {len(successful_methods)} methods: {successful_methods}")
        
        # Verify files exist on disk
        for method, result in results[0].items():
            if result is not None:
                assert os.path.exists(result), f"Image file not found: {result}"
                print(f"✅ {method}: {result}")
    
    def test_math_question_image_generation(self):
        """Test image generation for a mathematical question"""
        test_question = TestQuestion("A rectangle has length 8 cm and width 5 cm. What is its area?")
        questions = [test_question]
        
        # Generate images
        results = self.image_gen.generate_images_parallel(questions)
        
        # Verify results
        assert len(results) == 1
        assert results[0] is not None
        
        # Check methods
        successful_methods = [method for method, result in results[0].items() if result is not None]
        print(f"✅ Math question generated images with {len(successful_methods)} methods: {successful_methods}")
        
        # Verify files exist
        for method, result in results[0].items():
            if result is not None:
                assert os.path.exists(result), f"Image file not found: {result}"
                print(f"✅ {method}: {result}")
    
    def test_multiple_questions_parallel(self):
        """Test parallel image generation for multiple questions"""
        test_questions = [
            # Geometry
            # TestQuestion("A triangular park has a base of 30 meters and a height of 24 meters. What is the area of the park?"),
            # TestQuestion("A ladder is leaning against a wall. The foot of the ladder is 9 feet away from the wall, and the top touches the wall at 12 feet high. How long is the ladder?"),
            # TestQuestion("A water tank is shaped like a cylinder with a radius of 7 meters and a height of 15 meters. What is the volume of the tank? (Use π ≈ 3.14)"),
            # TestQuestion("A gift box is shaped like a cube with edges measuring 5 cm. What is the total surface area of the box?"),
            # TestQuestion("A regular hexagon has all sides equal. Find the measure of one interior angle."),
            # TestQuestion("A circular garden has a diameter of 14 meters. Find its circumference. (Use π ≈ 3.14)"),
            # TestQuestion("A fish tank is 20 cm long, 12 cm wide, and 15 cm high. How many cubic centimeters of water can it hold?"),
            # TestQuestion("In a triangle, two angles measure 65° and 45°. What is the measure of the third angle?"),
            # TestQuestion("A trapezoid has bases of 10 cm and 16 cm, and a height of 8 cm. What is its area?"),
            # TestQuestion("A tree casts a shadow 18 meters long. At the same time, a 2-meter-tall signpost casts a shadow 3 meters long. How tall is the tree?"),
            # TestQuestion("Find the perimeter of a square with side length 6 meters"),

            # Numbers

            # TestQuestion("A pizza is cut into 12 equal slices. If Maria eats 3 slices and John eats 2 slices, how many slices are left?"),
            # TestQuestion("There are 28 students in a class. If each student gets 2 pencils, how many pencils are needed in total?"),
            # TestQuestion("A box has 36 chocolates. If 9 friends share them equally, how many chocolates does each friend get?"),
            # TestQuestion("There are 48 chairs in the hall arranged in 6 equal rows. How many chairs are there in each row?"),
            # TestQuestion("Sam has 25 apples. If he puts them into bags of 5 apples each, how many bags will he need?"),
            # TestQuestion("A bakery makes 120 cupcakes in a day. If they pack them into boxes of 10, how many boxes can they fill?"),
            # TestQuestion("There are 42 candies. If 7 children share them equally, how many candies will each child get?"),
            # TestQuestion("A train has 9 coaches, and each coach has 72 seats. How many seats are there in total?"),
            # TestQuestion("A farmer collects 96 eggs and puts them into cartons of 12 eggs each. How many cartons will he need?"),
            # TestQuestion("A shop sells pencils in packs of 8. If Lucy buys 7 packs, how many pencils does she have in total?"),
            # TestQuestion("There are 15 pizzas, and each pizza is cut into 8 slices. How many slices are there altogether?"),
            # TestQuestion("A stadium has 20 rows with 50 seats in each row. How many seats are there in the stadium?")

            
            # TestQuestion("In a class of 40 students, 18 like football, 15 like basketball, and 10 like both. How many students like only football?"),
            # TestQuestion("A survey shows that 60 people like tea, 45 like coffee, and 25 like both. How many people like only tea?"),
            # TestQuestion("In a school, 120 students were surveyed. 70 said they play cricket, 55 said they play football, and 30 said they play both. How many students play neither?"),
            # TestQuestion("A bag has 5 red balls, 3 blue balls, and 2 green balls. If one ball is picked at random, what is the probability of getting a blue ball?"),
            # TestQuestion("A coin is tossed twice. What is the probability of getting exactly one head?"),
            # TestQuestion("A die is rolled once. What is the probability of getting an even number greater than 2?"),
            # TestQuestion("The marks of 10 students in a test are: 15, 18, 20, 12, 25, 22, 18, 20, 15, 17. What is the mean of the marks?"),
            # TestQuestion("The ages of a group of friends are: 14, 15, 15, 16, 17, 17, 18. What is the median age?"),
            # TestQuestion("The shoe sizes of 12 students are recorded as: 7, 8, 8, 9, 7, 8, 10, 9, 8, 7, 8, 9. What is the mode?"),
            # TestQuestion("The bar graph shows the number of books read by students in one month: Ali – 5, Sara – 8, John – 6, Mary – 7. Who read the most books and how many?"),
            # TestQuestion("A pie chart shows the favorite fruits of a group of children: 40% like apples, 30% like bananas, 20% like grapes, and 10% like oranges. If there are 200 children, how many like bananas?"),
            # TestQuestion("In a line graph showing the temperature over 5 days, the temperatures were: Day 1 – 20°C, Day 2 – 22°C, Day 3 – 24°C, Day 4 – 23°C, Day 5 – 25°C. On which day was it the hottest?")

            # Division
            # TestQuestion("Mia has 29 marbles. She wants to put the same number of marbles in each of the four gift boxes shown below and keep exactly 9 marbles in her marble pouch. After she does this, how many marbles will be in each box?")
            # TestQuestion("Caleb bought 9 identical gift bags for a party.He plans to pack them into 3 identical boxes so that every box holds the same number of bags. Look at the picture of Caleb’s gift bags:"),
            # TestQuestion("Teresa picked 24 apples. She wants to put the apples into the three baskets shown below so that each basket gets the same number of apples.")
            # TestQuestion("Maya picked 36 apples. She wants to share them equally among the 6 empty baskets shown below."),
            # TestQuestion("Marisol has 13 beads and will string them equally on the 5 bracelets shown below.")
            # TestQuestion("Mia picked 25 apples. She wants to put the apples into the 5 baskets shown below so that each basket has the same number of apples. How many apples will go in each basket?")
            # TestQuestion("Maya bought 32 stickers and wants to put the same number of stickers in each of the 8 gift bags shown below. How many stickers will go in each bag?")
            TestQuestion("Mila has 8 empty baskets like the ones shown below. Eight empty woven baskets in two neat rows of four on a wooden table She plans to put 8 peaches in each basket. Before she starts filling the baskets, she sets aside 11 peaches to make jam. How many peaches did Mila pick altogether?")
        ]
        
        # Generate images for all questions
        results = self.image_gen.generate_images_parallel(test_questions)
        
        # Verify results
        assert len(results) == 3
        
        total_successful = 0
        for i, question_results in enumerate(results):
            assert question_results is not None
            successful_methods = [method for method, result in question_results.items() if result is not None]
            total_successful += len(successful_methods)
            print(f"✅ Question {i+1}: {len(successful_methods)} methods succeeded")
        
        assert total_successful > 0, "No images generated for any questions"
        print(f"✅ Total successful image generations: {total_successful}")
    
    def test_prompt_generation(self):
        """Test that educational prompts are being generated correctly"""
        test_question = "Solve for x: 2x + 5 = 13"
        
        # Test the prompt generation method directly
        prompt = self.image_gen._generate_educational_prompt(test_question)
        
        # Verify prompt was generated
        assert prompt is not None
        assert len(prompt) > 50  # Should be a substantial prompt
        assert test_question not in prompt  # Original question shouldn't be in the generated prompt
        
        print(f"✅ Generated prompt: {prompt[:100]}...")
    
    def test_generated_images_directory(self):
        """Test that generated_images directory is created and used"""
        test_question = TestQuestion("What is 7 - 3?")
        questions = [test_question]
        
        # Remove directory if it exists
        import shutil
        if os.path.exists("generated_images"):
            shutil.rmtree("generated_images")
        
        # Generate images
        results = self.image_gen.generate_images_parallel(questions)
        
        # Verify directory was created
        assert os.path.exists("generated_images"), "generated_images directory not created"
        
        # Verify files are in the directory
        files_in_dir = os.listdir("generated_images")
        assert len(files_in_dir) > 0, "No files created in generated_images directory"
        
        print(f"✅ Created {len(files_in_dir)} files in generated_images directory")

if __name__ == "__main__":
    """Run tests directly with python tests/test_image_generation.py"""
    test_instance = TestImageGeneration()
    test_instance.setup_method()
    
    print("🧪 Running image generation tests...")
    
    try:
        # test_instance.test_single_question_image_generation()
        # print("✅ Single question test passed")
        
        # test_instance.test_math_question_image_generation() 
        # print("✅ Math question test passed")
        
        # test_instance.test_prompt_generation()
        # print("✅ Prompt generation test passed")
        
        # test_instance.test_generated_images_directory()
        # print("✅ Directory creation test passed")
        
        test_instance.test_multiple_questions_parallel()
        print("✅ Multiple questions test passed")
        
        # print("\n🎉 All image generation tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()