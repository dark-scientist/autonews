#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}/streamlit-app"

# If backend output exists, use it directly to avoid manual copy.
BACKEND_RESULTS="${ROOT_DIR}/auto_news_intelligence/output/results.json"
if [[ -f "${BACKEND_RESULTS}" ]]; then
  export RESULTS_JSON_PATH="${BACKEND_RESULTS}"
fi

streamlit run app.py --server.port "${PORT:-8502}"

