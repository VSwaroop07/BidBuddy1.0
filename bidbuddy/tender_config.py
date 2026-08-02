"""
Configuration for the tender-analysis feature (formerly bidbuddy2/config.py).

Ported to reuse Django's settings/BASE_DIR instead of a hardcoded
Windows path, and to read Tesseract/Poppler paths from the environment
so this works both on your local Windows machine and on the Linux
deploy target (Render, where build.sh already apt-installs poppler
and tesseract onto the system PATH).
"""

import os

from decouple import config as env
from django.conf import settings

# ==========================================================
# FOLDERS
# ==========================================================

BASE_DIR = settings.BASE_DIR

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
SUMMARY_FOLDER = os.path.join(BASE_DIR, "summaries")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)


# ==========================================================
# OCR
# ==========================================================
# On Linux (Render) these are left blank and pytesseract/pdf2image
# find tesseract/poppler on the system PATH (installed by build.sh).
# On Windows locally, set TESSERACT_PATH / POPPLER_PATH in your .env
# if they aren't already on your PATH, e.g.:
#   TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
#   POPPLER_PATH=C:\poppler\Library\bin

TESSERACT_PATH = env("TESSERACT_PATH", default="")

POPPLER_PATH = env("POPPLER_PATH", default="") or None


# ==========================================================
# GEMINI
# ==========================================================

GEMINI_API_KEY = getattr(settings, "GEMINI_API_KEY", "") or env("GEMINI_API_KEY", default="")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable not found."
    )

MODEL_NAME = "gemini-2.5-flash"


# ==========================================================
# AI SETTINGS
# ==========================================================

MAX_RETRIES = 3

RETRY_DELAY = 5

REQUEST_TIMEOUT = 120

MAX_INPUT_CHARS = 7000


# ==========================================================
# OCR SETTINGS
# ==========================================================

OCR_DPI = 300

MAX_PAGES = 3


# ==========================================================
# LOGGING
# ==========================================================

LOG_LEVEL = "INFO"
