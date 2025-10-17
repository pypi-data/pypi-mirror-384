#!/usr/bin/env python3
"""
Generate test questions for ALL DI formats
"""

import json

# Sample questions for each format based on title and skill
def generate_question_for_format(skill, grade, format_number, title):
    """Generate appropriate question for each format."""
    
    subject = skill.lower().replace("symbol identification and place value", "place value")
    subject = subject.replace("percent, ratio, probability", "probability")
    
    # Grade-appropriate questions based on format title
    questions = {
        # EQUALITY AND BASIC CONCEPTS
        "EQUALITY INTRODUCTION": {
            "question": f"3 = ?",
            "answer": "3",
            "options": ["2", "3", "4", "5"]
        },
        
        # ADDITION
        "TEACHING ADDITION THE SLOW WAY": {
            "question": "What is 2 + 1?",
            "answer": "3", 
            "options": ["2", "3", "4", "5"]
        },
        "TEACHING ADDITION THE FAST WAY": {
            "question": "Add: 1 + 4 = ?",
            "answer": "5",
            "options": ["3", "4", "5", "6"]
        },
        "SOLVING MISSING ADDENDS": {
            "question": "5 + ? = 8",
            "answer": "3",
            "options": ["2", "3", "4", "5"]
        },
        "ADDING THREE SINGLE-DIGIT NUMBERS": {
            "question": "What is 2 + 3 + 4?",
            "answer": "9",
            "options": ["8", "9", "10", "11"]
        },
        "ADDING TWO NUMERALS WITH RENAMING": {
            "question": "What is 17 + 15?",
            "answer": "32",
            "options": ["30", "31", "32", "33"]
        },
        "COMPLEX ADDITION FACTS WITH A TOTAL LESS THAN 20": {
            "question": "What is 9 + 7?",
            "answer": "16",
            "options": ["15", "16", "17", "18"]
        },
        
        # SUBTRACTION
        "SUBTRACTION WITH LINES": {
            "question": "You have 5 lines. Cross out 2. How many are left?",
            "answer": "3",
            "options": ["2", "3", "4", "5"]
        },
        "TEACHING REGROUPING": {
            "question": "What is 14 - 6?",
            "answer": "8",
            "options": ["6", "7", "8", "9"]
        },
        "SUBTRACTION WITH RENAMING": {
            "question": "What is 32 - 18?",
            "answer": "14",
            "options": ["12", "13", "14", "15"]
        },
        "TENS NUMBERS MINUS ONE": {
            "question": "What is 30 - 1?",
            "answer": "29",
            "options": ["28", "29", "30", "31"]
        },
        "RENAMING NUMBERS WITH ZEROS": {
            "question": "What is 100 - 34?",
            "answer": "66",
            "options": ["64", "65", "66", "67"]
        },
        
        # MULTIPLICATION
        "SINGLE DIGIT MULTIPLICATION": {
            "question": "What is 3 × 4?",
            "answer": "12",
            "options": ["10", "11", "12", "13"]
        },
        "MISSING-FACTOR MULTIPLICATION": {
            "question": "6 × ? = 24",
            "answer": "4",
            "options": ["3", "4", "5", "6"]
        },
        "ONE-DIGIT FACTOR TIMES TWO-DIGIT FACTOR—RENAMING": {
            "question": "What is 4 × 17?",
            "answer": "68",
            "options": ["64", "66", "68", "70"]
        },
        "TWO-DIGIT FACTOR TIMES TWO-DIGIT FACTOR": {
            "question": "What is 12 × 13?",
            "answer": "156",
            "options": ["144", "150", "156", "160"]
        },
        
        # DIVISION
        "INTRODUCING DIVISION": {
            "question": "What is 12 ÷ 3?",
            "answer": "4",
            "options": ["3", "4", "5", "6"]
        },
        "INTRODUCING DIVISION WITH REMAINDERS": {
            "question": "What is 13 ÷ 4?",
            "answer": "3 R1",
            "options": ["3", "3 R1", "4", "4 R1"]
        },
        "DIVISION WITH TWO-DIGIT QUOTIENTS": {
            "question": "What is 84 ÷ 4?",
            "answer": "21",
            "options": ["20", "21", "22", "23"]
        },
        
        # FRACTIONS
        "INTRODUCING FRACTIONS": {
            "question": "What fraction of this circle is shaded? (half shaded)",
            "answer": "1/2",
            "options": ["1/3", "1/2", "2/3", "3/4"]
        },
        "READING FRACTIONS": {
            "question": "How do you read 3/4?",
            "answer": "three fourths",
            "options": ["three fours", "three fourths", "four thirds", "four threes"]
        },
        "ADDING AND SUBTRACTING FRACTIONS WITH LIKE DENOMINATORS": {
            "question": "What is 2/5 + 1/5?",
            "answer": "3/5",
            "options": ["2/5", "3/5", "3/10", "4/5"]
        },
        
        # DECIMALS
        "READING DECIMALS": {
            "question": "How do you read 0.7?",
            "answer": "seven tenths",
            "options": ["seven", "seventy", "seven tenths", "seven hundredths"]
        },
        "WRITING DECIMALS": {
            "question": "Write 'four tenths' as a decimal.",
            "answer": "0.4",
            "options": ["0.04", "0.4", "4.0", "40"]
        },
        "MULTIPLYING DECIMALS": {
            "question": "What is 0.3 × 0.2?",
            "answer": "0.06",
            "options": ["0.5", "0.6", "0.06", "0.006"]
        },
        
        # GEOMETRY
        "IDENTIFICATION/DEFINITION—TRIANGLE": {
            "question": "Which shape is a triangle?",
            "answer": "The three-sided shape",
            "options": ["The four-sided shape", "The three-sided shape", "The round shape", "The five-sided shape"]
        },
        "FINDING THE AREA OF RECTANGLES": {
            "question": "Calculate the area of a rectangle with length 6 cm and width 4 cm.",
            "answer": "24 cm²",
            "options": ["10 cm²", "20 cm²", "24 cm²", "28 cm²"]
        },
        "CALCULATING THE VOLUME OF BOXES": {
            "question": "Calculate the volume of a box with length 4 cm, width 3 cm, and height 2 cm.",
            "answer": "24 cm³",
            "options": ["9 cm³", "14 cm³", "24 cm³", "32 cm³"]
        },
        
        # MEASUREMENT
        "METRIC CONVERSIONS": {
            "question": "How many centimeters are in 3 meters?",
            "answer": "300",
            "options": ["30", "300", "3000", "30000"]
        },
        "EXPRESSING TIME AS MINUTES AFTER THE HOUR": {
            "question": "If it's 3:15, how do you say the time?",
            "answer": "fifteen minutes after three",
            "options": ["quarter to three", "fifteen minutes after three", "three fifteen", "half past three"]
        },
        
        # COUNTING
        "INTRODUCING NEW NUMBERS": {
            "question": "Count to 10. What comes after 7?",
            "answer": "8",
            "options": ["6", "7", "8", "9"]
        },
        "RATIONAL COUNTING": {
            "question": "How many dots are there? ● ● ● ●",
            "answer": "4",
            "options": ["3", "4", "5", "6"]
        },
        
        # PLACE VALUE
        "INTRODUCING NEW NUMERALS": {
            "question": "What number is this: 7",
            "answer": "seven",
            "options": ["six", "seven", "eight", "nine"]
        },
        "READING TEEN NUMERALS USING PLACE VALUE CONCEPTS": {
            "question": "What number is 1 ten and 5 ones?",
            "answer": "15",
            "options": ["14", "15", "16", "51"]
        },
        
        # BASIC FACTS
        "PLUS-ONE FACTS": {
            "question": "What is 6 + 1?",
            "answer": "7",
            "options": ["5", "6", "7", "8"]
        },
        
        # DATA ANALYSIS
        "SORTING": {
            "question": "Sort these shapes: circle, square, circle, triangle. How many circles?",
            "answer": "2",
            "options": ["1", "2", "3", "4"]
        },
        "CREATING PICTURE GRAPHS": {
            "question": "In a picture graph, each symbol represents 2 students. If there are 3 symbols, how many students?",
            "answer": "6",
            "options": ["3", "5", "6", "9"]
        },
        
        # PERCENT/PROBABILITY
        "CONVERTING PERCENT TO DECIMAL": {
            "question": "Convert 25% to a decimal.",
            "answer": "0.25",
            "options": ["0.025", "0.25", "2.5", "25"]
        },
        "WRITING PROBABILITY FRACTIONS": {
            "question": "What is the probability of getting heads when flipping a coin?",
            "answer": "1/2",
            "options": ["1/4", "1/3", "1/2", "2/3"]
        },
        
        # PRE-ALGEBRA
        "USING AND PLOTTING A FUNCTION": {
            "question": "If y = x + 2 and x = 3, what is y?",
            "answer": "5",
            "options": ["1", "3", "5", "6"]
        },
        "COMBINING INTEGERS": {
            "question": "What is (-3) + 5?",
            "answer": "2",
            "options": ["-8", "-2", "2", "8"]
        }
    }
    
    # Default question if not found
    default = {
        "question": f"Solve this {skill.lower()} problem for grade {grade}.",
        "answer": "Correct answer",
        "options": ["Option A", "Correct answer", "Option C", "Option D"]
    }
    
    # Find matching question
    for key, question_data in questions.items():
        if key in title.upper():
            return {
                "name": f"Grade {grade} {skill} - {format_number}",
                "question": question_data["question"],
                "answer": question_data["answer"],
                "options": question_data["options"],
                "subject": subject,
                "grade": grade,
                "language": "en",
                "country": "UAE",
                "expected_di_skill": skill
            }
    
    return {
        "name": f"Grade {grade} {skill} - {format_number}",
        "question": default["question"],
        "answer": default["answer"],
        "options": default["options"],
        "subject": subject,
        "grade": grade,
        "language": "en",
        "country": "UAE",
        "expected_di_skill": skill
    }

def main():
    with open('edu_configs/di_formats.json', 'r') as f:
        data = json.load(f)
    
    all_questions = []
    for skill_name, skill_data in data.get('skills', {}).items():
        formats = skill_data.get('formats', [])
        for fmt in formats:
            grade = fmt.get('grade', 'Unknown')
            title = fmt.get('title', 'No title')
            format_num = fmt.get('format_number', 'No number')
            
            question = generate_question_for_format(skill_name, grade, format_num, title)
            all_questions.append(question)
    
    # Print as Python list format
    print("        # ============= ALL DI FORMAT QUESTIONS =============")
    for q in sorted(all_questions, key=lambda x: (str(x['grade']), x['subject'], x['name'])):
        print("        {")
        for key, value in q.items():
            if isinstance(value, str):
                print(f'            "{key}": "{value}",')
            elif isinstance(value, list):
                print(f'            "{key}": {value},')
            else:
                print(f'            "{key}": {value},')
        print("        },")

if __name__ == "__main__":
    main()