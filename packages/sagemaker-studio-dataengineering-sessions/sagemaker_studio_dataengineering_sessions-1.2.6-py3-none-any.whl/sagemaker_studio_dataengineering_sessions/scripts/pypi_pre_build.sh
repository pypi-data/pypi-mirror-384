#!/bin/bash

# File path
PYPROJECT_FILE="pyproject.toml"

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macos
    sed -i '' '
    /\[tool\.hatch\.env\.collectors\.custom\]/s/^/#/
    /path = "\.hatch\/hatch_plugin\.py"/s/^/#/
    /\[tool\.hatch\.build\.hooks\.custom\]/s/^/#/
    /path = "src\/sagemaker_studio_dataengineering_sessions\/scripts\/build_hooks\.py"/s/^/#/
    ' "$PYPROJECT_FILE"
else
    # linux
    sed -i '
    /\[tool\.hatch\.env\.collectors\.custom\]/s/^/#/
    /path = "\.hatch\/hatch_plugin\.py"/s/^/#/
    /\[tool\.hatch\.build\.hooks\.custom\]/s/^/#/
    /path = "src\/sagemaker_studio_dataengineering_sessions\/scripts\/build_hooks\.py"/s/^/#/
    ' "$PYPROJECT_FILE"
fi