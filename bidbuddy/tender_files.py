"""
Tender File Manager (ported from bidbuddy2/file_manager.py)
Handles all file operations for the tender-analysis feature.
"""

import json
import os
import logging

from .tender_config import SUMMARY_FOLDER

logger = logging.getLogger("BidBuddy")


# ==========================================================
# SAVE RESULT
# ==========================================================

def save_result(job_id, result_data):
    summary_path = os.path.join(SUMMARY_FOLDER, job_id + ".txt")

    with open(summary_path, "w", encoding="utf-8") as fp:
        json.dump(result_data, fp, indent=4, ensure_ascii=False)

    logger.info("Summary saved : %s", summary_path)


# ==========================================================
# LOAD RESULT
# ==========================================================

def load_result(job_id):
    summary_path = os.path.join(SUMMARY_FOLDER, job_id + ".txt")

    if not os.path.exists(summary_path):
        return None

    with open(summary_path, "r", encoding="utf-8") as fp:
        return json.load(fp)


# ==========================================================
# DELETE PDF
# ==========================================================

def cleanup_pdf(pdf_path):
    try:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            logger.info("Deleted PDF : %s", pdf_path)

    except Exception:
        logger.exception("Unable to delete PDF.")


# ==========================================================
# DELETE SUMMARY
# ==========================================================

def cleanup_summary(job_id):
    summary_path = os.path.join(SUMMARY_FOLDER, job_id + ".txt")

    try:
        if os.path.exists(summary_path):
            os.remove(summary_path)
            logger.info("Deleted Summary : %s", summary_path)

    except Exception:
        logger.exception("Unable to delete summary.")


# ==========================================================
# RESULT EXISTS
# ==========================================================

def result_exists(job_id):
    summary_path = os.path.join(SUMMARY_FOLDER, job_id + ".txt")
    return os.path.exists(summary_path)
