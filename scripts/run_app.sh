#!/bin/bash
set -e
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py
