"""
KNF Predictor - Ultra-fast supramolecular stability prediction
"""

__version__ = "2.0.0"
__author__ = "Prasanna P. Kulkarni"

# Import prediction functions
from .predictor import predict_single, predict_batch

# Make everything available at package level
__all__ = [
    "predict_single",
    "predict_batch",
    "__version__",
    "__author__"
]
