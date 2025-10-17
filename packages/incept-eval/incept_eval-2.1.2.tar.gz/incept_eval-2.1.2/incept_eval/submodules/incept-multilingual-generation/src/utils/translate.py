import time
import json
import re
import html
from typing import Dict, Any, List, Tuple, Sequence
import logging
import os
import requests

logger = logging.getLogger(__name__)

from google.cloud import translate_v2 as translate

from src.llms import format_messages_for_api, solve_with_llm
from src.utils.progress_bar import ProgressBar
from src.utils.json_repair import parse_json

_ARABIC_CHARS = re.compile(r"[\u0600-\u06FF]")  # Arabic Unicode block

class GoogleTranslateREST:
    """
    Thin wrapper around Google Translate v2 REST API using an API key only.
    """
    def __init__(self, api_key: str | None = None, timeout: float = 30.0):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not set. Provide a v2 Translate API key.")
        self.timeout = timeout
        self.session = requests.Session()
        self.url = "https://translation.googleapis.com/language/translate/v2"

    def translate_batch_en_to_ar(
        self,
        texts: Sequence[str],
        max_retries: int = 3,
        backoff_base: float = 0.7,
    ) -> List[str]:
        """
        Translates a batch of English strings to Arabic.
        Returns outputs aligned with 'texts'.
        """
        if not texts:
            return []
        payload = {
            "q": list(texts),            # API supports array of q
            "source": "en",
            "target": "ar",
            "format": "text",
            "key": self.api_key,
        }

        for attempt in range(max_retries + 1):
            try:
                r = self.session.post(self.url, data=payload, timeout=self.timeout)
                # 413 can happen if payload too large; caller should re-batch smaller.
                if r.status_code == 413:
                    raise PayloadTooLarge("Payload too large")
                r.raise_for_status()
                data = r.json()
                translations = data["data"]["translations"]
                # Unescape &quot;, &lt;, etc.
                return [html.unescape(item.get("translatedText", "")) for item in translations]
            except PayloadTooLarge:
                # Let caller handle by re-batching with smaller size
                raise
            except requests.HTTPError as he:
                # Quota / rate / key issues: try a brief backoff for 429/5xx; fail fast for 4xx key errors.
                status = he.response.status_code if he.response is not None else None
                if status in (429, 500, 502, 503, 504) and attempt < max_retries:
                    time.sleep(backoff_base * (2 ** attempt))
                    continue
                # Helpful logging content for the caller
                try:
                    err_json = r.json()
                except Exception:
                    err_json = {}
                msg = err_json.get("error", {}).get("message", str(he))
                raise RuntimeError(f"Google Translate REST error (HTTP {status}): {msg}") from he
            except (requests.Timeout, requests.ConnectionError) as net_err:
                if attempt < max_retries:
                    time.sleep(backoff_base * (2 ** attempt))
                    continue
                raise RuntimeError(f"Network error calling Translate API: {net_err}") from net_err


class PayloadTooLarge(Exception):
    pass



def _translate_with_llm(
    initial_dict: Dict,
    target_language: str = "arabic",
    provider_requested: str = 'openai',
    progress: ProgressBar = None
) -> Dict:
    """
    Translate the structured response to the target language.
    Uses LLM to translate all text fields while preserving structure.
    """
    print(f"🌐 TRANSLATE: Translating {initial_dict}")
    if target_language.lower() not in ["arabic", "english"]:
        logger.error(
            f"❌ MODULE 5 TRANSLATE: Unsupported target language '{target_language}'")
        return initial_dict

    translation_start = time.time()

    try:
        structured_dict = str(initial_dict)

        if target_language.lower() == "arabic":
            structured_response = solve_with_llm(
                format_messages_for_api(
                    "أنت خبير ترجمة تعليمية. الجواب النهائي فقط بصيغة JSON صالحة.",
                    f"ترجم المحتوى التعليمي التالي إلى العربية:\n"
                    f"- حافظ على هيكل JSON وأسماء الحقول الإنجليزية\n"
                    f"- ترجم فقط القيم النصية\n"
                    f"- استخدم المصطلحات التعليمية العربية الصحيحة\n\n"
                    f"{structured_dict}",
                ),
                max_tokens=2000,  # Reduced from 25000 for faster translation
                provider=provider_requested
            )
        else:  # English or any other language - default to English
            structured_response = solve_with_llm(
                format_messages_for_api(
                    "You are an educational translation expert. Final answer only in valid JSON format.",
                    f"Translate the following educational content to {target_language}:\n"
                    f"- Preserve JSON structure and English field names exactly\n"
                    f"- Only translate the text values\n"
                    f"- Use proper educational terminology\n\n"
                    f"{structured_dict}",
                ),
                max_tokens=2000,  # Reduced from 25000 for faster translation
                provider=provider_requested
            )
        progress.update(1)

        translation_time = time.time() - translation_start

        # Validate response before JSON parsing
        if not structured_response or (isinstance(structured_response, str) and not structured_response.strip()):
            logger.warning("⚠️ MODULE 5 TRANSLATE: Empty response from LLM, returning original")
            return initial_dict

        if isinstance(structured_response, str):
            try:
                structured_response = parse_json(structured_response)
            except json.JSONDecodeError as json_error:
                logger.warning(f"⚠️ MODULE 5 TRANSLATE: Invalid JSON from LLM: {json_error}, returning original")
                return initial_dict
        expected_keys = {"type", "question", "options", "answer", "difficulty",
                            "explanation", "detailed_explanation", "voiceover_script"}
        if not isinstance(structured_response, dict) or not expected_keys.issubset(structured_response.keys()):
            logger.warning(
                "⚠️ MODULE 5 TRANSLATE: Translated response missing expected keys, returning original")
            return initial_dict

        # check that detailed_explanation has steps and insights
        de = structured_response.get("detailed_explanation", {})
        if not isinstance(de, dict) or "steps" not in de or "personalized_academic_insights" not in de:
            logger.warning(
                "⚠️ MODULE 5 TRANSLATE: Translated detailed_explanation missing expected fields, returning original")
            return initial_dict

        return structured_response
    except Exception as e:
        translation_time = time.time() - translation_start
        logger.error(
            f"❌ MODULE 5 TRANSLATE: Translation failed after {translation_time:.2f}s: {e}")
        return initial_dict


_ARABIC_CHARS = re.compile(r"[\u0600-\u06FF]")

def _is_arabic(text: str) -> bool:
    return bool(_ARABIC_CHARS.search(text))

def _collect_strings(node: Any, path: str = "") -> List[Tuple[str, str]]:
    """
    Traverse JSON-like structure and collect all string leaves.
    Returns list of (path, original_string). Path uses JSON-pointer-like keys.
    Only collects strings from translatable content fields.
    """
    # Fields that should NEVER be translated (metadata/structural)
    SKIP_KEYS = {
        "type", "difficulty", "answer", "di_formats_used",
        "answer_choice", "question_id"
    }

    out = []
    if isinstance(node, str):
        out.append((path, node))
    elif isinstance(node, dict):
        for k, v in node.items():
            # Skip metadata fields entirely
            if k in SKIP_KEYS:
                continue
            child = f"{path}/{k}" if path else f"/{k}"
            out.extend(_collect_strings(v, child))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            child = f"{path}/{i}"
            out.extend(_collect_strings(v, child))
    return out

def _set_by_path(root: Any, path: str, value: str) -> None:
    if not path or not path.startswith("/"):
        return
    parts = path.strip("/").split("/")
    cur = root
    for i, part in enumerate(parts):
        last = i == len(parts) - 1
        if isinstance(cur, list):
            idx = int(part)
            if last:
                cur[idx] = value
            else:
                cur = cur[idx]
        else:  # dict
            if last:
                cur[part] = value
            else:
                cur = cur.get(part)

def _batch(xs: List[str], size: int) -> List[List[str]]:
    return [xs[i:i+size] for i in range(0, len(xs), size)]

def _translate_values_to_arabic_rest(initial: Any, adapter: GoogleTranslateREST, progress=None) -> Any:
    """
    Deep-copy `initial`, translating only string values to Arabic via REST API.
    Keys remain in English. Values already in Arabic are left unchanged.
    """
    collected = _collect_strings(initial)
    if not collected:
        # No progress update here - will be handled by caller
        return initial

    paths, originals = zip(*collected)

    # Start with a reasonably large batch; shrink on 413
    batch_size = 100
    translated_all: List[str] = []

    # Work through the strings in order
    remaining = list(originals)
    while remaining:
        chunk = remaining[:batch_size]
        remaining = remaining[batch_size:]

        # Skip translation for values that already look Arabic
        # (preserves user-provided Arabic or previous passes)
        mask = [not _is_arabic(s) for s in chunk]
        to_translate = [s for s, need in zip(chunk, mask) if need]

        try:
            if to_translate:
                out = adapter.translate_batch_en_to_ar(to_translate)
                # Sanity: some items could come back non-Arabic (rare); keep original in such cases
                it = iter(out)
                stitched = []
                for s, need in zip(chunk, mask):
                    if not need:  # already Arabic
                        stitched.append(s)
                    else:
                        t = next(it, s)
                        stitched.append(t if _is_arabic(t) else s)
                translated_all.extend(stitched)
            else:
                translated_all.extend(chunk)
        except PayloadTooLarge:
            # Halve the batch and retry this slice
            if batch_size == 1:
                # Can't shrink further; fall back to original chunk
                translated_all.extend(chunk)
            else:
                remaining = chunk + remaining  # put back and try with smaller batches
                batch_size = max(1, batch_size // 2)
        except Exception as e:
            # On hard failure, keep originals for this chunk and continue
            logger.error(f"Translate REST chunk failed: {e}")
            translated_all.extend(chunk)

        # Progress tracking moved to outer function to avoid updating per-batch

    # Rebuild deep copy
    result = json.loads(json.dumps(initial))
    for p, val in zip(paths, translated_all):
        _set_by_path(result, p, val)
    return result

def _translate_with_google_cloud(
    initial_dict: Dict,
    target_language: str = "arabic",   # kept for signature compatibility
    provider_requested: str = "google_rest",
    progress=None
) -> Dict:
    """
    STRICT values-only English→Arabic via Google Translate REST (API key).
    - Keys remain English.
    - Verifies Arabic characters in outputs; otherwise keeps original value.
    """
    if target_language.lower() != "arabic":
        logger.warning("ℹ️ MODULE 5 TRANSLATE: This layer only supports English→Arabic; proceeding with Arabic.")

    translation_start = time.time()

    try:
        adapter = GoogleTranslateREST()  # reads GEMINI_API_KEY
        structured_response = _translate_values_to_arabic_rest(initial_dict, adapter, progress=None)

        # Update progress once per item (not per batch) to avoid overcounting
        if progress:
            progress.update(1)

        # ---- Your original validations ----
        if not structured_response or not isinstance(structured_response, dict):
            logger.warning("⚠️ MODULE 5 TRANSLATE: Invalid translated root; returning original")
            return initial_dict

        # Core required keys (options is optional for fill-in questions)
        required_keys = {
            "type", "question", "answer", "difficulty",
            "explanation", "detailed_explanation", "voiceover_script"
        }
        if not required_keys.issubset(structured_response.keys()):
            missing = required_keys - set(structured_response.keys())
            logger.warning(f"⚠️ MODULE 5 TRANSLATE: Missing required keys {missing}; returning original")
            logger.debug(f"Available keys: {structured_response.keys()}")
            return initial_dict

        de = structured_response.get("detailed_explanation", {})
        if not isinstance(de, dict) or "steps" not in de or "personalized_academic_insights" not in de:
            logger.warning("⚠️ MODULE 5 TRANSLATE: detailed_explanation missing fields; returning original")
            return initial_dict

        logger.info(f"✅ MODULE 5 TRANSLATE: REST values-only EN→AR ok in {time.time() - translation_start:.2f}s")
        return structured_response

    except Exception as e:
        logger.error(f"❌ MODULE 5 TRANSLATE: REST init/translate failed after {time.time() - translation_start:.2f}s: {e}")
        return initial_dict



def execute_translate(initial_dict: Dict, target_language: str = "arabic", provider_requested: str = "google", progress: ProgressBar = None) -> Dict:
    """
    Translate the structured response to the target language.
    Uses Google Cloud Translation to translate all text fields while preserving structure.
    """
    if provider_requested == "google":
        return _translate_with_google_cloud(initial_dict, target_language, provider_requested, progress)
    else:
        return _translate_with_llm(initial_dict, target_language, provider_requested, progress)