#!/bin/bash
# Fix numpy/pandas compatibility issues
# This script reinstalls numpy and pandas to ensure binary compatibility

echo "Fixing numpy/pandas compatibility..."

# Uninstall existing versions
pip uninstall -y numpy pandas

# Install compatible versions
pip install "numpy>=1.24.0,<2.0.0"
pip install "pandas>=2.0.0,<3.0.0"

echo "Done! Try running the server again."

