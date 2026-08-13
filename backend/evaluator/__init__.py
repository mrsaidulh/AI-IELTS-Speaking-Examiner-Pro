# Evaluator package initialization
import sys
from pathlib import Path

# Try relative import first, then fallback to module import
try:
    from .evaluator import evaluate
except ImportError:
    try:
        from evaluator import evaluate
    except ImportError:
        pass
