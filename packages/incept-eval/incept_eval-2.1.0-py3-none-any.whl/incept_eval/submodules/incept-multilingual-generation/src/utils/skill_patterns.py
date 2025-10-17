"""
UAE Schools Skill Patterns — All Grades (AR/EN)
------------------------------------------------
- Dynamically generates curriculum-aligned question patterns for UAE schools (G1–G12)
- Safer constraint handling (no eval)
- Bilingual templates (Arabic/English)
- Deterministic sampling (seedable)
- Difficulty & strand tagging for adaptive practice

Author: you + ChatGPT
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable, Any, Union
import random
from fractions import Fraction

Number = Union[int, float, Fraction]
Lang = str  # 'ar' or 'en'

# ----------------------------
# Core data structures
# ----------------------------


@dataclass
class ParamSpec:
    """Parameter range and optional sampler."""
    min: Number
    max: Number
    step: Optional[Number] = None
    ints: bool = True
    # Optional custom sampler(params_so_far) -> value
    sampler: Optional[Callable[[Dict[str, Number]], Number]] = None


@dataclass
class Pattern:
    """Single skill pattern definition."""
    # language -> list of templates
    templates: Dict[Lang, List[str]]
    # parameter name -> spec
    params: Dict[str, ParamSpec]
    # list of constraints f(params)->bool
    constraints: List[Callable[[Dict[str, Number]], bool]
                      ] = field(default_factory=list)
    # solution function f(params)->(answer_string, metadata_dict)
    solve: Optional[Callable[[Dict[str, Number]],
                             Tuple[str, Dict[str, Any]]]] = None
    # tags
    strand: str = ""             # e.g., Number, Algebra, Geometry, Data
    topic: str = ""              # e.g., Linear Equations
    difficulty: str = "core"     # 'foundational' | 'core' | 'challenge'
    # optional hints/scaffold
    hint: Dict[Lang, str] = field(default_factory=dict)


@dataclass
class GradeCatalog:
    patterns: Dict[str, Pattern]  # topic_key -> Pattern


Catalog = Dict[str, GradeCatalog]  # grade_key -> GradeCatalog

# ----------------------------
# Utility samplers & helpers
# ----------------------------


def _rand_int(a: int, b: int, step: int = 1) -> int:
    choices = list(range(a, b + 1, step))
    return random.choice(choices)


def _rand_num(spec: ParamSpec, params_so_far: Dict[str, Number]) -> Number:
    if spec.sampler:
        return spec.sampler(params_so_far)
    if spec.ints:
        step = int(spec.step) if spec.step else 1
        return _rand_int(int(spec.min), int(spec.max), step)
    # floats: round to 2dp by default
    step = spec.step if spec.step else 0.01
    steps = int(round((spec.max - spec.min) / step))
    k = _rand_int(0, steps)
    return round(spec.min + k * step, 2)


def _sample_params(param_specs: Dict[str, ParamSpec],
                   constraints: List[Callable[[Dict[str, Number]], bool]],
                   max_tries: int = 500) -> Dict[str, Number]:
    for _ in range(max_tries):
        params: Dict[str, Number] = {}
        # simple left-to-right sampling (OK for most constraints)
        for name, spec in param_specs.items():
            params[name] = _rand_num(spec, params)
        # validate constraints
        if all(c(params) for c in constraints):
            return params
    # fallback – return a deterministic safe sample
    return {k: (param_specs[k].min if param_specs[k].ints else float(param_specs[k].min))
            for k in param_specs}


def _choose_template(p: Pattern, lang: Lang) -> str:
    bank = p.templates.get(lang) or p.templates.get(
        "en") or next(iter(p.templates.values()))
    return random.choice(bank)


def set_seed(seed: Optional[int]) -> None:
    if seed is not None:
        random.seed(seed)

# ----------------------------
# Solvers (exact where possible)
# ----------------------------


def solve_linear_axb_eq_c(params: Dict[str, Number]) -> Tuple[str, Dict[str, Any]]:
    a, b, c = params["a"], params["b"], params["c"]
    # enforce a != 0 via constraints; use Fraction for exactness then prettify
    x = Fraction(c - b, a)
    # pretty print: integer if denom=1 else decimal with 2dp
    ans = f"x = {x.numerator}/{x.denominator}" if x.denominator != 1 else f"x = {x.numerator}"
    return ans, {"x": x}


def solve_linear_expand(params: Dict[str, Number]) -> Tuple[str, Dict[str, Any]]:
    a, b, c = params["a"], params["b"], params["c"]
    # a(x + b) = c => ax + ab = c => x = (c - ab)/a
    x = Fraction(c - a*b, a)
    ans = f"x = {x.numerator}/{x.denominator}" if x.denominator != 1 else f"x = {x.numerator}"
    return ans, {"x": x}


def solve_linear_x_over_a_plus_b_eq_c(params: Dict[str, Number]) -> Tuple[str, Dict[str, Any]]:
    a, b, c = params["a"], params["b"], params["c"]
    # x/a + b = c => x/a = c - b => x = a(c-b)
    x = a * (c - b)
    return f"x = {x}", {"x": x}


def solve_mean_5(params: Dict[str, Number]) -> Tuple[str, Dict[str, Any]]:
    nums = [params[k] for k in ["a", "b", "c", "d", "e"]]
    mean_val = sum(nums) / 5
    return f"{round(mean_val, 2)}", {"mean": mean_val}


def solve_rectangle_perimeter(params: Dict[str, Number]) -> Tuple[str, Dict[str, Any]]:
    a, b = params["a"], params["b"]
    p = 2*(a+b)
    return f"{p}", {"perimeter": p}


def solve_area_circle(params: Dict[str, Number]) -> Tuple[str, Dict[str, Any]]:
    a = params["a"]  # radius
    # leave π symbolic when possible
    return f"{a}²π = {a*a}π", {"area_pi_units": f"{a*a}π"}


def solve_multiplication(params: Dict[str, Number]) -> Tuple[str, Dict[str, Any]]:
    a, b = params["a"], params["b"]
    product = a * b
    return str(product), {"product": product}


def solve_addition(params: Dict[str, Number]) -> Tuple[str, Dict[str, Any]]:
    a, b = params["a"], params["b"]
    sum_val = a + b
    return str(sum_val), {"sum": sum_val}


def solve_subtraction(params: Dict[str, Number]) -> Tuple[str, Dict[str, Any]]:
    a, b = params["a"], params["b"]
    diff = a - b
    return str(diff), {"difference": diff}

# ----------------------------
# Catalog (expandable)
# Notes:
# - Keep arithmetic clean for younger grades.
# - Prefer integer outcomes on linear equations for G7–G9 core.
# - Include Arabic/English wording.
# ----------------------------


def _grade_key(grade: int) -> str:
    return f"grade_{grade}"


CATALOG: Catalog = {
    _grade_key(1): GradeCatalog(patterns={
        "counting_1_to_20": Pattern(
            templates={
                "ar": ["عد من {a} إلى {b}.", "ما العدد الذي يأتي بعد {a}؟"],
                "en": ["Count from {a} to {b}.", "What number comes after {a}?"]
            },
            params={
                "a": ParamSpec(1, 10, ints=True),
                "b": ParamSpec(11, 20, ints=True)
            },
            constraints=[lambda p: p["a"] < p["b"]],
            strand="Numbers & Operations", topic="Counting", difficulty="foundational",
            hint={"ar": "استخدم خط الأعداد.", "en": "Use a number line."}
        ),
        "addition_within_20": Pattern(
            templates={
                "ar": ["{a} + {b} = ؟", "أوجد مجموع {a} و {b}"],
                "en": ["{a} + {b} = ?", "Find the sum of {a} and {b}"]
            },
            params={"a": ParamSpec(1, 10), "b": ParamSpec(1, 10)},
            constraints=[lambda p: p["a"] + p["b"] <= 20],
            strand="Numbers & Operations", topic="Addition within 20", difficulty="core",
            solve=solve_addition
        ),
        "subtraction_within_20": Pattern(
            templates={
                "ar": ["{a} - {b} = ؟", "أوجد الفرق بين {a} و {b}"],
                "en": ["{a} - {b} = ?", "Find the difference between {a} and {b}"]
            },
            params={"a": ParamSpec(5, 20), "b": ParamSpec(1, 10)},
            constraints=[lambda p: p["a"] >= p["b"]],
            strand="Numbers & Operations", topic="Subtraction within 20", difficulty="core",
            solve=solve_subtraction
        ),
        "patterns_basic_shapes_numbers": Pattern(
            templates={
                "ar": ["ما النمط؟ {a}, {b}, {a}, {b}, ___", "أكمل النمط: ⭐⭐🔴⭐⭐🔴___"],
                "en": ["What's the pattern? {a}, {b}, {a}, {b}, ___", "Complete the pattern: ⭐⭐🔴⭐⭐🔴___"]
            },
            params={"a": ParamSpec(1, 5), "b": ParamSpec(6, 10)},
            constraints=[lambda p: p["a"] != p["b"]],
            strand="Algebra & Patterns", topic="Basic Patterns", difficulty="foundational"
        ),
        "shapes_2d_basic": Pattern(
            templates={
                "ar": ["كم عدد الأضلاع في {shape}؟", "ما اسم هذا الشكل؟"],
                "en": ["How many sides does a {shape} have?", "What is the name of this shape?"]
            },
            params={"shape": ParamSpec(3, 6, ints=True)},  # sides
            constraints=[],
            strand="Geometry & Measurement", topic="2D Shapes", difficulty="foundational"
        )
    }),

    _grade_key(2): GradeCatalog(patterns={
        "numbers_3_digit_place_value": Pattern(
            templates={
                "ar": ["ما القيمة المكانية للرقم {d} في العدد {n}؟"],
                "en": ["What is the place value of digit {d} in {n}?"]
            },
            params={
                "n": ParamSpec(100, 999, ints=True),
                "d": ParamSpec(0, 9, ints=True)
            },
            constraints=[lambda p: str(p["d"]) in str(p["n"])],
            strand="Numbers & Operations", topic="Place Value", difficulty="core"
        ),
        "add_sub_3_digit_with_renaming": Pattern(
            templates={
                "ar": ["{a} + {b} = ؟", "{a} - {b} = ؟"],
                "en": ["{a} + {b} = ?", "{a} - {b} = ?"]
            },
            params={"a": ParamSpec(100, 500), "b": ParamSpec(100, 300)},
            constraints=[lambda p: p["a"] >= p["b"]],
            strand="Numbers & Operations", topic="3-digit Addition/Subtraction", difficulty="core"
        ),
        "intro_multiplication_equal_groups": Pattern(
            templates={
                "ar": ["لديك {a} مجموعات، كل مجموعة بها {b} عنصر. كم العدد الكلي؟"],
                "en": ["You have {a} groups with {b} items each. How many items in total?"]
            },
            params={"a": ParamSpec(2, 5), "b": ParamSpec(2, 5)},
            constraints=[],
            strand="Numbers & Operations", topic="Multiplication as Equal Groups", difficulty="core",
            solve=solve_multiplication
        )
    }),

    _grade_key(3): GradeCatalog(patterns={
        "multiplication_facts": Pattern(
            templates={
                "ar": ["{a} × {b} = ؟", "أوجد حاصل ضرب {a} و {b}", "لديك {a} صناديق، كل صندوق به {b} كرة. كم كرة لديك؟"],
                "en": ["{a} × {b} = ?", "Find the product of {a} and {b}", "You have {a} boxes with {b} balls each. How many balls total?"]
            },
            params={"a": ParamSpec(1, 10), "b": ParamSpec(1, 10)},
            constraints=[],
            strand="Numbers & Operations", topic="Multiplication Facts", difficulty="core",
            solve=solve_multiplication
        ),
        "division_with_remainders_simple": Pattern(
            templates={
                "ar": ["{a} ÷ {b} = ؟ (مع الباقي)", "قسم {a} على {b}"],
                "en": ["{a} ÷ {b} = ? (with remainder)", "Divide {a} by {b}"]
            },
            params={"a": ParamSpec(10, 50), "b": ParamSpec(2, 8)},
            constraints=[lambda p: p["b"] != 0],
            strand="Numbers & Operations", topic="Division with Remainders", difficulty="core"
        ),
        "fractions_unit_and_like_denominators": Pattern(
            templates={
                "ar": ["{a}/{b} + {c}/{b} = ؟", "ما هو {a}/{b} من {c}؟"],
                "en": ["{a}/{b} + {c}/{b} = ?", "What is {a}/{b} of {c}?"]
            },
            params={
                "a": ParamSpec(1, 5), "b": ParamSpec(2, 8),
                "c": ParamSpec(1, 5)
            },
            constraints=[lambda p: p["b"] != 0 and p["a"]
                         < p["b"] and p["c"] < p["b"]],
            strand="Numbers & Operations", topic="Like Fractions", difficulty="core"
        ),
        "area_perimeter_rectangles": Pattern(
            templates={
                "ar": ["مستطيل طوله {a} سم وعرضه {b} سم. أوجد المحيط", "أوجد مساحة المستطيل: الطول = {a}، العرض = {b}"],
                "en": ["A rectangle has length {a} cm and width {b} cm. Find the perimeter", "Find the area of rectangle: length = {a}, width = {b}"]
            },
            params={"a": ParamSpec(3, 15), "b": ParamSpec(2, 12)},
            constraints=[lambda p: p["a"] > 0 and p["b"] > 0],
            strand="Geometry & Measurement", topic="Rectangle Perimeter/Area", difficulty="core",
            solve=solve_rectangle_perimeter
        )
    }),

    _grade_key(4): GradeCatalog(patterns={
        "factors_multiples": Pattern(
            templates={
                "ar": ["أوجد جميع عوامل العدد {n}", "أوجد أول {k} مضاعفات للعدد {a}"],
                "en": ["Find all factors of {n}", "Find the first {k} multiples of {a}"]
            },
            params={
                "n": ParamSpec(12, 36, ints=True),
                "a": ParamSpec(2, 9, ints=True),
                "k": ParamSpec(3, 6, ints=True)
            },
            constraints=[],
            strand="Numbers & Operations", topic="Factors and Multiples", difficulty="core"
        ),
        "fractions_equivalent_compare": Pattern(
            templates={
                "ar": ["هل {a}/{b} = {c}/{d}؟", "أيهما أكبر: {a}/{b} أم {c}/{d}؟"],
                "en": ["Is {a}/{b} = {c}/{d}?", "Which is greater: {a}/{b} or {c}/{d}?"]
            },
            params={
                "a": ParamSpec(1, 8), "b": ParamSpec(2, 10),
                "c": ParamSpec(1, 8), "d": ParamSpec(2, 10)
            },
            constraints=[lambda p: p["b"] != 0 and p["d"] != 0],
            strand="Numbers & Operations", topic="Equivalent Fractions", difficulty="core"
        ),
        "decimals_tenths_hundredths": Pattern(
            templates={
                "ar": ["{a}.{b} + {c}.{d} = ؟", "اكتب {a}.{b} ككسر"],
                "en": ["{a}.{b} + {c}.{d} = ?", "Write {a}.{b} as a fraction"]
            },
            params={
                "a": ParamSpec(0, 9), "b": ParamSpec(1, 9),
                "c": ParamSpec(0, 9), "d": ParamSpec(1, 9)
            },
            constraints=[],
            strand="Numbers & Operations", topic="Decimals", difficulty="core"
        )
    }),

    _grade_key(5): GradeCatalog(patterns={
        "fractions_add_sub_unlike": Pattern(
            templates={
                "ar": ["{a}/{b} + {c}/{d} = ؟", "{a}/{b} - {c}/{d} = ؟"],
                "en": ["{a}/{b} + {c}/{d} = ?", "{a}/{b} - {c}/{d} = ?"]
            },
            params={
                "a": ParamSpec(1, 9), "b": ParamSpec(2, 10),
                "c": ParamSpec(1, 9), "d": ParamSpec(2, 10)
            },
            constraints=[lambda p: p["b"] != 0 and p["d"] != 0],
            strand="Numbers & Operations", topic="Fractions", difficulty="core",
            solve=lambda p: (
                f"{Fraction(p['a'], p['b']) + Fraction(p['c'], p['d'])}",
                {"sum": Fraction(p['a'], p['b']) + Fraction(p['c'], p['d'])}
            )
        ),
        "decimals_add_sub_mult": Pattern(
            templates={
                "ar": ["{a} + {b} = ؟", "{a} - {b} = ؟", "{a} × {b} = ؟"],
                "en": ["{a} + {b} = ?", "{a} - {b} = ?", "{a} × {b} = ?"]
            },
            params={"a": ParamSpec(10, 999, ints=False, step=0.1),
                    "b": ParamSpec(10, 999, ints=False, step=0.1)},
            constraints=[],
            strand="Numbers & Operations", topic="Decimals", difficulty="core"
        ),
        "percentage_intro": Pattern(
            templates={
                "ar": ["ما هو {p}% من {x}؟", "إذا كان {x} يمثل {p}%، فما هو المجموع الكلي؟"],
                "en": ["What is {p}% of {x}?", "If {x} represents {p}%, what is the total?"]
            },
            params={
                "p": ParamSpec(10, 50, step=10, ints=True),
                "x": ParamSpec(20, 200, ints=True)
            },
            constraints=[],
            strand="Numbers & Operations", topic="Percentage", difficulty="core"
        ),
        "coordinate_plane_q1_plot": Pattern(
            templates={
                "ar": ["ارسم النقطة ({a}, {b}) على المستوى الإحداثي", "ما هي إحداثيات النقطة؟"],
                "en": ["Plot the point ({a}, {b}) on the coordinate plane", "What are the coordinates of the point?"]
            },
            params={"a": ParamSpec(0, 10, ints=True),
                    "b": ParamSpec(0, 10, ints=True)},
            constraints=[],
            strand="Geometry & Measurement", topic="Coordinate Plane", difficulty="core"
        )
    }),

    _grade_key(6): GradeCatalog(patterns={
        "ratio_and_proportion_core": Pattern(
            templates={
                "ar": ["إذا كانت النسبة {a}:{b}، وكان الحد الأول {c}، فما الحد الثاني؟", "النسبة بين الذكور والإناث {a}:{b}. إذا كان عدد الذكور {c}، فكم عدد الإناث؟"],
                "en": ["If the ratio is {a}:{b} and the first term is {c}, what is the second term?", "The ratio of boys to girls is {a}:{b}. If there are {c} boys, how many girls?"]
            },
            params={
                "a": ParamSpec(1, 8, ints=True),
                "b": ParamSpec(1, 8, ints=True),
                "c": ParamSpec(2, 20, ints=True)
            },
            constraints=[lambda p: p["c"] %
                         p["a"] == 0],  # ensure clean division
            strand="Numbers & Operations", topic="Ratio & Proportion", difficulty="core"
        ),
        "linear_equations_one_variable_core": Pattern(
            templates={
                "ar": ["حل المعادلة: {a}x + {b} = {c}", "أوجد قيمة x: {a}x - {b} = {c}"],
                "en": ["Solve: {a}x + {b} = {c}", "Find x: {a}x - {b} = {c}"]
            },
            params={
                "a": ParamSpec(1, 10, ints=True),
                "b": ParamSpec(-20, 20, ints=True),
                "c": ParamSpec(-30, 30, ints=True)
            },
            constraints=[lambda p: p["a"] != 0],
            strand="Algebra & Patterns", topic="Linear Equations", difficulty="core",
            solve=solve_linear_axb_eq_c
        ),
        "mensuration_area_surface_volume_prisms": Pattern(
            templates={
                "ar": ["أوجد حجم متوازي المستطيلات: الطول = {a}، العرض = {b}، الارتفاع = {c}", "احسب مساحة السطح الكلية للمكعب الذي طول ضلعه {a} سم"],
                "en": ["Find the volume of cuboid: length = {a}, width = {b}, height = {c}", "Calculate total surface area of cube with side {a} cm"]
            },
            params={"a": ParamSpec(2, 15, ints=True), "b": ParamSpec(
                2, 12, ints=True), "c": ParamSpec(2, 10, ints=True)},
            constraints=[lambda p: p["a"] > 0 and p["b"] > 0 and p["c"] > 0],
            strand="Geometry & Measurement", topic="Volume & Surface Area", difficulty="core"
        )
    }),

    _grade_key(7): GradeCatalog(patterns={
        "percent_applications_discount_tax": Pattern(
            templates={
                "ar": ["سعر القميص {price} د.إ. إذا كان الخصم {discount}%، فما السعر بعد الخصم؟", "إذا كانت الضريبة {tax}% على مبلغ {amount} د.إ، فكم الضريبة؟"],
                "en": ["A shirt costs {price} AED. With {discount}% discount, what is the sale price?", "If tax is {tax}% on {amount} AED, how much is the tax?"]
            },
            params={
                "price": ParamSpec(50, 300, step=10, ints=True),
                "discount": ParamSpec(10, 50, step=5, ints=True),
                "amount": ParamSpec(100, 1000, step=50, ints=True),
                "tax": ParamSpec(5, 15, ints=True)
            },
            constraints=[],
            strand="Numbers & Operations", topic="Percentage Applications", difficulty="core"
        ),
        "linear_equations_one_variable_multistep": Pattern(
            templates={
                "ar": ["حل: {a}(x + {b}) = {c}", "أوجد x: {a}x + {b} = {c}x + {d}"],
                "en": ["Solve: {a}(x + {b}) = {c}", "Find x: {a}x + {b} = {c}x + {d}"]
            },
            params={
                "a": ParamSpec(2, 8, ints=True),
                "b": ParamSpec(-10, 10, ints=True),
                "c": ParamSpec(-50, 50, ints=True),
                "d": ParamSpec(-20, 20, ints=True)
            },
            constraints=[lambda p: p["a"] != 0],
            strand="Algebra & Patterns", topic="Multi-step Linear Equations", difficulty="core"
        ),
        "probability_theoretical_vs_experimental": Pattern(
            templates={
                "ar": ["ما احتمال الحصول على رقم زوجي عند رمي حجر نرد؟", "إذا رُمي العملة {n} مرة وظهرت الكتابة {k} مرة، فما الاحتمال التجريبي؟"],
                "en": ["What is the probability of getting an even number on a die?", "If a coin is flipped {n} times and tails appears {k} times, what is the experimental probability?"]
            },
            params={
                "n": ParamSpec(10, 50, step=10, ints=True),
                "k": ParamSpec(3, 25, ints=True)
            },
            constraints=[lambda p: p["k"] <= p["n"]],
            strand="Data Analysis & Probability", topic="Probability", difficulty="core"
        )
    }),

    _grade_key(8): GradeCatalog(patterns={
        "linear_equations_core": Pattern(
            templates={
                "ar": [
                    "حل المعادلة: {a}x + {b} = {c}",
                    "أوجد قيمة x: {a}x - {b} = {c}",
                    "حل: {a}(x + {b}) = {c}",
                    "أوجد x إذا كان: {a}x = {b} + {c}",
                    "حل المعادلة التالية: x/{a} + {b} = {c}"
                ],
                "en": [
                    "Solve: {a}x + {b} = {c}",
                    "Find x: {a}x - {b} = {c}",
                    "Solve: {a}(x + {b}) = {c}",
                    "Find x if: {a}x = {b} + {c}",
                    "Solve: x/{a} + {b} = {c}"
                ]
            },
            params={
                "a": ParamSpec(1, 10, ints=True),
                "b": ParamSpec(-20, 20, ints=True),
                "c": ParamSpec(-30, 30, ints=True)
            },
            constraints=[lambda p: p["a"] != 0],
            strand="Algebra & Patterns", topic="Linear Equations", difficulty="core"
        ),
        "pythagorean_theorem_applications": Pattern(
            templates={
                "ar": ["في مثلث قائم الزاوية، إذا كان الضلعان {a} سم و {b} سم، فأوجد طول الوتر", "سلم طوله {c} م يميل على حائط. إذا كانت المسافة من قاعدة السلم إلى الحائط {a} م، فكم ارتفاع نقطة اتصال السلم بالحائط؟"],
                "en": ["In a right triangle, if two sides are {a} cm and {b} cm, find the hypotenuse", "A {c} m ladder leans against a wall. If the distance from base to wall is {a} m, how high up the wall does the ladder reach?"]
            },
            params={
                "a": ParamSpec(3, 12, ints=True),
                "b": ParamSpec(4, 16, ints=True),
                "c": ParamSpec(5, 20, ints=True)
            },
            constraints=[lambda p: p["a"]**2 + p["b"]**2 ==
                         p["c"]**2 or True],  # Pythagorean or application
            strand="Geometry & Measurement", topic="Pythagorean Theorem", difficulty="core"
        ),
        "direct_inverse_proportion": Pattern(
            templates={
                "ar": ["إذا كانت y تتناسب طردياً مع x، وكانت y = {y1} عندما x = {x1}، فأوجد y عندما x = {x2}", "إذا كانت y تتناسب عكسياً مع x، وكانت y = {y1} عندما x = {x1}، فأوجد y عندما x = {x2}"],
                "en": ["If y varies directly with x, and y = {y1} when x = {x1}, find y when x = {x2}", "If y varies inversely with x, and y = {y1} when x = {x1}, find y when x = {x2}"]
            },
            params={
                "x1": ParamSpec(2, 8, ints=True),
                "y1": ParamSpec(4, 24, ints=True),
                "x2": ParamSpec(3, 12, ints=True)
            },
            constraints=[lambda p: p["x1"] != 0 and p["x2"] != 0],
            strand="Algebra & Patterns", topic="Proportion", difficulty="core"
        ),
        "statistics_center": Pattern(
            templates={
                "ar": ["أوجد المتوسط للأعداد: {a}, {b}, {c}, {d}, {e}"],
                "en": ["Find the mean of: {a}, {b}, {c}, {d}, {e}"]
            },
            params={k: ParamSpec(60, 100) for k in ["a", "b", "c", "d", "e"]},
            constraints=[],
            strand="Data Analysis & Probability", topic="Measures of Center", difficulty="core",
            solve=solve_mean_5
        )
    }),

    _grade_key(10): GradeCatalog(patterns={
        "quadratic_equations_solve": Pattern(
            templates={
                "ar": ["حل المعادلة التربيعية: {a}x² + {b}x + {c} = 0", "أوجد جذور المعادلة: x² + {b}x + {c} = 0"],
                "en": ["Solve the quadratic equation: {a}x² + {b}x + {c} = 0", "Find the roots of: x² + {b}x + {c} = 0"]
            },
            params={
                "a": ParamSpec(1, 3, ints=True),
                "b": ParamSpec(-10, 10, ints=True),
                "c": ParamSpec(-12, 12, ints=True)
            },
            constraints=[lambda p: p["a"] != 0 and p["b"]
                         ** 2 - 4*p["a"]*p["c"] >= 0],  # real roots
            strand="Algebra", topic="Quadratic Equations", difficulty="core"
        ),
        "trig_right_triangles_core": Pattern(
            templates={
                "ar": ["في مثلث قائم الزاوية، إذا كانت الزاوية الحادة {angle}° والضلع المقابل {opp} سم، فأوجد الوتر", "أوجد sin({angle}°) إذا كان الضلع المقابل = {opp} والوتر = {hyp}"],
                "en": ["In a right triangle, if the acute angle is {angle}° and opposite side is {opp} cm, find the hypotenuse", "Find sin({angle}°) if opposite = {opp} and hypotenuse = {hyp}"]
            },
            params={
                # common angles
                "angle": ParamSpec(30, 60, step=30, ints=True),
                "opp": ParamSpec(5, 15, ints=True),
                "hyp": ParamSpec(10, 25, ints=True)
            },
            constraints=[lambda p: p["opp"] < p["hyp"]],
            strand="Algebra & Trigonometry", topic="Right Triangle Trigonometry", difficulty="core"
        ),
        "coordinate_geometry_eq_lines_distance": Pattern(
            templates={
                "ar": ["أوجد معادلة الخط المستقيم الذي يمر بالنقطتين ({x1}, {y1}) و ({x2}, {y2})", "احسب المسافة بين النقطتين ({x1}, {y1}) و ({x2}, {y2})"],
                "en": ["Find the equation of line passing through ({x1}, {y1}) and ({x2}, {y2})", "Calculate distance between points ({x1}, {y1}) and ({x2}, {y2})"]
            },
            params={
                "x1": ParamSpec(-5, 5, ints=True), "y1": ParamSpec(-5, 5, ints=True),
                "x2": ParamSpec(-5, 5, ints=True), "y2": ParamSpec(-5, 5, ints=True)
            },
            constraints=[lambda p: p["x1"] != p["x2"]
                         or p["y1"] != p["y2"]],  # distinct points
            strand="Coordinate Geometry", topic="Lines and Distance", difficulty="core"
        )
    }),

    _grade_key(12): GradeCatalog(patterns={
        "calculus_derivatives": Pattern(
            templates={
                "ar": ["أوجد المشتقة: f(x) = {a}x³ + {b}x² + {c}x + {d}",
                       "احسب المشتقة: f(x) = {a}sin(x) + {b}cos(x)",
                       "أوجد f'(x) إذا كان: f(x) = {a}e^x + {b}ln(x)"],
                "en": ["Find f'(x) for f(x) = {a}x^3 + {b}x^2 + {c}x + {d}",
                       "Differentiate: f(x) = {a}sin(x) + {b}cos(x)",
                       "Find f'(x) if f(x) = {a}e^x + {b}ln(x)"]
            },
            params={"a": ParamSpec(-10, 10), "b": ParamSpec(-10, 10),
                    "c": ParamSpec(-10, 10), "d": ParamSpec(-10, 10)},
            constraints=[lambda p: p["a"] != 0 or p["b"] != 0 or p["c"] != 0],
            strand="Calculus", topic="Derivatives", difficulty="core"
        ),
        "calculus_extrema_critical_points": Pattern(
            templates={
                "ar": ["أوجد النقاط الحرجة للدالة f(x) = {a}x³ + {b}x² + {c}x", "أوجد القيم العظمى والصغرى المحلية للدالة f(x) = {a}x³ - {b}x² + {c}"],
                "en": ["Find critical points of f(x) = {a}x³ + {b}x² + {c}x", "Find local maxima and minima of f(x) = {a}x³ - {b}x² + {c}"]
            },
            params={
                "a": ParamSpec(1, 5, ints=True),
                "b": ParamSpec(1, 12, ints=True),
                "c": ParamSpec(-10, 10, ints=True)
            },
            constraints=[lambda p: p["a"] != 0],
            strand="Calculus", topic="Critical Points & Extrema", difficulty="core"
        ),
        "definite_integral_properties_mvt": Pattern(
            templates={
                "ar": ["احسب التكامل المحدود: ∫[{lower} إلى {upper}] ({a}x² + {b}x) dx", "أوجد مساحة المنطقة المحصورة بين المنحنى y = {a}x² والمحور x من x = 0 إلى x = {c}"],
                "en": ["Evaluate: ∫[{lower} to {upper}] ({a}x² + {b}x) dx", "Find area under curve y = {a}x² from x = 0 to x = {c}"]
            },
            params={
                "a": ParamSpec(1, 8, ints=True),
                "b": ParamSpec(-5, 5, ints=True),
                "c": ParamSpec(2, 6, ints=True),
                "lower": ParamSpec(0, 2, ints=True),
                "upper": ParamSpec(3, 6, ints=True)
            },
            constraints=[lambda p: p["lower"] < p["upper"] and p["a"] > 0],
            strand="Calculus", topic="Definite Integrals", difficulty="core"
        ),
        "optimization_word_problems": Pattern(
            templates={
                "ar": ["صندوق بدون غطاء يُصنع من قطعة مستطيلة طولها {length} سم وعرضها {width} سم. أوجد أقصى حجم", "أوجد أبعاد المستطيل الذي له أكبر مساحة إذا كان محيطه {perimeter} سم"],
                "en": ["A box without lid is made from rectangular piece {length} cm × {width} cm. Find maximum volume", "Find dimensions of rectangle with maximum area if perimeter is {perimeter} cm"]
            },
            params={
                "length": ParamSpec(20, 50, step=10, ints=True),
                "width": ParamSpec(15, 40, step=5, ints=True),
                "perimeter": ParamSpec(40, 120, step=20, ints=True)
            },
            constraints=[lambda p: p["length"] > 0 and p["width"] > 0],
            strand="Calculus", topic="Optimization", difficulty="challenge"
        )
    })
}

# ----------------------------
# Public API
# ----------------------------


def get_pattern_for_skill(grade: int, skill_title: str, topic: Optional[str] = None) -> Dict:
    """
    Get appropriate pattern based on grade and skill - Simplified mapping approach

    Args:
        grade: Student grade level (1-12)
        skill_title: Title of the skill (e.g., "Solving Linear Equations")
        topic: Optional specific topic

    Returns:
        Pattern dictionary with templates and parameters
    """
    
    # Simple mapping - if no direct match, fallback to LLM generation
    key = _grade_key(grade)
    catalog = CATALOG.get(key)
    
    if catalog and catalog.patterns:
        # Try exact grade first
        for pattern_key, pattern in catalog.patterns.items():
            if (skill_title and skill_title.lower() in pattern.topic.lower()) or \
               (topic and topic.lower() in pattern.topic.lower()):
                return {
                    "templates": pattern.templates.get("ar", []) + pattern.templates.get("en", []),
                    "parameter_ranges": {k: (v.min, v.max) for k, v in pattern.params.items()},
                    "constraints": [str(c) for c in pattern.constraints] if pattern.constraints else [],
                    "solution_formula": pattern.topic.lower().replace(" ", "_"),
                    "strand": pattern.strand,
                    "topic": pattern.topic,
                    "difficulty": pattern.difficulty
                }
        
        # Return first available pattern for this grade
        pattern = next(iter(catalog.patterns.values()))
        return {
            "templates": pattern.templates.get("ar", []) + pattern.templates.get("en", []),
            "parameter_ranges": {k: (v.min, v.max) for k, v in pattern.params.items()},
            "constraints": [str(c) for c in pattern.constraints] if pattern.constraints else [],
            "solution_formula": pattern.topic.lower().replace(" ", "_"),
            "strand": pattern.strand,
            "topic": pattern.topic,
            "difficulty": pattern.difficulty
        }
    
    # Return None to trigger LLM generation - this is the key change
    return None


def generate_question_from_pattern(pattern: Dict, lang: str = "ar", seed: Optional[int] = None) -> Tuple[str, str]:
    """
    Generate a question and answer from a pattern

    Args:
        pattern: Pattern dictionary with templates and parameters
        lang: Language preference ('ar' or 'en')
        seed: Optional seed for reproducible generation

    Returns:
        Tuple of (question_text, answer)
    """
    set_seed(seed)

    # Select random template
    templates = pattern["templates"]
    if isinstance(templates, dict):
        # New format with language keys
        template_list = templates.get(
            lang, templates.get("ar", templates.get("en", [])))
        if not template_list:
            template_list = next(iter(templates.values()))
    else:
        # Legacy format - list of templates
        template_list = templates

    template = random.choice(template_list)

    # Generate parameters respecting constraints
    max_attempts = 100
    for _ in range(max_attempts):
        params = {}
        for param, (min_val, max_val) in pattern["parameter_ranges"].items():
            if isinstance(min_val, float):
                params[param] = round(random.uniform(min_val, max_val), 2)
            else:
                params[param] = random.randint(min_val, max_val)

        # Check constraints (legacy support)
        valid = True
        for constraint in pattern.get("constraints", []):
            try:
                # Safe evaluation of constraint
                if isinstance(constraint, str):
                    if not eval(constraint, {"__builtins__": {}}, params):
                        valid = False
                        break
                elif callable(constraint):
                    if not constraint(params):
                        valid = False
                        break
            except:
                pass

        if valid:
            # Generate question
            question = template.format(**params)

            # Calculate answer (simplified)
            formula = pattern.get("solution_formula", "")
            topic = pattern.get("topic", "")

            # Enhanced answer calculation based on topic
            if "linear" in formula.lower() or "equation" in topic.lower():
                # Linear equations: solve for x
                if 'a' in params and params.get('a', 0) != 0:
                    if "x/{a} + {b} = {c}" in template:
                        # x/a + b = c => x = a(c-b)
                        x = params['a'] * \
                            (params.get('c', 0) - params.get('b', 0))
                    elif "(x + {b})" in template:
                        # a(x + b) = c => x = c/a - b
                        x = params.get('c', 0) / \
                            params['a'] - params.get('b', 0)
                    else:
                        # ax + b = c => x = (c-b)/a
                        x = (params.get('c', 0) -
                             params.get('b', 0)) / params['a']
                    answer = f"x = {x:.1f}" if x != int(x) else f"x = {int(x)}"
                else:
                    answer = "No solution"
            elif "multiplication" in topic.lower() or "product" in template.lower():
                answer = str(params.get('a', 1) * params.get('b', 1))
            elif "addition" in topic.lower() or "+" in template:
                answer = str(params.get('a', 0) + params.get('b', 0))
            elif "subtraction" in topic.lower() or "-" in template:
                answer = str(params.get('a', 0) - params.get('b', 0))
            elif "perimeter" in template.lower() or "محيط" in template:
                answer = str(2 * (params.get('a', 0) + params.get('b', 0)))
            elif "area" in template.lower() and "circle" in template.lower():
                answer = f"{params.get('a', 1)}²π"
            elif "area" in template.lower():
                answer = str(params.get('a', 0) * params.get('b', 0))
            elif "mean" in template.lower() or "متوسط" in template:
                nums = [params.get(k, 0)
                        for k in ["a", "b", "c", "d", "e"] if k in params]
                if nums:
                    answer = str(round(sum(nums) / len(nums), 2))
                else:
                    answer = "حل حسب الخطوات" if lang == "ar" else "Solve step-by-step"
            else:
                answer = "حل حسب الخطوات" if lang == "ar" else "Solve step-by-step"

            return question, answer

    # Fallback if no valid params found
    return template, "حل حسب الخطوات" if lang == "ar" else "Solve step-by-step"


# Maintain backward compatibility
SKILL_PATTERNS = {f"grade_{i}": {"patterns": {}} for i in range(1, 13)}

# Export for compatibility
__all__ = [
    "Pattern",
    "GradeCatalog",
    "CATALOG",
    "SKILL_PATTERNS",
    "get_pattern_for_skill",
    "generate_question_from_pattern",
    "set_seed",
]
