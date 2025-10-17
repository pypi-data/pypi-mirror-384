import json
import logging
import os
from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Optional: allow overriding the JSON path via ENV var
_SPIKY_CONFIG_PATH = os.environ.get(
    "SPIKY_CONFIG_PATH", "spiky_points_of_view.json")
_SPIKY_CACHE = {"data": None, "mtime": None, "path": _SPIKY_CONFIG_PATH}


def _load_spiky_points(path: str = _SPIKY_CONFIG_PATH) -> Dict[str, Any]:
    """
    Load spiky points JSON with a tiny mtime cache so dynamic edits are picked up.
    If the JSON file changes on disk, it's reloaded automatically.
    """
    try:
        stat = os.stat(path)
        if (
            _SPIKY_CACHE["data"] is not None
            and _SPIKY_CACHE["mtime"] == stat.st_mtime
            and _SPIKY_CACHE["path"] == path
        ):
            return _SPIKY_CACHE["data"]

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        _SPIKY_CACHE.update(
            {"data": data, "mtime": stat.st_mtime, "path": path})
        return data

    except (FileNotFoundError, json.JSONDecodeError):
        # Fail safely with empty structure if file is missing or malformed.
        return {}
    except Exception:
        return {}


def _normalize_subject(subject: str) -> str:
    """
    Normalize common subject names to match the JSON keys
    (e.g., 'social studies' -> 'social_studies').
    """
    raw = subject.strip().lower()
    alias = {
        "social studies": "social_studies",
        "language arts": "language_arts",
        "lang arts": "language_arts",
        "science": "science",
        "mathematics": "mathematics",
        "math": "mathematics",
        "history": "history",
    }
    return alias.get(raw, raw.replace("-", " ").replace(" ", "_"))


def _select_spiky_points(
    spiky_config: Dict[str, Any],
    subject: str,
    max_high: int = 3,
    max_medium: int = 2,
) -> List[Dict[str, Any]]:
    """
    Pick context-relevant spiky points (favor 'high' priority).
    Includes 'all_subjects' and subject-matching contexts.
    """
    subject_key = _normalize_subject(subject)
    points = spiky_config.get(
        "uae_educational_priorities", {}).get("spiky_points", [])
    relevant = []
    for p in points:
        ctx = (p.get("context") or "").lower()
        if ctx == "all_subjects":
            relevant.append(p)
        else:
            # e.g. "social_studies,history,civics"
            split = [c.strip().lower() for c in ctx.split(",")]
            if subject_key in split:
                relevant.append(p)

    high = [p for p in relevant if (p.get("priority") or "").lower() == "high"]
    medium = [p for p in relevant if (
        p.get("priority") or "").lower() == "medium"]

    selected = high[:max_high] + medium[:max_medium]
    # Keep only the bits the prompt needs (less token bloat)
    trimmed = [
        {
            "id": p.get("id"),
            "directive": p.get("directive"),
            "examples": p.get("examples", []),
            "priority": p.get("priority", ""),
        }
        for p in selected
    ]
    return trimmed


def _subject_contexts(spiky_config: Dict[str, Any], subject: str) -> List[str]:
    ctx = spiky_config.get("subject_specific_contexts", {})
    return ctx.get(_normalize_subject(subject), [])


def _adaptation_guidelines(spiky_config: Dict[str, Any]) -> Dict[str, str]:
    return spiky_config.get("adaptation_guidelines", {})



class SolutionStep(BaseModel):
    """Individual step in detailed solution."""
    title: str
    content: str
    image: Optional[str] = None
    image_alt_text: Optional[str] = None


class AcademicInsight(BaseModel):
    """Insight for specific student answer."""
    answer: str
    insight: str


class VoiceoverStep(BaseModel):
    """Voiceover script for a specific step."""
    step_number: int
    script: str


class VoiceoverScript(BaseModel):
    """Complete voiceover scripts."""
    question_script: str
    answer_choice_scripts: Optional[List[str]] = None
    # explanation_step_scripts: List[VoiceoverStep]


class DetailedExplanation(BaseModel):
    """Detailed step-by-step explanation."""
    steps: List[SolutionStep]
    personalized_academic_insights: List[AcademicInsight]


class UsedDIFormat(BaseModel):
    """A DI format that was used in scaffolding generation"""
    title: Optional[str] = Field(default=None, description="Title of the format")
    skill_name: Optional[str] = Field(default=None, description="Name of the DI skill")  
    format_number: Optional[str] = Field(default=None, description="Format number identifier")

class ScaffoldingResponse(BaseModel):
    """Structured response from GPT-5 for scaffolding."""
    detailed_explanation: DetailedExplanation = Field(
        default_factory=lambda: DetailedExplanation(steps=[], personalized_academic_insights=[]))
    voiceover_script: VoiceoverScript = Field(
        default_factory=lambda: VoiceoverScript(
            question_script="", explanation_step_scripts=[]))
    explanation: Optional[str] = None  # New field for explanation text
    di_formats_used: Optional[List[UsedDIFormat]] = Field(
        default=None,
        description="Exact DI format sections that were used to generate the scaffolding steps"
    )


class BatchScaffoldingResponse(BaseModel):
    """Batch scaffolding response for multiple questions (10 at a time)."""
    scaffoldings: List[ScaffoldingResponse] = Field(
        description="List of scaffolding responses, one per question in same order as input"
    )


@dataclass
class ScaffoldedSolution:
    """Complete scaffolded solution with step-by-step guidance."""
    question: str
    answer: str
    explanation: str
    detailed_explanation: DetailedExplanation
    voiceover_script: VoiceoverScript
    generation_status: str
    grade: int = 8
    subject: str = "general"
    language: str = "english"
    di_formats_used: Optional[List[Dict[str, Any]]] = None
