from __future__ import annotations

from typing import Callable, List, Dict, Any, Optional
import logging
import json
from openai import OpenAI
import base64
from pydantic import BaseModel
from src.llms import produce_structured_response_openai
import concurrent.futures
import traceback

logger = logging.getLogger(__name__)

class ImageRanking(BaseModel):
    """Single image evaluation"""
    rank: int
    image_index: int
    score: int
    strengths: List[str]
    weaknesses: List[str]
    changes_required: List[str]  # Concrete changes needed for regeneration
    recommendation: str  # "ACCEPT" or "REJECT"


class QualityCheckResult(BaseModel):
    """Quality check result for multiple images"""
    rankings: List[ImageRanking]
    best_image_index: int
    overall_feedback: str


class ImageQualityChecker:
    """
    DI (Direct Instruction) rubric-based checker.
    - Keeps your existing interface and return types.
    - Computes a DI-weighted score and returns it as ImageRanking.score.
    - Applies DI "gates" (hard fails). If any gate trips, recommendation = REJECT.
    - Fills strengths/weaknesses/changes_required with actionable, regeneration-ready feedback.
    """

    def __init__(self):
        self.client = OpenAI(timeout=120.0)

    # -------------------------
    # Internal: DI rubric config
    # -------------------------
    _criteria = [
        # (name, weight)
        ("Task fidelity (givens-only)", 25),
        ("Quantitative accuracy", 15),
        ("Canonical representation", 15),
        ("Clarity & salience", 10),
        ("Consistency", 10),
        ("Age fit", 10),
        ("Locale/units", 5),
        ("Accessibility", 10),
    ]

    _gates = ["answer_leakage", "representation_mismatch", "quant_count_mismatch", "label_invention", "descriptive_text"]

    def _batch_system_prompt(self) -> str:
        # DI rubric with gates; instruct the model to compute weighted total but
        # return ONLY your existing schema fields (no extra keys), to preserve compatibility.
        return """You are evaluating educational images using a Direct Instruction (DI) rubric.

DI GATES (hard fails — if any is true, the image must be REJECTED even if visually appealing):
- answer_leakage: The image reveals totals/solutions/derived values that students should compute (e.g., sum, perimeter, area, solved x).
- representation_mismatch: The visual does not use the canonical DI representation for the concept:
  • Multiplication → rectangular array (rows×cols) or equal groups
  • Division → equal groups/partitioning
  • Fractions (concept/compare/equivalence) → fraction bars or area models (NOT pie by default)
  • Ratios/proportions → tape diagram or ratio table (NOT pie)
  • Place value → base-ten blocks (units/rods/flats)
  • Number lines only when explicitly required (correct endpoints & intervals)
- quant_count_mismatch: Counts, ticks, or scale do not match givens (e.g., 24 requested but 23 shown; number-line intervals don't divide range).
- label_invention: Labels/categories/units created that the prompt did not give (e.g., invented axis categories/units).
- descriptive_text: Inappropriate text usage - descriptive text/labels in real-world/counting images (except measurements like "5cm", "90°") OR missing essential labels in charts/Venn diagrams.

RUBRIC CRITERIA (weights sum to 100):
1) Task fidelity (givens-only) = 25
2) Quantitative accuracy = 15
3) Canonical representation = 15
4) Clarity & salience = 10
5) Consistency = 10
6) Age fit = 10
7) Locale/units = 5
8) Accessibility = 10

SCORING & OUTPUT CONTRACT:
- Score each criterion 0–100 and compute the weighted total (0–100).
- Only recommend ACCEPT if total ≥ 70 AND all DI gates are false.
- You MUST return objects that match the caller's expected schema EXACTLY:
  rankings[].{rank, image_index, score, strengths[], weaknesses[], changes_required[], recommendation}
  and top-level {best_image_index, overall_feedback}.
- Do NOT include any extra keys (e.g., no 'rubric' object in the output). Instead, summarize key rubric comments under strengths/weaknesses and the overall_feedback.
- For REJECTED images, 'changes_required' MUST be concrete, one-line edits that can be applied directly in a regeneration prompt (e.g., 'Render exactly 24 apples arranged as 4 rows × 6 columns; remove totals.').
- SPECIAL RULES BY IMAGE TYPE:
  • Real-world/counting images: NO descriptive text, labels, or words (like 'apples', 'books', 'total'). Numbers/measurements OK when essential (e.g., "5cm", "90°").
  • Charts (bar/line/pie): MUST have series labels, axis labels, legend - these are essential for functionality. NO answer-revealing values.
  • Venn diagrams: MUST have group/set labels (e.g., "Math", "Science") but NO numbers in regions; overlap must reflect intersections.
  • SVG arithmetic: NO descriptive text (like 'apples', 'total'); numbers only for operators/quantities. Never show the final total.
"""

    def _batch_user_prompt(
        self,
        image_urls: List[str],
        expected_description: str,
        educational_context: str,
        age_group: str,
        gate_hints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        url_list = "\n".join([f"Image {i+1}: {url}" for i, url in enumerate(image_urls)])
        hints = ", ".join(gate_hints or []) if gate_hints else "none"
        text = f"""Evaluate these {len(image_urls)} images against the expected description using the DI rubric.

Educational Context: {educational_context}
Target Age Group: {age_group}

Expected Description:
{expected_description}

Images to evaluate:
{url_list}

Preflight gate hints: {hints}

INSTRUCTIONS:
- Rank best to worst.
- For each image, compute the DI weighted total (0–100) and place it in 'score'.
- If any DI gate is true, set recommendation to REJECT (even if score is high).
- Put brief rubric-aligned notes in strengths/weaknesses.
- In changes_required, give concrete, one-line edits (no narratives).
- overall_feedback: 1–2 line summary with the reason the winner was chosen and 1–2 universal fixes for the set."""
        # Vision inputs: each image as "image_url"
        content = [{"type": "text", "text": text}]
        for url in image_urls:
            if url.startswith("http"):
                content.append({"type": "image_url", "image_url": {"url": url}})
            else:
                try:
                    with open(url, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")
                    content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
                except Exception as e:
                    logger.error(f"Failed to read local image {url}: {e}")
        return {"role": "user", "content": content}

    # -------------------------
    # Public API (unchanged)
    # -------------------------
    def check_image_quality_batch(
        self,
        image_urls: List[str],
        expected_description: str,
        educational_context: str = "",
        age_group: str = ""
    ) -> QualityCheckResult:
        """
        Evaluates multiple images in parallel using individual checks,
        then compares scores and assigns rankings.
        """
        try:
            if not image_urls:
                return QualityCheckResult(
                    rankings=[],
                    best_image_index=0,
                    overall_feedback="Error: No images provided"
                )

            logger.info(f"[DI QA] Evaluating {len(image_urls)} image(s) in parallel")

            # Run individual checks in parallel for all images
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(image_urls)) as executor:
                # Submit all tasks
                futures = []
                for i, image_url in enumerate(image_urls):
                    logger.info(f"Submitting QA task for image {i+1}: {image_url}")
                    future = executor.submit(
                        self.check_single_image,
                        image_url,
                        expected_description,
                        educational_context,
                        age_group
                    )
                    futures.append((i, future))
                
                # Collect results
                rankings = []
                for i, future in futures:
                    try:
                        result = future.result(timeout=90)  # 90 second timeout per image
                        # Update the image_index to match the input order
                        result.image_index = i
                        rankings.append(result)
                        logger.info(f"Image {i} evaluated - score: {result.score}, recommendation: {result.recommendation}")
                    except Exception as e:
                        error_details = traceback.format_exc()
                        logger.error(f"[DI QA] Failed to evaluate image {i}: {repr(e)}")
                        logger.error(f"[DI QA] Full traceback for image {i}:\n{error_details}")
                        rankings.append(ImageRanking(
                            rank=999,  # Will be updated after sorting
                            image_index=i,
                            score=0,
                            strengths=[],
                            weaknesses=[f"Evaluation failed: {repr(e)}"],
                            changes_required=[f"Technical error: {repr(e)}"],
                            recommendation="REJECT"
                        ))
            
            # Sort by score (descending) and assign final ranks
            rankings.sort(key=lambda r: r.score, reverse=True)
            for rank_idx, ranking in enumerate(rankings):
                ranking.rank = rank_idx + 1
            
            # Determine best image
            best_index = rankings[0].image_index if rankings else 0
            best_score = rankings[0].score if rankings else 0
            
            # Create overall feedback
            if rankings:
                accepted = [r for r in rankings if r.recommendation == "ACCEPT"]
                rejected = [r for r in rankings if r.recommendation == "REJECT"]
                overall = f"Evaluated {len(rankings)} images in parallel. "
                overall += f"Best score: {best_score}. "
                overall += f"{len(accepted)} accepted, {len(rejected)} rejected."
            else:
                overall = "No images could be evaluated successfully."

            return QualityCheckResult(
                rankings=rankings,
                best_image_index=best_index,
                overall_feedback=overall
            )

        except Exception as e:
            logger.error(f"[DI QA] Error in batch evaluation: {e}")
            return QualityCheckResult(
                rankings=[],
                best_image_index=0,
                overall_feedback=f"Error checking images: {str(e)}"
            )

    def check_single_image(
        self,
        image_url: str,
        expected_description: str,
        educational_context: str = "",
        age_group: str = ""
    ) -> ImageRanking:
        """
        Drop-in: same signature & return type.
        Uses DI gates to decide ACCEPT/REJECT but maps into your existing JSON schema.
        """
        try:
            # Prepare image
            if image_url.startswith("http"):
                image_content = {"type": "image_url", "image_url": {"url": image_url}}
            else:
                with open(image_url, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                image_content = {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}

            system_prompt = """Evaluate this educational image using a Direct Instruction (DI) rubric.

DI GATES (hard fails — if any is true, you must REJECT):
- answer_leakage (reveals totals/solutions/derived values)
- representation_mismatch (non-canonical visual for the concept)
- quant_count_mismatch (counts/ticks/scale wrong)
- label_invention (labels/units/categories not given)
- descriptive_text (inappropriate text usage: question text in the images, OR missing essential labels in charts/Venn)
- overlap (objects overlap in the image, unless explicitly required - eg. venn diagrams or intersecting lines)
_ insufficient_spacing (objects are stuck together when they shouldn't be)

CRITERIA & WEIGHTS (sum to 100):
Task fidelity (givens-only)=25; 
Quantitative accuracy=15; 
Canonical representation=15;
Clarity & salience=10; 
Consistency=10; 
Age fit=10; 
Locale/units=5; 
Accessibility=10.

SCORING:
- Compute a weighted total (0–100).
- PASS (map to ACCEPT) only if total ≥ 70 and no DI gates are true.
- Otherwise FAIL (map to REJECT).

IMPORTANT OUTPUT:
Provide your evaluation in structured format with:
- evaluation: "PASS" or "FAIL" 
- score: weighted total (0-100)
- feedback: 2-4 sentence summary of rubric observations
- issues: list of atomic, actionable edits for regeneration if FAIL
- strengths: list of positive observations about the image"""

            user_text = f"""Educational Context: {educational_context}
Target Age Group: {age_group}

Expected Description:
{expected_description}

Evaluate the single image against the DI rubric, compute the weighted total, and decide ACCEPT/REJECT accordingly.
If REJECT, list all issues as atomic edits (no narratives)."""

            # Use structured output with produce_structured_response_openai
            class SingleImageResult(BaseModel):
                evaluation: str  # "PASS" or "FAIL"
                score: float
                feedback: str
                issues: List[str]
                strengths: List[str]

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [{"type": "text", "text": user_text}, image_content]},
            ]

            result = produce_structured_response_openai(
                messages=messages,
                structure_model=SingleImageResult,
                model="gpt-5",
                instructions=None,
                temperature=1.0,
                max_output_tokens=None
            )
            
            evaluation = result.evaluation
            total_score = int(round(float(result.score)))

            return ImageRanking(
                rank=1,
                image_index=0,
                score=total_score,
                recommendation="ACCEPT" if evaluation == "PASS" else "REJECT",
                strengths=result.strengths,
                weaknesses=result.issues,
                changes_required=result.issues,
            )

        except Exception as e:
            full_error = traceback.format_exc()
            logger.error(f"[DI QA] Error in single-image evaluation: {repr(e)}")
            logger.error(f"[DI QA] Exception type: {type(e).__name__}")
            logger.error(f"[DI QA] Exception args: {e.args}")
            logger.error(f"[DI QA] Full traceback:\n{full_error}")
            logger.error(f"[DI QA] Image URL: {image_url}")
            logger.error(f"[DI QA] Expected description: {expected_description[:200]}...")
            logger.error(f"[DI QA] Educational context: {educational_context}")
            logger.error(f"[DI QA] Age group: {age_group}")
            return ImageRanking(
                rank=1,
                image_index=0,
                score=0,
                recommendation="REJECT",
                strengths=[],
                weaknesses=[f"Error during evaluation: {repr(e)} (type: {type(e).__name__})"],
                changes_required=[f"Technical error occurred: {repr(e)} (type: {type(e).__name__})"]
            )
