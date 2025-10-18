#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade build twine
python -m build
# Upload to TestPyPI first (recommended):
# python -m twine upload --repository testpypi dist/*
python -m twine upload dist/*
