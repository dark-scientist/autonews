#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}/auto_news_intelligence"

streamlit run app_upload.py --server.port "${PORT:-8501}"

