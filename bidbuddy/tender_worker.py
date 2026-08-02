"""
Tender Worker — Single-Call Gemini Edition

Uploads the PDF directly to Gemini Files API and analyses it in ONE API call.
No local OCR. No separate text-extraction step.
This halves quota usage vs. the two-call approach.
"""

import logging
import time
import os

from google import genai
from google.genai import types

from .tender_config import (
    GEMINI_API_KEY,
    MODEL_NAME,
    MAX_RETRIES,
    RETRY_DELAY,
)
from .tender_ai import parse_ai_response
from .tender_files import save_result, cleanup_pdf

logger = logging.getLogger("BidBuddy")

client = genai.Client(api_key=GEMINI_API_KEY)

ANALYSIS_PROMPT = """
You are an expert Indian Government Tender Analyst.

Read this tender document and return ONLY valid JSON. Do NOT return markdown.

Return exactly:

{
  "summary": "",
  "classification": "",
  "compliance": ""
}

Rules:
- classification must be one of: roads, buildings, dams, other
- summary should be 2-3 sentences describing what the tender is for
- compliance should be plain text bullet points of key requirements
"""


# ==========================================================
# UPLOAD PDF TO GEMINI FILES API
# ==========================================================

def _upload_pdf(pdf_path):
    """Upload PDF to Gemini Files API and wait until it is ACTIVE."""
    logger.info("Uploading PDF to Gemini Files API: %s", pdf_path)

    with open(pdf_path, "rb") as f:
        uploaded = client.files.upload(
            file=f,
            config=types.UploadFileConfig(
                mime_type="application/pdf",
                display_name=os.path.basename(pdf_path),
            ),
        )

    logger.info("Upload complete. Waiting for file to be ACTIVE...")

    # Poll until active (usually instant, max ~60s)
    for _ in range(30):
        info = client.files.get(name=uploaded.name)
        if info.state.name == "ACTIVE":
            logger.info("File is ACTIVE: %s", uploaded.uri)
            return uploaded
        time.sleep(2)

    raise Exception("Gemini file processing timed out.")


# ==========================================================
# ANALYSE PDF IN ONE CALL
# ==========================================================

def _analyse_pdf(uploaded_file):
    """Send the uploaded file + prompt to Gemini in a single API call."""
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            logger.info("Calling Gemini for analysis (%d/%d)...", attempt + 1, MAX_RETRIES)

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    uploaded_file,
                    ANALYSIS_PROMPT,
                ],
            )

            return response.text

        except Exception as ex:
            last_error = ex
            logger.warning("Gemini call failed: %s", ex)

            if attempt < MAX_RETRIES - 1:
                sleep = RETRY_DELAY * (attempt + 1)
                logger.info("Retrying in %d seconds...", sleep)
                time.sleep(sleep)

    raise last_error


# ==========================================================
# MAIN ENTRY POINT
# ==========================================================

def process_pdf(job_id, pdf_path):
    logger.info("Started Job ID: %s", job_id)

    uploaded_file = None

    try:
        # ── Step 1: Upload PDF (once) ──────────────────────────────────────────
        uploaded_file = _upload_pdf(pdf_path)

        # ── Step 2: Analyse in ONE Gemini call ────────────────────────────────
        raw_response = _analyse_pdf(uploaded_file)

        logger.info("Gemini analysis complete.")

        # ── Step 3: Parse & save result ───────────────────────────────────────
        result_data = parse_ai_response(raw_response)
        save_result(job_id, result_data)

        logger.info("Job completed: %s", job_id)

    except Exception as ex:
        logger.exception(ex)
        save_result(
            job_id,
            {
                "summary": "Error: " + str(ex),
                "classification": "other",
                "compliance": "",
            },
        )

    finally:
        # ── Always clean up Gemini file and local PDF ─────────────────────────
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
                logger.info("Deleted file from Gemini Files API.")
            except Exception:
                logger.warning("Could not delete Gemini file.")

        cleanup_pdf(pdf_path)
        logger.info("Worker finished: %s", job_id)
