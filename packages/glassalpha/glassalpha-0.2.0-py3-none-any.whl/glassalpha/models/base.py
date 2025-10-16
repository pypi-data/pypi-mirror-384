# SPDX-License-Identifier: Apache-2.0
"""Base wrapper functionality for tabular model wrappers.

This module provides common functionality that prevents regression of
the chronic save/load and column handling issues.
"""

import logging
from pathlib import Path
from typing import Any

from glassalpha.constants import ERR_NOT_FITTED

# Conditional imports
try:
    import joblib

    JOBLIB_AVAILABLE = True
except ImportError:
    joblib = None
    JOBLIB_AVAILABLE = False

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)


def _ensure_fitted(obj: Any, attr: str = "_fitted_", message: str = ERR_NOT_FITTED) -> None:
    """Ensure object is fitted, raise if not.

    Args:
        obj: Object to check
        attr: Attribute name to check (not used for tabular wrappers)
        message: Error message to raise

    Raises:
        ValueError: If object is not fitted

    """
    # For tabular wrappers, check if model attribute exists
    if (hasattr(obj, "model") and obj.model is None) or (hasattr(obj, "_is_fitted") and not obj._is_fitted):
        raise ValueError(message)


class BaseTabularWrapper:
    """Base class for tabular model wrappers with robust save/load and column handling."""

    def __init__(self) -> None:
        """Initialize base wrapper."""
        self.model = None
        self.feature_names_ = None
        self.n_classes = None
        self._is_fitted = False

    def _ensure_fitted(self) -> None:
        """Ensure model is fitted, raise if not.

        Raises:
            ValueError: If model is not loaded/fitted

        """
        if self.model is None:
            raise ValueError(ERR_NOT_FITTED)

    def _prepare_x(self, X: Any) -> Any:
        """Robust DataFrame column handling - uses centralized feature alignment.

        Contract compliance: Uses shared align_features function for consistent
        feature drift handling across all wrappers.

        Args:
            X: Input features (DataFrame or array)

        Returns:
            Prepared features with proper alignment

        """
        return self._align_features(X)

    def _align_features(self, X: Any) -> Any:
        """Shared feature alignment helper - contract compliance.

        Implements the exact feature drift contract:
        1. Same names → return in expected order
        2. Same width but renamed → accept positionally
        3. Otherwise → reindex (drop extras, fill missing with 0)

        Args:
            X: Input features (DataFrame or array)

        Returns:
            Aligned features with proper column handling

        """
        # Pass-through when not a DataFrame or we don't know expected names
        expected = getattr(self, "feature_names_", None)
        if not PANDAS_AVAILABLE or not isinstance(X, pd.DataFrame) or not expected:
            return X

        expected = list(expected)

        # 1) Exact name match → return in expected order
        if list(X.columns) == expected:
            return X[expected]

        # 2) Same width but renamed → accept positionally, then name as expected
        if X.shape[1] == len(expected):
            X_positional = X.iloc[:, : len(expected)].copy()
            X_positional.columns = expected
            return X_positional

        # 3) Check for feature mismatch before reindexing
        actual_cols = set(X.columns)
        expected_cols = set(expected)
        overlap = actual_cols.intersection(expected_cols)

        # If there's no overlap in feature names, this is likely an error
        if not overlap:
            # Provide helpful error message about preprocessing mismatch
            error_msg = (
                f"❌ Feature mismatch: Model expects {len(expected)} features but data has {len(X.columns)} columns.\n"
                f"\n"
                f"This usually means:\n"
                f"  • Model trained on preprocessed data (one-hot encoded, scaled)\n"
                f"  • But you're providing raw data with categorical columns\n"
                f"\n"
                f"Solutions:\n"
                f"  1. Use the same preprocessing pipeline that was used during training\n"
                f"  2. Retrain the model on the current data format\n"
                f"  3. Check glassalpha.com/guides/preprocessing/ for preprocessing verification\n"
                f"\n"
                f"Expected features: {expected[:5]}... ({len(expected)} total)\n"
                f"Got features: {list(X.columns)[:5]}... ({len(X.columns)} total)"
            )
            raise ValueError(error_msg)

        # If we're missing too many features (more than half), also raise error
        missing_count = len(expected_cols - actual_cols)
        if missing_count > len(expected) // 2:
            missing_features = list(expected_cols - actual_cols)[:10]
            extra_features = list(actual_cols - expected_cols)[:10]

            error_msg = (
                f"❌ Feature mismatch: Too many missing features.\n"
                f"\n"
                f"Expected: {len(expected)} features\n"
                f"Got: {len(X.columns)} columns\n"
                f"Missing: {missing_count} features\n"
                f"\n"
                f"Missing features (first 10): {missing_features}\n"
                f"Extra features (first 10): {extra_features}\n"
                f"\n"
                f"This usually indicates a preprocessing mismatch between training and inference.\n"
                f"See: glassalpha.com/guides/preprocessing/"
            )
            raise ValueError(error_msg)

        # Otherwise reindex: drop extras, fill missing with 0
        return X.reindex(columns=expected, fill_value=0)

    def save(self, path: Path) -> None:
        """Save model state to file.

        Args:
            path: File path to save to

        Raises:
            ValueError: If no model to save
            ImportError: If joblib not available

        """
        if not JOBLIB_AVAILABLE:
            msg = "joblib is required for saving models"
            raise ImportError(msg)

        self._ensure_fitted()

        save_dict = {
            "model": self.model,
            "feature_names_": self.feature_names_,
            "n_classes": self.n_classes,
            "_is_fitted": self._is_fitted,
        }

        # Create parent directory if it doesn't exist
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(save_dict, path)
        logger.info(f"Saved model state to {path}")

    def load(self, path: Path) -> "BaseTabularWrapper":
        """Load model state from file.

        Args:
            path: File path to load from

        Returns:
            Self (for method chaining)

        Raises:
            ImportError: If joblib not available

        """
        if not JOBLIB_AVAILABLE:
            msg = "joblib is required for loading models"
            raise ImportError(msg)

        save_dict = joblib.load(path)

        self.model = save_dict["model"]
        self.feature_names_ = save_dict.get("feature_names_")
        self.n_classes = save_dict.get("n_classes")
        self._is_fitted = save_dict.get("_is_fitted", True)

        logger.info(f"Loaded model state from {path}")
        return self
