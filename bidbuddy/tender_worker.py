"""
Tender Worker (ported from bidbuddy2/worker.py)

Coordinates OCR -> AI -> Save Result -> Cleanup
"""

import logging

from .tender_ocr import pdf_to_text
from .tender_ai import ask_llm, parse_ai_response
from .tender_files import save_result, cleanup_pdf

logger = logging.getLogger("BidBuddy")


# ==========================================================
# MAIN WORKER
# ==========================================================

def process_pdf(job_id, pdf_path):
    logger.info("Started processing Job ID : %s", job_id)

    try:
        # ----------------------------------------------
        # OCR
        # ----------------------------------------------
        logger.info("Starting OCR...")

        extracted_text = pdf_to_text(pdf_path)

        logger.info("OCR completed (%d characters).", len(extracted_text))

        # ----------------------------------------------
        # AI
        # ----------------------------------------------
        logger.info("Calling AI...")

        ai_response = ask_llm(extracted_text)

        logger.info("AI completed.")

        # ----------------------------------------------
        # PARSE
        # ----------------------------------------------
        result_data = parse_ai_response(ai_response)

        # ----------------------------------------------
        # SAVE
        # ----------------------------------------------
        save_result(job_id, result_data)

        logger.info("Job completed successfully : %s", job_id)

    except Exception as ex:
        logger.exception(ex)

        save_result(
            job_id,
            {
                "summary": "Error : " + str(ex),
                "classification": "",
                "compliance": "",
            },
        )

    finally:
        # ----------------------------------------------
        # ALWAYS DELETE PDF
        # ----------------------------------------------
        cleanup_pdf(pdf_path)

        logger.info("Worker finished : %s", job_id)
