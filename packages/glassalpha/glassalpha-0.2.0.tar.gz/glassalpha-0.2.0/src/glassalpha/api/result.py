"""AuditResult: Immutable result object with rich API

Phase 2: Core structure with deep immutability.
"""

from __future__ import annotations

import types
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


def _freeze_array(arr: np.ndarray) -> np.ndarray:
    """Make array C-contiguous and read-only.

    This ensures arrays in results cannot be mutated, maintaining
    audit integrity for compliance requirements.

    Args:
        arr: Array to freeze

    Returns:
        Read-only, C-contiguous copy of array

    """
    # Always create a copy to avoid modifying the original
    arr = np.array(arr, copy=True, order="C")
    arr.setflags(write=False)
    return arr


class MetricsProxy:
    """Immutable wrapper that supports both dict and attribute access.

    Enables intuitive API usage:
        result.performance.accuracy  # Attribute access
        result.performance['accuracy']  # Dict access
        result.performance.keys()  # Dict methods

    """

    def __init__(self, data: Mapping[str, Any]):
        """Initialize with immutable data."""
        object.__setattr__(self, "_data", types.MappingProxyType(dict(data)))

    def __getattr__(self, name: str) -> Any:
        """Support attribute access for metrics."""
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        try:
            return self._data[name]
        except KeyError:
            available = ", ".join(sorted(self._data.keys())[:5])
            raise AttributeError(
                f"Metric '{name}' not found. Available metrics: {available}..."
                if len(self._data) > 5
                else f"Metric '{name}' not found. Available metrics: {available}"
            ) from None

    def __getitem__(self, key: str) -> Any:
        """Support dict-style access."""
        return self._data[key]

    def __repr__(self) -> str:
        """Show available metrics."""
        return f"MetricsProxy({list(self._data.keys())})"

    def __len__(self) -> int:
        """Return number of metrics."""
        return len(self._data)

    def __iter__(self):
        """Iterate over metric names."""
        return iter(self._data)

    def keys(self):
        """Return metric names."""
        return self._data.keys()

    def values(self):
        """Return metric values."""
        return self._data.values()

    def items(self):
        """Return metric items."""
        return self._data.items()

    def get(self, key, default=None):
        """Get metric with default."""
        return self._data.get(key, default)

    def __contains__(self, key):
        """Check if metric exists."""
        return key in self._data


@dataclass(frozen=True)
class AuditResult:
    """Immutable audit result with deterministic ID.

    All audit results are deeply immutable to ensure compliance integrity.
    Results can be compared via strict equality (result.id) or tolerance-based
    equality (result.equals()) for cross-platform reproducibility.

    Attributes:
        id: SHA-256 hash of canonical result dict (deterministic)
        schema_version: Result schema version (e.g., "0.2.0")
        manifest: Provenance metadata (Mapping, immutable)
        performance: Performance metrics (PerformanceMetrics)
        fairness: Fairness metrics (FairnessMetrics)
        calibration: Calibration metrics (CalibrationMetrics)
        stability: Stability test results (StabilityMetrics)
        explanations: SHAP explanation summary (ExplanationSummary | None)
        recourse: Recourse generation summary (RecourseSummary | None)

    Examples:
        >>> result = ga.audit.from_model(model, X, y, protected_attributes={"gender": gender})
        >>> result.performance.accuracy  # 0.847
        >>> result.to_pdf("audit.pdf")
        >>> config = result.to_config()  # For reproduction

    """

    # Core identity
    id: str  # SHA-256 hash of canonical result dict
    schema_version: str  # e.g., "0.2.0"

    # Manifest (provenance, not hashed)
    manifest: Mapping[str, Any]

    # Metric sections (will be Mapping-like, immutable)
    performance: Mapping[str, Any]  # Will be PerformanceMetrics in full impl
    fairness: Mapping[str, Any]  # Will be FairnessMetrics
    calibration: Mapping[str, Any]  # Will be CalibrationMetrics
    stability: Mapping[str, Any]  # Will be StabilityMetrics
    explanations: Mapping[str, Any] | None = None  # Will be ExplanationSummary
    recourse: Mapping[str, Any] | None = None  # Will be RecourseSummary

    def __post_init__(self) -> None:
        """Freeze all mutable containers after initialization."""
        # Wrap manifest in MappingProxyType for immutability
        if not isinstance(self.manifest, types.MappingProxyType):
            object.__setattr__(self, "manifest", types.MappingProxyType(dict(self.manifest)))

        # Wrap metrics in MetricsProxy (supports both .attr and ['key'] access)
        for field in ["performance", "fairness", "calibration", "stability", "explanations", "recourse"]:
            value = getattr(self, field)
            if value is not None and not isinstance(value, MetricsProxy):
                object.__setattr__(self, field, MetricsProxy(value))

    def __eq__(self, other: object) -> bool:
        """Strict equality via result.id.

        Two results are equal if and only if their IDs match.
        This ensures byte-identical reproducibility for compliance.

        For tolerance-based comparison, use result.equals().
        """
        if not isinstance(other, AuditResult):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Stable hash via result.id (first 16 hex chars).

        Enables use in sets and as dict keys.
        Hash is stable across pickle round-trips.
        """
        return int(self.id[:16], 16)

    def __getstate__(self) -> dict[str, Any]:
        """Pickle support: convert MappingProxyType to dict."""
        state = {
            "id": self.id,
            "schema_version": self.schema_version,
            "manifest": dict(self.manifest),
            "performance": dict(self.performance),
            "fairness": dict(self.fairness),
            "calibration": dict(self.calibration),
            "stability": dict(self.stability),
            "explanations": dict(self.explanations) if self.explanations else None,
            "recourse": dict(self.recourse) if self.recourse else None,
        }
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Unpickle support: restore frozen dataclass fields."""
        # Restore each field using object.__setattr__ (frozen dataclass)
        object.__setattr__(self, "id", state["id"])
        object.__setattr__(self, "schema_version", state["schema_version"])
        object.__setattr__(self, "manifest", types.MappingProxyType(state["manifest"]))
        object.__setattr__(self, "performance", types.MappingProxyType(state["performance"]))
        object.__setattr__(self, "fairness", types.MappingProxyType(state["fairness"]))
        object.__setattr__(self, "calibration", types.MappingProxyType(state["calibration"]))
        object.__setattr__(self, "stability", types.MappingProxyType(state["stability"]))
        object.__setattr__(
            self,
            "explanations",
            types.MappingProxyType(state["explanations"]) if state["explanations"] else None,
        )
        object.__setattr__(
            self,
            "recourse",
            types.MappingProxyType(state["recourse"]) if state["recourse"] else None,
        )

    def equals(
        self,
        other: AuditResult,
        rtol: float = 1e-5,
        atol: float = 1e-8,
    ) -> bool:
        """Tolerance-based equality across all metrics.

        Use this for cross-platform reproducibility testing where
        floating point differences may occur due to different BLAS
        implementations or CPU architectures.

        Args:
            other: Result to compare against
            rtol: Relative tolerance (default: 1e-5)
            atol: Absolute tolerance (default: 1e-8)

        Returns:
            True if all metrics match within tolerance

        Examples:
            >>> result1 == result2  # Strict: byte-identical IDs
            False
            >>> result1.equals(result2, rtol=1e-5)  # Tolerant: float differences OK
            True

        """
        if self.id == other.id:
            return True

        # Compare each metric section with tolerance
        sections = ["performance", "fairness", "calibration", "stability"]
        for section in sections:
            self_metrics = dict(getattr(self, section))
            other_metrics = dict(getattr(other, section))

            if self_metrics.keys() != other_metrics.keys():
                return False

            for key, v1 in self_metrics.items():
                v2 = other_metrics[key]

                # Handle None gracefully
                if v1 is None and v2 is None:
                    continue
                if v1 is None or v2 is None:
                    return False

                # Compare with tolerance
                try:
                    if not np.allclose(v1, v2, rtol=rtol, atol=atol, equal_nan=True):
                        return False
                except (TypeError, ValueError):
                    # Non-numeric comparison
                    if v1 != v2:
                        return False

        return True

    def __repr__(self) -> str:
        """Compact repr for logging."""
        return f"AuditResult(id='{self.id[:12]}...', schema_version='{self.schema_version}')"

    def _repr_html_(self) -> str:
        """Rich display in Jupyter (O(1) complexity).

        Shows high-level summary without computing expensive metrics.
        """
        # Type-guard formatting to prevent crashes
        perf = dict(self.performance)

        acc = perf.get("accuracy")
        acc_str = f"{acc:.3f}" if isinstance(acc, (int, float)) else "N/A"

        auc = perf.get("roc_auc")
        auc_str = f"{auc:.3f}" if isinstance(auc, (int, float)) else "N/A"

        fair = dict(self.fairness)
        dp_max = fair.get("demographic_parity_max_diff")
        dp_str = f"{dp_max:.3f}" if isinstance(dp_max, (int, float)) else "N/A"

        return f"""
        <div style="border:1px solid #ddd; padding:10px; border-radius:5px;">
            <h3>GlassAlpha Audit Result</h3>
            <table>
                <tr><td><b>ID:</b></td><td><code>{self.id[:16]}...</code></td></tr>
                <tr><td><b>Accuracy:</b></td><td>{acc_str}</td></tr>
                <tr><td><b>ROC AUC:</b></td><td>{auc_str}</td></tr>
                <tr><td><b>Fairness (max ΔDP):</b></td><td>{dp_str}</td></tr>
            </table>
            <p><i>Use <code>result.to_pdf('audit.pdf')</code> for full report</i></p>
        </div>
        """

    def summary(self) -> dict[str, Any]:
        """Lightweight summary for logging (O(1)).

        Returns dictionary with key metrics for quick inspection.
        Does not compute expensive operations.

        Returns:
            Dictionary with id, schema_version, and key metrics

        """
        return {
            "id": self.id[:16],
            "schema_version": self.schema_version,
            "performance": {
                k: dict(self.performance)[k]
                for k in ["accuracy", "precision", "recall", "f1"]
                if k in dict(self.performance)
            },
            "fairness": {
                k: dict(self.fairness)[k]
                for k in ["demographic_parity_max_diff", "equalized_odds_max_diff"]
                if k in dict(self.fairness)
            },
        }

    def to_json(self, path: str | Path, *, overwrite: bool = False) -> None:
        """Export to JSON with atomic write.

        Uses same canonicalization as result.id computation
        (strict JSON, NaN→null, Inf→sentinel).

        Args:
            path: Output path for JSON file
            overwrite: If True, overwrite existing file

        Raises:
            GlassAlphaError: If file exists and overwrite=False

        """
        msg = (
            "JSON export for AuditResult is not yet implemented. "
            "Workaround: Access metrics directly via result.performance, result.fairness, etc. "
            "and serialize manually with json.dumps(). "
            "Track progress: https://github.com/GlassAlpha/glassalpha/issues"
        )
        raise NotImplementedError(msg)

    def to_html(self, path: str | Path, *, overwrite: bool = False) -> Path:
        """Export to HTML file with atomic write.

        Args:
            path: Output path for HTML file
            overwrite: If True, overwrite existing file

        Returns:
            Path to generated HTML file

        Raises:
            GlassAlphaError: If file exists and overwrite=False

        Example:
            >>> result = ga.audit.from_model(model, X, y)
            >>> result.to_html("audit_report.html")

        """
        from pathlib import Path

        output_path = Path(path)

        # Check for existing file
        if output_path.exists() and not overwrite:
            from ..exceptions import FileExistsError as GAFileExistsError

            raise GAFileExistsError(path=str(output_path))

        # Generate HTML content using existing _repr_html_ method
        html_content = self._repr_html_()

        # Write to file atomically
        output_path.write_text(html_content, encoding="utf-8")

        # Generate manifest sidecar
        from ..provenance import write_manifest_sidecar

        try:
            write_manifest_sidecar(dict(self.manifest), output_path)
        except Exception:
            pass  # Non-critical

        return output_path

    def to_pdf(self, path: str | Path, *, overwrite: bool = False) -> Path:
        """Export to PDF with atomic write.

        Args:
            path: Output path for PDF file
            overwrite: If True, overwrite existing file

        Returns:
            Path to generated PDF file

        Raises:
            GlassAlphaError: If file exists and overwrite=False
            ImportError: If PDF dependencies not installed (pip install glassalpha[all])

        Example:
            >>> result = ga.audit.from_model(model, X, y)
            >>> result.to_pdf("audit.pdf")

        """
        from pathlib import Path

        output_path = Path(path)

        # Check for existing file
        if output_path.exists() and not overwrite:
            from ..exceptions import FileExistsError as GAFileExistsError

            raise GAFileExistsError(path=str(output_path))

        # Convert AuditResult to AuditResults format for PDF renderer
        from ..pipeline.audit import AuditResults

        # Create AuditResults instance from AuditResult data
        audit_results = AuditResults(
            model_performance=dict(self.performance),
            fairness_analysis=dict(self.fairness),
            drift_analysis={},  # Not in AuditResult
            stability_analysis=dict(self.stability),
            explanations=dict(self.explanations) if self.explanations else {},
            data_summary={
                "n_samples": self.manifest.get("n_samples", 0),
                "n_features": self.manifest.get("n_features", 0),
            },
            schema_info={},
            model_info={
                "model_type": self.manifest.get("model_type", "unknown"),
                "fingerprint": self.manifest.get("model_fingerprint", "unknown"),
            },
            selected_components={},
            trained_model=None,
            execution_info={"provenance_manifest": dict(self.manifest)},
            manifest=dict(self.manifest),
            success=True,
            error_message=None,
        )

        # Import PDF renderer
        try:
            from ..report import PDFConfig, render_audit_pdf
        except ImportError:
            raise ImportError(
                "PDF generation requires additional dependencies.\n"
                "Install with: pip install 'glassalpha[all]'\n"
                "Or use HTML output: result.to_html('audit.html')",
            ) from None

        # Create PDF configuration
        pdf_config = PDFConfig(
            page_size="A4",
            title="ML Model Audit Report",
            author="GlassAlpha",
            subject="Machine Learning Model Compliance Assessment",
            optimize_size=True,
        )

        # Use deterministic timestamp if SOURCE_DATE_EPOCH is set
        import os
        from datetime import UTC, datetime

        source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
        if source_date_epoch:
            report_date = datetime.fromtimestamp(int(source_date_epoch), tz=UTC).strftime("%Y-%m-%d")
            generation_date = datetime.fromtimestamp(int(source_date_epoch), tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            report_date = datetime.now().strftime("%Y-%m-%d")
            generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Generate PDF
        pdf_path = render_audit_pdf(
            audit_results=audit_results,
            output_path=output_path,
            config=pdf_config,
            report_title=f"ML Model Audit Report - {report_date}",
            generation_date=generation_date,
        )

        # Generate manifest sidecar
        from ..provenance import write_manifest_sidecar

        try:
            write_manifest_sidecar(dict(self.manifest), output_path)
        except Exception:
            pass  # Non-critical

        return pdf_path

    def to_config(self) -> dict[str, Any]:
        """Generate config dict for reproduction.

        Returns dict with all parameters needed to reproduce this result:
        - model fingerprint
        - data hashes (with "sha256:" prefix)
        - protected attributes (categories + order)
        - random seed
        - expected result ID

        Returns:
            Dictionary with reproduction parameters

        """
        return {
            "model": {
                "fingerprint": self.manifest["model_fingerprint"],
                "type": self.manifest["model_type"],
            },
            "data": {
                "X_hash": self.manifest["data_hash_X"],  # "sha256:abc..."
                "y_hash": self.manifest["data_hash_y"],
                "n_samples": self.manifest["n_samples"],
                "n_features": self.manifest["n_features"],
            },
            "protected_attributes": self.manifest["protected_attributes_categories"],
            "random_seed": self.manifest["random_seed"],
            "expected_result_id": self.id,
            "schema_version": self.schema_version,
        }

    def save(self, path: str | Path, *, overwrite: bool = False) -> Path:
        """Save audit result (auto-detects format from extension).

        Args:
            path: Output file path (.html or .pdf)
            overwrite: If True, overwrite existing file

        Returns:
            Path to generated file

        Raises:
            GlassAlphaError: If file exists and overwrite=False
            ImportError: If PDF format requested but dependencies not installed

        Example:
            >>> result = ga.audit.from_model(model, X, y)
            >>> result.save("audit.html")  # HTML format
            >>> result.save("audit.pdf")   # PDF format

        """
        from pathlib import Path

        path = Path(path)

        if path.suffix.lower() == ".pdf":
            return self.to_pdf(path, overwrite=overwrite)
        if path.suffix.lower() in [".html", ".htm"]:
            return self.to_html(path, overwrite=overwrite)
        raise ValueError(f"Unknown format: {path.suffix}. Use .pdf or .html extension")

    def to_evidence_pack(self, output_path: str | Path, *, overwrite: bool = False) -> Path:
        """Export audit result to evidence pack.

        Creates a tamper-evident ZIP bundle containing:
        - Audit report (HTML format)
        - Provenance manifest
        - Policy decision stub
        - Verification instructions
        - Checksums for all artifacts

        Args:
            output_path: Output ZIP path (.zip extension)
            overwrite: If True, overwrite existing file

        Returns:
            Path to generated evidence pack ZIP

        Raises:
            GlassAlphaError: If file exists and overwrite=False
            ImportError: If evidence pack dependencies not available

        Example:
            >>> result = ga.audit.from_model(model, X, y)
            >>> result.to_evidence_pack("audit_evidence.zip")
            PosixPath('audit_evidence.zip')

            >>> # Include custom output path
            >>> result.to_evidence_pack("custom_name.zip")
        """
        from pathlib import Path

        output_path = Path(output_path)

        # Check for existing file
        if output_path.exists() and not overwrite:
            from ..exceptions import FileExistsError as GAFileExistsError

            raise GAFileExistsError(path=str(output_path))

        # Validate extension
        if output_path.suffix.lower() != ".zip":
            raise ValueError(f"Evidence pack must have .zip extension, got {output_path.suffix}")

        # First save as HTML for the evidence pack
        html_path = output_path.with_suffix(".html")
        self.to_html(html_path, overwrite=overwrite)

        # Create evidence pack from HTML report
        from ..evidence import create_evidence_pack

        pack_path = create_evidence_pack(
            audit_report_path=html_path,
            output_path=output_path,
            include_badge=True,
        )

        return pack_path
