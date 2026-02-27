#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/auto_news_intelligence"
FRONTEND_DIR="${ROOT_DIR}/streamlit-app"
PYTHON_BIN="${PYTHON_BIN:-python3}"

URL_FILE="${1:-}"

echo "[STEP 1/4] Backend directory: ${BACKEND_DIR}"
cd "${BACKEND_DIR}"

if [[ -n "${URL_FILE}" ]]; then
  echo "[STEP 2/4] Ingest URLs from file: ${URL_FILE}"
  "${PYTHON_BIN}" add_urls.py "${URL_FILE}"
else
  echo "[STEP 2/4] URL ingest skipped (no file provided)"
fi

echo "[STEP 3/4] Downloading and processing articles..."
"${PYTHON_BIN}" download_new_articles.py
"${PYTHON_BIN}" runner.py

echo "[STEP 4/4] Publishing results to frontend..."
cp output/results.json "${FRONTEND_DIR}/results.json"
echo "[DONE] Frontend data updated: ${FRONTEND_DIR}/results.json"

