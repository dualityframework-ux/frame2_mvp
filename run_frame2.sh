#!/bin/bash
# Start the frame² Streamlit app from the repo root.
set -e
cd "$(dirname "$0")"
echo "⚾ starting frame² red sox intelligence..."
if [ -d .venv ]; then source .venv/bin/activate; elif [ -d venv ]; then source venv/bin/activate; fi
export PYTHONPATH=.
streamlit run app/app.py --server.port 8510
