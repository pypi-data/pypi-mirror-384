# one_file_wolfram_solver.py
# Minimal end-to-end Wolfram|Alpha solver for a GeneratedQuestion.
# Uses app id EKTPA9X3JY by default (override via WOLFRAM_APP_ID env var or function arg).

from typing import Optional, List, Tuple
import os
import json
import urllib.parse
import urllib.request

from src.wolfram.types import WolframSolveResponse


# --- Minimal Wolfram|Alpha glue ---

WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID", "EKTPA9X3JY")
WOLFRAM_ENDPOINT = "https://api.wolframalpha.com/v2/query"


def _http_get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _build_url(input_text: str, podstate: Optional[str] = None, app_id: Optional[str] = None) -> str:
    params = {
        "appid": app_id or WOLFRAM_APP_ID,
        "input": input_text,
        "output": "json",
        "format": "plaintext",
        "reinterpret": "true",
        "scantimeout": "10",
        "podtimeout": "15",
        "parsetimeout": "15",
    }
    if podstate:
        params["podstate"] = podstate
    return f"{WOLFRAM_ENDPOINT}?{urllib.parse.urlencode(params)}"


def _pods(result: dict) -> List[dict]:
    q = result.get("queryresult", {})
    return q.get("pods", []) if q.get("success") else []


def _text_from_pod(pod: dict) -> str:
    texts = []
    for sp in pod.get("subpods", []):
        pt = (sp.get("plaintext") or "").strip()
        if pt:
            texts.append(pt)
            continue
        img = sp.get("img") or {}
        alt = (img.get("alt") or "").strip()
        if alt:
            texts.append(alt)
    return "\n".join(texts).strip()


def _find_pod_by_titles(pods: List[dict], titles: List[str]) -> Optional[dict]:
    wanted = {t.lower() for t in titles}
    for pod in pods:
        t = (pod.get("title") or pod.get("id") or "").lower()
        if t in wanted:
            return pod
    # fallback: substring match
    for pod in pods:
        t = (pod.get("title") or pod.get("id") or "").lower()
        if any(w in t for w in wanted):
            return pod
    return None


def _extract_rationale(pods: List[dict]) -> str:
    pod = _find_pod_by_titles(pods, ["Input interpretation", "Input"])
    return _text_from_pod(pod) if pod else ""


def _extract_answer(pods: List[dict]) -> str:
    priority = [
        "Result", "Results", "Final result", "Exact result", "Decimal approximation",
        "Solution", "Solutions", "Value", "Numeric approximation",
        "Definite integral", "Indefinite integral",
        "Chemical names and formulas", "Molar mass", "Balance", "Approximate forms"
    ]
    pod = _find_pod_by_titles(pods, priority)
    if pod:
        txt = _text_from_pod(pod)
        if txt:
            return txt
    # next: first primary pod
    for pod in pods:
        if pod.get("primary"):
            t = _text_from_pod(pod)
            if t:
                return t
    # last resort: first pod with any text
    for pod in pods:
        t = _text_from_pod(pod)
        if t:
            return t
    return ""


def _find_step_state(pods: List[dict]) -> Optional[str]:
    # Catch variants: "step-by-step", "show steps", "solution steps"
    keys = ("step-by-step", "step by step", "show steps", "solution steps")
    for pod in pods:
        for state in (pod.get("states") or []):
            name = (state.get("name") or "").lower()
            if any(k in name for k in keys) and state.get("input"):
                return state["input"]
    return None


def _extract_steps_from_pods(pods: List[dict]) -> List[str]:
    step_like = [
        "Step-by-step solution", "Steps", "Possible intermediate steps",
        "Derivation", "Solution", "Balancing steps", "Proof", "Work"
    ]

    # First try to find dedicated step pods
    pod = _find_pod_by_titles(pods, step_like)
    if pod:
        text = _text_from_pod(pod)
        if text:
            lines = [ln.strip(" •\t-→") for ln in text.splitlines()]
            steps = [ln for ln in lines if ln]
            if steps:
                return steps

    # If no dedicated step pod, extract meaningful info from all pods
    # Skip Input and Result pods as they're usually just the question and final answer
    steps = []
    skip_titles = {"input", "result", "input interpretation"}

    for pod in pods:
        title = (pod.get("title") or "").lower()
        pod_id = (pod.get("id") or "").lower()

        # Skip input and pure result pods
        if title in skip_titles or pod_id in skip_titles:
            continue

        # Extract meaningful intermediate information
        if title and title not in ["", "none"]:
            pod_text = _text_from_pod(pod)
            if pod_text and pod_text not in steps:
                # Add pod title as context if it's informative
                if title not in ["result", "input"] and "step" not in title.lower():
                    step_entry = f"{pod['title']}: {pod_text}"
                else:
                    step_entry = pod_text

                # Split multi-line responses into separate steps
                for line in step_entry.splitlines():
                    clean_line = line.strip()
                    if clean_line and clean_line not in steps:
                        steps.append(clean_line)

    return steps


def wolfram_solve(question_text: str,
                  subject: Optional[str] = None,
                  app_id: Optional[str] = None) -> WolframSolveResponse:
    """
    Minimal end-to-end function.
    Calls Wolfram|Alpha, and returns (rationale, working_steps, answer).
    Also updates gq.rationale / gq.working_steps / gq.answer in place.
    """
    try:
        
        subj = (subject or "").strip()
        qtext = question_text.strip()
        # Light-touch hinting of subject without changing semantics:
        # Prepend "Calculate:" for mathematical queries to avoid encyclopedic results
        prefix = "Calculate: " if subj == "mathematics" else ""
        input_text = f"{prefix}{qtext}" if not subj else f"{prefix}{qtext} ({subj})"

        # First pass
        data = _http_get(_build_url(input_text, app_id=app_id))
        pods = _pods(data)

        # Try to extract steps from initial response
        steps = _extract_steps_from_pods(pods)

        # Optional second pass to retrieve step-by-step, if available
        step_state = _find_step_state(pods)
        if step_state:
            steps_data = _http_get(_build_url(input_text, podstate=step_state, app_id=app_id))
            detailed_steps = _extract_steps_from_pods(_pods(steps_data))
            # Use detailed steps if they're more comprehensive
            if len(detailed_steps) > len(steps):
                steps = detailed_steps

        rationale = _extract_rationale(pods)
        answer = _extract_answer(pods)

        # if neither answer nor steps found, return empty
        if not answer and not steps:
            return WolframSolveResponse(rationale="", working_steps=[], answer="")

        return WolframSolveResponse(
            rationale=rationale,
            working_steps=steps,
            answer=answer,
        )
    except Exception as e:
        print(f"Wolfram solve failed: {e}")
        return WolframSolveResponse(rationale="", working_steps=[], answer="")
