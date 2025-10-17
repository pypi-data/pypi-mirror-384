from __future__ import annotations

from importlib import resources

from module_qc_analysis_tools._version import __version__

data = resources.files("module_qc_analysis_tools") / "data"

__all__ = ("__version__", "data")
