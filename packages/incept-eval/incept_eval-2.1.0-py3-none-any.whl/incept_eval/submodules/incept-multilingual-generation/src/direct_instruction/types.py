from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union, Any


class UsedDIFormat(BaseModel):
    """A DI format that was used to generate insights"""
    title: Optional[str] = Field(default=None, description="Title of the format")
    skill_name: Optional[str] = Field(default=None, description="Name of the DI skill")
    format_number: Optional[str] = Field(default=None, description="Format number identifier")
    step_numbers_used: Optional[List[int]] = Field(default=None, description="Specific step numbers (1-indexed) from the format that were referenced")
    steps_used: Optional[List[str]] = Field(default=None, description="Exact text of the specific steps that were referenced")
    
class DIInsightsResponse(BaseModel):
    """Response from GPT-5 DI insights analysis"""
    insights: List[str] = Field(description="List of teaching insights, max 6 items, each under 100 chars", default_factory=list)
    has_relevant_insights: bool = Field(description="True if relevant insights exist, False if none", default=False)
    formats_used: Optional[List[UsedDIFormat]] = Field(default=None, description="Exact formats that were referenced to generate insights")


class SequenceItem(BaseModel):
    """Individual sequence item within a grade progression."""
    sequence_number: int
    problem_type: str
    example_questions: Optional[List[str]] = []
    visual_aids: Optional[List[str]] = []

class GradeProgression(BaseModel):
    """Grade-level progression containing sequence items."""
    grade: int
    sequence: List[SequenceItem]


class FormatStep(BaseModel):
    """Individual step in a format with teacher and student components."""
    step_number: int
    teacher_action: str
    student_response: Optional[str] = None
    notes: Optional[str] = None

class FormatPart(BaseModel):
    """A part within a format (e.g., Part A, Part B)."""
    part_name: str
    description: Optional[str] = None
    steps: List[FormatStep]

class Format(BaseModel):
    """Individual format within a skill/chapter."""
    format_number: str  # e.g., "7.1"
    title: str  # e.g., "EQUALITY INTRODUCTION"
    parts: List[FormatPart]


class TeachingFormat(BaseModel):
    """Teaching format from the JSON."""
    format_number: str
    title: str
    parts: List[FormatPart]
    assigned_grade: Optional[int] = None
    sequence_numbers: Optional[List[int]] = None
    grade_assignment_reasoning: Optional[str] = None


class Skill(BaseModel):
    """Individual skill with all its data."""
    name: str
    instruction_sequence_pages: str
    chapter_pages: str
    progression: Optional[List[GradeProgression]] = None
    formats: List[TeachingFormat]
    pitfalls: Optional[List[str]] = []
    processed_at: Optional[str] = None
    formats_processed_at: Optional[str] = None
    sequence_error: Optional[str] = None
    formats_error: Optional[str] = None


class Metadata(BaseModel):
    """Metadata for the DI formats document."""
    version: str
    source_document: str
    total_skills_processed: int
    summary: Dict[str, Union[int, str]]
    last_updated: str
    extraction_timestamp: Optional[str] = None
    extractor_version: Optional[str] = None
    status: Optional[str] = None
    completion_timestamp: Optional[str] = None
    grades_assigned_at: Optional[str] = None


class DIFormatsData(BaseModel):
    """Complete Direct Instruction formats data structure."""
    metadata: Metadata
    skills: Dict[str, Skill]

class SkillMappingResponse(BaseModel):
    """Response from LLM skill mapping"""
    is_mappable: bool = Field(description="Whether the skill can be mapped to a DI skill")
    di_skill_name: Optional[str] = Field(description="The DI skill name if mappable, None otherwise")
    confidence: float = Field(description="Confidence score 0-1")
    reasoning: str = Field(description="Brief explanation of the mapping decision")

class ExtractedFormat(BaseModel):
    """Lightweight extracted teaching format for downstream insights."""
    title: str = "Teaching Format"
    skill_name: Optional[str] = None
    format_number: Optional[str] = None
    steps: List[str] = Field(default_factory=list)

class PipelineState(BaseModel):
    question: str
    subject: str
    grade: int
    available_skills: List[str] = Field(default_factory=list)
    # Stage outputs and accumulators
    mapping: Optional[SkillMappingResponse] = None
    passages: str = ""
    doc_ids: List[str] = Field(default_factory=list)
    extracted_formats: List[ExtractedFormat] = Field(default_factory=list)
    pitfalls: List[str] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    has_relevant_insights: bool = False


class MapOutput(BaseModel):
    """Minimal output for skill mapping stage."""
    mapping: SkillMappingResponse

class ExtractInput(BaseModel):
    """Input for extracting teacher_action steps from passages for a specific question."""
    question: str
    passages: str

class ExtractOutput(BaseModel):
    """Output of extraction stage: a list of formats with steps."""
    extracted_formats: List[ExtractedFormat] = Field(default_factory=list)

class InsightsInput(BaseModel):
    question: str
    grade: int
    subject: str
    extracted_formats: List[ExtractedFormat] = Field(default_factory=list)
    pitfalls: List[str] = Field(default_factory=list)

class InsightsOutput(BaseModel):
    """Minimal output for insights stage."""
    insights: List[str] = Field(default_factory=list)
    has_relevant_insights: bool = False

class DIScaffoldingInsights(BaseModel):
    """Complete DI insights for scaffolding including the formatted text and source formats."""
    insights_text: str = Field(default="", description="Formatted DI insights text to include in the prompt")
    source_formats: Optional[List[Dict[str, Any]]] = Field(default=None, description="The actual DI format sections that were found and used")