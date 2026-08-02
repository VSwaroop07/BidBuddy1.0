#!/usr/bin/env bash
# build.sh — Render build script
set -e

echo "==> Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq poppler-utils tesseract-ocr tesseract-ocr-eng

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Running database migrations..."
python manage.py migrate