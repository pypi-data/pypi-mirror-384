"""
Setup wizard for first-run configuration.

This module provides an interactive setup wizard that guides users through
configuring AII for first use, including LLM provider selection, API key
acquisition, and configuration persistence.
"""

from aii.cli.setup.wizard import SetupWizard, WizardContext

__all__ = ["SetupWizard", "WizardContext"]
