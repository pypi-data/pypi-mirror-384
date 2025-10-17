"""
Foundry SDK Artifacts Package.

This package provides a release management system for creating
experiment releases from trained models during training runs.

The system uses a single BaseReleaseManager interface that model families
implement to handle experiment-specific release creation with standardized
directory structures and metadata generation.

Key Components:
- BaseReleaseManager: Single interface for release management
- XGBFamily: XGBoost implementation of BaseReleaseManager
- Release structure: release_<version>/ with bundle.json, metrics.json, model_params/
"""

from foundry_sdk.artifacts.base import BaseReleaseManager
from foundry_sdk.artifacts.families.xgb_family import XGBFamily

__all__ = [
    # Base interface
    "BaseReleaseManager",
    # Model family implementations
    "XGBFamily",
]
