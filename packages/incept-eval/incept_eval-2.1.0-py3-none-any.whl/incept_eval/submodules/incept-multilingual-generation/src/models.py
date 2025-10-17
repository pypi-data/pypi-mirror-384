from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Pydantic models for the database schema

class Country(BaseModel):
    id: Optional[UUID] = None
    code: str
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EducationSystem(BaseModel):
    id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    code: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Subject(BaseModel):
    id: Optional[UUID] = None
    name: str
    code: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Grade(BaseModel):
    id: Optional[UUID] = None
    education_system_id: UUID
    grade_number: int
    grade_name: str
    age_group: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Topic(BaseModel):
    id: Optional[UUID] = None
    education_system_id: UUID
    subject_id: UUID
    grade_id: UUID
    name: str
    description: Optional[str] = None
    sequence_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Chapter(BaseModel):
    id: Optional[UUID] = None
    topic_id: UUID
    name: str
    description: Optional[str] = None
    sequence_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class SubTopic(BaseModel):
    id: Optional[UUID] = None
    chapter_id: UUID
    name: str
    description: Optional[str] = None
    sequence_order: int = 0
    learning_objectives: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class QuestionType(BaseModel):
    id: Optional[UUID] = None
    name: str
    code: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

class Language(BaseModel):
    id: Optional[UUID] = None
    name: str
    code: str
    created_at: Optional[datetime] = None

class Question(BaseModel):
    id: Optional[UUID] = None
    sub_topic_id: UUID
    language_id: UUID
    question_type_id: UUID
    question_text: str
    question_data: Optional[dict] = None
    difficulty_level: str = "medium"
    points: int = 1
    time_limit_seconds: Optional[int] = None
    explanation: Optional[str] = None
    hints: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None