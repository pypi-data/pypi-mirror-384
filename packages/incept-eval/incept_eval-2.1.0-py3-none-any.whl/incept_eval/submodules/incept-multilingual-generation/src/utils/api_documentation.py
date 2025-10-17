#!/usr/bin/env python3
"""
API Documentation utility for generating comprehensive endpoint documentation.
"""

def get_api_documentation():
    """
    Returns all possible keys and their explanations for the v1/generate_questions endpoint.
    """
    return {
        "endpoint": "/v1/generate_questions",
        "method": "POST",
        "description": "Generate educational questions with scaffolding and optional image generation",
        "request_parameters": {
            "grade": {
                "type": "integer",
                "required": True,
                "description": "Student grade level (1-12)",
                "example": 3
            },
            "subject": {
                "type": "string",
                "required": True,
                "description": "Subject area for question generation",
                "valid_values": ["mathematics", "science", "english", "arabic", "social_studies", "islamic_studies"],
                "example": "mathematics"
            },
            "count": {
                "type": "integer",
                "required": True,
                "description": "Number of questions to generate",
                "range": "1-100",
                "example": 20
            },
            "language": {
                "type": "string",
                "required": False,
                "default": "arabic",
                "description": "Language for question text",
                "valid_values": ["arabic", "english"],
                "example": "english"
            },
            "difficulty": {
                "type": "string",
                "required": False,
                "default": "medium",
                "description": "Difficulty level of questions",
                "valid_values": ["easy", "medium", "hard"],
                "example": "medium"
            },
            "translate": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Apply additional translation/transformation layer after generation",
                "example": False
            },
            "model": {
                "type": "string",
                "required": False,
                "default": "falcon",
                "description": "LLM provider for scaffolding generation",
                "valid_values": ["falcon", "openai", "dspy"],
                "notes": {
                    "falcon": "UAE Sovereign AI model (Falcon H1-34B) - no API key required",
                    "openai": "OpenAI GPT models - requires OPENAI_API_KEY",
                    "dspy": "DSPy-optimized generation running with Falcon H1-34B backend - no API key required"
                },
                "example": "falcon"
            },
            "instructions": {
                "type": "string",
                "required": False,
                "description": "Natural language instructions for question generation",
                "example": "Generate basic multiplication questions"
            },
            "question_type": {
                "type": "string",
                "required": False,
                "default": "mcq",
                "description": "Type of questions to generate",
                "valid_values": ["mcq", "fill-in", "mixed"],
                "example": "mcq"
            },
            "enable_images": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Enable parallel image generation for questions",
                "notes": "Requires ENABLE_IMAGE_GENERATION=true and GEMINI_API_KEY",
                "example": True
            },
            "skill": {
                "type": "object",
                "required": False,
                "description": "Specific skill context for targeted question generation",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique identifier for the skill",
                        "example": "mult_facts_3"
                    },
                    "title": {
                        "type": "string",
                        "description": "Human-readable skill title",
                        "example": "Multiplication Facts"
                    },
                    "unit_name": {
                        "type": "string",
                        "description": "Educational unit containing the skill",
                        "example": "Multiplication Unit"
                    },
                    "lesson_title": {
                        "type": "string",
                        "description": "Specific lesson within the unit",
                        "example": "Times Tables Practice"
                    }
                }
            }
        },
        "response_format": {
            "data": {
                "type": "array",
                "description": "Array of generated questions",
                "items": {
                    "type": {
                        "type": "string",
                        "description": "Question type (mcq, fill-in)"
                    },
                    "question": {
                        "type": "string",
                        "description": "Question text in specified language"
                    },
                    "options": {
                        "type": "array",
                        "description": "Multiple choice options (null for fill-in)"
                    },
                    "answer": {
                        "type": "string",
                        "description": "Correct answer"
                    },
                    "difficulty": {
                        "type": "string",
                        "description": "Question difficulty level"
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Brief solution explanation"
                    },
                    "detailed_explanation": {
                        "type": "object",
                        "description": "Step-by-step solution with scaffolding",
                        "properties": {
                            "steps": "Array of solution steps (40-50 words each)",
                            "personalized_academic_insights": "Array of misconception corrections"
                        }
                    },
                    "voiceover_script": {
                        "type": "object",
                        "description": "Audio narration scripts"
                    },
                    "image_url": {
                        "type": "string",
                        "description": "Generated educational image URL (if enabled)"
                    }
                }
            },
            "request_id": {
                "type": "string",
                "description": "Unique request identifier (UUID)"
            },
            "total_questions": {
                "type": "integer",
                "description": "Number of questions generated"
            },
            "grade": {
                "type": "integer",
                "description": "Grade level used"
            },
            "language": {
                "type": "string",
                "description": "Language of generated content"
            }
        },
        "example_request": {
            "curl": """curl --location 'http://localhost:8000/v1/generate_questions' \\
--header 'Content-Type: application/json' \\
--data '{
    "grade": 3,
    "count": 20,
    "subject": "mathematics",
    "language": "english",
    "translate": false,
    "model": "falcon",
    "instructions": "Generate basic multiplication questions",
    "skill": {
        "id": "mult_facts_3",
        "title": "Multiplication Facts",
        "unit_name": "Multiplication Unit",
        "lesson_title": "Times Tables Practice"
    }
}'"""
        },
        "model_details": {
            "falcon": {
                "name": "Falcon H1-34B",
                "provider": "UAE Technology Innovation Institute",
                "requirements": "None - publicly accessible",
                "features": ["Multilingual", "Arabic excellence", "UAE sovereign AI"]
            },
            "openai": {
                "name": "GPT-4/GPT-3.5-turbo",
                "provider": "OpenAI",
                "requirements": "OPENAI_API_KEY environment variable",
                "features": ["Structured outputs", "Function calling", "High accuracy"]
            },
            "dspy": {
                "name": "DSPy with Falcon H1-34B",
                "provider": "Stanford DSPy + UAE TII",
                "requirements": "None - uses Falcon backend",
                "features": ["Optimized prompts", "Self-improving", "Educational quality metrics"]
            }
        },
        "notes": {
            "performance": "Image generation runs in parallel with text generation for optimal speed",
            "quality": "Questions validated using SymPy for mathematical accuracy",
            "cultural": "Content aligned with UAE curriculum and cultural standards",
            "fallback": "Automatic OpenAI fallback if Falcon is unavailable",
            "dspy_backend": "DSPy optimization uses Falcon H1-34B as the underlying model for UAE compliance"
        }
    }