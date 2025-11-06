#!/bin/bash
# Format all Python code using black and isort

echo "Running black..."
black src tests

echo "Running isort..."
isort --profile=black --float-to-top src tests

echo "Formatting complete!"
