"""
Example: Integrating XGBFamily with BenchmarkPipeline training abstraction.

This example shows how to save hyperparameters and model weights from your
existing training pipeline using the artifacts system.
"""

import json
from pathlib import Path

from foundry_sdk.artifacts import XGBFamily
from foundry_sdk.artifacts.schema import ArchitectureSpec, BundleSchema, DataSpec, EnvironmentSpec, LineageSpec
from foundry_sdk.artifacts.utils import create_manifest, save_json


def save_xgb_experiment_artifacts(
    xgb_model,
    training_config,
    data_config,
    experiment_name: str,
    output_dir: Path,
    sku_tuples=None,
):
    """
    Save complete XGBoost experiment artifacts.

    Args:
        xgb_model: Trained XGBoost model from xgb_pipeline.run_experiment()
        training_config: Your TrainingConfig object
        data_config: Your DataConfig object
        experiment_name: Name for this experiment
        output_dir: Directory to save artifacts
        sku_tuples: Optional SKU information for lineage

    """
    # Create XGBoost family handler
    xgb_family = XGBFamily()

    # Verify this is an XGBoost model
    if not xgb_family.can_handle_model(xgb_model):
        raise ValueError(f"Model type {type(xgb_model)} is not supported by XGBFamily")

    # Create bundle directory structure
    bundle_dir = output_dir / f"{experiment_name}_bundle"
    bundle_subdir = bundle_dir / "bundle"
    model_dir = bundle_dir / "model"

    bundle_subdir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    # 1. Extract architecture specification (includes hyperparameters)
    arch_data = xgb_family.extract_architecture_spec(xgb_model, training_config)
    arch_spec = ArchitectureSpec(class_path=arch_data["class_path"], **arch_data)

    # 2. Extract data specification
    data_spec_data = xgb_family.extract_data_spec(data_config=data_config)
    data_spec = DataSpec(**data_spec_data)

    # 3. Create lineage information
    lineage_data = {
        "experiment_name": experiment_name,
        "training_strategy": "INDIVIDUAL",  # From your ModelingStrategy
        "created_at": None,  # Will be set by Pydantic
    }

    if sku_tuples:
        lineage_data["sku_count"] = len(sku_tuples)
        lineage_data["sku_sample"] = str(sku_tuples[:5])  # First 5 for reference

    lineage_spec = LineageSpec(**lineage_data)

    # 4. Create environment specification
    env_spec = EnvironmentSpec(
        python="3.11",  # Adjust as needed
        foundry_sdk="0.1.0",  # Your version
        # Add other relevant package versions
    )

    # 5. Create complete bundle schema
    bundle = BundleSchema(
        bundle_version="0.1",
        family="xgboost",
        arch=arch_spec,
        data_spec=data_spec,
        lineage=lineage_spec,
        env=env_spec,
    )

    # 6. Save model weights
    saved_files = xgb_family.save_model_weights(xgb_model, model_dir)
    print(f"Saved model files: {saved_files}")

    # 7. Save bundle JSON
    bundle_json_path = bundle_subdir / "foundry_bundle.json"
    save_json(bundle.dict(), bundle_json_path)

    # 8. Create metrics file (extract from your pipeline if available)
    metrics_data = {
        "model_type": training_config.model_configs[0].model_type,
        "quantile_alpha": getattr(training_config.model_configs[0], "quantile_alpha", None),
        "num_features": arch_data.get("num_features"),
        "num_boosted_rounds": arch_data.get("num_boosted_rounds"),
        "created_at": None,  # Will be set automatically
    }

    # Add any performance metrics you have
    # if hasattr(xgb_model, "best_score"):
    #     metrics_data["best_score"] = xgb_model.best_score

    metrics_path = bundle_subdir / "metrics.json"
    save_json(metrics_data, metrics_path)

    # 9. Create manifest for integrity checking
    manifest = create_manifest(bundle_dir)
    manifest_path = bundle_subdir / "MANIFEST.json"
    save_json(manifest.dict(), manifest_path)

    # 10. Create README
    readme_content = f"""# XGBoost Model: {experiment_name}

## Overview
- **Model Type**: {training_config.model_configs[0].model_type}
- **Quantile Alpha**: {getattr(training_config.model_configs[0], "quantile_alpha", "N/A")}
- **Features**: {arch_data.get("num_features", "Unknown")}
- **Boosting Rounds**: {arch_data.get("num_boosted_rounds", "Unknown")}

## Hyperparameters
```json
{json.dumps(arch_data.get("hyperparameters", {}), indent=2)}
```

## Usage
```python
from foundry_sdk.artifacts import XGBFamily
family = XGBFamily()
model, bundle = family.load_bundle("{bundle_dir}")
```
"""

    readme_path = bundle_dir / "README.md"
    readme_path.write_text(readme_content)

    print(f"✅ Saved complete experiment artifacts to: {bundle_dir}")
    print("📊 Bundle contains: model weights, hyperparameters, data config, lineage")

    return bundle_dir


def load_xgb_experiment(bundle_path: Path):
    """
    Load XGBoost experiment from saved artifacts.

    Args:
        bundle_path: Path to the bundle directory

    Returns:
        Tuple of (model, bundle_schema)

    """
    xgb_family = XGBFamily()

    # Load bundle schema
    from foundry_sdk.artifacts.utils import validate_bundle_structure

    bundle = validate_bundle_structure(bundle_path)

    # Validate it's XGBoost
    xgb_family.validate_bundle(bundle)

    # Reconstruct model
    model = xgb_family.reconstruct_model(bundle)

    # Load weights
    model_dir = bundle_path / "model"
    loaded_model = xgb_family.load_model_weights(model, model_dir, bundle)

    print(f"✅ Loaded XGBoost model from: {bundle_path}")
    print(f"📊 Model type: {bundle.get_family_specific_data('arch').get('model_type')}")
    print(f"🔧 Hyperparameters: {bundle.get_family_specific_data('arch').get('hyperparameters')}")

    return loaded_model, bundle


# Example usage with your training pipeline:
def example_integration():
    """Example showing complete integration with your pipeline."""
    # Your existing training code
    xgb_config = TrainingConfig(random_state=42)
    xgb_config.add_model_config(
        model_type="xgboost_quantile",
        quantile_alpha=0.7,
        hyperparameters={
            "tree_method": "hist",
            "max_depth": 6,
            "learning_rate": 0.3,
            "subsample": 1.0,
            "colsample_bytree": 1.0,
            "reg_alpha": 0.0,
            "reg_lambda": 1.0,
            "random_state": 42,
        },
    )

    xgb_pipeline = BenchmarkPipeline(data_config=data_config, training_config=xgb_config, output_dir=Path("model_test"))

    xgb_pipeline.load_and_prepare_data()
    xgb_model = xgb_pipeline.run_experiment(
        sku_tuples=sku_tuples, modeling_strategy=ModelingStrategy.INDIVIDUAL, experiment_name="test_exp"
    )

    # NEW: Save artifacts using the artifacts system
    bundle_path = save_xgb_experiment_artifacts(
        xgb_model=xgb_model,
        training_config=xgb_config,
        data_config=data_config,
        experiment_name="test_exp",
        output_dir=Path("artifacts"),
        sku_tuples=sku_tuples,
    )

    # Later: Load the saved model
    loaded_model, bundle = load_xgb_experiment(bundle_path)

    # Verify hyperparameters were preserved
    saved_hyperparams = bundle.get_family_specific_data("arch")["hyperparameters"]
    original_hyperparams = xgb_config.model_configs[0].hyperparameters

    print("✅ Hyperparameters match:", saved_hyperparams == original_hyperparams)


if __name__ == "__main__":
    example_integration()
