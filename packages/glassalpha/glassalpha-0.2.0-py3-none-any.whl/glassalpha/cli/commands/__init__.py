"""CLI commands for GlassAlpha.

Commands organized by functional area (Phase 3 refactor complete):
- audit.py: Core audit command and shift analysis
- explain.py: Explanation commands (reasons, recourse)
- config_cmds.py: Configuration commands (validate, config_list, config_template, config_cheat)
- system.py: System commands (doctor, list_components, docs)
- evidence.py: Evidence pack commands (export, verify)

ARCHITECTURE NOTE: Exception handling in CLI commands intentionally
suppresses Python tracebacks (using 'from None') to provide clean
user-facing error messages. This is the correct pattern for CLI tools.
"""

# Core commands
from .audit import audit

# Note: cache is NOT imported here to keep CLI startup fast (<300ms)
# It's imported directly in main.py only when needed
from .config_cmds import (
    config_cheat_cmd,
    config_list_cmd,
    config_template_cmd,
    validate,
)
from .evidence import export_evidence_pack, verify_evidence_pack
from .explain import reasons, recourse
from .publish_check import publish_check
from .system import docs, doctor, list_components_cmd

__all__ = [
    "audit",
    # "cache",  # Excluded to avoid slow imports
    "config_cheat_cmd",
    "config_list_cmd",
    "config_template_cmd",
    "docs",
    "doctor",
    "export_evidence_pack",
    "list_components_cmd",
    "publish_check",
    "reasons",
    "recourse",
    "validate",
    "verify_evidence_pack",
]
