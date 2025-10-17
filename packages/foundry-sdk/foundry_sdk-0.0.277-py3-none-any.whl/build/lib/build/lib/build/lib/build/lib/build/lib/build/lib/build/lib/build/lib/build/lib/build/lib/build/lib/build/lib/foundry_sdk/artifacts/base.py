"""
Abstract base classes for the artifacts system.

This module defines the core interfaces that all model family implementations
must provide for artifact creation functionality.
"""

import typing as t
from abc import ABC, abstractmethod
from pathlib import Path

from foundry_sdk.artifacts.utils import save_json


class BaseReleaseManager(ABC):
    """
    Abstract base class for model family handlers.

    Each model family (torch-lightning, xgboost, etc.) must implement this
    interface to integrate with the artifact creation system.
    """

    @property
    @abstractmethod
    def family_name(self) -> str:
        """Return the unique identifier for this model family."""
        ...

    @abstractmethod
    def save_model_params(self, output_dir: Path, model: t.Any) -> None:
        """
        Save model parameters to output directory.

        Args:
            output_dir: Directory to save parameters to
            model: Model to save parameters for

        """
        ...

    def export_release(
        self,
        output_dir: Path,
        bundle: dict = None,
        metrics: dict = None,
        model: t.Any = None,
    ) -> Path:
        """
        Export release with standardized structure.

        Creates the release directory structure and coordinates saving of
        bundle.json, metrics.json, and model parameters.

        Args:
            output_dir: Base directory for release
            bundle: Bundle metadata dictionary
            metrics: Optional metrics dictionary
            model_params: Model parameters dictionary

        Returns:
            Path to created release directory

        """
        self.check_bundle(bundle)

        name = f"release_{bundle['release_name']}"

        # Create directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create folder inside directory with name release_[name]
        release_dir = output_dir / name
        release_dir.mkdir(parents=True, exist_ok=True)

        # Save bundle.json, metrics.json

        bundle_file = release_dir / "bundle.json"
        save_json(bundle, bundle_file)

        if metrics:
            metrics_file = release_dir / "metrics.json"
            save_json(metrics, metrics_file)

        # Create model_params folder
        model_params_dir = release_dir / "model_params"
        model_params_dir.mkdir(parents=True, exist_ok=True)

        # Get full path to model_params folder and call self.save_model_params
        # If model_params is a dict with models, iterate through them

        self.save_model_params(model_params_dir, model)

        return release_dir

    def check_bundle(self, bundle: dict) -> None:
        """
        Validate bundle dictionary structure.

        Ensures required fields are present in the bundle metadata.

        Args:
            bundle: Bundle metadata dictionary

        Raises:
            ValueError: If required fields are missing

        """
        required_fields = ["release_name"]
        for field in required_fields:
            if field not in bundle:
                raise ValueError(f"Bundle missing required field: {field}")
