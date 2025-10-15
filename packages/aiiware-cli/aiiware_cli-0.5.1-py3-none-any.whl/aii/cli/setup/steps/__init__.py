"""
Wizard step implementations.

Each step in the setup wizard is implemented as a subclass of WizardStep.
"""

from aii.cli.setup.steps.base import WizardStep, StepResult

__all__ = ["WizardStep", "StepResult"]
