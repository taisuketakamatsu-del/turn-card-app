#!/bin/bash
# uv が Python 3.12 と必要なライブラリを自動で用意して起動する
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
uv run --python 3.12 --with-requirements requirements.txt streamlit run app.py
