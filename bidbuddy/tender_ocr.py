"""
Tender OCR Module (ported from bidbuddy2/ocr.py)
Converts PDF to text using Poppler + Tesseract.
"""

import logging

from pdf2image import convert_from_path
import pytesseract

from .tender_config import (
    POPPLER_PATH,
    TESSERACT_PATH,
    OCR_DPI,
    MAX_PAGES,
    MAX_INPUT_CHARS,
)

logger = logging.getLogger("BidBuddy")

# ==========================================================
# TESSERACT CONFIGURATION
# ==========================================================

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ==========================================================
# OCR A SINGLE PAGE
# ==========================================================

def extract_text_from_page(page):
    text = pytesseract.image_to_string(page, lang="eng")
    return text.strip()


# ==========================================================
# PDF TO TEXT
# ==========================================================

def pdf_to_text(pdf_path):
    logger.info("Reading PDF : %s", pdf_path)

    pages = convert_from_path(
        pdf_path,
        dpi=OCR_DPI,
        poppler_path=POPPLER_PATH,
    )

    if not pages:
        raise Exception("Unable to read PDF.")

    logger.info("PDF contains %d pages.", len(pages))

    pages = pages[:MAX_PAGES]

    logger.info("Processing first %d page(s).", len(pages))

    extracted = []

    for page_number, page in enumerate(pages, start=1):
        logger.info("OCR Page %d...", page_number)

        text = extract_text_from_page(page)

        if text:
            extracted.append(f"\n\n========== PAGE {page_number} ==========\n\n")
            extracted.append(text)

    final_text = "".join(extracted).strip()

    if not final_text:
        raise Exception("No text extracted from PDF.")

    logger.info("OCR extracted %d characters.", len(final_text))

    if len(final_text) > MAX_INPUT_CHARS:
        logger.info("Truncating OCR text to %d characters.", MAX_INPUT_CHARS)
        final_text = final_text[:MAX_INPUT_CHARS]

    return final_text
