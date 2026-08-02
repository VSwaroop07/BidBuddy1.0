#!/usr/bin/env bash
# build.sh — Render build script (Gemini-native, no system OCR tools needed)
set -e

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Running database migrations..."
python manage.py migrate