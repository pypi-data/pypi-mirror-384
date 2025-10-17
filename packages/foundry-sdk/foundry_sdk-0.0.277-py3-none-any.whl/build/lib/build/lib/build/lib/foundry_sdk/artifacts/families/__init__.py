"""
Model family implementations for foundry-sdk.

This package contains concrete implementations of BaseModelFamily for different
model types like XGBoost, PyTorch Lightning, sklearn, etc.
"""

from foundry_sdk.artifacts.families.xgb_family import XGBFamily

__all__ = [
    "XGBFamily",
]
