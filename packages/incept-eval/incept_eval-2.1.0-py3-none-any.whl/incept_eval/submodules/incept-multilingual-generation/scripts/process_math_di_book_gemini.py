from typing import Dict, Any, List
import logging
import os
import pdfplumber
import tiktoken
import json
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
    ]
)

logger = logging.getLogger(__name__)

# Configuration constants
MAX_OUTPUT_TOKENS = 48000  # Maximum tokens for Gemini response
TEMPERATURE = 0.1  # Low temperature for consistent extraction


class SubSkill(BaseModel):
    """Model for a sub-skill within a skill."""
    name: str = Field(description="Name of the sub-skill")
    teaching_methodologies: List[str] = Field(
        description="Teaching methodologies specific to this sub-skill",
        default_factory=list
    )
    question_creation_methodologies: List[str] = Field(
        description="Question creation methodologies for this sub-skill",
        default_factory=list
    )
    visual_aids: List[str] = Field(
        description="Visual aids used for this sub-skill",
        default_factory=list
    )


class Skill(BaseModel):
    """Model for a complete skill with its sub-skills."""
    skill_name: str = Field(description="Name of the main skill")
    description: str = Field(description="Description of the skill", default="")
    sub_skills: List[SubSkill] = Field(
        description="List of sub-skills under this main skill",
        default_factory=list
    )
    general_teaching_methodologies: List[str] = Field(
        description="General teaching methodologies that apply to the entire skill",
        default_factory=list
    )
    extraction_timestamp: str = Field(
        description="Timestamp when the information was extracted",
        default_factory=lambda: datetime.now().isoformat()
    )


class BookInformation(BaseModel):
    """Structured model for complete book information extraction."""
    skills: List[Skill] = Field(
        description="List of all skills covered in the book",
        default_factory=list
    )
    extraction_timestamp: str = Field(
        description="Timestamp when the information was extracted",
        default_factory=lambda: datetime.now().isoformat()
    )


PROMPT = """You are an expert at extracting information from a large mathematics education book.

###Book Text:
Here is the entire text of the book:
{book_text}

###Task:
Extract ALL skills and sub-skills covered in this book. For each skill, identify:
1. The main skill name (e.g., "Addition", "Subtraction", "Multiplication")
2. All sub-skills under that main skill (e.g., "Single-digit addition", "Addition with regrouping")
3. Teaching methodologies for each sub-skill
4. Question creation methodologies for each sub-skill  
5. Visual aids mentioned for each sub-skill
6. General teaching methodologies that apply to the entire skill

###Instructions: 
- Be comprehensive - extract ALL skills and sub-skills from the book
- Be highly concise and to the point, but without diluting the information
- Group related sub-skills under their appropriate main skill
- Don't duplicate information across skills/sub-skills

###Critical: 
- Convert any classroom specific interaction such as "point to", or "say", or "ask", into an online equivalent, where the teacher is an application, and not a humanoid 
- Example: Don't write "Teacher points to a row of 10 apples...", just write "Display a row of 10 apples..."
- DON'T make up stuff that is not in the book - only extract what is explicitly mentioned
- If a methodology or visual aid applies to multiple sub-skills, include it for each relevant sub-skill
- Be EXHAUSTIVE. Don't miss any information.
"""

# Initialize LangChain Google Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=TEMPERATURE,
    max_output_tokens=MAX_OUTPUT_TOKENS
)

def extract_information_from_book(book_text: str) -> BookInformation:
    """Extract information from the book text using LangChain structured output."""
    
    logger.info("Book text length: %d characters", len(book_text))
    logger.info("Book text preview: %s...%s", book_text[:500], book_text[-500:])

    logger.info("Sending request to Gemini 2.5 Pro for book information extraction")
    logger.info("Generation config: max_output_tokens=%d, temperature=%.1f", MAX_OUTPUT_TOKENS, TEMPERATURE)
    
    try:
        # Create structured output chain with LangChain
        structured_llm = llm.with_structured_output(BookInformation)
        
        # Create prompt template
        prompt_template = ChatPromptTemplate.from_template(PROMPT)
        
        # Create the chain
        chain = prompt_template | structured_llm
        
        # Execute the chain
        result = chain.invoke({"book_text": book_text})
        
        logger.info("Structured response received: %s", type(result))
        return result
        
    except Exception as e:
        logger.error("LangChain API call failed: %s", e)
        raise Exception(f"LangChain API call failed: {str(e)}")


def read_math_di_book():
    """Main function to process the Direct Instruction Mathematics book."""
    # Correct the path to go up one directory from scripts to project root, then into data
    project_root = os.path.dirname(os.path.dirname(__file__))
    pdf_path = os.path.join(project_root, "data", "Direct_Instruction_Mathematics.pdf")
    
    logger.info(f"Processing PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        logger.error(f"Error: PDF file not found at {pdf_path}")
        return
    
    page_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text += page.extract_text()
    
    return page_text

def count_tokens_in_book(book_text: str) -> int:
    """Count tokens in the book text."""
    encoding = tiktoken.encoding_for_model("gpt-4o")
    return len(encoding.encode(book_text))


def save_individual_skill_files(information: BookInformation) -> List[str]:
    """Save each skill to a separate JSON file.
    
    Args:
        information: The BookInformation object containing all skills
        
    Returns:
        List of paths where the files were saved
    """
    project_root = os.path.dirname(os.path.dirname(__file__))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a skills directory
    skills_dir = os.path.join(project_root, "data", "skills")
    os.makedirs(skills_dir, exist_ok=True)
    
    saved_files = []
    
    for skill in information.skills:
        # Create a safe filename from skill name
        safe_skill_name = "".join(c for c in skill.skill_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_skill_name = safe_skill_name.replace(' ', '_').lower()
        filename = f"{safe_skill_name}_{timestamp}.json"
        
        output_path = os.path.join(skills_dir, filename)
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(skill.model_dump_json(indent=2))
            logger.info("Successfully wrote skill '%s' to: %s", skill.skill_name, output_path)
            saved_files.append(output_path)
        except Exception as e:
            logger.error("Failed to write skill file for '%s': %s", skill.skill_name, e)
            raise
    
    return saved_files


def save_complete_book_information(information: BookInformation) -> str:
    """Save the complete book information to a single JSON file.
    
    Args:
        information: The BookInformation object to save
        
    Returns:
        The path where the file was saved
    """
    project_root = os.path.dirname(os.path.dirname(__file__))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"complete_book_information_{timestamp}.json"
    
    output_path = os.path.join(project_root, "data", output_filename)
    
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(information.model_dump_json(indent=2))
        logger.info("Successfully wrote complete book information to: %s", output_path)
        return output_path
    except Exception as e:
        logger.error("Failed to write complete book information file: %s", e)
        raise

if __name__ == "__main__":
    book_text = read_math_di_book()
    # book_text = book_text[:50000]
    logger.info("Book text length: %d", len(book_text))
    logger.info("Book text preview: %s...%s", book_text[:500], book_text[-500:])
    logger.info("Book text tokens: %d", count_tokens_in_book(book_text))



    information = extract_information_from_book(book_text)
    
    # Log summary of extracted information
    logger.info("Extraction Summary:")
    logger.info("Total skills extracted: %d", len(information.skills))
    
    for skill in information.skills:
        logger.info("Skill: %s", skill.skill_name)
        logger.info("  Sub-skills count: %d", len(skill.sub_skills))
        for sub_skill in skill.sub_skills:
            logger.info("    - %s", sub_skill.name)
    
    # Print the structured data as JSON for easy reading
    print(information.model_dump_json(indent=2))
    
    # Save complete book information to a single file
    complete_file_path = save_complete_book_information(information)
    print(f"\nComplete book information saved to: {complete_file_path}")
    
    # Save individual skill files
    skill_file_paths = save_individual_skill_files(information)
    print(f"\nIndividual skill files saved:")
    for path in skill_file_paths:
        skill_name = os.path.basename(path).replace('.json', '').replace('_' + datetime.now().strftime("%Y%m%d"), '')
        print(f"  - {skill_name}: {path}")
    
    print(f"\nTotal files created: {len(skill_file_paths) + 1}")  