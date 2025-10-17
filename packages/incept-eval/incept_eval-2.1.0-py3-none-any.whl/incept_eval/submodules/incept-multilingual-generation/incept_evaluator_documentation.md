# Incept Evaluator: Educational Question Quality Assessment Framework

## Table of Contents
- [Overview](#overview)
- [Evaluation Methodology](#evaluation-methodology)
- [Evaluation Dimensions](#evaluation-dimensions)
- [Section-Based Evaluation](#section-based-evaluation)
- [Scoring System](#scoring-system)
- [Weights and Aggregation](#weights-and-aggregation)
- [Comprehensive Evaluation Output](#comprehensive-evaluation-output)
- [Baseline Tracking](#baseline-tracking)
- [Usage Examples](#usage-examples)

---

## Overview

**Incept Evaluator** is a comprehensive quality assessment framework for educational mathematics questions, designed to evaluate both the **pedagogical quality** and **technical correctness** of AI-generated questions.

### Key Features
- **Subject-Agnostic Design**: Math-friendly but not math-specific
- **Three-Section Evaluation**: Question, Scaffolding, and Image sections evaluated independently
- **10 Evaluation Dimensions**: Comprehensive coverage of quality, accuracy, and pedagogical value
- **Automated LLM-Based Evaluation**: Uses OpenAI GPT models for consistent, scalable assessment
- **Baseline Tracking**: Continuous quality monitoring across commits and time
- **0-10 Scoring Scale**: Clear scoring bands from Excellent to Unacceptable

---

## Evaluation Methodology

### Single-Shot LLM Evaluation
Unlike iterative evaluation approaches, Incept Evaluator uses a **single LLM call per question** to:
1. Evaluate all 10 dimensions simultaneously
2. Identify issues and strengths
3. Generate actionable improvement suggestions
4. Provide section-specific scores and recommendations

### Evaluation Pipeline
```
Question Input → LLM Evaluator → {
    ├─ Question Section Evaluation (7 dimensions)
    ├─ Scaffolding Section Evaluation (3 dimensions)
    ├─ Image Section Evaluation (placeholder)
    ├─ Overall Score Calculation
    └─ Recommendation (accept/revise/reject)
}
```

---

## Evaluation Dimensions

Incept Evaluator assesses **10 distinct dimensions** across educational quality, technical accuracy, and pedagogical value:

### 1. Correctness & Factual Accuracy
**Purpose**: Evaluates mathematical accuracy, factual correctness, and answer key validity

**Scoring Criteria**:
- **9-10**: Perfect accuracy in all facts, calculations, and answer keys
- **7-8**: Mostly correct with minor computational or factual errors
- **5-6**: Generally correct but contains some notable errors
- **3-4**: Multiple significant errors affecting reliability
- **1-2**: Fundamentally incorrect or misleading

**Pre-Check Rules** (Auto-Reject Triggers):
- Answer letter doesn't map to an option
- Correct answer not present among options
- Impossible patterns (e.g., special angles for non-special problems)

### 2. Grade Level Appropriateness
**Purpose**: Assesses if complexity and content match the target grade level

**Scoring Criteria**:
- **9-10**: Perfectly calibrated to specified grade level
- **7-8**: Well-aligned with minor deviations in complexity
- **5-6**: Roughly appropriate but some misalignment
- **3-4**: Significant mismatch with grade expectations
- **1-2**: Completely inappropriate for target grade

### 3. Difficulty Consistency
**Purpose**: Checks if actual difficulty matches the declared level

**Scoring Criteria**:
- **9-10**: Actual difficulty perfectly matches declaration
- **7-8**: Good alignment with slight variance
- **5-6**: Moderate mismatch between declared and actual
- **3-4**: Significant discrepancy in difficulty
- **1-2**: Complete mismatch or undefined difficulty

### 4. Language & Clarity
**Purpose**: Evaluates grammar, clarity, and appropriateness of language

**Scoring Criteria**:
- **9-10**: Crystal clear, grammatically perfect, age-appropriate
- **7-8**: Clear with minor language issues
- **5-6**: Generally understandable but needs polish
- **3-4**: Confusing or grammatically problematic
- **1-2**: Incomprehensible or severely flawed language

### 5. Educational Impact (Pedagogical Value)
**Purpose**: Assesses learning potential and educational value

**Scoring Criteria**:
- **9-10**: Exceptional learning opportunity with clear objectives
- **7-8**: Good educational value with solid learning outcomes
- **5-6**: Moderate educational benefit
- **3-4**: Limited learning value
- **1-2**: No educational merit or potentially harmful

### 6. Explanation & Guidance Quality
**Purpose**: Evaluates if explanations guide learning vs just stating answers

**Scoring Criteria**:
- **9-10**: Excellent step-by-step guidance promoting understanding
- **7-8**: Good explanations with clear reasoning
- **5-6**: Basic explanations present but could be clearer
- **3-4**: Poor explanations or just answer statements
- **1-2**: No useful explanation or misleading guidance

**Critical Check**: Flag "leakage" if explanation reveals exact option text

### 7. Request Compliance (Instruction Adherence)
**Purpose**: Measures adherence to specified requirements and format

**Scoring Criteria**:
- **9-10**: Perfectly follows all instructions and requirements
- **7-8**: Good compliance with minor deviations
- **5-6**: Partially compliant with some requirements missed
- **3-4**: Major deviations from instructions
- **1-2**: Completely ignores requirements

### 8. Format & Structure (Format Compliance)
**Purpose**: Checks structural correctness (MCQ options, answer format, etc.)

**Scoring Criteria**:
- **9-10**: Perfect format (e.g., 4 options A-D for MCQ)
- **7-8**: Good structure with minor formatting issues
- **5-6**: Acceptable format but needs improvement
- **3-4**: Poor formatting affecting usability
- **1-2**: Completely wrong or unusable format

**MCQ Requirements**: 4 options (A-D), answer as letter mapping to option

### 9. Direct Instruction Compliance (DI Compliance)
**Purpose**: Evaluates adherence to DI principles, scaffolding formats, and grade-level language

**Scoring Criteria**:
- **9-10**: Fully aligned with DI guidance across principles, format, and vocabulary
- **7-8**: Minor DI lapses but overall aligned
- **5-6**: Notable DI issues that need revision
- **3-4**: Major DI violations (missing scaffolds, inconsistent tone)
- **1-2**: Fundamentally breaks DI expectations

**DI Sub-Metrics** (weighted):
- General Principles (40%): Conciseness, clarity, explicit instruction
- Format Alignment (35%): Proper scaffolding structure
- Grade Language (25%): Age-appropriate vocabulary

### 10. Query Relevance (VETO DIMENSION)
**Purpose**: Assesses how well the generated question matches the original user query/instructions/skill context

**Scoring Criteria**:
- **9-10**: Perfectly aligned with query topic, skill, and educational intent
- **7-8**: Relevant to query with minor topic drift
- **5-6**: Partially relevant but some misalignment with query intent
- **3-4**: Significant deviation from requested topic/skill
- **1-2**: Completely off-topic or unrelated to original query

**⚠️ VETO POWER**: Query relevance score < 4.0 (0.4 normalized) triggers **automatic REJECT** regardless of other scores.

---

## Section-Based Evaluation

Incept Evaluator performs **three independent section evaluations** per question:

### Question Section
**Dimensions Evaluated** (7):
- Correctness
- Grade Alignment
- Difficulty Alignment
- Language Quality
- Instruction Adherence
- Format Compliance
- Query Relevance

**Section Score Calculation**:
```
question_section_score = average(7 question dimensions)
```

**Focus**: Question text clarity, options formatting, answer correctness, topic alignment

### Scaffolding Section
**Dimensions Evaluated** (3):
- Pedagogical Value
- Explanation Quality
- DI Compliance

**Section Score Calculation**:
```
scaffolding_section_score = average(3 scaffolding dimensions)
```

**Focus**: Explanation quality, step-by-step guidance, DI adherence

### Image Section
**Status**: Placeholder (not yet implemented)

**Current Behavior**: Automatically assigned perfect score (1.0) with note "Image evaluation not yet implemented"

**Future Implementation**: Will evaluate image relevance, quality, and educational value

---

## Scoring System

### Score Scale
All dimensions use a **0-10 scale**, normalized to **0.0-1.0** for internal processing:

| Band | Score | Description |
|------|-------|-------------|
| **Excellent** | 9-10 | Exceptional quality, meets all criteria perfectly |
| **Good** | 7-8 | Good quality with minor issues that don't affect core functionality |
| **Acceptable** | 5-6 | Acceptable but with notable issues requiring attention |
| **Poor** | 3-4 | Significant problems, major revisions needed |
| **Unacceptable** | 1-2 | Fundamentally flawed, complete rework required |

### Score Normalization
```python
# LLM returns 0-10 scores
raw_score = 8.0

# Normalized to 0.0-1.0
normalized_score = raw_score / 10.0  # = 0.8
```

---

## Weights and Aggregation

### Overall Score Calculation

**Step 1**: Calculate Academic Overall (excludes DI)
```python
academic_dimensions = [
    correctness, grade_alignment, difficulty_alignment,
    language_quality, pedagogical_value, explanation_quality,
    instruction_adherence, format_compliance, query_relevance
]

academic_overall = sum(academic_dimensions) / 9
```

**Step 2**: Extract DI Score
```python
di_overall = di_compliance_score
```

**Step 3**: Weighted Overall Score
```python
overall_score = (academic_overall * 0.75) + (di_overall * 0.25)
```

**Weights Summary**:
- **Academic Dimensions**: 75% weight
- **DI Compliance**: 25% weight

### DI Sub-Metric Weighting
```python
di_overall = (
    general_principles * 0.40 +
    format_alignment * 0.35 +
    grade_language * 0.25
)
```

### Recommendation Logic

**REJECT** if any of:
- Answer letter doesn't map to any option
- Correct answer not present among options
- Impossible pattern detected (e.g., special angles for cos(x) = -1/3)
- Query relevance < 0.4 (VETO POWER)
- Correctness < 0.4
- Format compliance < 0.4
- DI compliance < 0.3

**ACCEPT** if all of:
- Correctness ≥ 0.6
- Format compliance ≥ 0.6
- DI compliance ≥ 0.7
- Query relevance ≥ 0.7
- Overall score ≥ 0.7
- No critical issues detected

**REVISE** otherwise:
- Structure is OK and answer is correct
- But has issues (topic drift, weak explanation, minor format flaws)

---

## Comprehensive Evaluation Output

### Per-Question Output (JSONL)
When running `run_comprehensive_evaluation.py`, each question is written as a separate JSONL record:

```json
{
  "timestamp": "2025-09-23T08:52:09.303812",
  "grade": 5,
  "skill_index": 1,
  "substandard_id": "5.NBT.A.1",
  "lesson_title": "Understanding Place Value",
  "unit_name": "Number and Operations in Base Ten",
  "question_index": 0,
  "request": {
    "grade": 5,
    "count": 1,
    "subject": "mathematics",
    "language": "english",
    "question_type": "mcq",
    "difficulty": "medium"
  },
  "question": {
    "type": "mcq",
    "difficulty": "medium",
    "question": "Which number represents 3 thousands, 5 hundreds, 2 tens, and 7 ones?",
    "options": ["A) 3,257", "B) 3,527", "C) 5,327", "D) 2,537"],
    "answer": "B",
    "explanation": "...",
    "detailed_explanation": {...},
    "voiceover_script": {...}
  },
  "question_evaluation": {
    "question_id": 0,
    "overall_score": 0.85,
    "recommendation": "accept",
    "question_section": {
      "section_score": 0.87,
      "issues": [],
      "strengths": ["Clear question text", "Well-formatted options"],
      "recommendation": "accept"
    },
    "scaffolding_section": {
      "section_score": 0.82,
      "issues": ["Explanation could be more detailed"],
      "strengths": ["Good step-by-step breakdown"],
      "recommendation": "revise"
    },
    "image_section": {
      "section_score": 1.0,
      "issues": [],
      "strengths": ["Image evaluation not yet implemented"],
      "recommendation": "accept"
    }
  },
  "overall_evaluation": {
    "overall_score": 0.85,
    "scores": {
      "correctness": 0.95,
      "grade_alignment": 0.90,
      "difficulty_alignment": 0.80,
      "language_quality": 0.92,
      "pedagogical_value": 0.78,
      "explanation_quality": 0.75,
      "instruction_adherence": 0.88,
      "format_compliance": 0.95,
      "di_compliance": 0.82,
      "query_relevance": 0.90
    },
    "section_scores": {
      "question": {
        "average_score": 0.87,
        "count": 1
      },
      "scaffolding": {
        "average_score": 0.82,
        "count": 1
      },
      "image": {
        "average_score": 1.0,
        "count": 1
      }
    }
  },
  "duration": 3.2,
  "success": true
}
```

### Grade Summary Output
Summary statistics per grade saved to `summary_grade_{grade}.json`:

```json
{
  "grade": 5,
  "timestamp": "2025-09-23T10:15:30.123456",
  "total_skills": 45,
  "total_questions": 2250,
  "successful_skills": 45,
  "durations": {
    "mean": 4.2,
    "median": 3.8,
    "p90": 6.5,
    "p95": 7.8,
    "p99": 9.2,
    "min": 1.5,
    "max": 12.3
  },
  "scores": {
    "mean": 0.82,
    "median": 0.84,
    "min": 0.45,
    "max": 0.96,
    "p25": 0.75,
    "p75": 0.88,
    "std": 0.12
  },
  "dimension_scores": {
    "correctness": {
      "mean": 0.89,
      "median": 0.91,
      "std": 0.08,
      "min": 0.65,
      "max": 0.98
    },
    "grade_alignment": {
      "mean": 0.86,
      "median": 0.88,
      "std": 0.09,
      "min": 0.55,
      "max": 0.95
    },
    "difficulty_alignment": {
      "mean": 0.78,
      "median": 0.80,
      "std": 0.11,
      "min": 0.45,
      "max": 0.92
    },
    "language_quality": {
      "mean": 0.87,
      "median": 0.89,
      "std": 0.07,
      "min": 0.68,
      "max": 0.96
    },
    "pedagogical_value": {
      "mean": 0.81,
      "median": 0.83,
      "std": 0.10,
      "min": 0.58,
      "max": 0.94
    },
    "explanation_quality": {
      "mean": 0.79,
      "median": 0.81,
      "std": 0.11,
      "min": 0.52,
      "max": 0.93
    },
    "instruction_adherence": {
      "mean": 0.84,
      "median": 0.86,
      "std": 0.09,
      "min": 0.60,
      "max": 0.95
    },
    "format_compliance": {
      "mean": 0.90,
      "median": 0.92,
      "std": 0.06,
      "min": 0.72,
      "max": 0.98
    },
    "di_compliance": {
      "mean": 0.75,
      "median": 0.77,
      "std": 0.13,
      "min": 0.40,
      "max": 0.91
    },
    "query_relevance": {
      "mean": 0.88,
      "median": 0.90,
      "std": 0.08,
      "min": 0.65,
      "max": 0.97
    }
  },
  "section_scores": {
    "question": {
      "mean": 0.85,
      "median": 0.87,
      "std": 0.09,
      "count": 2250
    },
    "scaffolding": {
      "mean": 0.78,
      "median": 0.80,
      "std": 0.12,
      "count": 2250
    },
    "image": {
      "mean": 1.0,
      "median": 1.0,
      "std": 0.0,
      "count": 2250
    }
  },
  "quality_distribution": {
    "accept": 1580,
    "revise": 580,
    "reject": 90,
    "total": 2250,
    "accept_rate": 0.702,
    "reject_rate": 0.040
  },
  "error_taxonomy": {
    "mathematical": 145,
    "pedagogical": 312,
    "linguistic": 87,
    "format": 56,
    "query_mismatch": 34,
    "total_errors": 634
  }
}
```

### All Grades Summary
Combined summary saved to `summary_all_grades.json`:

```json
{
  "timestamp": "2025-09-23T12:00:00.000000",
  "model": "dspy",
  "grades_evaluated": [3, 4, 5, 6, 7, 8],
  "grade_summaries": [...],
  "overall": {
    "total_skills": 270,
    "total_questions": 13500,
    "mean_duration": 4.1,
    "mean_score": 0.81
  },
  "aggregated_dimension_scores": {
    "correctness": {
      "mean": 0.88,
      "std": 0.04,
      "min": 0.82,
      "max": 0.92
    },
    "grade_alignment": {
      "mean": 0.85,
      "std": 0.05,
      "min": 0.78,
      "max": 0.91
    },
    "difficulty_alignment": {
      "mean": 0.76,
      "std": 0.06,
      "min": 0.68,
      "max": 0.84
    },
    "language_quality": {
      "mean": 0.86,
      "std": 0.04,
      "min": 0.81,
      "max": 0.92
    },
    "pedagogical_value": {
      "mean": 0.80,
      "std": 0.05,
      "min": 0.73,
      "max": 0.87
    },
    "explanation_quality": {
      "mean": 0.78,
      "std": 0.06,
      "min": 0.70,
      "max": 0.86
    },
    "instruction_adherence": {
      "mean": 0.83,
      "std": 0.04,
      "min": 0.77,
      "max": 0.89
    },
    "format_compliance": {
      "mean": 0.89,
      "std": 0.03,
      "min": 0.85,
      "max": 0.93
    },
    "di_compliance": {
      "mean": 0.74,
      "std": 0.07,
      "min": 0.65,
      "max": 0.83
    },
    "query_relevance": {
      "mean": 0.87,
      "std": 0.04,
      "min": 0.82,
      "max": 0.93
    }
  },
  "aggregated_quality_distribution": {
    "accept": 9480,
    "revise": 3450,
    "reject": 570,
    "accept_rate": 0.702,
    "reject_rate": 0.042
  },
  "aggregated_error_taxonomy": {
    "mathematical": 876,
    "pedagogical": 1854,
    "linguistic": 523,
    "format": 342,
    "query_mismatch": 198,
    "total": 3793
  }
}
```

### Error Taxonomy Classification

The evaluation system automatically classifies errors into five categories based on issue text:

| Error Type | Description | Example Issues |
|------------|-------------|----------------|
| **Mathematical** | Calculation errors, incorrect answers, wrong values | "answer is incorrect", "calculation error in step 2", "wrong option selected" |
| **Pedagogical** | Learning design issues, explanation quality, DI compliance | "explanation too brief", "missing scaffolding steps", "DI format not followed" |
| **Linguistic** | Language quality, grammar, clarity, vocabulary | "grammar error", "unclear wording", "vocabulary too advanced for grade" |
| **Format** | Structural issues, MCQ format problems | "missing option D", "answer letter doesn't map", "incorrect format" |
| **Query Mismatch** | Topic relevance, alignment with request | "off-topic", "doesn't match skill", "query relevance low" |

---

## Baseline Tracking

### Continuous Quality Monitoring
Every evaluation is automatically appended to `baseline_evaluation.json` (last 100 evaluations kept):

```json
{
  "evaluations": [
    {
      "timestamp": "2025-09-23T08:52:09.303812",
      "commit_hash": "01abd7fdcbc8492dd34dd63303b946157250dacc",
      "request_id": "363f22f5-a1c9-491e-9a64-603959b6f8cd",
      "overall_score": 0.80,
      "aggregate_scores": {
        "correctness": 0.96,
        "grade_alignment": 0.94,
        "difficulty_alignment": 0.58,
        "language_quality": 0.91,
        "pedagogical_value": 0.71,
        "explanation_quality": 0.60,
        "instruction_adherence": 0.79,
        "format_compliance": 0.91,
        "di_compliance": 0.65,
        "query_relevance": 0.88,
        "overall": 0.80
      },
      "total_issues": 32,
      "total_strengths": 43,
      "compliance_report": {
        "count_compliance": {
          "requested": 10,
          "generated": 10,
          "compliant": true
        },
        "grade_compliance": {
          "requested": 8,
          "response_grade": 8,
          "compliant": true
        },
        "type_distribution": {"mcq": 9, "fill-in": 1},
        "difficulty_distribution": {"medium": 8, "easy": 2},
        "quality_distribution": {
          "accept": 5,
          "revise": 5,
          "reject": 0
        },
        "di_compliance": {
          "average_score": 0.65,
          "hard_failures": [],
          "breakdown": [...]
        },
        "section_scores": {
          "question": {"average_score": 0.82, "count": 10},
          "scaffolding": {"average_score": 0.68, "count": 10},
          "image": {"average_score": 1.0, "count": 10}
        }
      },
      "recommendations": [
        "✅ Overall quality is appropriate",
        "✏️ Revise 5 question(s) based on suggestions"
      ],
      "question_count": 10,
      "quality_distribution": {
        "accept": 5,
        "revise": 5,
        "reject": 0
      }
    }
  ]
}
```

### Baseline Use Cases
1. **Regression Detection**: Compare current evaluations against historical baselines
2. **A/B Testing**: Track quality changes across different commits/models
3. **Trend Analysis**: Monitor quality improvements over time
4. **Dimension Tracking**: Identify which dimensions improve or degrade

---

## Usage Examples

### 1. Evaluate Single API Response
```python
from src.evaluator.v3 import evaluate_api_response
from src.dto.question_generation import GenerateQuestionsRequest, GenerateQuestionResponse

# Create request and response objects
request = GenerateQuestionsRequest(
    grade=5,
    subject="mathematics",
    instructions="Generate questions about fractions",
    count=3
)

response = GenerateQuestionResponse(
    data=[...],  # List of GeneratedQuestion objects
    request_id="123-456",
    total_questions=3,
    grade=5
)

# Evaluate
evaluation, report = evaluate_api_response(
    request=request,
    response=response,
    generate_report=True,
    update_baseline=True,
    baseline_file="baseline_evaluation.json"
)

print(f"Overall Score: {evaluation.overall_score:.2%}")
print(report)
```

### 2. Run Comprehensive Curriculum Evaluation
```bash
# Evaluate all grades with OpenAI
python -m src.evaluator.run_comprehensive_evaluation \
    --grades 3 4 5 6 7 8 \
    --model openai

# Evaluate single grade with resume capability
python -m src.evaluator.run_comprehensive_evaluation \
    --grades 5 \
    --model dspy \
    --max-skills 10

# Disable resume (overwrite existing)
python -m src.evaluator.run_comprehensive_evaluation \
    --grades 3 \
    --model openai \
    --no-resume
```

### 3. Custom Evaluator with Parallel Workers
```python
from src.evaluator.v3 import ResponseEvaluator

# Create evaluator with custom parallelism
evaluator = ResponseEvaluator(parallel_workers=10)

# Evaluate
evaluation = evaluator.evaluate_response(
    request=request,
    response=response,
    update_baseline=True,
    baseline_file="custom_baseline.json"
)

# Generate report
report = evaluator.generate_report(evaluation)
```

### 4. API Endpoint Integration
```python
# In server.py - automatic evaluation on request
@app.post("/v2/generate_questions")
async def generate_questions_v2(request: GenerateQuestionsRequest):
    # Generate questions
    generated_questions = await orchestrator.execute_complete_pipeline(...)

    # Evaluate if requested
    if request.evaluate:
        from src.evaluator.v3 import ResponseEvaluator

        response_obj = GenerateQuestionResponse(
            data=generated_questions,
            request_id=request_id,
            total_questions=len(generated_questions),
            grade=request.grade
        )

        evaluator = ResponseEvaluator(parallel_workers=20)
        evaluation = evaluator.evaluate_response(request, response_obj)

        # Include evaluation in response
        response_obj.evaluation = evaluation

    return response_obj
```

---

## Recent Enhancements

### Enhanced Comprehensive Evaluation

The comprehensive evaluation script (`src/evaluator/run_comprehensive_evaluation.py`) has been enhanced with advanced analytics:

#### New Features

**1. Dimension-Level Statistics** ✅
- **Per-Grade Tracking**: Mean, median, std, min, max for all 10 dimensions
- **Cross-Grade Aggregation**: Dimension performance across all evaluated grades
- **Variance Analysis**: Identify which dimensions have highest variability

**2. Section-Level Statistics** ✅
- **Question Section**: Independent tracking of question quality metrics
- **Scaffolding Section**: Independent tracking of explanation/DI metrics
- **Image Section**: Placeholder tracking (perfect score until implemented)

**3. Quality Distribution** ✅
- **Accept/Revise/Reject Counts**: Total questions in each category
- **Acceptance Rate**: Percentage of questions meeting quality standards
- **Rejection Rate**: Percentage of questions requiring regeneration

**4. Error Taxonomy Classification** ✅
- **Automatic Classification**: Issues categorized into 5 types
- **Error Type Counts**: Mathematical, Pedagogical, Linguistic, Format, Query Mismatch
- **Total Error Tracking**: Overall error volume across evaluation

#### Example Output

**Console Output:**
```
📊 Summary:
   Duration: mean=4.2s, p95=7.8s, p99=9.2s
   Quality: mean=82.00%, median=84.00%
   Quality Distribution: Accept=1580, Revise=580, Reject=90
   Error Taxonomy: Math=145, Pedagogical=312, Linguistic=87, Format=56, Query=34
   Saved to: data/evaluation_results/dspy/summary_grade_5.json
```

**Combined Summary Output:**
```
✨ Evaluation complete!
   Total skills: 270
   Total questions: 13500
   Mean duration: 4.1s
   Mean quality: 81.00%

   📊 Quality Distribution:
      Accept: 9480 (70.2%)
      Revise: 3450
      Reject: 570 (4.2%)

   🔍 Error Taxonomy (Total: 3793):
      Mathematical: 876
      Pedagogical: 1854
      Linguistic: 523
      Format: 342
      Query Mismatch: 198

   Results saved to: data/evaluation_results/dspy
```

#### Usage

Run with enhanced metrics (automatic):
```bash
python -m src.evaluator.run_comprehensive_evaluation --grades 5 --model dspy
```

The enhanced statistics are automatically included in:
- `summary_grade_{grade}.json` - Per-grade detailed breakdown
- `summary_all_grades.json` - Cross-grade aggregated metrics
- Console output - Real-time progress with key metrics

---

## Recommendations for Future Enhancements

### Priority 1: Critical Enhancements
1. **✅ Implement Image Evaluation**: Replace placeholder with actual image quality assessment
2. **✅ Add Human Validation Loop**: Sample 10% of evaluations for expert review and calibration
3. **✅ Alternative LLM Providers**: Add support for additional evaluation providers

### Priority 2: Data Enrichment
4. **📊 Enhanced Error Taxonomy**: Expand structured classification of issues
5. **📈 Correlation Analysis**: Track inter-metric correlations in baseline analysis
6. **🎯 Subject Expansion**: Add subject-specific evaluation prompts beyond mathematics

### Priority 3: Scenario Coverage
7. **🔄 Multi-Scenario Support**: Extend beyond Question Generation to other educational scenarios:
   - Solution Generation
   - Hint Provision
   - Misconception Analysis
   - Exercise Selection

---

## Conclusion

**Incept Evaluator** provides a robust, scalable framework for automated educational question quality assessment for K-8 mathematics question generation. The three-section evaluation approach, combined with 10 comprehensive dimensions and baseline tracking, enables continuous quality monitoring and improvement.

**Key Strengths**:
- ✅ Comprehensive 10-dimension evaluation
- ✅ Section-based scoring (Question, Scaffolding, Image)
- ✅ Automated LLM-based assessment with override rules
- ✅ Built-in baseline tracking with git commit correlation
- ✅ Clear 0-10 scoring bands with normalization
- ✅ Query relevance veto power for topic alignment

**Future Enhancements**:
- 🔄 Human expert validation loop
- 🔄 Additional LLM provider integration
- 🔄 Complete image evaluation implementation
- 🔄 Enhanced error taxonomy and correlation analysis
- 🔄 Multi-scenario evaluation support

For questions or contributions, refer to the implementation in `src/evaluator/v3.py` and the comprehensive evaluation runner in `src/evaluator/run_comprehensive_evaluation.py`.

---

## Quick Reference

### File Structure
```
incept-multilingual-generation/
├── src/
│   └── evaluator/
│       ├── v3.py                              # Core evaluator implementation
│       └── run_comprehensive_evaluation.py     # Curriculum-wide evaluation script
├── baseline_evaluation.json                    # Rolling baseline (last 100 evaluations)
├── data/
│   └── evaluation_results/
│       └── {model}/                            # Model-specific results (openai, dspy, etc.)
│           ├── evaluation_grade_{grade}.jsonl  # Per-question detailed results
│           ├── summary_grade_{grade}.json      # Per-grade statistics
│           └── summary_all_grades.json         # Cross-grade aggregated metrics
└── incept_evaluator_documentation.md          # This file
```

### Key Metrics Summary

| Metric Category | Metrics | Purpose |
|----------------|---------|---------|
| **10 Evaluation Dimensions** | Correctness, Grade Alignment, Difficulty Alignment, Language Quality, Pedagogical Value, Explanation Quality, Instruction Adherence, Format Compliance, DI Compliance, Query Relevance | Comprehensive quality assessment |
| **3 Section Scores** | Question, Scaffolding, Image | Independent section evaluation |
| **Quality Distribution** | Accept, Revise, Reject counts and rates | Production readiness |
| **Error Taxonomy** | Mathematical, Pedagogical, Linguistic, Format, Query Mismatch | Root cause analysis |
| **Performance Metrics** | Duration (mean, p95, p99), Success rates | System performance |

### Scoring Thresholds

| Recommendation | Criteria |
|---------------|----------|
| **ACCEPT** | Correctness ≥ 0.6, Format ≥ 0.6, DI ≥ 0.7, Query Relevance ≥ 0.7, Overall ≥ 0.7, No critical issues |
| **REJECT** | Answer mapping error, Correct answer missing, Impossible pattern, Query Relevance < 0.4, Correctness < 0.4, Format < 0.4, DI < 0.3 |
| **REVISE** | All other cases |

### Overall Score Calculation
```
Academic Overall = Average of 9 dimensions (excluding DI)
DI Overall = DI Compliance score
Overall Score = (Academic Overall × 0.75) + (DI Overall × 0.25)
```

### DI Score Calculation
```
DI Overall = (General Principles × 0.40) + (Format Alignment × 0.35) + (Grade Language × 0.25)
```

---

## Support and Troubleshooting

### Common Issues

**Issue**: "LLM did NOT return section_evaluations"
- **Cause**: LLM response missing required section breakdown
- **Solution**: Check LLM provider configuration, verify JSON schema compliance

**Issue**: High rejection rate (>10%)
- **Cause**: Possible systematic issues in question generation or evaluation criteria
- **Solution**: Review rejected questions, check error taxonomy for patterns

**Issue**: Low DI compliance scores (<0.5)
- **Cause**: Missing or incomplete scaffolding, non-DI-aligned explanations
- **Solution**: Review DI principles, enhance scaffolding generation (Module 5)

### Performance Optimization

- **Parallel Workers**: Default 6, optimal range 3-6, adjust based on workload and API rate limits
- **Concurrent Requests**: Set to 1 in comprehensive evaluation to avoid database lock issues with DSPy
- **Caching**: LLM evaluation responses not cached (ensures fresh evaluation)

### Contact

For issues, feature requests, or contributions:
- Implementation: `src/evaluator/v3.py`
- Evaluation Script: `src/evaluator/run_comprehensive_evaluation.py`
- Documentation: This file (`incept_evaluator_documentation.md`)
