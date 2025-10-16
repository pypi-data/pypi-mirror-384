# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - v0.2.1 Pre-PyPI Simplification

### Changed (Breaking)

- **BREAKING**: Renamed `GAConfig` → `AuditConfig` for clarity and consistency
- **BREAKING**: Moved example configs from `src/glassalpha/data/configs/` → `src/glassalpha/configs/` for clearer structure
- **BREAKING**: Simplified reproducibility configuration structure
  - **Migration**: Move `reproducibility:` fields to root level:
    - `reproducibility.random_seed` → `random_seed`
    - `reproducibility.strict` → `strict`
    - `reproducibility.thread_control` → `thread_control`
  - **Rationale**: Eliminates nested structure as part of v0.2.0 simplification. No backward compatibility provided since no external users yet (pre-PyPI).
- **CLI Command Organization** (Complete Refactor)
  - Extracted 4530-line `_legacy.py` monolith into 5 focused modules:
    - `audit.py` (1562 lines): Core audit command with shift analysis
    - `explain.py` (1733 lines): Explanation commands (reasons, recourse)
    - `config_cmds.py` (612 lines): Configuration management commands
    - `system.py` (453 lines): Environment checking and system info
    - `evidence.py` (156 lines): Evidence pack export and verification
  - Removed redundant `commands.py` backward compatibility shim
  - Updated architecture rules to prevent half-done refactors (Section 9: "No Half-Done Refactors")
  - Result: 36% reduction in largest file, clear functional organization, all tests passing
- Removed unused model registration functions (`register_xgboost`, `register_lightgbm`)
- Removed empty `config/` directory to eliminate architectural confusion
- Updated all documentation and manifest files to reference new config paths

### Removed

- **Registry Compatibility Stubs** (Architectural Cleanup)
  - Deleted `src/glassalpha/core/__init__.py` (168 lines of compatibility shims)
  - Deleted `src/glassalpha/datasets/registry.py` (88 lines)
  - Deleted `src/glassalpha/metrics/registry.py` (37 lines)
  - Replaced with explicit availability checking in CLI and pipeline
  - Component listing now uses direct runtime dependency checks
  - Dataset loading uses simple dict lookup with direct imports
  - Result: 293 lines removed, zero abstraction layers, fully explicit logic

**Major architectural simplification** before PyPI launch. All breaking changes documented below.

### Fixed

- **Recourse Command PolicyConstraints API** (P0 - Critical Fix)

  - Fixed parameter name mismatches in `PolicyConstraints.__init__` (now accepts both `feature_costs`/`cost_weights` and `feature_bounds`/`bounds`)
  - Fixed validation functions to accept multiple calling conventions (`validate_monotonic_constraints`, `validate_feature_bounds`)
  - Added XGBoost Booster wrapper for `predict_proba` compatibility in recourse generation
  - Documented known limitation: XGBoost models have limited recourse support due to DMatrix feature name constraints
  - Recommendation: Use sklearn-compatible models (LogisticRegression, RandomForest) for recourse, or use `glassalpha reasons` for XGBoost models
  - Result: Recourse command no longer crashes on PolicyConstraints initialization

- **PDF Generation Timeout Protection** (P0 - Critical Fix)
  - Fixed CLI progress_callback bug: `pdf_progress_relay` was defined but never passed to worker function
  - Added timeout enforcement to progress monitoring loop (5 minute max, 90 second stall detection)
  - Added `pytest-timeout` plugin to prevent tests from hanging indefinitely (180 second default)
  - Result: Tests no longer freeze during PDF generation, proper timeout handling in CLI

### Added

- **Evidence Pack Export** (E3: Enhancement 3 - v0.3.0)
  - CLI commands: `glassalpha export-evidence-pack`, `glassalpha verify-evidence-pack`
  - API method: `AuditResult.to_evidence_pack()` for programmatic export
  - Creates tamper-evident ZIP bundles with all audit artifacts and checksums
  - Generates SVG badges with pass/fail status and metrics for social sharing
  - Verification instructions included for independent validation
  - Deterministic pack naming and content for reproducible sharing
  - Exit code 0 for successful verification, 1 for failures (CLI integration ready)

### Architecture Simplification Complete ✅

**🎉 Successfully completed major architecture simplification with 100% test pass rate achieved.**

- **Deleted 16 test files** testing intentionally removed complexity (72 failing tests → 0)
- **Removed backwards compatibility tech debt** (4 modules deleted, no circular imports)
- **Achieved 1,090 passing tests** (100% pass rate, 44 skipped, 1 xpassed)
- **Simplified config imports** (`glassalpha.config` works directly)
- **Fixed deep merge function** for proper config dictionary merging
- **Updated PolicyConstraints class** for test compatibility
- **Fixed XGBoost logger paths** in softmax coercion tests

**Result**: Clean, maintainable codebase ready for PyPI launch and enterprise extension.

### Architecture Simplification (Breaking Changes)

**Note**: v0.2.0 is the first production release. Prior versions were internal development only with no external users, so migration guides are not provided.

- **Replaced Dynamic Registries with Explicit Dispatch**

  - Removed `src/glassalpha/core/registry.py` (187 lines) - dynamic plugin system
  - Removed `src/glassalpha/profiles/` (97 lines) - profile abstraction layer
  - Removed `src/glassalpha/core/interfaces.py` (156 lines) - interface declarations
  - Implemented explicit dispatch in `models/__init__.py`, `explain/__init__.py`, `metrics/__init__.py`
  - Imports now use `load_model()`, `select_explainer()`, `compute_metrics()` directly

- **Flattened Directory Structure**

  - Consolidated `models/tree_models.py` (XGBoost + LightGBM in one file)
  - Consolidated `explain/shap.py` (TreeSHAP + KernelSHAP together)
  - Consolidated `metrics/fairness.py` (all fairness metrics in one file)
  - Removed `src/glassalpha/core/` directory (replaced with direct imports)

- **Simplified Configuration System**

  - Removed profile-based configuration (`audit_profile` parameter)
  - Simplified YAML config to direct model/explainer/metric specification
  - Removed `src/glassalpha/config/strict.py` validation layer
  - Config now specifies `model.type`, `explainers.strategy`, `metrics.*` directly

- **Consolidated Similar Code**

  - Tree models (XGBoost, LightGBM) share 90% logic → single file
  - SHAP explainers (TreeSHAP, KernelSHAP) share patterns → single file
  - Fairness metrics share computation patterns → single file
  - Result: Easier to maintain and understand related functionality

- **Clear Error Messages for Extension Points**
  - `ValueError(f"Unknown model_type: {model_type}")` instead of registry lookup failures
  - `ImportError` with specific installation instructions for optional dependencies
  - Result: Users get actionable error messages with clear fixes

### Changed

- **CLI Simplification (Breaking)**

  - Reduced `audit` command parameters from 16 to 8 (50% reduction)
  - Moved runtime options to config file: `fast_mode`, `compact_report`, `no_fallback`
  - Moved `model.save_path` to config (was `--save-model` flag)
  - Auto-detect CI environment for reproduction mode (no manual flag needed)
  - Deleted debug flags: `--show-defaults`, `--check-output`, `--override`

- **Strict Mode Consolidation (Breaking)**

  - Consolidated 3 modes (`strict`, `strict_full`, `quick_mode`) into single `--strict` flag
  - New semantics: `--strict` requires artifact preprocessing and explicit schemas
  - Default mode allows built-in datasets with implicit schemas

- **Configuration Validation (Breaking)**

  - Moved all validation from `strict.py` to Pydantic validators in `schema.py`
  - Deleted `src/glassalpha/config/strict.py` (279 lines removed)
  - Validation now automatic on config construction

- **Exception Hierarchy (Breaking)**

  - Standardized all exceptions under `GlassAlphaError` base class
  - Added error codes: `ConfigError` (GAE5001), `ModelError` (GAE3001), `ExplainerError` (GAE3002), `MetricError` (GAE3003), `DeterminismError` (GAE6001), `BootstrapError` (GAE6002)
  - All exceptions now include: code, message, fix suggestion, docs link
  - `StrictModeError` removed (now raises `ValueError` from Pydantic)

- **Utils Package Organization**
  - Comprehensive `__init__.py` with 13 commonly-used utilities exported
  - Documented module responsibilities (12 modules)
  - Cleaner imports: `from glassalpha.utils import hash_dataframe, set_global_seed`

### Removed

- Deleted `src/glassalpha/config/strict.py` (279 lines) - validation now in Pydantic
- Deleted `src/glassalpha/profiles/base.py` (97 lines) - unused abstraction layer
- Removed `quick_mode` parameter from validation
- Removed `strict_full` flag (consolidated to `strict`)
- Removed `StrictModeError` exception (use `ValueError`)
- Removed 8 CLI parameters (moved to config or deleted)

### Performance

- ~850 lines of code removed across codebase
- 50% reduction in CLI parameters (16 → 8)
- Simpler architecture: single validation path, consistent exceptions
- Better maintainability: less abstraction overhead

### Added

- **Determinism Framework (Phase 1-3 Implementation)**

  - `DeterminismValidator` class for validating audit reproducibility
  - `validate_audit_determinism()` convenience function for quick validation
  - `DeterminismReport` dataclass with comprehensive validation results
  - Test isolation fixtures (`isolate_determinism_state`, `deterministic_env`)
  - Deterministic explainer selection with `select_explainer_deterministic()`
  - `ExplainerUnavailableError` for strict mode explainer validation
  - Comprehensive determinism user guide (`site/docs/guides/determinism.md`)
  - API documentation for determinism utilities

- **CI Hardening**

  - Dedicated determinism validation workflow (`.github/workflows/determinism.yml`)
  - Cross-platform hash validation (Linux + macOS)
  - Multi-run determinism tests (5 consecutive runs)
  - SHAP availability verification before determinism tests
  - Framework validation tests for `DeterminismValidator` and explainer selection

- **API Completeness for Launch**
  - Implemented `AuditResult.to_pdf()` method for PDF export from notebook results
  - PDF generation converts lightweight AuditResult to pipeline format for rendering
  - `result.save("audit.pdf")` now works (delegates to `to_pdf()`)
  - Automatic manifest sidecar generation for reproducibility

### Fixed

- **Determinism Critical Fixes (95% Reliability Achievement)**

  - Added SHAP availability check to `test_cli_determinism_regression_guard`
  - Test skips gracefully when SHAP unavailable (prevents non-deterministic fallback)
  - Enforced `sort_keys=True` for all JSON serialization in CLI commands
  - Enforced `sort_keys=True` in model I/O state serialization
  - Verified bootstrap operations use `np.random.RandomState(seed)` for determinism
  - Updated CI to verify SHAP before running determinism tests
  - Validated all JSON exports use deterministic serialization

- API documentation alignment with v0.2.0 implementation
  - Updated docs to show dict-based metric access (current) vs future rich objects (v0.3.0)
  - Marked policy gates as coming in v0.3.0 (planned feature E1)
  - Marked evidence pack export as coming in v0.3.0 (planned feature E3)
  - Marked plot methods as coming in v0.3.0 (planned feature QW4)
- Resolved `NotImplementedError` for `to_pdf()` method

### Added (Previous)

- **User-Facing Progress Bars** (P0 Feature - Notebook UX Completion)

  - CLI `audit` command shows progress bar during execution
  - `from_model()` API shows progress bar in notebooks (auto-detects Jupyter vs terminal)
  - Progress bars respect strict mode (disabled in strict mode for professional output)
  - Progress bars respect `GLASSALPHA_NO_PROGRESS=1` environment variable
  - Bootstrap operations (fairness + calibration CIs) show nested progress bars
  - Auto-detection of notebook environment via `tqdm.auto`
  - Why critical: Provides visual feedback during 30-60 second audits, improves UX

- **Distribution Infrastructure (P0 - PyPI Blockers)**

  - Packaging validation: `check-manifest` and `validate-pyproject` in CI
  - `twine check` validates wheel metadata before upload
  - Import time test enforces <200ms budget for CLI responsiveness
  - Import time tolerance: 200ms local, 300ms CI
  - Lazy loading verification: Heavy dependencies not loaded at import

- **Cross-Platform Wheel Building (P0)**

  - cibuildwheel workflow for Linux (x86_64) + macOS (x86_64, arm64)
  - Python 3.11, 3.12, 3.13 wheel building
  - Deterministic build environment (pinned BLAS threads, locale, timezone)
  - Smoke tests verify wheel installs and basic import on all platforms
  - TestPyPI publication on RC tags (e.g., `v0.2.1rc1`)

- **Testing Infrastructure (P1)**

  - Deterministic test environment via `pytest_sessionstart` hook
  - Environment pinning: `PYTHONHASHSEED=0`, `TZ=UTC`, `LC_ALL=C`, single-threaded BLAS
  - Property-based tests with Hypothesis for calibration metrics
    - ECE/MCE/Brier score invariants (range checks, MCE >= ECE)
    - Perfect calibration edge cases
    - Determinism verification across runs
    - Bootstrap CI coverage validation
  - Property-based tests for fairness/threshold selection
    - Youden threshold maximization property
    - Prevalence threshold matches positive rate
    - Rate metrics in [0, 1] range
    - Confusion matrix sum invariants
  - Notebook testing with pytest-nbmake
    - Automated execution of all example notebooks in CI
    - 180-second timeout per notebook
    - Validates API examples don't break

- **Security and Quality Gates (P1)**
  - pip-audit security scanning in CI (CVE detection)
  - Security report artifact uploaded for review (90-day retention)
  - Tox configuration for multi-Python testing (3.11, 3.12, 3.13)
  - Minimum dependency testing via `constraints/min.txt`
  - Pre-commit hooks (ruff, black, mypy, codespell, yamllint)

### Changed

- Temporarily disabled Docker workflow to focus CI resources on PyPI distribution (reassess in Phase 3)
- Added Hypothesis (>=6.92) to dev dependencies for property testing
- Updated CI to include security job in deployment gate

### Fixed

- **QuickStart Adult Income Configuration** (Critical User Experience Fix)

  - Fixed target column mismatch: `income` → `income_over_50k`
  - Fixed protected attributes: `["gender", "race"]` → `["sex", "race"]`
  - QuickStart now uses dataset schema functions instead of hardcoded mappings
  - Adult Income audits now work immediately after `glassalpha quickstart`

- **Matplotlib PNG Optimization** (File Size + Warning Fix)

  - Removed `optimize=True` parameter from `matplotlib.savefig()` (requires matplotlib >= 3.10)
  - Added Pillow-based PNG compression (30-50% file size reduction)
  - HTML reports reduced from ~57MB to ~15-20MB
  - Fixed warning: `"FigureCanvasAgg.print_png() got an unexpected keyword argument 'optimize'"`
  - Added `pillow>=10.0` to core dependencies

- **Reasons/Recourse Commands with Wrapped Models** (ECOA Compliance Feature Fix)

  - Fixed SHAP TreeExplainer compatibility with `XGBoostWrapper`
  - Commands now extract native model from wrapper automatically
  - Added informative message when extracting model: `"Extracted native model from wrapper"`
  - Improved error messages with actionable guidance
  - Both `reasons` and `recourse` commands now work with `--save-model` output

- **Documentation and Guides**

  - Updated CLI examples to use `--output` flag
  - Corrected `reasons` and `recourse` command examples (use `--model` + `--data`, not `--config`)
  - Added comprehensive [Strict Mode Guide](site/docs/guides/strict-mode.md)
  - Added [Troubleshooting Guide](site/docs/getting-started/troubleshooting.md)
  - Improved strict mode warning message with documentation link

- **Testing and Quality**

  - Added comprehensive smoke test script (`scripts/smoke_test.sh`)
  - Tests all critical user journeys before PyPI publication
  - Validates: QuickStart (both datasets), file sizes, warnings, model saving, CLI commands

- Added `refresh()` method to `_PassthroughProgressBar` for API completeness

---

## [0.2.0] - 2025-10-07

### Added

- **Complete API Redesign** (Breaking Changes - Pre-1.0)

  - **New High-Level API**: Best-in-class ergonomics with byte-identical reproducibility
    - `ga.audit.from_model(model, X, y, protected_attributes)` - Primary API for notebook use
    - `ga.audit.from_predictions(y_true, y_pred, y_proba, protected_attributes)` - For pre-computed predictions
    - `ga.audit.from_config(config_path)` - For CI/CD reproducibility pipelines
    - All entry points return immutable `AuditResult` objects
  - **Lazy Module Loading (PEP 562)**: Import speed <200ms (was >2s)
    - Heavy dependencies (sklearn, xgboost, matplotlib) loaded on first use
    - Enables fast `--help` and interactive shell startup
  - **Immutable Result Objects**: Deep immutability for compliance audit integrity
    - Frozen dataclasses with read-only NumPy arrays
    - `MappingProxyType` for nested dictionaries
    - Pickle support via `__getstate__`/`__setstate__`
  - **Dual Access Patterns**: Dict + attribute styles for metrics
    - `result.performance.accuracy` or `result.performance["accuracy"]`
    - Tab completion in notebooks and IPython shells
  - **Deterministic Hashing**: SHA-256 with canonical JSON for result verification
    - `compute_result_id()` for byte-identical result comparison
    - `hash_data_for_manifest()` with dtype-aware hashing (categorical, datetime, string, boolean)
    - `result_id` enables reproducibility validation in CI/CD
  - **Rich Error Messages**: Machine-readable error codes with fix suggestions
    - 10 error classes: GAE1001-GAE4001
    - Each error includes: code, message, fix, docs URL
    - Example: `GAE1009_AUC_WITHOUT_PROBA` with actionable fix
  - **Metric Registry**: Metadata for all 13 metrics
    - `MetricSpec` dataclass with display name, description, tolerances, requirements
    - Performance metrics: accuracy, precision, recall, f1, roc_auc, pr_auc, brier_score, log_loss
    - Fairness metrics: demographic_parity_diff, equalized_odds_max_diff, equal_opportunity_diff
    - Calibration metrics: ece, mce
    - Stability metrics: monotonicity_violations
  - **API Stability Index**: Three-tier stability levels (Stable/Beta/Experimental)
    - Stable: `from_model()`, `from_predictions()`, `from_config()`, `AuditResult` core API
    - Beta: `equals()`, `summary()`, plot methods, tolerance policy
    - Experimental: `_repr_html_()`, `__hash__()`, internal canonicalization
  - **Tolerance Policy**: Default tolerances for metric comparisons
    - Standard (performance, fairness): `rtol=1e-5`, `atol=1e-8`
    - Calibration (looser): `rtol=1e-4`, `atol=1e-6`
    - Counts (exact): `rtol=0.0`, `atol=0.0`
  - **Comprehensive Documentation**:
    - API reference: [Entry Points](https://glassalpha.com/reference/api/audit-entry-points)
    - User guides: [Missing Data](https://glassalpha.com/guides/missing-data), [Probability Requirements](https://glassalpha.com/guides/probability-requirements)
    - Technical specs: [Stability Index](https://glassalpha.com/reference/api/stability-index), [Tolerance Policy](https://glassalpha.com/reference/api/tolerance-policy)
  - **Test Coverage**: 213 tests, 86% overall coverage, 90% for implemented code
    - 20 import/lazy loading tests
    - 50 immutability tests
    - 26 entry point signature tests
    - 56 determinism/hashing tests
    - 46 error handling tests
    - 19 edge case tests
  - **Files Created**:
    - Core API: `src/glassalpha/api/result.py`, `src/glassalpha/api/metrics.py`, `src/glassalpha/api/audit.py`
    - Hashing: `src/glassalpha/core/canonicalization.py`
    - Errors: `src/glassalpha/exceptions.py`
    - Registry: `src/glassalpha/metrics/registry.py`
  - **Note**: Entry point implementations (connecting to existing pipeline) deferred to follow-on work

- **Industry-Specific Compliance Guides** (P0 Feature - Distribution & Adoption)

  - **Banking & Credit**: SR 11-7, ECOA, FCRA compliance workflows
    - Credit scoring, loan pricing, fraud detection use cases
    - Policy gate configuration for banking regulations
    - SR 11-7 requirements mapped to CLI commands
    - Common audit failures and remediation strategies
    - Documentation: [Banking Compliance Guide](site/docs/compliance/banking-guide.md)
  - **Insurance**: NAIC Model Act #670, rate fairness, anti-discrimination
    - Pricing, underwriting, claims model workflows
    - Actuarial justification documentation
    - Rate parity analysis and proxy feature detection
    - State-specific considerations (CA Prop 103, NY Reg 187, CO SB 21-169)
    - Documentation: [Insurance Compliance Guide](site/docs/compliance/insurance-guide.md)
  - **Healthcare**: HIPAA, health equity mandates, clinical validation
    - Risk stratification, diagnostic support, resource allocation workflows
    - IRB and quality committee submission guidance
    - Health equity analysis (CMS quality measures, state mandates)
    - Dataset bias detection for healthcare disparities
    - Documentation: [Healthcare Compliance Guide](site/docs/compliance/healthcare-guide.md)
  - **Fraud Detection**: FCRA adverse action, FTC fairness guidelines
    - Transaction fraud, account takeover, application fraud workflows
    - False positive equity analysis
    - FCRA-compliant reason codes and adverse action notices
    - Consumer protection and recourse mechanisms
    - Documentation: [Fraud Detection Compliance Guide](site/docs/compliance/fraud-guide.md)
  - **Why critical**: Enables faster adoption by providing industry-specific entry points, demonstrates regulatory understanding, improves SEO and discoverability

- **Role-Based Workflow Guides** (P0 Feature - Distribution & Adoption)

  - **ML Engineer Workflow**: Implementation, CI/CD integration, debugging
    - Local development loop with fast iteration
    - CI/CD integration with GitHub Actions and pre-commit hooks
    - Notebook development with inline HTML display
    - Performance optimization strategies
    - Reproducibility debugging and troubleshooting
    - Documentation: [ML Engineer Workflow](site/docs/guides/ml-engineer-workflow.md)
  - **Compliance Officer Workflow**: Evidence packs, policy gates, regulator communication
    - Evidence pack generation for regulatory submissions
    - Policy-as-code gate establishment
    - Regulator response workflows
    - Communication templates for cover letters and findings
    - Audit trail and verification procedures
    - Documentation: [Compliance Officer Workflow](site/docs/guides/compliance-workflow.md)
  - **Model Validator Workflow**: Independent verification, challenge testing, red flags
    - Evidence pack integrity verification
    - Independent audit reproduction
    - Challenge testing (threshold sensitivity, distribution shifts, edge cases)
    - Red flag taxonomy (critical, warning, advisory)
    - Validation opinion letter templates
    - Documentation: [Model Validator Workflow](site/docs/guides/validator-workflow.md)
  - **Why critical**: Different personas need different workflows, builds trust through tailored guidance, enables enterprise adoption

- **Compliance Overview Landing Page** (P0 Feature - Navigation & UX)

  - **Role/industry picker**: Decision tree for quick navigation
  - **Common scenarios**: "I need SR 11-7 compliance" → Banking guide + workflow
  - **Regulatory framework coverage**: Summary of SR 11-7, NAIC, HIPAA, FCRA, ECOA
  - **Core capabilities overview**: Audit reports, evidence packs, policy gates, reproducibility
  - **Cross-links**: All industry guides, role workflows, examples
  - Documentation: [Compliance Overview](site/docs/compliance/index.md)
  - **Why critical**: Reduces time-to-value, helps users find relevant content quickly

- **Documentation Navigation Reorganization** (P0 Feature - UX & Discoverability)

  - **Guides section restructured** into three subsections:
    - **Industry Guides**: Banking, Insurance, Healthcare, Fraud Detection (ordered by potential customer base)
    - **Role Guides**: ML Engineers, Compliance Officers, Model Validators (ordered by user base size)
    - **How-To Guides**: Task-based guides (Reason Codes, Preprocessing, Recourse, etc.) ordered by usage likelihood
  - **SR 11-7 mapping enhanced** with cross-links to new banking and compliance guides
  - **Why critical**: Easier navigation, better SEO, clearer value proposition

- **E6.5: Demographic Shift Simulator** (P0 Feature - Distribution Robustness Testing)

  - **Post-stratification reweighting**: Simulates demographic distribution changes via sample weights
    - Tests model robustness under realistic population shifts
    - Adjusts group proportions by specified percentage points (e.g., +10pp, -5pp)
    - Mathematically sound reweighting: `weight[group] *= (p_target / p_original)`
    - Validates shifted proportion stays within [0.01, 0.99] bounds
  - **Before/after metrics comparison**: Recomputes all metrics with adjusted weights
    - **Fairness**: TPR, FPR, demographic parity, precision, recall
    - **Calibration**: ECE, Brier score (with bootstrap CIs)
    - **Performance**: Accuracy, F1, precision, recall
  - **Degradation detection**: Quantifies metric changes under demographic shifts
    - Reports absolute differences (percentage points)
    - Supports configurable degradation thresholds for CI gates
    - Gate statuses: PASS (no violations), WARNING (approaching threshold), FAIL (exceeds threshold)
  - **CLI integration**: `--check-shift` and `--fail-on-degradation` flags
    - Syntax: `--check-shift attribute:shift` (e.g., `gender:+0.1` for +10pp increase)
    - Multiple shifts supported: `--check-shift gender:+0.1 --check-shift age:-0.05`
    - Exit code 1 if degradation exceeds threshold (CI-friendly)
  - **JSON export**: Complete shift analysis results in sidecar file
    - Exports: shift_specification, baseline_metrics, shifted_metrics, degradation, gate_status, violations
    - File: `{output}.shift_analysis.json`
    - Programmatically parseable for dashboards and monitoring
  - **Deterministic execution**: Fully seeded for reproducibility
    - Seeded weight computation
    - Seeded metric recomputation
    - Byte-identical results across runs
  - **Validation**:
    - Binary attribute requirement (multi-class deferred to enterprise)
    - Feasibility checks (prevent impossible shifts)
    - Clear error messages with exact format requirements
  - Configuration: CLI-only feature (no YAML config required)
  - API: `run_shift_analysis()`, `ShiftAnalysisResult`, `ShiftSpecification`, `compute_shifted_weights()`
  - Test coverage: 30+ contract tests + German Credit integration (parsing, validation, reweighting, metrics, determinism)
  - Module: `glassalpha.metrics.shift.{reweighting, runner}`
  - Documentation: [Shift Testing Guide](site/docs/guides/shift-testing.md) with CI/CD integration examples
  - **Why critical**: Regulatory stress testing (EU AI Act), production readiness validation, CI/CD deployment gates

- **E8: SR 11-7 Compliance Mapping Document** (P1 Feature - Banking Regulatory Guidance)

  - **Comprehensive clause-to-artifact mapping**: Maps all SR 11-7 sections to specific GlassAlpha features
    - Section III.A (Documentation, Testing, Monitoring) → Audit PDF, Shift Testing, CI/CD
    - Section III.B (Validation, Sensitivity, Outcomes) → Calibration, Perturbations, Recourse
    - Section III.C (Assumptions, Data Quality, Limitations) → Manifests, Dataset Bias, Model Card
    - Section IV (Independence, Evidence) → Reproducibility, Evidence Packs
    - Section V (Fairness) → Group, Intersectional, Individual Fairness
  - **Examiner Q&A examples**: Ready-to-use responses for common audit questions
  - **Citation templates**: How to reference GlassAlpha artifacts in compliance documentation
  - **Quick reference table**: One-page summary of SR 11-7 coverage
  - **Validation workflows**: Commands demonstrating reproducibility and independence
  - **Evidence pack structure**: Complete audit bundle for regulatory submission
  - **Sample size guidance**: Statistical power requirements per protected group
  - **Monitoring integration**: CI/CD examples for ongoing model risk management
  - Documentation: [SR 11-7 Mapping](site/docs/compliance/sr-11-7-mapping.md)
  - **Why critical**: Enables banking institutions to demonstrate SR 11-7 compliance, supports regulatory audits

- **E9: README Positioning Refresh** (P1 Feature - Distribution & Adoption)

  - **Pain-first messaging**: Opens with "Ever tried explaining your ML model to a regulator?"
  - **Policy-as-code emphasis**: Shows YAML-based compliance rules, not dashboards
  - **Feature highlights**: Comprehensive listing of completed E-series features
    - Compliance & Fairness: E5, E5.1, E10, E11, E12
    - Explainability & Outcomes: E2, E2.5
    - Robustness & Stability: E6, E6+, E6.5, E10+
    - Regulatory Compliance: SR 11-7, Evidence Packs, Reproducibility
  - **Statistical rigor positioning**: "95% confidence intervals on everything"
  - **Byte-identical reproducibility**: SHA256-verified evidence packs
  - **CI/CD deployment gates**: Shift testing examples with `--fail-on-degradation`
  - **Three-part differentiation**: Policy-as-code, reproducibility, statistical confidence
  - **Why critical**: Improves conversion from repo visitors to users, positions against dashboards/SaaS tools

- **1.2C: QuickStart CLI Generator** (P0 Feature - Onboarding & Adoption)

  - **Complete project scaffolding**: `glassalpha quickstart` generates ready-to-run audit projects
    - Directory structure: data/, models/, reports/, configs/
    - Audit configuration file (audit_config.yaml) with sensible defaults
    - Example run script (run_audit.py) demonstrating programmatic API
    - Project README with next steps and advanced usage examples
    - .gitignore tailored for GlassAlpha projects
  - **Interactive mode**: Guided prompts for dataset and model selection
    - Dataset choices: German Credit (1K samples), Adult Income (48K samples)
    - Model choices: XGBoost (recommended), LightGBM (fast), Logistic Regression (simple)
    - Customizable project name
  - **Non-interactive mode**: Command-line flags for CI/CD automation
    - `--dataset`, `--model`, `--output` flags
    - `--no-interactive` for scripted project generation
  - **Time-to-first-audit**: <60 seconds from install to generated audit report
    - `cd my-audit-project && python run_audit.py`
    - No manual config editing required for built-in datasets
  - **Documentation included**: Every generated project includes README with:
    - Quick start (3 commands to first audit)
    - CI/CD integration examples
    - Custom data setup instructions
    - Links to user guides and documentation
  - CLI: `glassalpha quickstart` (interactive), `glassalpha quickstart --dataset german_credit --model xgboost --no-interactive`
  - **Why critical**: Eliminates onboarding friction, enables immediate value demonstration

- **E6+: Adversarial Perturbation Sweeps** (P2 Feature - Robustness Verification)

  - **Epsilon-perturbation stability testing**: Validates model robustness under small input changes
    - Perturbs non-protected features by ε ∈ {0.01, 0.05, 0.1} (1%, 5%, 10% Gaussian noise)
    - Measures max prediction delta (L∞ norm) across all samples
    - Reports robustness score = max delta across epsilon values
  - **Protected feature exclusion**: Never perturbs gender, race, or other sensitive attributes
    - Prevents synthetic bias introduction during robustness testing
    - Validates that all features marked protected are excluded
  - **Gate logic**: Automatic PASS/FAIL/WARNING based on configurable threshold
    - PASS: max_delta < threshold
    - WARNING: threshold ≤ max_delta < 1.5 × threshold
    - FAIL: max_delta ≥ 1.5 × threshold
    - Default threshold: 0.15 (15% max prediction change)
  - **Deterministic perturbations**: Fully seeded for byte-identical reproducibility
    - Uses seeded Gaussian noise generation
    - Stable sort for epsilon values
  - **JSON export**: All results serializable for programmatic access
    - Exports: robustness_score, max_delta, per_epsilon_deltas, gate_status, threshold
  - **Conditional execution**: Only runs when `metrics.stability.enabled = true`
  - **Automatic integration**: Runs after fairness/calibration in audit pipeline
  - Configuration: `metrics.stability.enabled`, `metrics.stability.epsilon_values`, `metrics.stability.threshold`
  - CLI: Perturbation results included when stability metrics enabled
  - API: `run_perturbation_sweep()`, `PerturbationResult`
  - Test coverage: 22 contract tests + German Credit integration (determinism, epsilon validation, gates, protected features)
  - Module: `glassalpha.metrics.stability.perturbation`
  - **Why critical**: Emerging regulator demand for robustness proofs (EU AI Act, NIST AI RMF), prevents adversarial failures

- **E12: Dataset-Level Bias Audit** (P1 Feature - Root-Cause Bias Detection)

  - **Proxy Correlation Detection**: Identifies non-protected features correlating with protected attributes
    - Multi-level severity system: ERROR (|r|>0.5), WARNING (0.3<|r|≤0.5), INFO (|r|≤0.3)
    - Pearson correlation for continuous-continuous pairs
    - Point-biserial for continuous-categorical pairs
    - Cramér's V for categorical-categorical pairs
    - Flags potential indirect discrimination pathways
  - **Distribution Drift Analysis**: Detects feature distribution shifts between train and test
    - Kolmogorov-Smirnov test for continuous features
    - Chi-square test for categorical features
    - Identifies data quality issues and distribution mismatch
  - **Statistical Power for Sampling Bias**: Power calculations for detecting undersampling
    - Severity levels: ERROR (power<0.5), WARNING (0.5≤power<0.7), OK (power≥0.7)
    - Detects insufficient sample sizes before model training
    - Prevents false confidence in fairness metrics
  - **Continuous Attribute Binning**: Configurable binning strategies for age and other continuous protected attributes
    - Domain-specific bins (age: [18, 25, 35, 50, 65, 100])
    - Custom bins (user-specified)
    - Equal-width and equal-frequency strategies
    - Binning recorded in manifest for reproducibility
  - **Train/Test Split Imbalance Detection**: Chi-square tests for protected group distribution differences
    - Flags biased data splitting (e.g., gender representation differs between splits)
    - Prevents evaluation bias from imbalanced splits
  - **Automatic Integration**: All 5 checks run before model evaluation in audit pipeline
  - **JSON Export**: All results serializable for programmatic access
  - **Deterministic**: Fully seeded for byte-identical reproducibility
  - CLI: Dataset bias metrics included in standard audit output
  - API: `compute_dataset_bias_metrics()`, `compute_proxy_correlations()`, `compute_distribution_drift()`, `compute_sampling_bias_power()`, `detect_split_imbalance()`, `bin_continuous_attribute()`
  - Test coverage: 27 contract tests + 6 integration tests with German Credit dataset
  - Module: `glassalpha.metrics.fairness.dataset`
  - **Why critical**: Catches bias at the source (most unfairness originates in data, not models)

- **E5.1: Basic Intersectional Fairness** (P1 Feature - Sophistication Signal)

  - **Two-way intersectional analysis**: Detects bias at intersections of protected attributes (e.g., gender×race, age×income)
  - **Cartesian product group creation**: Automatically generates all intersectional groups from attribute combinations
  - **Full fairness metrics for each intersectional group**: TPR, FPR, precision, recall, selection rate computed per intersection
  - **Disparity metrics**: Max-min differences and ratios across intersectional groups
  - **Sample size warnings**: Reuses E10 infrastructure (n<10 ERROR, 10≤n<30 WARNING, n≥30 OK)
  - **Bootstrap confidence intervals**: 95% CIs for all intersectional metrics using E10 bootstrap infrastructure
  - **Statistical power analysis**: Power calculations for detecting disparity in each intersectional group
  - **Deterministic computation**: Fully seeded for byte-identical reproducibility
  - **Automatic integration**: Runs alongside group fairness when `data.intersections` specified in config
  - **JSON export**: All intersectional results serializable with nested structure
  - Configuration: `data.intersections: ["gender*race", "age*income"]` in YAML
  - CLI: Intersectional metrics included when intersections configured
  - API: `compute_intersectional_fairness()`, `create_intersectional_groups()`, `parse_intersection_spec()`
  - Test coverage: 23 tests covering parsing, group creation, metrics, CIs, sample warnings, determinism
  - Module: `glassalpha.metrics.fairness.intersectional`
  - Example: German Credit config updated with age×foreign_worker and gender×age intersections

- **E11: Individual Fairness Metrics** (P0 Feature - Legal Risk Coverage)

  - **Consistency Score**: Lipschitz-like metric measuring prediction stability for similar individuals
    - Configurable distance metrics (Euclidean, Mahalanobis)
    - Similarity threshold based on percentile of pairwise distances (default 90th)
    - Reports max and mean prediction differences for similar pairs
  - **Matched Pairs Report**: Identifies individuals with similar features but different predictions
    - Flags potential disparate treatment cases
    - Exports matched pairs with feature distance and prediction difference
    - Checks if protected attributes differ between matched pairs
  - **Counterfactual Flip Test**: Tests if protected attribute changes affect predictions
    - Detects disparate treatment at individual level
    - Computes disparate treatment rate across dataset
    - Supports multi-class protected attributes
  - **Automatic Integration**: Runs alongside group fairness metrics in audit pipeline
  - **JSON Export**: All results serializable for programmatic access and reporting
  - **Deterministic**: Fully seeded for byte-identical reproducibility
  - **Performance**: Pairwise distance computation optimized with vectorization
  - CLI: Individual fairness included in standard audit output
  - API: `IndividualFairnessMetrics`, `compute_consistency_score()`, `find_matched_pairs()`, `counterfactual_flip_test()`
  - Test coverage: 20+ contract tests covering determinism, edge cases, and integration
  - Module: `glassalpha.metrics.fairness.individual`

- **E10+: Calibration Confidence Intervals** (P1 Feature - Statistical Rigor for Calibration)

  - **Bootstrap CIs for ECE and Brier score**: 95% confidence intervals using deterministic bootstrap
    - Reuses E10's bootstrap infrastructure for consistency
    - Percentile method for CI computation (default: 1000 bootstrap samples)
    - Standard error calculation for uncertainty quantification
  - **Bin-wise CIs for calibration curve**: Error bars for observed frequency in each calibration bin
    - Enables visualization of uncertainty in calibration curves
    - Skips bins with <10 samples (insufficient for reliable bootstrap)
    - Exports bin-wise lower/upper bounds for plotting
  - **Backward compatible API**: Legacy `assess_calibration_quality()` still returns dict without CIs
    - New parameter: `compute_confidence_intervals=True` enables CIs
    - Returns `CalibrationResult` dataclass with optional CI fields
  - **Deterministic computation**: Fully seeded for byte-identical reproducibility
  - **JSON export**: All CIs serializable with `to_dict()` for programmatic access
  - **Automatic integration**: Ready for audit pipeline integration (deferred to follow-on work)
  - CLI: Calibration CIs available via API (PDF display deferred)
  - API: `compute_calibration_with_ci()`, `compute_bin_wise_ci()`, `assess_calibration_quality(compute_confidence_intervals=True)`
  - Module: `glassalpha.metrics.calibration.confidence`, `glassalpha.metrics.calibration.quality`
  - Test coverage: 25+ contract tests + German Credit integration tests
  - **Why P1**: Completes statistical rigor story (E10 covered fairness, E10+ covers calibration)

- **E10: Statistical Confidence & Uncertainty for Fairness Metrics** (P0 Feature)
  - Bootstrap confidence intervals for all fairness metrics (TPR, FPR, precision, recall, demographic parity)
  - Deterministic bootstrap with seeded random sampling for byte-identical reproducibility
  - Sample size adequacy checks (n<10 ERROR, 10≤n<30 WARNING, n≥30 OK)
  - Statistical power calculations for detecting disparity
  - Automatic integration with fairness runner and audit pipeline
  - Confidence interval data exported in JSON format for programmatic access
  - CLI: All fairness metrics now include 95% confidence intervals by default
  - API: `run_fairness_metrics()` accepts `compute_confidence_intervals`, `n_bootstrap`, `confidence_level`, `seed`
  - Test coverage: 21 comprehensive tests validating determinism, accuracy, and edge cases

### Changed

- **Config Schema**: Added `data.intersections` field for E5.1 intersectional fairness analysis
  - Validates intersection format: must be `"attr1*attr2"` for two-way intersections
  - Normalizes to lowercase and strips whitespace
  - Example: `intersections: ["gender*race", "age_years*foreign_worker"]`
- **Fairness Metrics Runner**: Enhanced to compute bootstrap CIs, sample size warnings, power analysis, and intersectional metrics
  - New parameter: `intersections` list for specifying intersectional analysis
  - Automatically computes intersectional fairness when intersections specified
  - Results nested under `intersectional` key in output
- **Audit Pipeline**:
  - Now passes seed to fairness runner for deterministic confidence intervals
  - Now passes intersections config to fairness runner for E5.1 analysis
  - Now computes E11 individual fairness metrics alongside group fairness
  - Passes full feature DataFrame to fairness metrics for individual-level analysis
- **AuditResults**: Fairness analysis now includes `sample_size_warnings`, `statistical_power`, `{metric}_ci`, and `individual_fairness` keys
- **`_compute_fairness_metrics()`**: Signature updated to accept full feature DataFrame for individual fairness computation

### Fixed

- None

### Performance

- Bootstrap CIs add ~2-3 seconds per fairness metric (with n_bootstrap=1000, n=200)
- No memory overhead (bootstrap samples not retained)
- Determinism has zero performance cost (uses existing seeding infrastructure)

### Security

- None

### Deprecated

- None

### Removed

- None

## Previous Releases

See Git history for previous changes.
