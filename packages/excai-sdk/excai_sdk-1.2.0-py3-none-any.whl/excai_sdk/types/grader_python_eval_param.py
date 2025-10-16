# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .fine_tuning.alpha.grader_python_script_param import GraderPythonScriptParam

__all__ = ["GraderPythonEvalParam"]


class GraderPythonEvalParam(GraderPythonScriptParam, total=False):
    pass_threshold: float
    """The threshold for the score."""
