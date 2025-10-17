from __future__ import annotations
import json
import random
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.question_gen_v1.module_2 import ExtractedPattern

@dataclass
class GeneratedQuestion:
    question_id: str
    pattern_id: str
    subject: str
    topic: str
    grade: Optional[int]
    difficulty: str
    language: str
    question_text: str
    parameter_values: Dict[str, Any]
    answer: str
    working_steps: List[str] = field(default_factory=list)
    rationale: str = ""
    constraints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

def _safe_list(x) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [str(x)]

def _seed_from(pattern_id: str) -> int:
    if not pattern_id:
        return 1337
    return int.from_bytes(pattern_id.encode("utf-8"), "little") % (2**31 - 1)

def sample_params(pattern: ExtractedPattern, question_index: int = 0) -> Dict[str, Any]:
    # Include question_index to ensure diverse numbers across questions using the same pattern
    base_seed = _seed_from(pattern.pattern_id)
    diverse_seed = base_seed + question_index * 7919  # Prime number for better distribution
    rnd = random.Random(diverse_seed)
    out: Dict[str, Any] = {}

    # Enhanced parameter generation with intelligent defaults for missing ranges
    for name, bounds in (pattern.parameter_ranges or {}).items():
        if bounds is None or len(bounds) < 2:
            # Generate smart defaults based on parameter name and question index
            val = _generate_smart_default(name, question_index, rnd, pattern)
        else:
            lo, hi = bounds
            if lo is None and hi is None:
                # Generate smart defaults when both bounds are missing
                val = _generate_smart_default(name, question_index, rnd, pattern)
            elif lo is None:
                if hi is not None:
                    try:
                        val = int(hi)
                    except (ValueError, TypeError):
                        val = _generate_smart_default(name, question_index, rnd, pattern)
                else:
                    val = _generate_smart_default(name, question_index, rnd, pattern)
            elif hi is None:
                if lo is not None:
                    try:
                        val = int(lo)
                    except (ValueError, TypeError):
                        val = _generate_smart_default(name, question_index, rnd, pattern)
                else:
                    val = _generate_smart_default(name, question_index, rnd, pattern)
            else:
                try:
                    # Handle float ranges for calculus
                    if '.' in str(lo) or '.' in str(hi):
                        lo_f, hi_f = float(lo), float(hi)
                        val = round(rnd.uniform(lo_f, hi_f), 2) if lo_f != hi_f else lo_f
                    else:
                        lo_i, hi_i = int(lo), int(hi)
                        val = lo_i if lo_i == hi_i else rnd.randint(lo_i, hi_i)
                except (ValueError, TypeError):
                    # Fallback to smart defaults if conversion fails
                    val = _generate_smart_default(name, question_index, rnd, pattern)
        out[name] = val

    # If no parameters were generated, extract from template
    if not out and pattern.template:
        out = _extract_params_from_template(pattern.template, question_index, rnd, pattern)

    return out

def _generate_smart_default(param_name: str, question_index: int, rnd, pattern=None) -> Any:
    """Generate intelligent default values based on parameter name patterns and context"""
    name_lower = param_name.lower()

    # Base value that changes with question index for diversity
    base_variation = (question_index * 3) + 1

    # Check if this is a calculus/advanced math pattern
    is_calculus = pattern and pattern.topic and 'calculus' in pattern.topic.lower()

    # Text-based mathematical parameters for calculus
    if 'expression' in name_lower or 'formula' in name_lower:
        expressions = [
            f"{rnd.randint(2,5)}x^2 + {rnd.randint(1,10)}x + {rnd.randint(1,20)}",
            f"{rnd.randint(1,4)}x^3 - {rnd.randint(2,8)}x^2 + {rnd.randint(1,15)}",
            f"sin({rnd.randint(2,4)}x) + {rnd.randint(1,5)}cos(x)",
            f"e^({rnd.randint(1,3)}x) + {rnd.randint(2,10)}",
            f"ln({rnd.randint(2,5)}x) + {rnd.randint(1,8)}x",
            f"{rnd.randint(2,6)}x^2 - {rnd.randint(3,12)}x",
        ]
        return rnd.choice(expressions)

    elif 'operation' in name_lower:
        operations = ['derivative', 'integral', 'limit', 'maximum', 'minimum',
                     'rate of change', 'area under curve', 'tangent line']
        return rnd.choice(operations)

    elif 'characteristic' in name_lower:
        characteristics = ['velocity', 'acceleration', 'rate of change',
                          'maximum value', 'minimum value', 'inflection point',
                          'average rate', 'instantaneous rate']
        return rnd.choice(characteristics)

    elif 'physical_quantity' in name_lower:
        quantities = ['position', 'velocity', 'temperature', 'pressure',
                     'concentration', 'population', 'profit', 'cost']
        return rnd.choice(quantities)

    elif 'field_of_study' in name_lower or 'application' in name_lower:
        fields = ['physics', 'economics', 'biology', 'engineering',
                 'chemistry', 'environmental science', 'medicine', 'finance']
        return rnd.choice(fields)

    elif 'value' in name_lower or 'bound' in name_lower:
        # For calculus, use smaller, cleaner numbers
        if is_calculus:
            return round(rnd.uniform(0.5, 5.0), 1)
        else:
            return rnd.randint(1 + base_variation, 20 + base_variation)

    # Numeric parameters
    elif any(word in name_lower for word in ['number', 'num', 'count', 'quantity']):
        return rnd.randint(1 + base_variation, 20 + base_variation)
    elif any(word in name_lower for word in ['age', 'year']):
        return rnd.randint(5 + base_variation, 25 + base_variation)
    elif any(word in name_lower for word in ['price', 'cost', 'money', 'dollar']):
        return rnd.randint(10 + base_variation, 100 + base_variation)
    elif any(word in name_lower for word in ['time', 'hour', 'minute']):
        if is_calculus:
            return round(rnd.uniform(0.5, 10.0), 1)
        return rnd.randint(1 + base_variation, 12 + base_variation)
    elif any(word in name_lower for word in ['distance', 'length', 'height']):
        return rnd.randint(5 + base_variation, 50 + base_variation)
    elif any(word in name_lower for word in ['weight', 'mass']):
        return rnd.randint(1 + base_variation, 30 + base_variation)
    else:
        # Generic diverse default
        return rnd.randint(2 + base_variation, 15 + base_variation)

def _extract_params_from_template(template: str, question_index: int, rnd, pattern=None) -> Dict[str, Any]:
    """Extract parameter names from template and generate diverse values"""
    import re
    params = {}
    placeholders = re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', template)

    for param_name in placeholders:
        params[param_name] = _generate_smart_default(param_name, question_index, rnd, pattern)

    return params

def render_template(template: str, params: Dict[str, Any]) -> str:
    def repl(m: re.Match) -> str:
        key = m.group(1)
        return str(params.get(key, f"{{{key}}}"))
    return PLACEHOLDER_RE.sub(repl, template)

def extract_instructional_text(template: str) -> str:
    m = re.search(r"Instructional Content:\s*(.*)", template, flags=re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else template.strip()

def first_json_block(text: str) -> Optional[dict]:
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None
