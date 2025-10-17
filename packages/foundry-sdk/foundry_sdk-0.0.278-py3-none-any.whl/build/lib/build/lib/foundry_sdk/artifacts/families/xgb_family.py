"""
XGBoost release management implementation.

This module provides XGBoost-specific release creation functionality
that implements the BaseReleaseManager interface.
"""

import typing as t
from pathlib import Path

from foundry_sdk.artifacts.base import BaseReleaseManager
from foundry_sdk.artifacts.utils import save_json


class XGBFamily(BaseReleaseManager):
    """
    XGBoost release manager implementation.

    Handles XGBoost-specific model parameter storage and release creation.
    """

    @property
    def family_name(self) -> str:
        """Return the unique identifier for XGBoost family."""
        return "xgboost"

    def save_model_params(self, output_dir: Path, model: t.Any) -> None:
        """
        Save XGBoost model parameters to output directory.

        Creates individual directories for each model with weights and metadata.

        Args:
            output_dir: Directory to save model parameters (model_params folder)
            model: XGBoost model to save

        """
        # Create unique directory for this model
        model_dirs = list(output_dir.glob("model_*"))
        model_idx = len(model_dirs) + 1
        model_dir = output_dir / f"model_{model_idx:03d}"
        model_dir.mkdir(parents=True, exist_ok=True)

        # Get the booster for XGBoost models
        if hasattr(model, "get_booster"):
            booster = model.get_booster()
        else:
            booster = model

        # Save model weights as JSON
        weights_file = model_dir / "weights.json"
        booster.save_model(str(weights_file))

        # Save model metadata
        metadata = {
            "model_index": model_idx,
            "model_type": type(model).__name__,
            "family": self.family_name,
        }

        # Try to extract additional model info if available
        try:
            if hasattr(booster, "num_features"):
                metadata["num_features"] = booster.num_features()
            if hasattr(booster, "num_boosted_rounds"):
                metadata["num_boosted_rounds"] = booster.num_boosted_rounds()
        except Exception:
            # If we can't extract these, that's ok
            pass

        metadata_file = model_dir / "metadata.json"
        save_json(metadata, metadata_file)
