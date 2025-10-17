# Incept Multilingual Question Generation

Educational question generation system with 5-module pipeline supporting UAE curriculum. Features mathematical computation, parallel image generation, and scaffolded solutions.

## Architecture

### Pipeline Flow
```
Module 1 (RAG) → Module 2 (Patterns) → Module 3 (Generation) → Module 4 (MCQ) → Module 5 (Scaffolding)
                                                ↓
                                        Image Generation (Parallel)
```

### Module Breakdown

| Module | Purpose | Technology | Input | Output |
|--------|---------|------------|-------|--------|
| **Module 1** | RAG Retrieval | DSPy, MongoDB Atlas, Multi-Stage Pipeline | Grade, Subject, Quantity | RetrievedSample[] |
| **Module 2** | Quality Pattern Extraction | DSPy RAG, Quality Scoring | RetrievedSample[] | ExtractedPattern[] (Max 10) |
| **Module 3** | Math Question Generation | DSPy, Grade-Aware Validation | ExtractedPattern[] | GeneratedQuestion[] |
| **Module 4** | MCQ Conversion | LLM, Pydantic | GeneratedQuestion[] | MultipleChoiceQuestion[] |
| **Module 5** | Scaffolding | LLM, Progress Tracking | MultipleChoiceQuestion[] | ScaffoldedSolution[] |
| **Image Gen** | Visual Content | Gemini, OpenAI DALL-E | GeneratedQuestion[] | ImageURL[] |

### Subject-Specific Implementations

**Mathematics Module (Module 3)**
- SymPy symbolic computation
- Parallel answer validation with ThreadPoolExecutor
- Mathematical formula verification
- Grade-appropriate value generation

**General Module (Module 3)**
- Subject-agnostic generation
- Pattern-based variation
- Cultural context integration

## Quick Start

```bash
# Install
poetry install

# Configure LLM Provider (used as default, can be overridden per request)
export LLM_PROVIDER=falcon  # UAE Sovereign AI (Falcon H1-34B), no API key
# OR
export LLM_PROVIDER=openai && export OPENAI_API_KEY=your-key

# Optional: Enable image generation
export ENABLE_IMAGE_GENERATION=true
export GEMINI_API_KEY=your-key

# Start server
poetry run uvicorn src.server:app --reload --port 8000
```

## API Endpoints

### Documentation Endpoint
```bash
GET /api/documentation
```
Returns complete API documentation with all possible keys and their explanations.

### LLM Completions Endpoint
```bash
POST /completions
```
Direct access to the LLM solving function with provider selection and language support.

**Request:**
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "What is 2+2?"}
  ],
  "max_tokens": 8000,
  "provider": "falcon",  // "falcon", "dspy", or "openai"
  "language": "english"  // "english", "arabic", "spanish", etc.
}
```

**Response:**
```json
{
  "response": "4"
}
```

### Question Generation Endpoint
```bash
POST /v2/generate_questions
```

**Request:**
```json
{
  "grade": 8,
  "subject": "mathematics",
  "count": 5,
  "difficulty": "medium",
  "language": "arabic",
  "model": "falcon",  # "falcon", "openai", or "dspy"
  "skill": {
    "title": "Linear Equations",
    "unit_name": "Algebra Unit"
  },
  "enable_images": true
}
```

**Response:**
```json
{
  "data": [
    {
      "type": "mcq",
      "question": "حل المعادلة: 2x + 5 = 13",
      "options": ["3", "4", "5", "6"],
      "answer": "4",
      "detailed_explanation": {
        "steps": [
          {"title": "Setup", "content": "نبدأ بالمعادلة الأصلية 2x + 5 = 13"},
          {"title": "Isolate", "content": "نطرح 5 من الطرفين للحصول على 2x = 8"},
          {"title": "Solve", "content": "نقسم على 2 للحصول على x = 4"}
        ]
      },
      "image_url": "https://...",
      "voiceover_script": {...}
    }
  ]
}
```

### Unified Evaluation Endpoint
```bash
POST /v1/evaluate_unified
```

Evaluate generated questions using unified evaluator with **configurable modules**.

**Module Configuration:**

You can now control which evaluation modules run by using the `modules` field:

```json
{
  "modules": {
    "v3_evaluation": true,           // V3 scaffolding/DI compliance (default: true)
    "answer_verification": true,     // GPT-4 answer correctness (default: true)
    "edubench_tasks": ["QA", "EC"],  // EduBench tasks to run (default: ["QA", "EC", "IP"])
                                     // Set to [] or null to skip EduBench
    // Future fine-grained controls:
    "v3_question_section": true,     // Include question section (default: true)
    "v3_scaffolding_section": true,  // Include scaffolding section (default: true)
    "v3_image_section": true         // Include image section (default: true)
  }
}
```

**Example Requests:**

**1. Full Evaluation (default - all modules enabled):**
```json
{
  "request": {
    "grade": 3,
    "count": 2,
    "subject": "mathematics",
    "instructions": "Generate multiplication word problems",
    "language": "arabic"
  },
  "questions": [
    {
      "type": "mcq",
      "question": "إذا كان لديك 4 علب من القلم وكل علبة تحتوي على 7 أقلام، كم عدد الأقلام لديك إجمالاً؟",
      "answer": "28",
      "difficulty": "medium",
      "explanation": "استخدام ضرب لحساب مجموع الأقلام في جميع العلب.",
      "options": {"A": "21", "B": "32", "C": "35", "D": "28"},
      "answer_choice": "D"
    }
  ]
}
```

**2. Only V3 Evaluation (skip answer verification and EduBench):**
```json
{
  "request": {...},
  "questions": [...],
  "modules": {
    "v3_evaluation": true,
    "answer_verification": false,
    "edubench_tasks": []
  }
}
```

**3. Only Answer Verification (fastest):**
```json
{
  "request": {...},
  "questions": [...],
  "modules": {
    "v3_evaluation": false,
    "answer_verification": true,
    "edubench_tasks": null
  }
}
```

**4. Custom EduBench Tasks Only:**
```json
{
  "request": {...},
  "questions": [...],
  "modules": {
    "v3_evaluation": false,
    "answer_verification": false,
    "edubench_tasks": ["QA", "IP"]  // Only Question Answering and Instructional Planning
  }
}
```

**Response (fields depend on enabled modules):**
```json
{
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "overall_scores": {
    "total_questions": 2,
    "v3_average": 0.87,                    // Only if v3_evaluation=true
    "answer_correctness_rate": 1.0,        // Only if answer_verification=true
    "total_edubench_tasks": 6              // Only if edubench_tasks not empty
  },
  "v3_scores": [                            // null if v3_evaluation=false
    {
      "overall": 0.87,
      "recommendation": "accept",
      "scores": {
        "correctness": 0.95,
        "grade_alignment": 0.90,
        "pedagogical_value": 0.85
      }
    }
  ],
  "answer_verification": [                  // null if answer_verification=false
    {
      "is_correct": true,
      "confidence": 10
    }
  ],
  "edubench_results": [                     // null if edubench_tasks=[] or null
    {
      "question_idx": 0,
      "task_type": "QA",
      "prompt": "Answer this question...",
      "response": "The student correctly calculated...",
      "timestamp": "2025-10-09T16:34:27.000Z"
    }
  ],
  "summary": {
    "evaluation_time_seconds": 24.5,
    "questions_evaluated": 2,
    "recommendation": "accept",              // Based on enabled metrics
    "modules_enabled": {
      "v3_evaluation": true,
      "answer_verification": true,
      "edubench_tasks": ["QA", "EC", "IP"]
    }
  }
}
```

**Available EduBench Tasks:**
- **QA**: Question Answering
- **EC**: Error Correction
- **IP**: Instructional Planning
- **AG**: Answer Generation (optional)

**Module Benefits:**
- **Performance**: Run only needed evaluations to reduce API latency
- **Cost**: Avoid GPT-4 calls when not needed (answer_verification)
- **Flexibility**: Custom evaluation workflows per use case
- **Backward Compatible**: Default behavior unchanged (all modules enabled)

### CLI Tool for Evaluation

The unified evaluator is also available as a CLI tool for batch processing and automation.

**Installation:**
```bash
poetry install
```

**Quick Start:**
```bash
# Generate example input file
poetry run incept-eval example > questions.json

# Run full evaluation
poetry run incept-eval evaluate questions.json --output results.json --pretty --verbose

# Quick single question evaluation
poetry run incept-eval quick-eval "What is 2+2?" "4" --grade 2 --pretty
```

**Module Selection:**
```bash
# Only V3 evaluation (skip answer verification and EduBench)
poetry run incept-eval evaluate questions.json --no-answer-verify --edubench

# Only answer verification (fastest)
poetry run incept-eval evaluate questions.json --no-v3 --edubench

# Custom EduBench tasks
poetry run incept-eval evaluate questions.json --edubench QA --edubench EC
```

**Available Commands:**
- `evaluate` - Evaluate questions from JSON file with configurable modules
- `quick-eval` - Quick evaluation of a single question
- `example` - Generate example input file
- `modules` - Show available evaluation modules

**See [CLI_USAGE.md](CLI_USAGE.md) for complete documentation and examples.**

## DSPy RAG System Architecture

The project features a sophisticated **DSPy-powered RAG system** that provides reusable, multi-stage retrieval-augmented generation capabilities across all modules.

### Core Components

**DSPyMongoRAG Engine**
- **Multi-Stage Pipeline**: Chain-of-thought RAG processing with customizable stages
- **MongoDB Atlas Integration**: Vector storage via LangChain's MongoDBAtlasVectorSearch
- **Structured Output**: Pydantic-based type safety with automatic JSON parsing
- **Critic-Revise Pattern**: Built-in response validation and improvement

### Key Features

**1. Multi-Stage Processing (`rag_retrieve` in Module 1)**
```python
# Example: 3-stage educational content retrieval
stages = [retrieve_stage, curation_stage, structuring_stage]
result = rag.run(stages=stages, initial_input=query)
```
- **Stage 1**: Context-aware retrieval with query rewriting
- **Stage 2**: Educational content curation and quality filtering
- **Stage 3**: Structured formatting into learning samples

**2. Easy Answer API (`easy_answer` method)**
```python
# Simple one-call RAG for quick enrichment
result = rag.easy_answer(question=query, grade=grade, k=8)
# Returns: {"answer": "...", "citations": [...], "confidence": 0.85}
```

### Performance Characteristics

**Quality Results**:
- **High-fidelity** educational content extraction
- **Context-aware** cultural and linguistic adaptation
- **Grade-appropriate** content filtering and adjustment

### Integration Examples

**Module 1**: Multi-stage educational content retrieval with sophisticated query rewriting and content curation
**Module 2**: Pattern enrichment using `easy_answer` for pedagogical guidance and constraint generation
**Module 3**: Educational context enhancement and validation support

This DSPy RAG system provides a **reusable foundation** for intelligent educational content processing across the entire pipeline.

## Technical Features

### Mathematical Processing
- **SymPy Integration**: Exact symbolic computation
- **Parallel Validation**: ThreadPoolExecutor for answer verification
- **Formula Verification**: Mathematical accuracy enforcement
- **Progress Tracking**: Real-time validation status

### Image Generation
- **Parallel Execution**: Non-blocking image generation alongside text
- **Multi-Provider**: Gemini (primary), OpenAI DALL-E (fallback)
- **Educational Context**: Grade and subject-appropriate visuals
- **Optional**: Complete disable via environment variable

### Cultural Integration
- **Arabic Education Standards**: Based on 4000+ production questions
- **UAE Curriculum Alignment**: Specific learning objectives
- **Quality Standards**: Mathematical precision, distractor validation
- **RTL Layout**: Proper Arabic text formatting

### Performance Optimizations
- **Async Pipeline**: Full async/await implementation
- **Parallel Processing**: Image generation + text processing
- **Progress Bars**: Real-time feedback on generation status
- **Connection Pooling**: Database efficiency

## Environment Variables

```bash
# Core
LLM_PROVIDER=falcon                    # "falcon"|"openai" (default for all modules)
OPENAI_API_KEY=sk-...                  # Required for OpenAI only (DSPy uses Falcon backend)

# Image Generation
ENABLE_IMAGE_GENERATION=true          # true|false
GEMINI_API_KEY=...                     # For visual content

# Database
POSTGRES_URI=postgresql://...          # Primary database
SUPABASE_URL=https://...               # Supabase integration
SUPABASE_KEY=...

# Development
DEV_MODE=false                         # Auto-upload to database
PORT=8000                              # Server port
```

## Module Details

### Module 1: Advanced RAG Retrieval
- **Core Engine**: DSPy-powered multi-stage RAG pipeline
- **Architecture**: 3-stage processing (Retrieve → Curate → Structure)
- **Vector Storage**: MongoDB Atlas with LangChain integration
- **Intelligence**: Context-aware query rewriting and educational content curation
- **Output**: High-quality structured educational samples

### Module 2: Quality-Focused Pattern Extraction
- **Quality Over Quantity**: Maximum 10 high-quality patterns (vs previous ~20)
- **Enhanced RAG**: DSPy-powered enrichment with pedagogical focus
- **Quality Scoring**: 0-10 scale based on educational value, template complexity, RAG confidence
- **Grade-Agnostic Design**: Natural scaling without rigid grade restrictions
- **Subject Extensions**: Math-specific enhancements with mathematical constraint detection
- **Performance Tracking**: Detailed progress bars with quality metrics
- **Output**: Top-ranked educational patterns with comprehensive metadata

### Module 3: Mathematics Question Generation
- **DSPy Framework**: Grade-aware question synthesis with validation pipeline
- **Advanced Validation**: Multi-stage question quality assessment
  - Mathematical correctness detection
  - Grade-appropriateness scoring (strict 7/10 threshold)
  - Vocabulary and concept complexity validation
- **Intelligent Correction**: Automated question improvement with DSPy
- **Parallel Processing**: ThreadPoolExecutor with optimal worker scaling (max 20)
- **Grade Intelligence**: Natural grade awareness without rigid constraints
- **Quality Control**: Comprehensive rejection of non-mathematical or inappropriate content
- **Performance**: Enhanced progress tracking with success/failure rates

### Module 4: MCQ Conversion
- Multiple choice format conversion
- Distractor generation
- Educational misconception analysis
- QTI-compatible output

### Module 5: Scaffolding
- 40-50 word detailed explanations (enhanced from 20-30)
- Arabic education quality standards integration
- Step-by-step solution breakdown
- Progress tracking for scaffolding generation

### Image Generation Module
- **Async Processing**: Parallel to text generation
- **Provider Fallback**: Gemini → OpenAI DALL-E
- **Educational Context**: Grade and subject-aware
- **Integration**: Automatic URL assignment to questions

## Technology Stack

**Core Framework**
- FastAPI (async API)
- Poetry (dependency management)
- Pydantic (data validation)

**AI/ML**
- **DSPy Framework**: Multi-stage RAG pipeline with chain-of-thought processing
- OpenAI GPT-4/3.5-turbo
- Falcon H1-34B (UAE Sovereign AI)
- **DSPyMongoRAG**: Custom RAG engine with educational content optimization
- Gemini (image generation)
- SymPy (mathematical computation)

**Data Layer**
- PostgreSQL (primary)
- MongoDB (vector storage)
- Supabase (hosting)
- LangChain (RAG pipeline)

**Processing**
- AsyncIO (concurrency)
- ThreadPoolExecutor (parallel validation)
- Progress tracking utilities

## Development

```bash
# Full feature development
ENABLE_IMAGE_GENERATION=true DEV_MODE=true poetry run uvicorn src.server:app --reload

# Mathematics testing with different models
curl -X POST "http://localhost:8000/v2/generate_questions" \
  -H "Content-Type: application/json" \
  -d '{"grade": 10, "subject": "mathematics", "count": 3, "model": "falcon"}'

# DSPy-optimized generation (uses Falcon backend)
curl -X POST "http://localhost:8000/v2/generate_questions" \
  -H "Content-Type: application/json" \
  -d '{"grade": 10, "subject": "mathematics", "count": 3, "model": "dspy"}'

# Project structure
src/
├── module_1.py              # DSPy RAG retrieval with multi-stage pipeline
├── module_2.py              # Quality-focused pattern extraction (max 10)
├── module_3_mathematics.py  # DSPy math generation with validation
├── module_4.py              # Enhanced MCQ conversion
├── module_5.py              # Scaffolding with progress
├── dspy_rag.py              # DSPyMongoRAG engine implementation
├── image_gen_module.py      # Parallel image generation
├── orchestrator.py          # Pipeline coordination
├── server.py                # FastAPI application
└── utils/
    ├── progress_bar.py      # Enhanced progress tracking
    ├── api_documentation.py # API endpoint documentation
    └── spiky_points_of_view.json  # Quality standards
```

## Quality Standards

Based on 4000+ production questions:
- **Curriculum Alignment**: Direct UAE curriculum mapping
- **Mathematical Precision**: SymPy verification for accuracy
- **Language Standards**: Grade-appropriate, tested with student populations
- **Cultural Integration**: Authentic UAE context without distraction
- **QTI Compatibility**: Standards-compliant structure

---

**Technical Support**: Full async pipeline with parallel processing, mathematical computation, and cultural education standards.