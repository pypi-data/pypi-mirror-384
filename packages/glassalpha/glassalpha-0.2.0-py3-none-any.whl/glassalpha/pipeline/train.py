"""Training utilities for GlassAlpha pipeline.

This module provides utilities for training models from configuration,
ensuring that model parameters from YAML configuration are properly
passed to the underlying estimators.
"""

import logging
import warnings
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def train_from_config(cfg: Any, X: pd.DataFrame, y: Any) -> Any:
    """Train a model from configuration parameters with optional calibration.

    Args:
        cfg: Configuration object with model.type, model.params, and optional model.calibration
        X: Training features
        y: Target values

    Returns:
        Trained model instance (potentially calibrated)

    Raises:
        ValueError: If model type is not found in registry
        RuntimeError: If model doesn't support fit method

    """
    # Get model type from config
    model_type = cfg.model.type

    # Load model using explicit dispatch
    from glassalpha.models import load_model

    try:
        model_class = load_model(model_type)
    except ValueError as e:
        msg = f"Unknown model type: {model_type}"
        raise ValueError(msg) from e

    logger.info(f"Training {model_type} model from configuration")

    # Get model wrapper instance
    model = model_class

    # Extract parameters from config
    params = dict(getattr(cfg.model, "params", {}))

    # Add random_state if specified in config
    if hasattr(cfg, "random_seed"):
        params["random_state"] = cfg.random_seed
    elif isinstance(cfg, dict) and "reproducibility" in cfg:
        # Backward compatibility for dict configs
        params["random_state"] = cfg.get("reproducibility", {}).get("random_seed", 42)

    # Fit model with parameters
    if not hasattr(model, "fit"):
        msg = f"Model type {model_type} does not support fit method"
        raise RuntimeError(msg)

    logger.info(f"Fitting model with parameters: {list(params.keys())}")
    logger.info(f"Parameter values: {params}")

    # Check if we need probability predictions
    # Default to True for audit purposes (needed for AUC, calibration, etc.)
    # Only set to False if user explicitly requests it via config
    require_proba = getattr(cfg.model, "require_proba", True)

    # Also check calibration config for later use
    calibration_config = getattr(cfg.model, "calibration", None)

    try:
        # Suppress sklearn convergence warnings for better UX
        # These warnings don't affect audit quality and scare users unnecessarily
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=Warning, message=".*lbfgs failed to converge.*")
            warnings.filterwarnings("ignore", category=Warning, message=".*TOTAL NO. OF ITERATIONS REACHED LIMIT.*")
            warnings.filterwarnings("ignore", category=Warning, message=".*Increase the number of iterations.*")

            model.fit(X, y, require_proba=require_proba, **params)
    except ValueError as e:
        # Provide helpful error messages for common issues
        error_msg = str(e)

        # Check for missing value errors
        if "NaN" in error_msg or "missing" in error_msg.lower():
            # Detect which columns have missing values
            import pandas as pd

            missing_info = {}
            if isinstance(X, pd.DataFrame):
                missing_cols = X.columns[X.isna().any()].tolist()
                missing_info = {
                    col: (X[col].isna().sum(), (X[col].isna().sum() / len(X)) * 100) for col in missing_cols
                }

            # Build helpful error message
            msg = "❌ Model training failed: Your data contains missing values (NaN)\n\n"

            if missing_info:
                msg += "Missing values detected in:\n"
                for col, (count, pct) in missing_info.items():
                    msg += f"  • {col}: {count} missing ({pct:.1f}%)\n"
                msg += "\n"

            msg += "💡 Quick fixes:\n"
            msg += "  1. Remove rows with missing values:\n"
            msg += "     df = df.dropna()\n\n"
            msg += "  2. Fill with mean/median/mode:\n"
            msg += "     # For numeric columns\n"
            msg += "     df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())\n"
            msg += "     # For categorical columns\n"
            msg += "     df[cat_cols] = df[cat_cols].fillna(df[cat_cols].mode().iloc[0])\n\n"
            msg += "  3. Use sklearn SimpleImputer (recommended):\n"
            msg += "     from sklearn.impute import SimpleImputer\n"
            msg += "     imputer = SimpleImputer(strategy='mean')  # or 'median', 'most_frequent'\n"
            msg += "     X_imputed = imputer.fit_transform(X)\n\n"
            msg += "📖 For more help, see: https://scikit-learn.org/stable/modules/impute.html"

            raise ValueError(msg) from e

        # Re-raise original error if not a known case
        raise

    logger.info(f"Model training completed for {model_type}")

    # Apply calibration if requested
    if calibration_config and calibration_config.method:
        from ..models.calibration import maybe_calibrate

        logger.info("Applying probability calibration")

        # Get the underlying sklearn-compatible estimator
        base_estimator = getattr(model, "model", model)

        # Apply calibration
        calibrated_estimator = maybe_calibrate(
            base_estimator,
            method=calibration_config.method,
            cv=calibration_config.cv,
            ensemble=calibration_config.ensemble,
        )

        # Update the model's estimator
        if hasattr(model, "model"):
            model.model = calibrated_estimator
            logger.info("Updated wrapper with calibrated estimator")
        else:
            # For models that don't have a .model attribute, we need to handle differently
            logger.warning("Model wrapper doesn't have .model attribute, calibration may not work properly")

        # Re-fit the calibrated estimator (CalibratedClassifierCV needs this)
        if hasattr(calibrated_estimator, "fit"):
            # Encode labels if the wrapper has label encoding
            y_for_calibration = y
            if hasattr(model, "_encode_labels"):
                y_for_calibration = model._encode_labels(y)
            elif hasattr(model, "classes_") and hasattr(model, "_label_encoder"):
                # Use existing label encoding if available
                y_for_calibration = model._label_encoder.transform(y)

            calibrated_estimator.fit(X, y_for_calibration)
            logger.info("Calibrated estimator fitted successfully")

    return model
