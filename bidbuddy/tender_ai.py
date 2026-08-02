"""
Tender AI Module (ported from bidbuddy2/ai.py)
Google Gemini, via the official google-genai SDK.
"""

import json
import logging
import re
import time

from google import genai

from .tender_config import (
    GEMINI_API_KEY,
    MODEL_NAME,
    MAX_RETRIES,
    RETRY_DELAY,
)

logger = logging.getLogger("BidBuddy")


# ==========================================================
# GEMINI CLIENT
# ==========================================================

client = genai.Client(api_key=GEMINI_API_KEY)


SYSTEM_PROMPT = """
You are an expert Indian Government Tender Analyst.

Analyse the tender.

Return ONLY JSON.

Do NOT return markdown.

Return exactly:

{
"summary":"",
"classification":"",
"compliance":""
}

classification must be one of

roads
buildings
dams
other

compliance should be plain text bullet points.
"""


# ==========================================================
# AI CALL
# ==========================================================

def ask_llm(tender_text):
    prompt = SYSTEM_PROMPT + "\n\nTender:\n\n" + tender_text

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            logger.info("Calling Gemini (%d/%d)", attempt + 1, MAX_RETRIES)

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )

            return response.text

        except Exception as ex:
            last_error = ex

            logger.warning(str(ex))

            if attempt < MAX_RETRIES - 1:
                sleep = RETRY_DELAY * (attempt + 1)
                logger.info("Retrying in %d seconds...", sleep)
                time.sleep(sleep)

    raise last_error


# ==========================================================
# REMOVE MARKDOWN
# ==========================================================

def remove_markdown(text):
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE)
        text = re.sub(r"```$", "", text)

    return text.strip()


# ==========================================================
# PARSE JSON
# ==========================================================

def to_string(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        return "\n".join(str(v) for v in value)

    if isinstance(value, dict):
        # Common Gemini pattern: {"text":"...."}
        if "text" in value:
            return str(value["text"]).strip()

        return json.dumps(value, indent=2, ensure_ascii=False)

    return str(value).strip()


def parse_ai_response(text):
    text = remove_markdown(text)

    try:
        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end <= start:
            raise ValueError("JSON not found.")

        obj = json.loads(text[start:end])

        summary = to_string(obj.get("summary"))
        classification = to_string(obj.get("classification")).lower()
        compliance = to_string(obj.get("compliance"))

        if classification not in ["roads", "buildings", "dams", "other"]:
            classification = "other"

        return {
            "summary": summary,
            "classification": classification,
            "compliance": compliance,
        }

    except Exception as ex:
        logger.exception(ex)

        return {
            "summary": "Unable to generate summary.",
            "classification": "other",
            "compliance": "",
        }
