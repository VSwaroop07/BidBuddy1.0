# Replace tender_ocr.py with Gemini-native PDF reading
# No more poppler, tesseract, pdf2image, pytesseract needed

"""
Tender OCR Module — Gemini Files API Edition
Uploads PDF directly to Gemini and extracts text natively.
No poppler or tesseract required.
"""

import logging
import time
import os

from google import genai
from google.genai import types

from .tender_config import (
    GEMINI_API_KEY,
    MAX_INPUT_CHARS,
    MAX_RETRIES,
    RETRY_DELAY,
)

logger = logging.getLogger("BidBuddy")

client = genai.Client(api_key=GEMINI_API_KEY)


def pdf_to_text(pdf_path):
    """
    Upload the PDF to Gemini Files API and extract its text content
    using Gemini's native multimodal understanding.
    No local OCR tools required.
    """
    logger.info("Uploading PDF to Gemini Files API: %s", pdf_path)

    # Upload the PDF file
    uploaded_file = None
    for attempt in range(MAX_RETRIES):
        try:
            with open(pdf_path, "rb") as f:
                uploaded_file = client.files.upload(
                    file=f,
                    config=types.UploadFileConfig(
                        mime_type="application/pdf",
                        display_name=os.path.basename(pdf_path),
                    ),
                )
            logger.info("Upload complete. File URI: %s", uploaded_file.uri)
            break
        except Exception as ex:
            logger.warning("Upload attempt %d failed: %s", attempt + 1, ex)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise

    # Wait for file to be processed (Active state)
    for _ in range(20):
        file_info = client.files.get(name=uploaded_file.name)
        if file_info.state.name == "ACTIVE":
            break
        logger.info("Waiting for Gemini to process file...")
        time.sleep(2)
    else:
        raise Exception("Gemini file processing timed out.")

    # Ask Gemini to extract all text from the PDF
    logger.info("Extracting text from PDF via Gemini...")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            uploaded_file,
            "Extract and return ALL text from this document exactly as written. "
            "Do not summarise. Do not add commentary. Return only the raw text.",
        ],
    )

    extracted_text = response.text.strip()

    # Clean up the uploaded file from Gemini
    try:
        client.files.delete(name=uploaded_file.name)
        logger.info("Deleted file from Gemini Files API.")
    except Exception:
        logger.warning("Could not delete file from Gemini Files API.")

    if not extracted_text:
        raise Exception("No text extracted from PDF.")

    logger.info("Extracted %d characters from PDF.", len(extracted_text))

    if len(extracted_text) > MAX_INPUT_CHARS:
        logger.info("Truncating to %d characters.", MAX_INPUT_CHARS)
        extracted_text = extracted_text[:MAX_INPUT_CHARS]

    return extracted_text
