"""
KNF Predictor - Ultra-fast supramolecular stability prediction
"""

__version__ = "2.0.1"
__author__ = "Prasanna P. Kulkarni"
__citation__ = """Kulkarni, P. P. (2025). A Physics-Informed Fingerprint for
Generalizable Prediction of Supramolecular Stability.
J. Chem. Inf. Model. (Submitted)"""

# Import prediction functions
from .predictor import predict_single, predict_batch

# Make everything available at package level
__all__ = [
    "predict_single",
    "predict_batch",
    "__version__",
    "__author__",
    "__citation__"
]
