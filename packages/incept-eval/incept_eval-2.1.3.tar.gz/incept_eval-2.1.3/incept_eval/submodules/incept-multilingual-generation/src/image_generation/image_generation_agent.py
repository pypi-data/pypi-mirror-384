"""
LangGraph-based Image Generation Agent
Orchestrates image generation using various tools based on question type
"""

import logging
import asyncio
import os
import json
import math
import traceback
import re
from typing import List, Dict, Optional, Any, Literal, TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# Import all image generation tools
from src.image_generation.gemini_image_gen import generate_image_gemini, edit_image_with_gemini
from src.image_generation.svg_image_gen import generate_svg_image
from src.image_generation.image_quality_checker_di import ImageQualityChecker
from src.image_generation.types import Shapes2DData, Shape3DData

# Import chart/visualization tools
from src.tools.image_generation.charts.simple_bar import generate_simple_bar
from src.tools.image_generation.charts.simple_box import generate_simple_box
from src.tools.image_generation.charts.simple_heatmap import generate_simple_heatmap
from src.tools.image_generation.charts.simple_histogram import generate_simple_histogram
from src.tools.image_generation.charts.simple_line import generate_simple_line
from src.tools.image_generation.charts.simple_pie import generate_simple_pie
from src.tools.image_generation.charts.simple_scatter import generate_simple_scatter

# Import educational visualization tools
from src.tools.image_generation.educational.clock_gen import generate_clock_image
from src.tools.image_generation.educational.ruler_gen import generate_ruler_image
from src.tools.image_generation.educational.number_line import generate_number_line
from src.tools.image_generation.educational.intersecting_lines_gen import generate_intersecting_lines_image
from src.tools.image_generation.educational.latex_equation_gen import generate_latex_equation_image
from src.tools.image_generation.educational.shape_2d_gen import generate_2d_shape_image
from src.tools.image_generation.educational.shape_3d_gen import generate_3d_shape_image
from src.tools.image_generation.educational.venn_diagram_gen import generate_venn_diagram_image
from src.tools.image_generation.charts.venn_diagram_simple import generate_venn_diagram_simple

# Import utility tools
from src.tools.image_generation.educational.html_animation_gen import generate_animation
from src.llms import llm_gpt5, produce_structured_response_openai
from pydantic import BaseModel
from typing import Dict, List, Optional

from src.image_generation.image_quality_checker_di import QualityCheckResult, ImageRanking

logger = logging.getLogger(__name__)


class ImageGenerationState(TypedDict):
    """State for the image generation graph"""
    question: str
    question_type: str
    grade: int
    subject: str
    image_type: Optional[str]
    image_prompt: Optional[str]
    generated_images: Optional[Dict[str, Any]]
    quality_check_results: Optional[Dict[str, Any]]
    final_image_url: Optional[str]
    retry_count: int
    max_retries: int
    error: Optional[str]


class ImageGenerationAgent:
    """Agent that orchestrates image generation using various tools"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-5", temperature=0)
        self.quality_checker = ImageQualityChecker()
        self.graph = self._build_graph()
        logger.info("Image Generation Agent initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(ImageGenerationState)
        
        # Add nodes
        workflow.add_node("analyze_question", self.analyze_question)
        workflow.add_node("generate_prompt", self.generate_image_prompt)
        workflow.add_node("generate_image", self.generate_image)
        workflow.add_node("quality_check", self.quality_check)
        workflow.add_node("select_best_image", self.select_best_image)
        workflow.add_node("handle_error", self.handle_error)
        
        # Add edges
        workflow.set_entry_point("analyze_question")
        workflow.add_edge("analyze_question", "generate_prompt")
        workflow.add_edge("generate_prompt", "generate_image")
        workflow.add_edge("generate_image", "quality_check")
        
        # Conditional edges
        workflow.add_conditional_edges(
            "quality_check",
            self.should_retry,
            {
                "retry": "generate_prompt",
                "success": "select_best_image",
                "gemini_fallback": "gemini_fallback_generation",
                "error": "handle_error"
            }
        )
        
        workflow.add_node("gemini_fallback_generation", self.gemini_fallback_generation)
        
        workflow.add_edge("gemini_fallback_generation", "quality_check")
        workflow.add_edge("select_best_image", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    async def analyze_question(self, state: ImageGenerationState) -> ImageGenerationState:
        """Analyze the question to determine appropriate image type"""
        logger.info(f"Analyzing question: {state['question'][:100]}...")
        
        analysis_prompt = f"""
        You are selecting the most appropriate image generation tool for an educational question,
        following Direct Instruction (DI) principles and grade sequencing.

        INPUT
        Question: {state['question']}
        Grade: {state['grade']}
        Subject: {state['subject']}

        TOOLS (exact names; choose exactly one)
        1. "counting_svg" — counting and basic + − × ÷ with discrete objects (exact quantities)
        2. "real_world" — real objects/scenes (avoid clutter; no extra props)
        3. "chart_bar" — categorical comparisons; safe default for simple data displays
        4. "chart_pie" — ONLY for parts-of-a-whole/composition (values sum to a whole)
        5. "chart_line" — time-series trends (NOT line plots on a number line)
        6. "chart_scatter" — correlation (secondary/late middle grades)
        7. "chart_box" — box-and-whisker (secondary/late middle grades)
        8. "chart_histogram" — frequency distribution (secondary/late middle grades)
        9. "chart_heatmap" — advanced; ONLY if explicitly requested in upper grades
        10. "chart_venn" — set relationships (labels only; no numbers inside regions)
        11. "geometric_2d_shape" — 2D shapes with ONLY the given measures
        12. "geometric_3d_shape" — 3D solids with ONLY the given dimensions
        13. "geometric_intersecting_lines" — parallel/perpendicular/transversal/coordinate geometry with ONLY given measures
        14. "mathematical_equation" — equations/expressions; show setup only (no steps/answers)
        15. "mathematical_number_line" — explicit position/movement; DI line plot/dot plot
        16. "mathematical_ruler" — length/measurement tasks
        17. "mathematical_clock" — time-reading tasks
        18. "animation" — multi-step motion (use sparingly)

        DI GRADE BANDS (gating)
        - K–2: allow counting_svg, real_world, mathematical_equation, mathematical_number_line, mathematical_ruler,
                mathematical_clock, geometric_2d_shape, chart_bar
        - 3–5: all K–2 plus chart_pie (ONLY composition), chart_venn
        - 6–8: all 3–5 plus geometric_3d_shape, geometric_intersecting_lines, chart_line, chart_scatter, chart_box, chart_histogram
        - 9–12: all tools allowed; chart_heatmap only if explicitly requested

        SELECTION RULES (apply in order; pick the first rule that fits)
        1) If time phrases (e.g., "o'clock", "quarter past") → "mathematical_clock".
        2) If measurement of length/units (cm/in/mm) without angles → "mathematical_ruler".
        3) If "number line", "line plot", or "dot plot" → "mathematical_number_line".
        4) If parallel/perpendicular/transversal, coordinate geometry  → "geometric_intersecting_lines".
        5) If named 2D shape (triangle, rectangle, circle, etc.) → "geometric_2d_shape".
        6) If named 3D solid (cube, cylinder, cone, etc.) → "geometric_3d_shape".
        7) If + − × ÷ with discrete quantities (and small integers) → "counting_svg"
        (× → arrays; ÷ → equal groups; lay out left → operator → right).
        8) If fractions **arithmetic/solve/compare** and no specific visual is requested → "mathematical_equation"
        (do NOT choose pie for fraction arithmetic).
        9) If equation/variable/solve/simplify → "mathematical_equation".
        10) If "Venn" mentioned → "chart_venn" (labels only; no numbers inside).
        11) If explicit "bar graph" → "chart_bar".
        12) If explicit "pie chart" AND the question is about composition/parts-of-a-whole → "chart_pie".
        13) If explicit "line graph"/"trend over time" → "chart_line".
        14) If explicit "scatter"/"correlation" → "chart_scatter".
        15) If explicit "box plot" → "chart_box".
        16) If explicit "histogram" → "chart_histogram".
        17) Otherwise: if mathematics with numerals but unclear visual → "mathematical_equation"; else "real_world".

        DI GUARDRAILS (must obey)
        - Never reveal answers or derived values; show ONLY given information.
        - Pie charts ONLY for composition (parts-of-whole). If not clearly composition, prefer "chart_bar".
        - "Line plot" (dots/x’s over a scale) is NOT "chart_line"; select "mathematical_number_line".
        - "counting_svg": exact object counts; uniform icons; NO text labels (numbers allowed only as operators/quantities).
        - "chart_venn": set labels only; NO numbers inside regions.
        - Geometry/angles: draw ONLY measures stated in the problem; no solved values.
        - If a tool is disallowed by the grade band, choose the simplest DI-appropriate allowed alternative
        (e.g., scatter/box/hist → chart_bar; 3D/intersecting_lines → geometric_2d_shape; otherwise mathematical_equation).

        OUTPUT (JSON only; no prose, no markdown)
        {{
        "tool": "<one of the tool names above>",
        "reasoning": "<one short line explaining the choice>"
        }}

        If ambiguous after applying the rules, choose "mathematical_equation" and say "default to setup only".
        """
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])
            analysis = json.loads(response.content)
            
            state["image_type"] = analysis["tool"]
            
            logger.info(f"Selected tool: {state['image_type']} - {analysis.get('reasoning', '')}")
            
        except Exception as e:
            logger.error(f"Error analyzing question: {e}")
            state["image_type"] = "real_world"  # Default fallback
        
        return state
    
    async def generate_image_prompt(self, state: ImageGenerationState) -> ImageGenerationState:
        """Generate appropriate prompt based on image type"""
        logger.info(f"Generating prompt for image type: {state['image_type']}")
        
        # Use specialized prompt generation based on type
        if state["image_type"] == "counting_svg":
            prompt = await self._generate_counting_svg_prompt(state)
        elif state["image_type"] == "real_world":
            prompt = await self._generate_real_world_prompt(state)
        elif "chart" in state["image_type"]:
            prompt = await self._generate_chart_prompt(state)
        elif "geometric" in state["image_type"]:
            prompt = await self._generate_geometric_prompt(state)
        elif "mathematical" in state["image_type"]:
            prompt = await self._generate_mathematical_prompt(state)
        elif state["image_type"] == "diagram":
            prompt = await self._generate_diagram_prompt(state)
        elif state["image_type"] == "animation":
            prompt = await self._generate_animation_prompt(state)
        else:
            prompt = await self._generate_generic_prompt(state)
        
        state["image_prompt"] = prompt
        logger.info(f"Generated prompt: {prompt[:100]}...")
        
        return state
    
    async def generate_image(self, state: ImageGenerationState) -> ImageGenerationState:
        """Generate image using appropriate tool based on type"""
        logger.info(f"Generating image of type: {state['image_type']}")
        
        try:
            image_type = state["image_type"]
            prompt = state["image_prompt"]
            
            # Route to appropriate generation method
            if image_type == "counting_svg":
                try:
                    # Check if this is a retry with feedback
                    qa_feedback = self._extract_qa_feedback(state)
                    if state.get("retry_count", 0) > 0 and qa_feedback and qa_feedback != "No specific feedback available":
                        # Get the original SVG code if available
                        original_svg = self._get_original_svg_code(state)
                        logger.info(f"SVG retry with feedback: {qa_feedback[:100]}...")
                        result = await self._run_sync_tool(generate_svg_image, prompt, qa_feedback, original_svg)
                    else:
                        # Initial generation
                        logger.info(f"Initial SVG generation with prompt: {prompt[:100]}...")
                        result = await self._run_sync_tool(generate_svg_image, prompt)
                    
                    if result:
                        
                        svg_result = json.loads(result)
                        # Handle new structured format
                        if "images" in svg_result:
                            state["generated_images"] = {"svg": {"images": svg_result["images"]}}
                            logger.info(f"SVG generation successful: {len(svg_result['images'])} images")
                        else:
                            # Legacy format fallback
                            state["generated_images"] = {"svg": {"image_urls": svg_result.get("image_paths", [])}}
                            logger.info(f"SVG generation successful: {len(svg_result.get('image_paths', []))} images")
                    else:
                        logger.error("SVG generation returned None")
                        state["generated_images"] = {}
                except Exception as e:
                    logger.error(f"SVG generation failed: {e}")
                    state["generated_images"] = {}
                    state["error"] = f"SVG generation failed: {str(e)}"
                    
            elif image_type == "real_world":
                # Generate with multiple methods in parallel
                results = await self._generate_multi_method_images(prompt)
                state["generated_images"] = results
                
            elif image_type == "chart_bar":
                result = await self._generate_bar_chart(state)
                if result:
                    state["generated_images"] = {"chart": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "chart_line":
                result = await self._generate_line_chart(state)
                if result:
                    state["generated_images"] = {"chart": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "chart_pie":
                result = await self._generate_pie_chart(state)
                if result:
                    state["generated_images"] = {"chart": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "chart_scatter":
                result = await self._generate_scatter_chart(state)
                if result:
                    state["generated_images"] = {"chart": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "chart_box":
                result = await self._generate_box_chart(state)
                if result:
                    state["generated_images"] = {"chart": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "chart_heatmap":
                result = await self._generate_heatmap_chart(state)
                if result:
                    state["generated_images"] = {"chart": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "chart_histogram":
                result = await self._generate_histogram_chart(state)
                if result:
                    state["generated_images"] = {"chart": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                    
            elif image_type == "chart_venn":
                result = await self._generate_venn_simple(state)
                if result:
                    state["generated_images"] = {"chart": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "geometric_2d_shape":
                result = await self._generate_2d_shapes(state)
                if result:
                    state["generated_images"] = {"geometric": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "geometric_3d_shape":
                result = await self._generate_3d_shapes(state)
                if result:
                    state["generated_images"] = {"geometric": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "geometric_intersecting_lines":
                result = await self._generate_intersecting_lines(state)
                if result:
                    state["generated_images"] = {"geometric": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "mathematical_equation":
                result = await self._generate_equation_image(state)
                if result:
                    state["generated_images"] = {"mathematical": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "mathematical_number_line":
                result = await self._generate_number_line_image(state)
                if result:
                    state["generated_images"] = {"mathematical": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "mathematical_ruler":
                result = await self._generate_ruler_image(state)
                if result:
                    state["generated_images"] = {"mathematical": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "mathematical_clock":
                result = await self._generate_clock_image(state)
                if result:
                    state["generated_images"] = {"mathematical": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            elif image_type == "diagram":
                # SVG disabled due to Cairo dependency - use multi-method generation instead
                results = await self._generate_multi_method_images(prompt)
                state["generated_images"] = results
                
            elif image_type == "animation":
                result = await self._generate_animation_image(state)
                if result:
                    state["generated_images"] = {"animation": {"image_urls": [result]}}
                else:
                    state["generated_images"] = {}
                
            else:
                # Default to multi-method generation
                results = await self._generate_multi_method_images(prompt)
                state["generated_images"] = results
            
            generated_images = state.get("generated_images") or {}
            if generated_images:
                logger.info(f"Successfully generated images: {list(generated_images.keys())}")
            else:
                logger.warning("No images were generated")
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            state["error"] = str(e)
            
        return state
    
    async def quality_check(self, state: ImageGenerationState) -> ImageGenerationState:
        """Check quality of generated images"""
        logger.info("Running quality check on generated images")
        
        if not state.get("generated_images"):
            state["error"] = "No images generated"
            return state
        
        try:
            # Run quality check on all generated images
            quality_results = {}
            
            generated_images = state.get("generated_images") or {}
            for method, image_data in generated_images.items():
                # Handle both new structured format and legacy format
                if isinstance(image_data, dict):
                    images_to_check = []
                    images_with_qa = []
                    
                    # New structured format
                    if "images" in image_data:
                        for img in image_data["images"]:
                            if img.get("qa_results") is not None:
                                # QA already performed, reuse results
                                images_with_qa.append(img)
                                logger.info(f"Reusing existing QA results for {method} image (score: {img['qa_results'].get('score', 'N/A')})")
                            else:
                                # Need to run QA
                                images_to_check.append(img["remote_url"] or img.get("local_path"))
                        
                        # Special handling for SVG with multiple images - run separate parallel QA
                        if method == "svg" and len(image_data["images"]) > 1:
                            logger.info(f"Running separate parallel QA on {len(image_data['images'])} SVG images")
                            
                            # Run QA on each image separately in parallel
                            qa_tasks = []
                            for i, img in enumerate(image_data["images"]):
                                image_url = img["remote_url"] or img.get("local_path")
                                logger.info(f"Queuing QA for SVG image {i+1}: {image_url}")
                                qa_tasks.append(
                                    self._run_sync_tool(
                                        self.quality_checker.check_single_image,
                                        image_url,
                                        state["image_prompt"],
                                        f"Grade {state['grade']} {state['subject']}",
                                        f"Grade {state['grade']} students"
                                    )
                                )
                            
                            # Execute all QA tasks in parallel
                            qa_results = await asyncio.gather(*qa_tasks, return_exceptions=True)
                            
                            # Process results and find the best one
                            best_score = -1
                            best_index = 0
                            rankings = []
                            
                            for i, qa_result in enumerate(qa_results):
                                if isinstance(qa_result, Exception):
                                    logger.error(f"QA failed for image {i}: {qa_result}")
                                    score = 0
                                    recommendation = "REJECT"
                                    changes_required = [f"QA evaluation failed: {str(qa_result)}"]
                                    overall_feedback = f"QA evaluation failed: {str(qa_result)}"
                                else:
                                    # check_single_image now returns ImageRanking object
                                    score = qa_result.score
                                    recommendation = qa_result.recommendation
                                    changes_required = qa_result.changes_required or []
                                    overall_feedback = ""  # ImageRanking doesn't have overall_feedback
                                    logger.info(f"QA result for image {i}: score={score}, recommendation={recommendation}")
                                
                                # Update image with QA results
                                image_data["images"][i]["qa_results"] = {
                                    "score": score,
                                    "recommendation": recommendation,
                                    "overall_feedback": overall_feedback if not isinstance(qa_result, Exception) else '',
                                    "changes_required": changes_required,
                                    "comparison_performed": False
                                }
                                
                                # Track best image
                                if score > best_score:
                                    best_score = score
                                    best_index = i
                                
                                # Create ranking entry
                                rankings.append(ImageRanking(
                                    rank=i+1,  # Will be re-sorted
                                    image_index=i,
                                    score=score,
                                    strengths=qa_result.strengths if not isinstance(qa_result, Exception) else [],
                                    weaknesses=qa_result.weaknesses if not isinstance(qa_result, Exception) else [],
                                    changes_required=changes_required,
                                    recommendation=recommendation
                                ))
                            
                            # Sort rankings by score (highest first)
                            rankings.sort(key=lambda x: x.score, reverse=True)
                            for i, ranking in enumerate(rankings):
                                ranking.rank = i + 1
                            
                            # Create synthetic batch result
                            synthetic_result = QualityCheckResult(
                                rankings=rankings,
                                best_image_index=best_index,
                                overall_feedback=f"Evaluated {len(image_data['images'])} images separately. Best score: {best_score}"
                            )
                            quality_results[method] = synthetic_result
                            logger.info(f"Parallel QA complete. Best image: {best_index} (score: {best_score})")
                            continue  # Skip the regular QA logic below
                    
                    # Legacy format fallback
                    elif "image_urls" in image_data:
                        images_to_check = image_data["image_urls"]
                    
                    # Run QA only on images that don't have existing results
                    if images_to_check:
                        logger.info(f"Running QA on {len(images_to_check)} images for method {method}")
                        result = await self._run_sync_tool(
                            self.quality_checker.check_image_quality_batch,
                            images_to_check, 
                            state["image_prompt"],
                            f"Grade {state['grade']} {state['subject']}",
                            f"Grade {state['grade']} students"
                        )
                        quality_results[method] = result
                    elif images_with_qa:
                        # Create a synthetic result from existing QA data
                        qa_data = images_with_qa[0]["qa_results"]
                        
                        synthetic_result = QualityCheckResult(
                            rankings=[ImageRanking(
                                rank=1,
                                image_index=0,
                                score=qa_data.get("score", 85),
                                strengths=["Pre-evaluated image"],
                                weaknesses=[],
                                changes_required=[],
                                recommendation=qa_data.get("recommendation", "ACCEPT")
                            )],
                            best_image_index=0,
                            overall_feedback=qa_data.get("overall_feedback", "Previously evaluated image")
                        )
                        quality_results[method] = synthetic_result
                        logger.info(f"Using cached QA results for {method}")
                    else:
                        logger.warning(f"No images to check for method {method}")
            
            state["quality_check_results"] = quality_results
            logger.info(f"Quality check complete. Results: {quality_results}")
            
            # Check if any images passed quality check
            passed_any = False
            for method, result in quality_results.items():
                if hasattr(result, 'rankings') and len(result.rankings) > 0:
                    if result.rankings[0].recommendation == "ACCEPT":
                        passed_any = True
                        break
            
            if not passed_any:
                state["retry_count"] = state.get("retry_count", 0) + 1
                logger.warning(f"No images passed quality check. Retry {state['retry_count']}/{state['max_retries']}")
            
        except Exception as e:
            logger.error(f"Error in quality check: {e}")
            state["error"] = str(e)
        
        return state
    
    async def select_best_image(self, state: ImageGenerationState) -> ImageGenerationState:
        """Select the best image from quality check results"""
        logger.info("Selecting best image from quality results")
        
        best_url = None
        
        # First try to find an ACCEPT image
        for method, result in state.get("quality_check_results", {}).items():
            if hasattr(result, 'rankings') and len(result.rankings) > 0:
                if result.rankings[0].recommendation == "ACCEPT":
                    # Get the image URL from the method's generated images
                    generated_images = state.get("generated_images") or {}
                    if method in generated_images:
                        method_data = generated_images[method]
                        
                        # Handle new structured format
                        if "images" in method_data and method_data["images"]:
                            best_url = method_data["images"][0]["remote_url"] or method_data["images"][0].get("local_path")
                        # Handle legacy format
                        elif "image_urls" in method_data:
                            urls = method_data["image_urls"]
                            if urls:
                                best_url = urls[0]
                        
                        if best_url:
                            logger.info(f"Selected ACCEPT image: {best_url}")
                            break
        
        # If no PASS images, take the first available image when max_retries is 0
        if not best_url and state.get("max_retries", 3) == 0:
            for method, image_data in (state.get("generated_images") or {}).items():
                if isinstance(image_data, dict):
                    # Handle new structured format
                    if "images" in image_data and image_data["images"]:
                        best_url = image_data["images"][0]["remote_url"] or image_data["images"][0].get("local_path")
                    # Handle legacy format
                    elif "image_urls" in image_data:
                        urls = image_data["image_urls"]
                        if urls:
                            best_url = urls[0]
                    
                    if best_url:
                        logger.info(f"Selected fallback image from {method}: {best_url}")
                        break
        
        if best_url:
            state["final_image_url"] = best_url
        else:
            logger.warning("No suitable image found")
            state["error"] = "No images available"
        
        return state
    
    def should_retry(self, state: ImageGenerationState) -> str:
        """Determine whether to retry generation"""
        if state.get("error"):
            return "error"
        
        passed_any = False
        for method, result in state.get("quality_check_results", {}).items():
            if hasattr(result, 'rankings') and len(result.rankings) > 0:
                if result.rankings[0].recommendation == "ACCEPT":
                    passed_any = True
                    break
        
        if passed_any:
            return "success"
        
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        image_type = state.get("image_type", "")
        
        # If max_retries is 0, skip retrying and proceed to select best available image
        if max_retries == 0:
            return "success"
        
        # For SVG generation, retry with feedback instead of Gemini fallback
        if image_type == "counting_svg":
            if retry_count <= max_retries:
                return "retry"
        else:
            # Fallback to Gemini editing on first failure for other image types
            if retry_count == 1:
                return "gemini_fallback"
        
        if retry_count <= max_retries:
            return "retry"
        else:
            return "success"  # Force success after max retries to select best available
    
    async def handle_error(self, state: ImageGenerationState) -> ImageGenerationState:
        """Handle errors in the workflow"""
        error = state.get("error", "Unknown error in image generation")
        logger.error(f"Image generation failed: {error}")
        
        # Set a default image URL or None
        state["final_image_url"] = None
        
        return state
    
    async def gemini_fallback_generation(self, state: ImageGenerationState) -> ImageGenerationState:
        """Fallback to Gemini image editing incorporating QA feedback"""
        logger.info("Falling back to Gemini image editing with QA feedback")
        
        # Extract QA feedback from the failed attempt
        qa_feedback = self._extract_qa_feedback(state)
        
        # Get the original failed image path
        original_image_path = self._get_original_image_path(state)
        
        if not original_image_path:
            logger.error("No original image path found for editing")
            state["error"] = "No original image available for editing"
            return state
        
        # Use Gemini image editing to improve the original image
        try:
            
            
            # Create edit instruction from feedback
            edit_instruction = self._create_edit_instruction(
                state.get("question", ""), 
                qa_feedback
            )
            
            updated_image_path = await self._run_sync_tool(
                edit_image_with_gemini,
                original_image_path,
                edit_instruction
            )
            
            if updated_image_path:
                # Update state with edited image results
                state["generated_images"] = {
                    "gemini_edited": {"image_urls": [updated_image_path]}
                }
                state["image_type"] = "gemini_edited"
                logger.info(f"Gemini image editing completed: {updated_image_path}")
            else:
                logger.error("Gemini image editing failed")
                state["error"] = "Gemini image editing failed"
            
        except Exception as e:
            logger.error(f"Gemini image editing failed: {e}")
            state["error"] = f"Gemini image editing failed: {str(e)}"
        
        return state
    
    def _extract_qa_feedback(self, state: ImageGenerationState) -> str:
        """Extract quality feedback from the best image only"""
        feedback_parts = []
        
        # First try to get feedback from the best image in generated_images
        generated_images = state.get("generated_images") or {}
        best_score = -1
        best_feedback = []
        
        for method, image_data in generated_images.items():
            if isinstance(image_data, dict) and "images" in image_data:
                for img in image_data["images"]:
                    qa_results = img.get("qa_results")
                    if qa_results and qa_results.get("score", 0) > best_score:
                        best_score = qa_results["score"]
                        if qa_results.get("changes_required"):
                            best_feedback = qa_results["changes_required"]
        
        if best_feedback:
            feedback_parts.extend(best_feedback)
            logger.info(f"Using feedback from best image (score: {best_score})")
        else:
            # Fallback to old method if no structured feedback found
            quality_results = state.get("quality_check_results", {})
            logger.info(f"Quality results: {quality_results}")
            if not quality_results:
                quality_results = {}
            for method, result in quality_results.items():
                if hasattr(result, 'rankings') and len(result.rankings) > 0:
                    ranking = result.rankings[0]
                    # Prioritize changes_required for concrete actionable feedback
                    if hasattr(ranking, 'changes_required') and ranking.changes_required:
                        feedback_parts.extend(ranking.changes_required)
                    # Fallback to weaknesses if changes_required is not available
                    elif hasattr(ranking, 'weaknesses') and ranking.weaknesses:
                        feedback_parts.extend(ranking.weaknesses)
                    if hasattr(result, 'overall_feedback') and result.overall_feedback:
                        feedback_parts.append(result.overall_feedback)
        
        return " ".join(feedback_parts) if feedback_parts else "No specific feedback available"
    
    def _get_original_image_path(self, state: ImageGenerationState) -> Optional[str]:
        """Extract the local file path of the original failed image"""
        generated_images = state.get("generated_images") or {}
        
        for method, image_data in generated_images.items():
            if isinstance(image_data, dict) and image_data.get("image_urls"):
                urls = image_data["image_urls"]
                if urls and len(urls) > 0:
                    image_path = urls[0]
                    
                    # If it's a local path, use it directly
                    if not image_path.startswith('http') and os.path.exists(image_path):
                        return image_path
                    
                    # If it's a Supabase URL, extract filename and build local path
                    elif image_path.startswith('http'):
                        # Extract filename from URL (last part before query params)
                        filename = image_path.split('/')[-1].split('?')[0]
                        local_path = f"generated_images/{filename}"
                        if os.path.exists(local_path):
                            logger.info(f"Found local copy of uploaded image: {local_path}")
                            return local_path
        
        return None
    
    def _get_original_svg_code(self, state: ImageGenerationState) -> Optional[str]:
        """Extract the SVG code from the best scoring image"""
        generated_images = state.get("generated_images") or {}
        best_score = -1
        best_svg_code = None
        
        for method, image_data in generated_images.items():
            if isinstance(image_data, dict) and "images" in image_data:
                for img in image_data["images"]:
                    qa_results = img.get("qa_results")
                    if qa_results and qa_results.get("score", 0) > best_score:
                        best_score = qa_results["score"]
                        # Get the SVG code from the best image - we need to store this!
                        best_svg_code = img.get("svg_code")  # Need to add this field
        
        return best_svg_code
    
    def _create_edit_instruction(self, question: str, feedback: str) -> str:
        """Create edit instruction for Gemini image editing based on QA feedback"""
        instruction = f"""Using the provided educational diagram image, make the following specific edits to fix these identified issues:
        {feedback}
        """
        
        return instruction.strip()
    
    async def _create_gemini_fallback_prompt(self, state: ImageGenerationState, qa_feedback: str) -> str:
        """Create enhanced prompt for Gemini incorporating QA feedback"""
        original_question = state.get("question", "")
        original_prompt = state.get("image_prompt", "")
        
        enhanced_prompt = f"""
Educational diagram for: {original_question}

IMPORTANT FEEDBACK TO ADDRESS:
{qa_feedback}

Original prompt attempt: {original_prompt}

Please create a clear, educational visual that addresses the specific issues mentioned in the feedback above. Focus on:
- Showing only the given information, not calculated answers
- Clear labeling and proper positioning
- Educational value without revealing solutions
- Professional, clean appearance suitable for learning materials
"""
        
        return enhanced_prompt.strip()
    
    # Helper methods
    
    async def _generate_real_world_prompt(self, state: ImageGenerationState) -> str:
        """Generate prompt for real-world images"""

        prompt_template = """When drafting a prompt for image generation for an illustration of this question, what should the prompt look like?  
        
        ###Question: 
        {question_text}

        ###Grade Level: 
        # {grade}

        ###Instructions:
        Generate a clear, detailed prompt for creating an educational image that:
        1. Illustrates the concept without revealing the answer - NEVER show the solution
        2. Uses age-appropriate visuals
        3. Is engaging and clear for students
        4. For math problems, show only the equation or problem setup, NOT the answer
        5. If there are objects in the question for counting, addition, subtraction, division, show the precise number of objects in the question. No more, no less. Don't include anything else, such as characters, background objects, etc.
        6. NO descriptive text, labels, or words in REAL-WORLD images (like "apples", "books", "total", etc.)
        7. Numbers and mathematical symbols are allowed ONLY when essential for measurements or calculations
        8. EXCEPTION: Charts and Venn diagrams MUST have essential labels (series names, group labels) to be functional
        
        ###Critical:
        - NEVER reveal the answer to the question in the image
        - DON'T add any formula 
        - DON'T add the question text
        - NO descriptive text or labels in REAL-WORLD/counting images
        - Charts/Venn diagrams MUST have essential functional labels
        - Only essential numbers/measurements allowed (e.g., "5cm", "90°")
        - Answer with only the prompt and nothing else
        """.format(question_text=state["question"], grade=state["grade"])

        response = await self.llm.ainvoke([HumanMessage(
            content=prompt_template.format(
                question=state["question"],
                grade=state["grade"]
            )
        )])
        
        return response.content
    
    async def _generate_counting_svg_prompt(self, state: ImageGenerationState) -> str:
        """Generate prompt for counting/arithmetic SVG images"""
        question = state["question"]
        
        # Create a concise prompt for SVG generation
        counting_prompt = f"""Create a brief, clear description for an SVG image showing: {question}

        Include:
        - What objects to show and how many
        - The mathematical operation symbol 
        - Basic arrangement (left group, operator, right group)
        - Never reveal the answer to the question
        
        Keep it concise - just the essential details for counting visualization."""
        
        response = await self.llm.ainvoke([HumanMessage(content=counting_prompt)])

        logger.info(f"Generated counting SVG prompt: {response.content}")
        return response.content
    
    async def _generate_chart_prompt(self, state: ImageGenerationState) -> str:
        """Generate prompt for chart/graph images"""
        # Extract data and chart requirements from question
        return f"Educational chart for: {state['question']}"
    
    async def _generate_geometric_prompt(self, state: ImageGenerationState) -> str:
        """Generate prompt for geometric images"""
        return f"Geometric illustration for: {state['question']} - CRITICAL: Show only the shape itself with any given measurements from the question. Do NOT label the shape with its name (like 'quadrilateral', 'triangle', etc.) or reveal answers like number of sides, angles, or properties."
    
    async def _generate_mathematical_prompt(self, state: ImageGenerationState) -> str:
        """Generate prompt for mathematical images"""
        return f"Mathematical visualization for: {state['question']} - IMPORTANT: Show only the problem setup, NOT the answer or solution steps"
    
    async def _generate_diagram_prompt(self, state: ImageGenerationState) -> str:
        """Generate prompt for diagram images"""
        return f"Educational diagram for: {state['question']}"
    
    async def _generate_animation_prompt(self, state: ImageGenerationState) -> str:
        """Generate prompt for animations"""
        return f"Educational animation showing: {state['question']}"
    
    async def _generate_generic_prompt(self, state: ImageGenerationState) -> str:
        """Generate generic educational prompt"""
        return f"Educational illustration for: {state['question']}"
    
    async def _generate_multi_method_images(self, prompt: str) -> Dict[str, Any]:
        """Generate images using Gemini only"""
        results = {}
        
        # Use only Gemini - generate only 1 image
        gemini_result = await self._run_sync_tool(generate_image_gemini, prompt, "1:1", 1)
        
        # Process result - Gemini now returns JSON like other tools
        if not isinstance(gemini_result, Exception):
            try:
                parsed_result = json.loads(gemini_result)
                if parsed_result.get("status") == "success" and parsed_result.get("image_paths"):
                    results["gemini"] = {
                        "image_urls": parsed_result["image_paths"]
                    }
            except Exception as e:
                logger.error(f"Failed to parse Gemini result: {e}")
        
        return results
    
    # Chart generation methods
    
    async def _generate_bar_chart(self, state: ImageGenerationState) -> Optional[str]:
        """Generate bar chart with data extracted from question"""
        # Extract data from question for bar chart
        data = await self._extract_chart_data(state, "bar")
        if not data or not data.get("series"):
            return None
        
        try:
            # Calculate smart Y-axis interval that works for both integers and decimals
            max_value = max(max(s["values"]) for s in data["series"])
            min_value = min(min(s["values"]) for s in data["series"])
            data_range = max_value - min_value
            
            # Check if all values are integers
            all_integers = all(
                all(isinstance(val, int) or val.is_integer() for val in s["values"])
                for s in data["series"]
            )
            
            # Calculate nice interval using powers of 10
            magnitude = 10 ** math.floor(math.log10(data_range))
            normalized_range = data_range / magnitude
            
            if normalized_range <= 1:
                nice_interval = 0.1 * magnitude
            elif normalized_range <= 2:
                nice_interval = 0.2 * magnitude
            elif normalized_range <= 5:
                nice_interval = 0.5 * magnitude
            else:
                nice_interval = 1.0 * magnitude
            
            # For integers, use smart minimum based on data range
            if all_integers:
                if data_range <= 20:
                    min_interval = 2  # Fine granularity for small ranges
                elif data_range <= 100:
                    min_interval = 5
                else:
                    min_interval = 10
                y_interval = max(nice_interval, min_interval)
            else:
                y_interval = nice_interval
            
            return await self._run_sync_tool(
                generate_simple_bar,
                data["series"],
                data.get("title", "Chart"),
                data.get("xlabel", "Categories"),
                data.get("ylabel", "Values"),
                data.get("width", 0.8),
                data.get("xlim"),
                data.get("ylim"),
                data.get("legend", True),
                data.get("xtick_rotation", 0),
                y_interval,
                data.get("background_color", "white")
            )
        except Exception as e:
            logger.error(f"Error generating bar chart: {e}")
            return None
    
    async def _generate_line_chart(self, state: ImageGenerationState) -> Optional[str]:
        """Generate line chart"""
        data = await self._extract_chart_data(state, "line")
        if not data:
            return None
        
        return await self._run_sync_tool(
            generate_simple_line,
            data["series"],
            data["title"],
            data["xlabel"],
            data["ylabel"],
            data.get("xlim"),
            data.get("ylim"),
            data.get("legend", True),
            data.get("grid", True),
            data.get("markers", True),
            data.get("background_color", "white")
        )
    
    async def _generate_pie_chart(self, state: ImageGenerationState) -> Optional[str]:
        """Generate pie chart"""
        data = await self._extract_chart_data(state, "pie")
        if not data:
            return None
        
        return await self._run_sync_tool(
            generate_simple_pie,
            data["labels"],
            data["values"],
            data["title"],
            data.get("colors"),
            data.get("explode"),
            data.get("show_percentages", True),
            data.get("background_color", "white")
        )
    
    async def _generate_scatter_chart(self, state: ImageGenerationState) -> Optional[str]:
        """Generate scatter plot"""
        data = await self._extract_chart_data(state, "scatter")
        if not data:
            return None
        
        return await self._run_sync_tool(
            generate_simple_scatter,
            data["series"],
            data["title"],
            data["xlabel"],
            data["ylabel"],
            data.get("xlim"),
            data.get("ylim"),
            data.get("legend", True),
            data.get("grid", True),
            data.get("point_size", 50),
            data.get("background_color", "white")
        )
    
    async def _generate_box_chart(self, state: ImageGenerationState) -> Optional[str]:
        """Generate box plot"""
        data = await self._extract_chart_data(state, "box")
        if not data:
            return None
        
        return await self._run_sync_tool(
            generate_simple_box,
            data["data_sets"],
            data["title"],
            data["xlabel"],
            data["ylabel"],
            data.get("show_outliers", True),
            data.get("background_color", "white")
        )
    
    async def _generate_heatmap_chart(self, state: ImageGenerationState) -> Optional[str]:
        """Generate heatmap"""
        data = await self._extract_chart_data(state, "heatmap")
        if not data:
            return None
        
        return await self._run_sync_tool(
            generate_simple_heatmap,
            data["data"],
            data["title"],
            data["xlabel"],
            data["ylabel"],
            data.get("x_labels"),
            data.get("y_labels"),
            data.get("colormap", "viridis"),
            data.get("show_values", True),
            data.get("background_color", "white")
        )
    
    async def _generate_histogram_chart(self, state: ImageGenerationState) -> Optional[str]:
        """Generate histogram"""
        data = await self._extract_chart_data(state, "histogram")
        if not data:
            return None
        
        return await self._run_sync_tool(
            generate_simple_histogram,
            data["data"],
            data["title"],
            data["xlabel"],
            data.get("ylabel", "Frequency"),
            data.get("bins", 10),
            data.get("color", "blue"),
            data.get("show_normal_curve", False),
            data.get("background_color", "white")
        )
    
    async def _generate_venn_simple(self, state: ImageGenerationState) -> Optional[str]:
        """Generate Venn diagram using venn library"""
        data = await self._extract_venn_data(state)
        if not data:
            return None
        
        return await self._run_sync_tool(
            generate_venn_diagram_simple,
            data["sets_data"],
            data.get("title"),
            data.get("colors"),
            data.get("background_color", "white")
        )
    
    # Educational visualization methods
    
    async def _generate_2d_shapes(self, state: ImageGenerationState) -> Optional[str]:
        """Generate 2D geometric shapes"""
        shapes_data = await self._extract_shape_data(state, "2d")
        if not shapes_data:
            return None
        
        return await self._run_sync_tool(
            generate_2d_shape_image,
            shapes_data["shapes"],
            shapes_data.get("title"),
            shapes_data.get("grid_size", (1, 1)),
            shapes_data.get("show_labels", True),
            shapes_data.get("show_measurements", True),
            shapes_data.get("background_color", "white")
        )
    
    async def _generate_3d_shapes(self, state: ImageGenerationState) -> Optional[str]:
        """Generate 3D geometric shapes"""
        shape_data = await self._extract_shape_data(state, "3d")
        if not shape_data:
            return None
        
        return await self._run_sync_tool(
            generate_3d_shape_image,
            shape_data["shape_type"],
            shape_data["dimensions"],
            shape_data.get("rotation"),
            shape_data.get("show_edges", True),
            shape_data.get("show_labels", True),
            shape_data.get("color", "lightblue"),
            shape_data.get("title"),
            shape_data.get("background_color", "white"),
            shape_data.get("units")
        )
    
    async def _generate_intersecting_lines(self, state: ImageGenerationState) -> Optional[str]:
        """Generate intersecting lines"""
        lines_data = await self._extract_lines_data(state)
        if not lines_data:
            return None
        
        return await self._run_sync_tool(
            generate_intersecting_lines_image,
            lines_data["lines"],
            lines_data.get("show_angles", False),
            lines_data.get("show_labels", True),
            lines_data.get("grid", True),
            lines_data.get("axis_range", 5),
            lines_data.get("title"),
            lines_data.get("background_color", "white")
        )
    
    async def _generate_equation_image(self, state: ImageGenerationState) -> Optional[str]:
        """Generate LaTeX equation image"""
        equation_data = await self._extract_equation_data(state)
        if not equation_data:
            return None
        
        return await self._run_sync_tool(
            generate_latex_equation_image,
            equation_data["equation"],
            equation_data.get("fontsize", 20),
            equation_data.get("color", "black"),
            equation_data.get("title"),
            equation_data.get("background_color", "white")
        )
    
    async def _generate_number_line_image(self, state: ImageGenerationState) -> Optional[str]:
        """Generate number line"""
        line_data = await self._extract_number_line_data(state)
        if not line_data:
            return None
        
        return await self._run_sync_tool(
            generate_number_line,
            line_data["start"],
            line_data["end"],
            line_data.get("marks"),
            line_data.get("highlight_points"),
            line_data.get("intervals"),
            line_data.get("show_arrows", True),
            line_data.get("title"),
            line_data.get("background_color", "white")
        )
    
    async def _generate_ruler_image(self, state: ImageGenerationState) -> Optional[str]:
        """Generate ruler image"""
        ruler_data = await self._extract_ruler_data(state)
        if not ruler_data:
            return None
        
        return await self._run_sync_tool(
            generate_ruler_image,
            ruler_data["length"],
            ruler_data.get("unit", "cm"),
            ruler_data.get("show_minor_marks", True),
            ruler_data.get("highlight_measurements"),
            ruler_data.get("orientation", "horizontal"),
            ruler_data.get("background_color", "white")
        )
    
    async def _generate_clock_image(self, state: ImageGenerationState) -> Optional[str]:
        """Generate clock image"""
        clock_data = await self._extract_clock_data(state)
        if not clock_data:
            return None
        
        return await self._run_sync_tool(
            generate_clock_image,
            clock_data["hour"],
            clock_data["minute"],
            clock_data.get("show_digital", False),
            clock_data.get("clock_style", "analog"),
clock_data.get("background_color", "white")
        )
    
    async def _generate_animation_image(self, state: ImageGenerationState) -> Optional[str]:
        """Generate animation"""
        return await self._run_sync_tool(
            generate_animation,
            state["image_prompt"],
            5,  # duration
            800,  # width
            600,  # height
            "white"  # background
        )
    
    async def _run_sync_tool(self, tool_func, *args, **kwargs):
        """Run a synchronous tool in an async context"""
        try:
            logger.info(f"Running sync tool: {tool_func.__name__} with args: {[str(arg)[:100] for arg in args]}")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, tool_func, *args, **kwargs)
            logger.info(f"Sync tool {tool_func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error in _run_sync_tool with {tool_func.__name__}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    # Data extraction methods for specialized tools
    
    async def _extract_chart_data(self, state: ImageGenerationState, chart_type: str) -> Optional[Dict[str, Any]]:
        """Extract data needed for chart generation from question"""
        try:
            if chart_type == "bar":
                extraction_prompt = f"""
                Extract data from this question to create a bar chart:
                
                Question: {state['question']}
                
                IMPORTANT: All labels (title, xlabel, ylabel, categories, series labels) MUST be in the SAME LANGUAGE as the question text.
                
                Return ONLY a JSON object in this exact format:
                {{
                    "title": "Chart Title",
                    "xlabel": "Categories",
                    "ylabel": "Values", 
                    "series": [{{
                        "categories": ["Category1", "Category2", "Category3"],
                        "values": [value1, value2, value3],
                        "label": "Series Name",
                        "color": "blue"
                    }}]
                }}
                """
            elif chart_type == "line":
                extraction_prompt = f"""
                Extract data from this question to create a line chart:
                
                Question: {state['question']}
                
                IMPORTANT: All labels (title, xlabel, ylabel, series labels) MUST be in the SAME LANGUAGE as the question text.
                
                Return ONLY a JSON object in this exact format:
                {{
                    "title": "Chart Title",
                    "xlabel": "X-axis",
                    "ylabel": "Y-axis",
                    "series": [{{
                        "x_values": [x1, x2, x3],
                        "y_values": [y1, y2, y3],
                        "label": "Series Name",
                        "color": "blue"
                    }}]
                }}
                """
            elif chart_type == "pie":
                extraction_prompt = f"""
                Extract data from this question to create a pie chart:
                
                Question: {state['question']}
                
                IMPORTANT: All labels (title and slice labels) MUST be in the SAME LANGUAGE as the question text.
                
                Return ONLY a JSON object in this exact format:
                {{
                    "title": "Chart Title",
                    "labels": ["Label1", "Label2", "Label3"],
                    "values": [value1, value2, value3]
                }}
                """
            elif chart_type == "scatter":
                extraction_prompt = f"""
                Extract data from this question to create a scatter plot:
                
                Question: {state['question']}
                
                IMPORTANT: All labels (title, xlabel, ylabel, series labels) MUST be in the SAME LANGUAGE as the question text.
                
                Return ONLY a JSON object in this exact format:
                {{
                    "title": "Chart Title",
                    "xlabel": "X-axis",
                    "ylabel": "Y-axis",
                    "series": [{{
                        "x_values": [x1, x2, x3],
                        "y_values": [y1, y2, y3],
                        "label": "Series Name",
                        "color": "blue"
                    }}]
                }}
                """
            elif chart_type == "box":
                extraction_prompt = f"""
                Extract data from this question to create a box plot:
                
                Question: {state['question']}
                
                IMPORTANT: All labels (title, xlabel, ylabel, dataset labels) MUST be in the SAME LANGUAGE as the question text.
                
                Return ONLY a JSON object in this exact format:
                {{
                    "title": "Chart Title",
                    "xlabel": "Categories",
                    "ylabel": "Values",
                    "data_sets": [{{
                        "data": [value1, value2, value3, value4, value5],
                        "label": "Dataset Name"
                    }}]
                }}
                """
            elif chart_type == "histogram":
                extraction_prompt = f"""
                Extract data from this question to create a histogram:
                
                Question: {state['question']}
                
                IMPORTANT: All labels (title, xlabel, ylabel) MUST be in the SAME LANGUAGE as the question text.
                
                Return ONLY a JSON object in this exact format:
                {{
                    "title": "Chart Title",
                    "xlabel": "Values",
                    "ylabel": "Frequency",
                    "data": [value1, value2, value3, value4, value5]
                }}
                """
            elif chart_type == "heatmap":
                extraction_prompt = f"""
                Extract data from this question to create a heatmap:
                
                Question: {state['question']}
                
                IMPORTANT: All labels (title, xlabel, ylabel, x_labels, y_labels) MUST be in the SAME LANGUAGE as the question text.
                
                Return ONLY a JSON object in this exact format:
                {{
                    "title": "Chart Title",
                    "xlabel": "X-axis",
                    "ylabel": "Y-axis",
                    "data": [[value1, value2], [value3, value4]],
                    "x_labels": ["X1", "X2"],
                    "y_labels": ["Y1", "Y2"]
                }}
                """
            else:
                logger.error(f"Unsupported chart type: {chart_type}")
                return None
            
            response = await self.llm.ainvoke([HumanMessage(content=extraction_prompt)])
            
            data = json.loads(response.content)
            return data
            
        except Exception as e:
            logger.error(f"Error extracting {chart_type} data: {e}")
            return None
    
    async def _extract_shape_data(self, state: ImageGenerationState, dimension: str) -> Optional[Dict[str, Any]]:
        """Extract shape data from question"""
        try:
            if dimension == "2d":
                extraction_prompt = f"""
                Extract 2D geometric shape information from this question and return structured data:
                
                Question: {state['question']}
                
                IMPORTANT: All labels MUST be in the SAME LANGUAGE as the question text.
                IMPORTANT: If the question mentions a specific triangle type (equilateral, isosceles, right), 
                include "triangle_type" in the size object with the appropriate value.
                
                Return a structured JSON object using these exact formats for each shape type:

                For RECTANGLE (width × height):
                {{
                    "shapes": [{{
                        "type": "rectangle",
                        "center": [0.0, 0.0],
                        "color": "lightblue",
                        "label": "",
                        "units": "cm",
                        "size": {{"width": 8.0, "height": 6.0}}
                    }}],
                    "show_measurements": true,
                    "show_labels": false
                }}

                For CIRCLE (radius or diameter):
                {{
                    "shapes": [{{
                        "type": "circle",
                        "center": [0.0, 0.0], 
                        "color": "lightblue",
                        "label": "",
                        "units": "cm",
                        "size": {{"radius": 5.0, "diameter": null}}
                    }}],
                    "show_measurements": true,
                    "show_labels": false
                }}

                For TRIANGLE - Extract ALL given information and set show/hide flags:
                
                Example: "In an isosceles triangle, two sides are 5 cm each and the base is 6 cm, what is the perimeter?"
                {{
                    "shapes": [{{
                        "type": "triangle",
                        "center": [0.0, 0.0],
                        "color": "lightblue", 
                        "label": "",
                        "units": "cm",
                        "size": {{
                            "base_side": 6.0,     // Given: base at bottom
                            "left_side": 5.0,     // Given: left side
                            "right_side": 5.0,    // Given: right side
                            "triangle_type": "isosceles",
                            "show_base_label": true,   // Show because given
                            "show_left_label": true,   // Show because given
                            "show_right_label": true,  // Show because given
                            "show_height_label": false // Hide because not given
                        }}
                    }}],
                    "show_measurements": true,
                    "show_labels": false
                }}
                
                Example: "A right triangle has base 8 cm and height 6 cm, find the hypotenuse"
                {{
                    "shapes": [{{
                        "type": "triangle", 
                        "center": [0.0, 0.0],
                        "color": "lightblue",
                        "label": "",
                        "units": "cm",
                        "size": {{
                            "base_side": 8.0,     // Given: base at bottom
                            "left_side": null,    // Unknown: hypotenuse (don't calculate)
                            "right_side": null,   // This will be calculated from height
                            "height": 6.0,        // Given: height
                            "triangle_type": "right",
                            "show_base_label": true,   // Show base
                            "show_left_label": false,  // Hide hypotenuse (answer)
                            "show_right_label": false, // Hide this side
                            "show_height_label": true  // Show height
                        }}
                    }}],
                    "show_measurements": true,
                    "show_labels": false
                }}
                
                CRITICAL FOR TRIANGLE ANGLES:
                - angle_base_left: Angle at bottom-left vertex (where base meets left side)
                - angle_left_right: Angle at top vertex (where left and right sides meet)  
                - angle_right_base: Angle at bottom-right vertex (where right side meets base)
                
                GEOMETRY RULES FOR RIGHT TRIANGLES:
                - The right angle (90°) is ALWAYS at angle_base_left
                - base_side = horizontal leg at bottom
                - left_side = vertical leg on left (from base to top)  
                - right_side = hypotenuse (diagonal from top to bottom-right)
                - Only put acute angles (< 90°) in angle_left_right or angle_right_base
                - Leave angle_base_left as null (90° is shown automatically)
                - When hypotenuse is given: put it in right_side field
                - When legs are given: put them in base_side and left_side fields
                - Only extract angles that are explicitly given in the question
                - Leave unknown/calculated angles as null

                For SQUARE (side length or diagonal):
                
                Example: "A square has side length 4 cm, find the area"
                {{
                    "shapes": [{{
                        "type": "square",
                        "center": [0.0, 0.0],
                        "color": "lightblue",
                        "label": "",
                        "units": "cm", 
                        "size": {{
                            "side": 4.0,
                            "diagonal": null,
                            "show_side_label": true,
                            "show_diagonal_label": false
                        }}
                    }}],
                    "show_measurements": true,
                    "show_labels": false
                }}
                
                Example: "A square has diagonal length 10 cm, find the side length"
                {{
                    "shapes": [{{
                        "type": "square",
                        "center": [0.0, 0.0],
                        "color": "lightblue",
                        "label": "",
                        "units": "cm",
                        "size": {{
                            "side": null,
                            "diagonal": 10.0,
                            "show_side_label": false,
                            "show_diagonal_label": true
                        }}
                    }}],
                    "show_measurements": true,
                    "show_labels": false
                }}

                For ELLIPSE (width × height with optional rotation):
                {{
                    "shapes": [{{
                        "type": "ellipse",
                        "center": [0.0, 0.0],
                        "color": "lightblue",
                        "label": "",
                        "units": "cm",
                        "size": {{"width": 8.0, "height": 4.0, "angle": 0}}
                    }}],
                    "show_measurements": true,
                    "show_labels": false
                }}

                For POLYGON (regular polygon with radius and number of sides):
                {{
                    "shapes": [{{
                        "type": "polygon",
                        "center": [0.0, 0.0],
                        "color": "lightblue",
                        "label": "",
                        "units": "cm",
                        "size": {{"radius": 5.0, "sides": 6, "rotation": 0}}
                    }}],
                    "show_measurements": true,
                    "show_labels": false
                }}

                CRITICAL: Extract shape information and determine labeling:
                - Extract the shape type from the question
                - Extract any dimensions that are explicitly provided (leave as null if not given)
                - If dimensions are provided, set show_measurements = true
                - If NO dimensions are provided, set show_measurements = false (shape will render with default dimensions but no labels)
                
                Examples with show_measurements = false:
                - "How many sides does a triangle have?" → type="triangle", dimensions with null values, show_measurements = false
                - "What shape has 4 equal sides?" → type="square", dimensions with null values, show_measurements = false
                
                Examples with show_measurements = true:
                - "A triangle has base 6 cm and height 4 cm." → type="triangle", extract given dimensions, show_measurements = true
                - "A circle has radius 5 cm." → type="circle", extract radius, show_measurements = true
                
                Extract the exact dimensions from the question text. Use "lightblue" color.
                Set show_measurements to true to display dimensions on the shape.
                
                For triangles:
                - If question says "equilateral triangle", set triangle_type to "equilateral"
                - If question says "isosceles triangle", set triangle_type to "isosceles" 
                - If question says "right triangle", set triangle_type to "right"
                - If no specific type mentioned but base and height given, set triangle_type to null (defaults to right)
                """
            else:  # 3d
                extraction_prompt = f"""
                Extract 3D geometric shape information from this question:
                
                Question: {state['question']}
                
                IMPORTANT: All labels MUST be in the SAME LANGUAGE as the question text.
                CRITICAL: Extract shape information and determine labeling:
                - Extract the shape type from the question
                - Extract any dimensions that are explicitly provided (leave as null if not given)
                - If dimensions are provided, set show_labels = true  
                - If NO dimensions are provided, set show_labels = false (shape will render with default dimensions but no labels)
                
                Examples with show_labels = false:
                - "How many circular faces does a cylinder have?" → type="cylinder", dimensions with null values, show_labels = false
                - "How many edges does a cube have?" → type="cube", dimensions with null values, show_labels = false
                
                Examples with show_labels = true:
                - "A cylinder has radius 4 cm and height 10 cm." → type="cylinder", extract given dimensions, show_labels = true
                - "A cube has side length 5 cm." → type="cube", extract side length, show_labels = true
                
                Examples for each shape type:
                
                For CUBE:
                - If volume given, side asked: "A cube has volume 125 cm³. What is the length of one side?"
                {{
                    "shape_type": "cube",
                    "dimensions": {{"side": 5, "volume": 125, "show_side": false, "show_volume": true}},
                    "title": null,
                    "show_labels": true,
                    "color": "lightblue",
                    "units": "cm"
                }}
                - If side given, volume asked: "A cube has side length 5 cm. What is its volume?"
                {{
                    "shape_type": "cube", 
                    "dimensions": {{"side": 5, "volume": 125, "show_side": true, "show_volume": false}},
                    "title": null,
                    "show_labels": true,
                    "color": "lightblue",
                    "units": "cm"
                }}
                
                For CUBOID (rectangular prism):
                - "A rectangular prism has dimensions 2×3×4 cm. What is its surface area?"
                {{
                    "shape_type": "cuboid",
                    "dimensions": {{"length": 2, "width": 3, "height": 4, "show_length": true, "show_width": true, "show_height": true}},
                    "title": null,
                    "show_labels": true,
                    "color": "lightblue", 
                    "units": "cm"
                }}
                
                For SPHERE:
                - "A sphere has radius 3 cm. What is its volume?"
                {{
                    "shape_type": "sphere",
                    "dimensions": {{"radius": 3}},
                    "title": null,
                    "show_labels": true,
                    "color": "lightblue",
                    "units": "cm"
                }}
                
                For CYLINDER:
                - "A cylinder has radius 4 cm and height 10 cm. What is its volume?"
                {{
                    "shape_type": "cylinder",
                    "dimensions": {{"radius": 4, "height": 10}},
                    "title": null,
                    "show_labels": true,
                    "color": "lightblue",
                    "units": "cm"
                }}
                
                For CONE:
                - "A cone has base radius 5 cm and height 12 cm. What is its volume?"
                {{
                    "shape_type": "cone",
                    "dimensions": {{"radius": 5, "height": 12}},
                    "title": null,
                    "show_labels": true,
                    "color": "lightblue",
                    "units": "cm"
                }}
                - "A cone has base radius 3 cm and slant height 10 cm. What is its height?"
                {{
                    "shape_type": "cone",
                    "dimensions": {{"radius": 3, "slant_height": 10}},
                    "title": null,
                    "show_labels": true,
                    "color": "lightblue",
                    "units": "cm"
                }}
                
                For PYRAMID:
                - "A square pyramid has base side 6 cm and height 8 cm. What is its volume?"
                {{
                    "shape_type": "pyramid",
                    "dimensions": {{"base_side": 6, "height": 8}},
                    "title": null,
                    "show_labels": true,
                    "color": "lightblue",
                    "units": "cm"
                }}
                - "A pyramid has base area 36 cm² and height 9 cm. What is its volume?"
                {{
                    "shape_type": "pyramid",
                    "dimensions": {{"base_area": 36, "height": 9}},
                    "title": null,
                    "show_labels": true,
                    "color": "lightblue",
                    "units": "cm"
                }}
                
                For TRIANGULAR_PRISM:
                - "A triangular prism has base side 4 cm and height 10 cm. What is its volume?"
                {{
                    "shape_type": "triangular_prism",
                    "dimensions": {{"base_side": 4, "height": 10}},
                    "title": null,
                    "show_labels": true,
                    "color": "lightblue",
                    "units": "cm"
                }}
                - "A triangular prism has base area 15 cm² and height 10 cm. What is its volume?"
                {{
                    "shape_type": "triangular_prism",
                    "dimensions": {{"base_area": 15, "height": 10}},
                    "title": null,
                    "show_labels": true,
                    "color": "lightblue",
                    "units": "cm"
                }}
                
                Available shape types: cube, cuboid, sphere, cylinder, cone, pyramid, triangular_prism
                """
            
            if dimension == "2d":
                # Use structured response for 2D shapes
                response = produce_structured_response_openai(
                    messages=[{"role": "user", "content": extraction_prompt}],
                    structure_model=Shapes2DData,
                    model="gpt-5",
                    instructions=None,
                    temperature=1.0,
                    max_output_tokens=None
                )
                logger.info(f"Extracted 2D shape data: {response}")
                result = response.model_dump()
                logger.info(f"2D SHAPE DEBUG: model_dump result = {result}")
                # Log specifically for triangles
                if result.get('shapes') and len(result['shapes']) > 0:
                    for i, shape in enumerate(result['shapes']):
                        if shape.get('type') == 'triangle':
                            logger.info(f"2D TRIANGLE DEBUG [{i}]: shape = {shape}")
                            logger.info(f"2D TRIANGLE DEBUG [{i}]: size = {shape.get('size', {})}")
                return result
            else:
                # Use structured response for 3D shapes
                response = produce_structured_response_openai(
                    messages=[{"role": "user", "content": extraction_prompt}],
                    structure_model=Shape3DData,
                    model="gpt-5",
                    instructions=None,
                    temperature=1.0,
                    max_output_tokens=None
                )
                logger.info(f"Extracted 3D shape data: {response}")
                result = response.model_dump()
                logger.info(f"3D SHAPE DEBUG: model_dump result = {result}")
                return result
            
        except Exception as e:
            logger.error(f"Error extracting {dimension} shape data: {e}")
            return None
    
    async def _extract_lines_data(self, state: ImageGenerationState) -> Optional[Dict[str, Any]]:
        """Extract line data from question"""
        try:
            extraction_prompt = f"""
            Extract line information from this geometry question:
            
            Question: {state['question']}
            
            IMPORTANT: All labels (line labels, title) MUST be in the SAME LANGUAGE as the question text.
            
            Determine what lines should be drawn and how they intersect.
            
            Return ONLY a JSON object in this exact format:
            {{
                "lines": [
                    {{
                        "point1": [x1, y1],  # First point of line
                        "point2": [x2, y2],  # Second point of line
                        "color": "blue",
                        "label": "Line 1"
                    }},
                    {{
                        "point1": [x3, y3],  # First point of second line
                        "point2": [x4, y4],  # Second point of second line
                        "color": "red",
                        "label": "Line 2"
                    }}
                    // Add more lines as needed
                ],
                "show_angles": true,  // Set to true for angle questions
                "title": null,  // Optional title
                "axis_range": 5  // How far axes extend (-5 to 5 by default)
            }}
            
            IMPORTANT: Each line MUST have "point1" and "point2" keys (not "start"/"end").
            
            For a right angle: Create two perpendicular lines that meet at 90 degrees.
            For parallel lines: Create lines with the same slope.
            For triangles: Create three lines that form a closed shape.
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=extraction_prompt)])
            
            data = json.loads(response.content)
            return data
            
        except Exception as e:
            logger.error(f"Error extracting lines data: {e}")
            return None
    
    async def _extract_equation_data(self, state: ImageGenerationState) -> Optional[Dict[str, Any]]:
        """Extract equation from question"""
        try:
            extraction_prompt = f"""
            Extract the mathematical equation that should be visualized from this question:
            
            Question: {state['question']}
            
            CRITICAL INSTRUCTIONS:
            - Extract ONLY the problem/equation that needs to be solved
            - DO NOT include the answer or solution
            - For "Solve for x" questions, show only the equation, NOT the value of x
            - For calculation questions, show only the expression, NOT the result
            
            Return JSON with the equation in LaTeX format (without $ delimiters).
            
            Example: 
            Question: "Solve for x: 2x + 5 = 15"
            Return: {{"equation": "2x + 5 = 15"}}
            
            Question: "What is 15 × 7?"
            Return: {{"equation": "15 x 7 = ?"}}
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=extraction_prompt)])
            
            # Handle potential LaTeX backslash escaping issues
            response_content = response.content.strip()
            
            # Try to parse directly first
            try:
                data = json.loads(response_content)
            except json.JSONDecodeError:
                # If that fails, try to fix common escape issues
                # Replace single backslashes with double backslashes for LaTeX
                
                # Find JSON content between braces
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    # Fix backslash escaping for LaTeX
                    json_str = json_str.replace('\\', '\\\\')
                    data = json.loads(json_str)
                else:
                    raise ValueError(f"Could not extract valid JSON from response: {response_content}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error extracting equation data: {e}")
            return None
    
    async def _extract_number_line_data(self, state: ImageGenerationState) -> Optional[Dict[str, Any]]:
        """Extract number line parameters from question"""
        try:
            extraction_prompt = f"""
            Extract number line parameters from this question:
            IMPORTANT: Only include values in "marks" that should be labeled. Don't reveal answers.
            IMPORTANT: All labels (title, point labels) MUST be in the SAME LANGUAGE as the question text.
            
            Question: {state['question']}
            
            Return ONLY a JSON object in this exact format:
            {{
                "start": number,
                "end": number,
                "marks": [values_to_label],  // Only include values that should show labels
                "highlight_points": [{{
                    "value": number,
                    "color": "red",
                    "label": "Point Name"
                }}],
                "intervals": number_of_tick_intervals,
                "title": "Number Line Title"
            }}
            
            For question "Show the number 7 on a number line from 0 to 10":
            {{
                "start": 0,
                "end": 10,
                "marks": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "highlight_points": [{{
                    "value": 7,
                    "color": "red", 
                    "label": "7"
                }}],
                "intervals": 10,
                "title": "Number Line 0-10"
            }}
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=extraction_prompt)])
            
            data = json.loads(response.content)
            return data
            
        except Exception as e:
            logger.error(f"Error extracting number line data: {e}")
            return None
    
    async def _extract_ruler_data(self, state: ImageGenerationState) -> Optional[Dict[str, Any]]:
        """Extract ruler parameters from question"""
        try:
            extraction_prompt = f"""
            Extract measurement parameters from this question:
            
            Question: {state['question']}
            
            Determine ruler length, unit, and measurements to highlight.
            Return JSON with length, unit, highlight_measurements.
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=extraction_prompt)])
            
            data = json.loads(response.content)
            return data
            
        except Exception as e:
            logger.error(f"Error extracting ruler data: {e}")
            return None
    
    async def _extract_clock_data(self, state: ImageGenerationState) -> Optional[Dict[str, Any]]:
        """Extract time from question"""
        try:
            extraction_prompt = f"""
            Extract time information from this question:
            
            Question: {state['question']}
            
            Determine what time should be shown on the clock.
            Return JSON with hour (0-23) and minute (0-59).
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=extraction_prompt)])
            
            data = json.loads(response.content)
            return data
            
        except Exception as e:
            logger.error(f"Error extracting clock data: {e}")
            return None
    
    async def _extract_venn_data(self, state: ImageGenerationState) -> Optional[Dict[str, Any]]:
        """Extract Venn diagram data from question"""
        try:
            
            
            class VennDiagramData(BaseModel):
                sets_data: Optional[Dict[str, List[int]]] = {}
                title: Optional[str] = None
                colors: Optional[List[str]] = None
                background_color: Optional[str] = "white"
            
            messages = [{
                "role": "user",
                "content": f"""Extract Venn diagram data from this question:
                
Question: {state['question']}

IMPORTANT: All set names/labels MUST be in the SAME LANGUAGE as the question text.

CRITICAL: Create ONLY the main sets mentioned in the question. DO NOT create separate sets for intersections like "overlap", "both", "all three", etc. Intersections are created automatically when sets share elements.

For Venn diagrams:
- Identify the main categories/groups from the question (e.g., "Math", "Science", "Cricket", "Football")  
- Create sets with numbered elements to represent totals
- Make elements overlap between sets to show intersections
- Use descriptive names for the main sets only (in the same language as the question)

Example for "10 like A, 8 like B, 3 like both":
- sets_data: {{"A": [1,2,3,4,5,6,7,8,9,10], "B": [8,9,10,11,12,13,14,15]}}
- This creates: A-only=7, intersection=3, B-only=5

WRONG: Don't create {{"A": [...], "B": [...], "Both": [...]}}
RIGHT: Create {{"A": [...], "B": [...]}} with shared elements

Maximum 5 main sets. Title should be null or descriptive.
"""
            }]
            
            result = produce_structured_response_openai(
                messages=messages, 
                structure_model=VennDiagramData,
                model="gpt-5",
                instructions=None,
                temperature=1.0,
                max_output_tokens=None
            )
            
            # Convert lists to sets for venn library
            sets_data_converted = {}
            for set_name, elements in result.sets_data.items():
                sets_data_converted[set_name] = set(elements)
            
            data = {
                "sets_data": sets_data_converted,
                "title": result.title,
                "colors": result.colors,
                "background_color": result.background_color
            }
            
            logger.info(f"Extracted Venn data: {data}")
            return data
            
        except Exception as e:
            logger.error(f"Error extracting Venn data: {e}")
            return None
    
    async def generate_image_for_question(
        self,
        question: str,
        grade: int = 5,
        subject: str = "mathematics"
    ) -> Optional[str]:
        """Main entry point to generate image for a question"""
        
        initial_state = ImageGenerationState(
            question=question,
            question_type="unknown",
            grade=grade,
            subject=subject,
            image_type=None,
            image_prompt=None,
            generated_images=None,
            quality_check_results=None,
            final_image_url=None,
            retry_count=0,
            max_retries=1,
            error=None
        )
        
        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)
            return final_state.get("final_image_url")
            
        except Exception as e:
            logger.error(f"Error in image generation workflow: {e}")
            return None